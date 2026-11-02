from core.ranking_reliability import evaluate_ranking_reliability

from core.topsis_explainability import explain_topsis
import json
from pathlib import Path
from core.application_scoring import apply_application_scores

import numpy as np
import pandas as pd
import streamlit as st

from core.catalogue import load_databases
from core.filtering import filter_databases
from core.explanations import explain_database
from core.ahp import get_ahp_details
from core.recommendation import recommend_databases
from storage.database import get_configuration_history, get_configuration

from core.topsis_explainability import explain_topsis
def find_inconsistent_triads(criteria, matrix, top_n=5):
    """Find groups of three criteria with conflicting judgments."""
    matrix = np.asarray(matrix, dtype=float)
    triads = []

    for i in range(len(criteria)):
        for j in range(i + 1, len(criteria)):
            for k in range(j + 1, len(criteria)):

                # Compare the direct judgment with the implied judgment.
                direct = matrix[i, k]
                implied = matrix[i, j] * matrix[j, k]

                discrepancy = abs(np.log(direct / implied))

                triads.append({
                    "Criteria A": criteria[i],
                    "Criteria B": criteria[j],
                    "Criteria C": criteria[k],
                    "A vs B": matrix[i, j],
                    "B vs C": matrix[j, k],
                    "A vs C": matrix[i, k],
                    "Discrepancy": discrepancy,
                })

    return sorted(
        triads,
        key=lambda item: item["Discrepancy"],
        reverse=True,
    )[:top_n]
ROOT = Path(__file__).resolve().parent


with open(ROOT / "data" / "applications.json", encoding="utf-8") as file:
    applications = json.load(file)

st.set_page_config(
    page_title="Database Recommendation System",
    page_icon="🗄️",
    layout="wide",
)

st.title("Database Selection & Recommendation System")
st.caption("Mandatory filtering + AHP weighting + TOPSIS ranking")

# --------------------------------------------------
# 1. Select application and filter databases
# --------------------------------------------------

databases = load_databases()

application_name = st.selectbox(
    "Choose your application type",
    [application["name"] for application in applications],
)
application = next(
    item for item in applications if item["name"] == application_name
)
databases = apply_application_scores(
    databases,
    application["id"]
)

st.write(application["description"])


candidates, excluded = filter_databases(
    databases,
    application["mandatory_requirements"],
)

verification_needed = [
    db for db in candidates
    if db.get("_filter_status") == "needs_verification"
]

eligible = [
    db for db in candidates
    if db.get("_filter_status") == "eligible"
]



left, middle, right = st.columns(3)
left.metric("Verified eligible", len(eligible))
middle.metric("Needs verification", len(verification_needed))
right.metric("Excluded", len(excluded))

if verification_needed:
    with st.expander("View databases needing verification"):
        for database in verification_needed:
            requirements = database.get(
                "_verification_requirements", []
            )
            st.write(
                f"**{database['name']}** — Verify: "
                + ", ".join(requirements)
            )


# --------------------------------------------------
# 2. Catalogue and explanations
# --------------------------------------------------

if eligible:
    rows = []

    for database in eligible:
        row = {
            "Database": database["name"],
            "Type": database["type"],
            "Status": database.get("_filter_status", "eligible"),
            "Needs verification": ", ".join(
                database.get("_verification_requirements", [])
            ) or "None",
        }
        row.update({
            key.replace("_", " ").title(): value
            for key, value in database.get("scores", {}).items()
        })
        rows.append(row)

    st.subheader("Eligible database catalogue")
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    chosen = st.selectbox(
        "Inspect a database",
        [database["name"] for database in eligible],
    )
    selected = next(
        database for database in eligible
        if database["name"] == chosen
    )
    explanation = explain_database(selected)

    st.subheader(f"Explanation: {chosen}")
    st.write("**Strengths**")
    st.write(", ".join(explanation["strengths"]) or "None identified")

    st.write("**Limitations**")
    st.write(", ".join(explanation["limitations"]) or "None identified")

    st.write("**Unknown criteria**")
    st.write(", ".join(explanation["unknown_criteria"]) or "None")

    st.info(explanation["summary"])

    if explanation["trade_offs"]:
        st.write("**Trade-offs**")
        for trade_off in explanation["trade_offs"]:
            st.write(f"- {trade_off}")

# --------------------------------------------------
# 3. AHP criteria weighting
# --------------------------------------------------

st.header("AHP: Criteria weighting")

if not eligible:
    st.warning("No eligible databases are available to rank.")
    st.stop()


# Load the six predefined criteria for the selected application.
default_criteria = application.get("default_criteria", [])

st.subheader("Active evaluation criteria")
st.caption(
    "Exactly six criteria are configured for this application. "
    "Criteria are predefined for the selected application."
)
criteria_labels = {
    "cost": "Cost",
    "scalability": "Scalability",
    "query_flexibility": "Query flexibility",
    "operational_simplicity": "Operational simplicity",
    "transaction_support": "Transaction support",
    "availability": "Availability",
    "security": "Security",
    "backup_recovery": "Backup and recovery",
    "concurrency_support": "Concurrency support",
    "ecosystem_support": "Ecosystem support",
    "document_model_support": "Document model support",
    "schema_flexibility": "Schema flexibility",
    "indexing_support": "Indexing support",
    "aggregation_support": "Aggregation support",
    "replication_support": "Replication support",
    "read_latency": "Read latency",
    "write_latency": "Write latency",
    "throughput": "Throughput",
    "persistence": "Persistence",
    "eviction_policy_support": "Eviction policy support",
    "replication_failover": "Replication and failover",
    "write_throughput": "Write throughput",
    "read_throughput": "Read throughput",
    "horizontal_scaling": "Horizontal scaling",
    "fault_tolerance": "Fault tolerance",
    "consistency_options": "Consistency options",
}
# Allow users to select or deselect the six predefined criteria.
selection_key = f"criteria_selection_{application['id']}"

if selection_key not in st.session_state:
    st.session_state[selection_key] = default_criteria.copy()

criteria = []

for criterion in default_criteria:
    checked = st.checkbox(
        criteria_labels.get(
            criterion,
            criterion.replace("_", " ").title()
        ),
        value=criterion in st.session_state[selection_key],
        key=f"{selection_key}_{criterion}"
    )

    if checked:
        criteria.append(criterion)

st.session_state[selection_key] = criteria
# Show which criteria still have missing scores.
unavailable_criteria = [
    criterion
    for criterion in criteria
    if any(
        database.get("scores", {}).get(criterion) is None
        for database in eligible
    )
]

if unavailable_criteria:
    st.info(
        "Some active criteria have unknown scores: "
        + ", ".join(
            criteria_labels.get(c, c.replace("_", " ").title())
            for c in unavailable_criteria
        )
        + ". Unknown scores remain null in the scoring file."
    )

st.caption(
    "Compare the importance of each pair of criteria. "
    "A value above 1 means the first criterion is more important."
)

scale_options = {
    "1 — Equal importance: Both criteria contribute equally.": 1,
    "2 — Intermediate value: Between equal and moderate importance.": 2,
    "3 — Moderate importance: One criterion is moderately more important.": 3,
    "4 — Intermediate value: Between moderate and strong importance.": 4,
    "5 — Strong importance: One criterion is strongly more important.": 5,
    "6 — Intermediate value: Between strong and very strong importance.": 6,
    "7 — Very strong importance: One criterion is very strongly favored.": 7,
    "8 — Intermediate value: Between very strong and extreme importance.": 8,
    "9 — Extreme importance: The highest degree of importance.": 9,
}

importance_options = {
    label: score
    for label, score in scale_options.items()
    if score > 1
}

pairwise_matrix = np.ones(
    (len(criteria), len(criteria)), dtype=float
)

with st.form("integrated_ahp_form"):

    for i in range(len(criteria)):
        for j in range(i + 1, len(criteria)):

            criterion_a = criteria[i]
            criterion_b = criteria[j]

            st.markdown(
                f"**Comparison: {criterion_a} vs {criterion_b}**"
            )

            direction = st.radio(
                "Which criterion is more important?",
                options=[
                    criterion_a,
                    "Equally Important",
                    criterion_b,
                ],
                horizontal=True,
                key=f"direction_{application['id']}_{i}_{j}",
            )

            value_label = st.selectbox(
                "Select degree of importance (Saaty's Scale)",
                list(importance_options.keys()),
                key=f"pair_{application['id']}_{i}_{j}",
            )

            importance = importance_options[value_label]

            if direction == criterion_a:
                value = importance
            elif direction == criterion_b:
                value = 1 / importance
            else:
                value = 1

            pairwise_matrix[i, j] = value
            pairwise_matrix[j, i] = 1 / value

    calculate_weights = st.form_submit_button(
        "Calculate AHP weights"
    )

if calculate_weights:

    try:
        details = get_ahp_details(pairwise_matrix)
        st.session_state["integrated_ahp"] = {
            "application_id": application["id"],
            "criteria": criteria,
            "matrix": pairwise_matrix.tolist(),
            "weights": details["weights"].tolist(),
            "cr": details["cr"],
            "consistent": details["is_consistent"],
        }
    except ValueError as error:
        st.error(str(error))

ahp_result = st.session_state.get("integrated_ahp")

if (
    ahp_result
    and ahp_result["application_id"] == application["id"]
    and ahp_result["criteria"] == criteria
):
    st.subheader("Calculated criteria weights")

    weights = ahp_result["weights"]

    st.dataframe(
        pd.DataFrame({
            "Criterion": criteria,
            "Weight": weights,
            "Weight (%)": np.array(weights) * 100,
        }).style.format({
            "Weight": "{:.4f}",
            "Weight (%)": "{:.2f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.metric("Consistency Ratio (CR)", f"{ahp_result['cr']:.4f}")

    if ahp_result["consistent"]:
        st.success("Comparisons are consistent (CR ≤ 0.10).")

    else:
        st.warning(
            "Comparisons are inconsistent. Review the judgments below "
            "and adjust them until CR ≤ 0.10."
        )

        st.subheader("Comparisons to Review")

        st.write(
            "Your answers conflict with each other. Start by reviewing "
            "these three comparisons from the most conflicting group."
        )

        triads = find_inconsistent_triads(
            ahp_result["criteria"],
            ahp_result["matrix"],
        )

        if triads:
            triad = triads[0]

            scale_meanings = {
                1: "Equal importance",
                2: "Intermediate importance",
                3: "Moderate importance",
                4: "Between moderate and strong",
                5: "Strong importance",
                6: "Between strong and very strong",
                7: "Very strong importance",
                8: "Between very strong and extreme",
                9: "Extreme importance",
            }

            comparisons_to_review = [
                (
                    triad["Criteria A"],
                    triad["Criteria B"],
                    triad["A vs B"],
                ),
                (
                    triad["Criteria B"],
                    triad["Criteria C"],
                    triad["B vs C"],
                ),
                (
                    triad["Criteria A"],
                    triad["Criteria C"],
                    triad["A vs C"],
                ),
            ]

            for criterion_a, criterion_b, value in comparisons_to_review:
                value = int(round(value))
                name_a = criterion_a.replace("_", " ").title()
                name_b = criterion_b.replace("_", " ").title()

                st.markdown(f"**{name_a} vs {name_b}**")

                st.write(
                    f"Your current choice: **{value} — "
                    f"{scale_meanings.get(value, 'Selected importance')}**"
                )

            st.info(
                "Return to these comparisons above and reconsider your "
                "choices. Change a value only if it reflects your actual "
                "preference, then click Calculate AHP weights again."
            )

        else:
            st.info(
                "No comparison group could be identified. Review your "
                "pairwise judgments and calculate the weights again."
            )
# --------------------------------------------------
# 4. TOPSIS ranking and SQLite persistence
# --------------------------------------------------

st.header("TOPSIS: Database ranking")

st.caption(
    "Scores are illustrative catalogue values on a 1–5 scale. "
    "Confirm the meaning and direction of each score before using "
    "rankings for real decisions."
)

criterion_types = {}

type_columns = st.columns(len(criteria))

for index, criterion in enumerate(criteria):
    # Cost score direction is not documented by the catalogue.
    default_type = "cost" if criterion == "cost" else "benefit"

    with type_columns[index]:
        criterion_types[criterion] = st.selectbox(
            f"{criterion}: direction",
            ["benefit", "cost"],
            index=["benefit", "cost"].index(default_type),
            key=f"direction_{application['id']}_{criterion}",
            help=(
                "Benefit: higher scores are better. "
                "Cost: lower scores are better."
            ),
        )

config_name = st.text_input(
    "Configuration name",
    value=f"{application['id']}_configuration",
)

if st.button("Rank eligible databases and save configuration"):
    if (
        not ahp_result
        or ahp_result["application_id"] != application["id"]
        or ahp_result["criteria"] != criteria
    ):
        st.error("Calculate AHP weights for this application first.")

    elif not ahp_result["consistent"]:
        st.error("Resolve AHP inconsistency before ranking.")

    elif not config_name.strip():
        st.error("Enter a configuration name.")

    else:
        missing_scores = [
            f"{database['name']}: "
            + ", ".join(
                criterion
                for criterion in criteria
                if database.get("scores", {}).get(criterion) is None
            )
            for database in eligible
            if any(
                database.get("scores", {}).get(criterion) is None
                for criterion in criteria
            )
        ]

        if missing_scores:
            st.error(
                "Cannot rank yet. Complete the missing scores in "
                "data/application_scores.json:\n\n"
                + "\n".join(missing_scores)
            )

        else:
            try:
                decision_matrix = [
                    [
                        database["scores"][criterion]
                        for criterion in criteria
                    ]
                    for database in eligible
                ]

                result = recommend_databases(
                    pairwise_matrix=ahp_result["matrix"],
                    decision_matrix=decision_matrix,
                    criteria_types=[
                        criterion_types[criterion]
                        for criterion in criteria
                    ],
                    alternatives=[
                        database["name"] for database in eligible
                    ],
                    config_name=config_name.strip(),
                    preferences={
                        "application_id": application["id"],
                        "application_name": application["name"],
                        "criteria": criteria,
                        "criteria_types": criterion_types,
                        "eligible_databases": [
                            database["name"] for database in eligible
                        ],
                    },
                )

                st.session_state["integrated_result"] = result
                st.success(
                    f"Configuration saved as version "
                    f"{result['config_version']}."
                )

            except (ValueError, TypeError) as error:
                st.error(str(error))

result = st.session_state.get("integrated_result")



# --------------------------------------------------
# 5. Ranking results, simple explanation and reliability
# --------------------------------------------------

if result:
    st.subheader("Database rankings")

    st.dataframe(
        pd.DataFrame(result["rankings"]),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("TOPSIS score comparison")

    ranking_df = pd.DataFrame(result["rankings"])

    if "score" in ranking_df.columns:
        chart_data = ranking_df.set_index("database")[["score"]]
        st.bar_chart(chart_data)

    if len(result["rankings"]) == 1:
        st.info(
            f"Only {result['rankings'][0]['database']} meets the "
            "mandatory requirements. A comparison with other eligible "
            "databases is not possible."
        )

    elif len(result["rankings"]) > 1:
        winner = result["rankings"][0]

        st.success(
            f"Recommended database: {winner['database']} "
            f"(score: {winner['score']:.4f})"
        )

        # Check that the current AHP weights match this application.
        valid_ahp = (
            ahp_result
            and ahp_result["application_id"] == application["id"]
            and ahp_result["criteria"] == criteria
        )

        if not valid_ahp:
            st.warning(
                "Calculate AHP weights for the current application "
                "and criteria to view the explanation."
            )

        else:
            try:
                decision_matrix = [
                    [
                        database["scores"][criterion]
                        for criterion in criteria
                    ]
                    for database in eligible
                ]

                database_names = [
                    database["name"] for database in eligible
                ]

                explanation_results = explain_topsis(
                    decision_matrix=decision_matrix,
                    weights=ahp_result["weights"],
                    criteria_types=[
                        criterion_types[criterion]
                        for criterion in criteria
                    ],
                    criteria_names=criteria,
                    alternatives=database_names,
                )

                winner_explanation = next(
                    item for item in explanation_results
                    if item["database"] == winner["database"]
                )

                st.markdown("### Why is this database recommended?")

                strong = winner_explanation["strong_criteria"]
                weak = winner_explanation["weak_criteria"]

                if strong:
                    st.write(
                        "**What it does well:** "
                        + ", ".join(
                            item.replace("_", " ") for item in strong
                        )
                        + "."
                    )

                if weak:
                    st.write(
                        "**Where other databases may do better:** "
                        + ", ".join(
                            item.replace("_", " ") for item in weak
                        )
                        + "."
                    )

                st.caption(
                    "The recommendation is based on the selected criteria, "
                    "their importance, and the scores of eligible databases."
                )

                # Detailed explanation is optional.
                with st.expander("View detailed explanation"):
                    st.write(
                        "**TOPSIS score:** "
                        f"{winner_explanation['topsis_score']:.4f}"
                    )

                    st.write(
                        "**Distance from the ideal database:** "
                        f"{winner_explanation['distance_from_ideal']:.4f}"
                    )

                    st.write(
                        "**Distance from the worst reference:** "
                        f"{winner_explanation['distance_from_worst']:.4f}"
                    )

                    st.caption(
                        "TOPSIS compares each database with ideal best and "
                        "worst reference points. A higher TOPSIS score is "
                        "better within the current comparison."
                    )

                    st.markdown("**How each criterion was used**")

                    detail_rows = []

                    for criterion, detail in (
                        winner_explanation["criteria"].items()
                    ):
                        detail_rows.append({
                            "Criterion": criterion.replace(
                                "_", " "
                            ).title(),
                            "Database score": detail["raw_score"],
                            "Importance (%)": detail["weight_percent"],
                            "Comparison": detail["performance_description"],
                        })

                    st.dataframe(
                        pd.DataFrame(detail_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.caption(
                        "Importance (%) is the weight calculated by AHP. "
                        "A higher weight means that criterion has more "
                        "influence in the TOPSIS comparison."
                    )

                    st.markdown("**What if criterion importance changes?**")

                    sensitivity_rows = []

                    for criterion, detail in (
                        winner_explanation["sensitivity"].items()
                    ):
                        change = detail["rank_change"]

                        if change > 0:
                            movement = f"Improved by {change} place(s)"
                        elif change < 0:
                            movement = f"Fell by {abs(change)} place(s)"
                        else:
                            movement = "No rank change"

                        sensitivity_rows.append({
                            "Criterion": criterion.replace(
                                "_", " "
                            ).title(),
                            "Original rank": detail["original_rank"],
                            "New rank": detail["new_rank"],
                            "New score": detail["new_score"],
                            "Result": movement,
                        })

                    st.dataframe(
                        pd.DataFrame(sensitivity_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.caption(
                        "This test increases one criterion's weight by 20% "
                        "at a time and recalculates TOPSIS. It does not "
                        "change the saved ranking."
                    )

            except (ValueError, TypeError, KeyError, StopIteration) as error:
                st.warning(
                    f"The explanation could not be generated: {error}"
                )

        # Reliability testing stays hidden unless the user opens it.
        with st.expander("Advanced: test ranking reliability"):
            st.write(
                "Check whether the recommendation changes when a database "
                "score is tested at different values."
            )

            st.caption(
                "The test uses low (1), middle (3), and high (5) scores. "
                "These are hypothetical scenarios, not predictions."
            )

            run_reliability = st.button(
                "Run reliability test",
                key="run_ranking_reliability",
            )

            if run_reliability:
                if not valid_ahp:
                    st.warning(
                        "Calculate AHP weights for the current application "
                        "and criteria first."
                    )
                else:
                    try:
                        reliability = evaluate_ranking_reliability(
                            decision_matrix=decision_matrix,
                            weights=ahp_result["weights"],
                            criteria_types=[
                                criterion_types[criterion]
                                for criterion in criteria
                            ],
                            alternatives=database_names,
                            criteria_names=criteria,
                        )

                        st.markdown("**Test results**")

                        col1, col2, col3 = st.columns(3)

                        col1.metric(
                            "Ranking stayed the same",
                            f"{reliability['ranking_order_stability_percent']:.1f}%",
                        )

                        col2.metric(
                            "Top choice stayed the same",
                            f"{reliability['top_recommendation_retention_percent']:.1f}%",
                        )

                        col3.metric(
                            "Average rank movement",
                            f"{reliability['average_absolute_rank_movement']:.2f}",
                        )

                        st.write(
                            "**Original ranking:** "
                            + " → ".join(reliability["baseline_order"])
                        )

                        with st.expander("View test scenarios"):
                            scenario_df = pd.DataFrame(
                                reliability["scenarios"]
                            )

                            scenario_df = scenario_df.rename(columns={
                                "database_tested": "Database tested",
                                "criterion_tested": "Criterion tested",
                                "scenario": "Test",
                                "original_score": "Original score",
                                "scenario_score": "Test score",
                                "new_winner": "New top choice",
                                "winner_retained": "Top choice unchanged",
                                "ranking_order_unchanged": "Full ranking unchanged",
                                "new_ranking": "New ranking",
                            })

                            scenario_df = scenario_df.drop(
                                columns=[
                                    "original_winner",
                                    "rank_changes",
                                ],
                                errors="ignore",
                            )

                            st.dataframe(
                                scenario_df,
                                use_container_width=True,
                                hide_index=True,
                            )

                        st.caption(reliability["interpretation"])

                    except (ValueError, TypeError, KeyError) as error:
                        st.error(
                            f"Reliability testing failed: {error}"
                        )

# --------------------------------------------------
# 6. Saved configuration history
# --------------------------------------------------

st.header("Saved configuration history")

# Known configuration names for the four application types.
configuration_options = [
    "general_web_app_configuration",
    "document_app_configuration",
    "real_time_cache_configuration",
    "distributed_wide_column_configuration",
]

history_name = st.selectbox(
    "Choose a configuration to inspect",
    configuration_options,
    key="history_name",
)

if st.button("Load configuration history"):
    history = get_configuration_history(history_name)
    st.session_state["integrated_history"] = history
    st.session_state["integrated_history_name"] = history_name

history = st.session_state.get("integrated_history", [])
loaded_name = st.session_state.get("integrated_history_name")

if loaded_name == history_name:
    if history:
        st.subheader(f"Version history: {history_name}")

        st.dataframe(
            pd.DataFrame(history),
            use_container_width=True,
            hide_index=True,
        )

        versions = [item["version"] for item in history]

        version = st.selectbox(
            "Select saved version",
            versions,
            index=len(versions) - 1,
            key=f"saved_version_{history_name}",
        )

        if st.button("View saved configuration"):
            saved = get_configuration(history_name, version=version)

            if saved:
                st.subheader(f"Configuration details — Version {version}")
                st.write(f"**Created at:** {saved['created_at']}")

                st.write("**Criteria weights**")
                st.json(saved["criteria_weights"])

                st.write("**Preferences**")
                st.json(saved["preferences"])
    else:
        st.info("No saved versions exist for this configuration yet.")

st.caption(
    "Prototype notice: catalogue scores are illustrative and need validation."
)
