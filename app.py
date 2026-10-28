
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from core.catalogue import load_databases
from core.filtering import filter_databases
from core.explanations import explain_database
from core.ahp import get_ahp_details
from core.recommendation import recommend_databases
from storage.database import get_configuration_history, get_configuration

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



# Load the ten predefined criteria for the selected application.
default_criteria = application.get("default_criteria", [])

st.subheader("Customise evaluation criteria")
st.caption(
    "Ten predefined criteria are available for this application. "
    "You can deselect criteria, but cannot add new ones. "
    "Only criteria with known scores for every eligible database "
    "can be used for ranking."
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

# Keep each application's custom selections separate.
selection_key = f"criteria_selection_{application['id']}"

if selection_key not in st.session_state:
    st.session_state[selection_key] = default_criteria.copy()

selected_criteria = []
columns = st.columns(2)

for index, criterion in enumerate(default_criteria):
    with columns[index % 2]:
        checked = st.checkbox(
            criteria_labels.get(
                criterion,
                criterion.replace("_", " ").title(),
            ),
            value=criterion in st.session_state[selection_key],
            key=f"{selection_key}_checkbox_{criterion}",
        )
        if checked:
            selected_criteria.append(criterion)

st.session_state[selection_key] = selected_criteria
criteria = selected_criteria


# Identify criteria that have numeric scores for every eligible database.
scored_criteria = [
    criterion
    for criterion in application.get("default_criteria", [])
    if all(
        isinstance(database.get("scores", {}).get(criterion), (int, float))
        and not isinstance(database.get("scores", {}).get(criterion), bool)
        for database in eligible
    )
]

# Show which criteria are currently unavailable.
unavailable_criteria = [
    criterion
    for criterion in application.get("default_criteria", [])
    if criterion not in scored_criteria
]

if unavailable_criteria:
    st.info(
        "These predefined criteria cannot currently be used because "
        "one or more eligible databases have unknown scores: "
        + ", ".join(
            criteria_labels.get(c, c.replace("_", " ").title())
            for c in unavailable_criteria
        )
    )

# Keep only selected criteria with known numeric scores.
criteria = [
    criterion for criterion in criteria
    if criterion in scored_criteria
]

if len(criteria) < 2:
    st.warning(
        "Select at least two criteria that have scores for every eligible database."
    )
    st.stop()

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
    if not ahp_result or ahp_result["application_id"] != application["id"] \
            or ahp_result["criteria"] != criteria:
        st.error("Calculate AHP weights for this application first.")
    elif not ahp_result["consistent"]:
        st.error("Resolve AHP inconsistency before ranking.")
    elif not config_name.strip():
        st.error("Enter a configuration name.")
    else:
        try:
            decision_matrix = [
                [database["scores"][criterion] for criterion in criteria]
                for database in eligible
            ]

            result = recommend_databases(
                pairwise_matrix=ahp_result["matrix"],
                decision_matrix=decision_matrix,
                criteria_types=[
                    criterion_types[criterion] for criterion in criteria
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
                f"Configuration saved as version {result['config_version']}."
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
