
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
    "1 - Equal": 1,
    "2": 2,
    "3 - Moderate": 3,
    "4": 4,
    "5 - Strong": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
}

pairwise_matrix = np.ones((len(criteria), len(criteria)), dtype=float)


with st.form("integrated_ahp_form"):
    for i in range(len(criteria)):
        for j in range(i + 1, len(criteria)):
            value_label = st.selectbox(
                f"{criteria[i]} compared with {criteria[j]}",
                list(scale_options.keys()),
                index=0,
                key=f"pair_{application['id']}_{criteria[i]}_{criteria[j]}",
            )
            value = scale_options[value_label]
            pairwise_matrix[i, j] = value
            pairwise_matrix[j, i] = 1 / value

    calculate_weights = st.form_submit_button("Calculate AHP weights")

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
            "Comparisons are inconsistent. Adjust them until CR ≤ 0.10 "
            "before generating recommendations."
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


if result:
    st.subheader("Database rankings")

    if len(result["rankings"]) == 1:
        only_database = result["rankings"][0]["database"]
        st.info(
            f"Only eligible database: {only_database}. "
            "No comparative ranking is possible because only one "
            "database satisfies the mandatory requirements."
        )
        st.dataframe(
            pd.DataFrame([{"database": only_database, "rank": 1}]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            pd.DataFrame(result["rankings"]),
            use_container_width=True,
            hide_index=True,
        )

        winner = result["rankings"][0]
        st.success(
            f"Recommended database: {winner['database']} "
            f"(TOPSIS score: {winner['score']:.4f})"
        )

        st.subheader("TOPSIS score comparison")

        ranking_df = pd.DataFrame(result["rankings"])

        if "score" in ranking_df.columns:
            chart_data = ranking_df.set_index("database")[["score"]]
            st.bar_chart(chart_data)

    
        # --------------------------------------------------
        # 4A. TOPSIS explainability
        # --------------------------------------------------

        st.subheader("Why did each database receive this rank?")

        st.caption(
            "This section explains the current TOPSIS ranking using "
            "criterion performance, AHP weights, ideal-reference "
            "distances, and weight sensitivity."
        )

        if len(eligible) < 2:
            st.info(
                "Explainability requires at least two eligible databases "
                "for a meaningful comparison."
            )

        elif len(criteria) < 2:
            st.info(
                "Select at least two criteria to generate the explanation."
            )

        elif (
            not ahp_result
            or ahp_result["application_id"] != application["id"]
            or ahp_result["criteria"] != criteria
        ):
            st.warning(
                "Recalculate AHP weights for the current criteria before "
                "viewing explainability."
            )

        else:
            try:
                # Rebuild the decision matrix in the same order as eligible.
                explanation_matrix = [
                    [
                        database["scores"][criterion]
                        for criterion in criteria
                    ]
                    for database in eligible
                ]

                explanation_results = explain_topsis(
                    decision_matrix=explanation_matrix,
                    weights=ahp_result["weights"],
                    criteria_types=[
                        criterion_types[criterion]
                        for criterion in criteria
                    ],
                    criteria_names=criteria,
                    alternatives=[
                        database["name"] for database in eligible
                    ],
                    sensitivity_percent=20,
                )

                explanation_names = [
                    item["database"] for item in explanation_results
                ]

                selected_explanation_name = st.selectbox(
                    "Choose a database to explain",
                    explanation_names,
                    key="topsis_explanation_database",
                )

                details = next(
                    item for item in explanation_results
                    if item["database"] == selected_explanation_name
                )

                st.markdown(
                    f"### {details['database']} — Rank {details['rank']}"
                )

                metric1, metric2, metric3 = st.columns(3)

                metric1.metric(
                    "TOPSIS score",
                    f"{details['topsis_score']:.4f}",
                )
                metric2.metric(
                    "Distance from ideal",
                    f"{details['distance_from_ideal']:.4f}",
                )
                metric3.metric(
                    "Distance from worst",
                    f"{details['distance_from_worst']:.4f}",
                )

                st.markdown("#### 1. Strengths and weaknesses")

                strong_labels = [
                    criterion.replace("_", " ").title()
                    for criterion in details["strong_criteria"]
                ]
                weak_labels = [
                    criterion.replace("_", " ").title()
                    for criterion in details["weak_criteria"]
                ]

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Strong relative performance**")
                    st.write(", ".join(strong_labels) or "None identified")

                with col2:
                    st.write("**Weak relative performance**")
                    st.write(", ".join(weak_labels) or "None identified")

                st.caption(
                    "Strengths and weaknesses are relative to the other "
                    "eligible databases, not absolute quality ratings."
                )

                st.markdown("#### 2. Criterion-level explanation")

                criterion_rows = []

                for criterion, item in details["criteria"].items():
                    criterion_rows.append({
                        "Criterion": criterion.replace("_", " ").title(),
                        "Database score (1–5)": item["raw_score"],
                        "AHP weight (%)": item["weight_percent"],
                        "Weighted normalized value": item["weighted_value"],
                        "Relative performance": item["performance_description"],
                        "Distance from ideal share (%)":
                            item["distance_from_ideal_share_percent"],
                        "Distance from worst share (%)":
                            item["distance_from_worst_share_percent"],
                    })

                criterion_df = pd.DataFrame(criterion_rows)

                st.dataframe(
                    criterion_df,
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "AHP weight (%) indicates criterion importance. The "
                    "distance-share columns show each criterion's share "
                    "of the database's squared distance from the respective "
                    "reference point; they are not direct contributions "
                    "to the final TOPSIS score."
                )

                st.markdown("#### 3. Weight sensitivity (+20%)")

                sensitivity_rows = []

                for criterion, item in details["sensitivity"].items():
                    change = item["rank_change"]

                    if change > 0:
                        interpretation = f"Improved by {change} rank(s)"
                    elif change < 0:
                        interpretation = f"Fell by {abs(change)} rank(s)"
                    else:
                        interpretation = "Rank unchanged"

                    sensitivity_rows.append({
                        "Increased criterion": criterion.replace(
                            "_", " "
                        ).title(),
                        "Original rank": item["original_rank"],
                        "New rank": item["new_rank"],
                        "Rank change": change,
                        "Interpretation": interpretation,
                        "New TOPSIS score": item["new_score"],
                    })

                st.dataframe(
                    pd.DataFrame(sensitivity_rows),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Sensitivity test: one criterion's weight is increased "
                    "by 20% at a time, then all weights are normalized and "
                    "TOPSIS is recalculated. This is a what-if test, not a "
                    "prediction of real-world database performance."
                )

            except (ValueError, TypeError, KeyError) as error:
                st.error(
                    f"Could not generate the TOPSIS explanation: {error}"
                )



# --------------------------------------------------
# 5. Saved configuration history
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
