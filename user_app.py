"""Clean user-facing AHP + TOPSIS workflow. Catalogue and score details stay in admin_app.py."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from core.catalogue import load_databases
from core.application_scoring import apply_application_scores
from core.filtering import filter_databases
from core.ahp import get_ahp_details
from core.recommendation import recommend_databases
from core.topsis_explainability import explain_topsis
from core.ranking_reliability import evaluate_ranking_reliability

ROOT = Path(__file__).resolve().parent
with open(ROOT / "data" / "applications.json", encoding="utf-8") as file:
    APPLICATIONS = json.load(file)

CRITERION_LABELS = {
    "free_self_hosted_availability": "Free self-hosted availability",
    "scalability": "Scalability",
    "high_availability_support": "High availability support",
    "security_features": "Security features",
    "query_flexibility": "Query flexibility",
    "transaction_support": "Transaction support",
    "document_model_support": "Document model support",
    "schema_flexibility": "Schema flexibility",
    "indexing_aggregation_support": "Indexing and aggregation support",
    "read_write_operation_support": "Read/write operation support",
    "persistence": "Persistence",
    "eviction_policy_support": "Eviction policy support",
    "consistency_options": "Consistency options",
    "replication_support": "Replication support",
}

SCALE = {
    "2 — Slightly more important": 2,
    "3 — Moderately more important": 3,
    "4 — Between moderate and strong": 4,
    "5 — Strongly more important": 5,
    "6 — Between strong and very strong": 6,
    "7 — Very strongly more important": 7,
    "8 — Between very strong and extreme": 8,
    "9 — Extremely more important": 9,
}


def _reset_for_application(app_id):
    for key in ("user_ahp", "user_result"):
        st.session_state.pop(key, None)
    # Application has been selected; move directly to the criteria step.
    st.session_state["user_step"] = 2
    st.session_state["user_application_id"] = app_id
    st.session_state["user_selected_criteria"] = next(
        app["default_criteria"] for app in APPLICATIONS if app["id"] == app_id
    ).copy()


def render_user_page():
    st.title("Database Recommendation")
    st.caption("Choose your application, select evaluation criteria, and compare their importance.")

    step = st.session_state.get("user_step", 1)
    st.progress(step / 4, text=f"Step {step} of 4")

    # Step 1: Application selection and mandatory filtering.
    if step == 1:
        st.subheader("1. Select your application")
        app_names = [app["name"] for app in APPLICATIONS]
        current_id = st.session_state.get("user_application_id")
        current_index = next(
            (i for i, app in enumerate(APPLICATIONS) if app["id"] == current_id), 0
        )
        selected_name = st.selectbox(
            "What are you building?", app_names, index=current_index,
            key="user_application_choice",
        )
        application = next(app for app in APPLICATIONS if app["name"] == selected_name)
        st.write(application["description"])
        if st.button("Continue", type="primary"):
            _reset_for_application(application["id"])
            st.rerun()
        return

    application = next(
        app for app in APPLICATIONS
        if app["id"] == st.session_state.get("user_application_id")
    )
    databases = apply_application_scores(load_databases(), application["id"])
    candidates, excluded = filter_databases(
        databases, application.get("mandatory_requirements", [])
    )
    eligible = [db for db in candidates if db.get("_filter_status") == "eligible"]

    if not eligible:
        st.error("No verified eligible databases are available for this application.")
        if st.button("Back to application selection"):
            st.session_state["user_step"] = 1
            st.rerun()
        return

    criteria = st.session_state.get(
        "user_selected_criteria", application["default_criteria"].copy()
    )

    # Step 2: Criteria selection. Database catalogue scores remain hidden.
    if step == 2:
        st.subheader("2. Choose evaluation criteria")
        st.write("Select the factors that matter for your application.")
        selected = []
        cols = st.columns(2)
        for index, criterion in enumerate(application["default_criteria"]):
            label = CRITERION_LABELS.get(
                criterion, criterion.replace("_", " ").title()
            )
            with cols[index % 2]:
                if st.checkbox(
                    label, value=criterion in criteria,
                    key=f"user_criterion_{application['id']}_{criterion}",
                ):
                    selected.append(criterion)
        if st.button("Continue to importance comparisons", type="primary"):
            if not selected:
                st.error("Select at least one criterion.")
            else:
                missing = [
                    criterion for criterion in selected
                    if any(db.get("scores", {}).get(criterion) is None for db in eligible)
                ]
                if missing:
                    st.error(
                        "The system does not have complete scoring data for: "
                        + ", ".join(CRITERION_LABELS.get(c, c) for c in missing)
                        + ". Please contact the administrator."
                    )
                else:
                    st.session_state["user_selected_criteria"] = selected
                    st.session_state.pop("user_ahp", None)
                    st.session_state.pop("user_result", None)
                    st.session_state["user_step"] = 3
                    st.rerun()
        if st.button("Back"):
            st.session_state["user_step"] = 1
            st.rerun()
        return

    criteria = st.session_state["user_selected_criteria"]

    # Step 3: Pairwise comparisons using the existing AHP implementation.
    if step == 3:
        st.subheader("3. Compare the importance of your criteria")
        st.caption(
            "For each pair, choose which criterion matters more. "
            "Choose equal importance when both matter equally."
        )
        matrix = np.ones((len(criteria), len(criteria)), dtype=float)
        with st.form("user_pairwise_form"):
            for i in range(len(criteria)):
                for j in range(i + 1, len(criteria)):
                    a, b = criteria[i], criteria[j]
                    a_label = CRITERION_LABELS.get(a, a.replace("_", " ").title())
                    b_label = CRITERION_LABELS.get(b, b.replace("_", " ").title())
                    st.markdown(f"**{a_label} compared with {b_label}**")
                    direction = st.radio(
                        "Which is more important?",
                        [a_label, "Equally important", b_label],
                        horizontal=True, key=f"user_dir_{application['id']}_{i}_{j}",
                    )
                    degree = st.selectbox(
                        "How much more important?",
                        list(SCALE.keys()),
                        key=f"user_degree_{application['id']}_{i}_{j}",
                    )
                    value = 1.0 if direction == "Equally important" else float(SCALE[degree])
                    if direction == b_label:
                        value = 1.0 / value
                    matrix[i, j] = value
                    matrix[j, i] = 1.0 / value
            submitted = st.form_submit_button("Calculate importance", type="primary")

        if submitted:
            try:
                details = get_ahp_details(matrix)
                st.session_state["user_ahp"] = {
                    "matrix": matrix.tolist(),
                    "weights": details["weights"].tolist(),
                    "cr": details["cr"],
                    "consistent": details["is_consistent"],
                    "criteria": criteria,
                }
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

        ahp = st.session_state.get("user_ahp")
        if ahp and ahp.get("criteria") == criteria:
            st.markdown("**Your criteria importance**")
            weights_df = pd.DataFrame({
                "Criterion": [CRITERION_LABELS.get(c, c) for c in criteria],
                "Weight": ahp["weights"],
                "Importance": [f"{w * 100:.2f}%" for w in ahp["weights"]],
            })
            st.dataframe(weights_df, hide_index=True, use_container_width=True)
            st.metric("Consistency ratio", f"{ahp['cr']:.4f}")
            if ahp["consistent"]:
                st.success("Your comparisons are consistent.")
                if st.button("Generate database ranking", type="primary"):
                    try:
                        matrix_scores = [
                            [db["scores"][criterion] for criterion in criteria]
                            for db in eligible
                        ]
                        result = recommend_databases(
                            pairwise_matrix=ahp["matrix"],
                            decision_matrix=matrix_scores,
                            criteria_types=["benefit"] * len(criteria),
                            alternatives=[db["name"] for db in eligible],
                            config_name=f"user_{application['id']}_configuration",
                            preferences={
                                "application_id": application["id"],
                                "application_name": application["name"],
                                "criteria": criteria,
                                "criteria_types": ["benefit"] * len(criteria),
                                "eligible_databases": [db["name"] for db in eligible],
                            },
                        )
                        st.session_state["user_result"] = result
                        st.session_state["user_step"] = 4
                        st.rerun()
                    except (ValueError, TypeError) as exc:
                        st.error(str(exc))
            else:
                st.warning("Your comparisons are inconsistent. Please review your choices and calculate again.")
        if st.button("Back to criteria"):
            st.session_state["user_step"] = 2
            st.rerun()
        return

    # Step 4: Separate results screen. No catalogue score table is exposed.
    if step == 4:
        st.subheader("4. Recommended databases")
        result = st.session_state.get("user_result")
        if not result:
            st.warning("No ranking is available yet. Please complete the previous steps.")
            if st.button("Restart"):
                st.session_state["user_step"] = 1
                st.rerun()
            return

        rankings = result["rankings"]
        ranking_df = pd.DataFrame(rankings)
        ranking_df["score"] = ranking_df["score"].map(lambda x: f"{x:.4f}")
        st.dataframe(ranking_df, hide_index=True, use_container_width=True)
        st.subheader("TOPSIS score comparison")
        chart_df = pd.DataFrame(result["rankings"]).set_index("database")[["score"]]
        st.bar_chart(chart_df)
        winner = result["rankings"][0]
        st.success(
            f"Recommended database: {winner['database']} "
            f"(TOPSIS score: {winner['score']:.4f})"
        )
        st.caption(
            "The ranking is based on your selected application, criteria, "
            "pairwise comparisons, and the system's evaluated database scores."
        )

        # Explainability: show why the top-ranked database performed well.
        valid_ahp = bool(
            st.session_state.get("user_ahp")
            and st.session_state["user_ahp"].get("criteria") == criteria
        )
        if len(rankings) > 1 and valid_ahp:
            ahp = st.session_state["user_ahp"]
            decision_matrix = [
                [db["scores"][criterion] for criterion in criteria]
                for db in eligible
            ]
            database_names = [db["name"] for db in eligible]
            criteria_types = ["benefit"] * len(criteria)

            try:
                explanations = explain_topsis(
                    decision_matrix=decision_matrix,
                    weights=ahp["weights"],
                    criteria_types=criteria_types,
                    criteria_names=criteria,
                    alternatives=database_names,
                )
                winner_explanation = next(
                    item for item in explanations
                    if item["database"] == winner["database"]
                )
                st.markdown("### Why is this database recommended?")
                strong = winner_explanation["strong_criteria"]
                weak = winner_explanation["weak_criteria"]
                if strong:
                    st.write("**What it does well:** " + ", ".join(
                        item.replace("_", " ") for item in strong
                    ) + ".")
                if weak:
                    st.write("**Where other databases may do better:** " + ", ".join(
                        item.replace("_", " ") for item in weak
                    ) + ".")
                with st.expander("View detailed explanation"):
                    st.write(f"**TOPSIS score:** {winner_explanation['topsis_score']:.4f}")
                    st.write(
                        "**Distance from the ideal database:** "
                        f"{winner_explanation['distance_from_ideal']:.4f}"
                    )
                    st.write(
                        "**Distance from the worst reference:** "
                        f"{winner_explanation['distance_from_worst']:.4f}"
                    )
                    detail_rows = []
                    for criterion, detail in winner_explanation["criteria"].items():
                        detail_rows.append({
                            "Criterion": criterion.replace("_", " ").title(),
                            "Database score": detail["raw_score"],
                            "Importance (%)": detail["weight_percent"],
                            "Comparison": detail["performance_description"],
                        })
                    st.markdown("**How each criterion was used**")
                    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

                    sensitivity_rows = []
                    for criterion, detail in winner_explanation["sensitivity"].items():
                        change = detail["rank_change"]
                        movement = (
                            f"Improved by {change} place(s)" if change > 0
                            else f"Fell by {abs(change)} place(s)" if change < 0
                            else "No rank change"
                        )
                        sensitivity_rows.append({
                            "Criterion": criterion.replace("_", " ").title(),
                            "Original rank": detail["original_rank"],
                            "New rank": detail["new_rank"],
                            "New score": detail["new_score"],
                            "Result": movement,
                        })
                    st.markdown("**What if criterion importance changes?**")
                    st.dataframe(pd.DataFrame(sensitivity_rows), use_container_width=True, hide_index=True)
                    st.caption(
                        "Sensitivity analysis increases one criterion's weight by 20% "
                        "at a time and recalculates TOPSIS. It does not change your saved ranking."
                    )
            except (ValueError, TypeError, KeyError, StopIteration) as error:
                st.warning(f"The explanation could not be generated: {error}")
        elif len(rankings) > 1:
            st.info("Complete the criteria importance comparisons to view the recommendation explanation.")

        # Ranking reliability testing: hypothetical score perturbation scenarios.
        if len(rankings) > 1:
            with st.expander("Advanced: test ranking reliability"):
                st.write(
                    "Check whether the recommendation changes when database "
                    "scores are tested at different values."
                )
                st.caption(
                    "The test uses low (1), middle (3), and high (5) scores. "
                    "These are hypothetical scenarios, not predictions."
                )
                if st.button("Run reliability test", key="user_run_ranking_reliability"):
                    if not valid_ahp:
                        st.warning("Complete the criteria importance comparisons first.")
                    else:
                        try:
                            reliability = evaluate_ranking_reliability(
                                decision_matrix=decision_matrix,
                                weights=st.session_state["user_ahp"]["weights"],
                                criteria_types=criteria_types,
                                alternatives=database_names,
                                criteria_names=criteria,
                            )
                            st.markdown("**Test results**")
                            c1, c2, c3 = st.columns(3)
                            c1.metric(
                                "Ranking stayed the same",
                                f"{reliability['ranking_order_stability_percent']:.1f}%",
                            )
                            c2.metric(
                                "Top choice stayed the same",
                                f"{reliability['top_recommendation_retention_percent']:.1f}%",
                            )
                            c3.metric(
                                "Average rank movement",
                                f"{reliability['average_absolute_rank_movement']:.2f}",
                            )
                            st.write("**Original ranking:** " + " → ".join(reliability["baseline_order"]))
                            with st.expander("View test scenarios"):
                                scenario_df = pd.DataFrame(reliability["scenarios"]).rename(columns={
                                    "database_tested": "Database tested",
                                    "criterion_tested": "Criterion tested",
                                    "scenario": "Test",
                                    "original_score": "Original score",
                                    "scenario_score": "Test score",
                                    "new_winner": "New top choice",
                                    "winner_retained": "Top choice unchanged",
                                    "ranking_order_unchanged": "Full ranking unchanged",
                                    "new_ranking": "New ranking",
                                }).drop(columns=["original_winner", "rank_changes"], errors="ignore")
                                st.dataframe(scenario_df, use_container_width=True, hide_index=True)
                            st.caption(reliability["interpretation"])
                        except (ValueError, TypeError, KeyError) as error:
                            st.error(f"Reliability testing failed: {error}")
        with st.expander("View your criteria importance"):
            st.dataframe(pd.DataFrame({
                "Criterion": [CRITERION_LABELS.get(c, c) for c in criteria],
                "Weight": result["criteria_weights"],
                "Importance": [f"{w * 100:.2f}%" for w in result["criteria_weights"]],
            }), hide_index=True, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start a new selection", type="primary"):
                st.session_state["user_step"] = 1
                st.session_state.pop("user_result", None)
                st.session_state.pop("user_ahp", None)
                st.rerun()
        with col2:
            if st.button("Change criteria or comparisons"):
                st.session_state["user_step"] = 2
                st.session_state.pop("user_result", None)
                st.rerun()
