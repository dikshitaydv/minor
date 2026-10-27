
import streamlit as st
import numpy as np
import pandas as pd

from core.ahp import get_ahp_details
from core.recommendation import recommend_databases

st.set_page_config(
    page_title="Database Selection System",
    page_icon="⚖️",
    layout="wide",
)

st.title("Database Selection & Recommendation System")
st.caption("AHP criteria weighting + TOPSIS database ranking")

# --------------------------------------------------
# 1. Criteria configuration
# --------------------------------------------------

st.header("1. Define criteria")

criteria_text = st.text_input(
    "Criteria (comma-separated)",
    value="Performance, Cost, Scalability",
)

criteria = [
    item.strip()
    for item in criteria_text.split(",")
    if item.strip()
]

if not criteria:
    st.warning("Enter at least one criterion.")
    st.stop()

if len(criteria) > 10:
    st.error("This implementation supports up to 10 criteria.")
    st.stop()

if len(criteria) != len(set(criteria)):
    st.error("Criterion names must be unique.")
    st.stop()

n = len(criteria)

# --------------------------------------------------
# 2. AHP pairwise comparisons
# --------------------------------------------------

st.header("2. Pairwise comparisons")

st.write(
    "Compare the importance of each pair of criteria. "
    "A value above 1 means the first criterion is more important."
)

scale_options = {
    "1 - Equal": 1,
    "2 - Between equal and moderate": 2,
    "3 - Moderate": 3,
    "4 - Between moderate and strong": 4,
    "5 - Strong": 5,
    "6 - Between strong and very strong": 6,
    "7 - Very strong": 7,
    "8 - Between very strong and extreme": 8,
    "9 - Extreme": 9,
}

# Reset comparisons when criterion names or order change.
criteria_key = tuple(criteria)

if st.session_state.get("criteria_key") != criteria_key:
    st.session_state["criteria_key"] = criteria_key
    st.session_state["comparison_values"] = {}

comparison_values = st.session_state["comparison_values"]
matrix = np.ones((n, n), dtype=float)

with st.form("ahp_form"):
    for i in range(n):
        for j in range(i + 1, n):
            key = f"{i}_{j}"

            st.markdown(f"**{criteria[i]} vs {criteria[j]}**")

            selected = st.selectbox(
                f"Importance of {criteria[i]} compared with {criteria[j]}",
                options=list(scale_options.keys()),
                index=0,
                key=f"ahp_{criteria_key}_{key}",
            )

            value = scale_options[selected]
            comparison_values[key] = value

            matrix[i, j] = value
            matrix[j, i] = 1.0 / value

    calculate = st.form_submit_button("Calculate AHP weights")

# Store calculated weights so they remain available on later reruns.
if calculate:
    try:
        details = get_ahp_details(matrix)

        st.session_state["ahp_details"] = {
            "weights": details["weights"].tolist(),
            "cr": details["cr"],
            "ci": details["ci"],
            "lambda_max": details["lambda_max"],
            "is_consistent": details["is_consistent"],
            "criteria": criteria.copy(),
            "matrix": matrix.tolist(),
            "normalized_matrix": details["normalized_matrix"].tolist(),
        }
    except ValueError as error:
        st.error(str(error))

details = st.session_state.get("ahp_details")

# Never reuse weights from a different criteria configuration.
if details and details["criteria"] != criteria:
    details = None

if details:
    st.subheader("AHP results")

    weights = details["weights"]

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

    col1, col2, col3 = st.columns(3)
    col1.metric("Consistency Ratio (CR)", f"{details['cr']:.4f}")
    col2.metric("Consistency Index (CI)", f"{details['ci']:.4f}")
    col3.metric("Lambda Max", f"{details['lambda_max']:.4f}")

    if details["is_consistent"]:
        st.success("Comparisons are consistent (CR ≤ 0.10).")
    else:
        st.warning("Comparisons are inconsistent (CR > 0.10).")

    with st.expander("View normalized comparison matrix"):
        st.dataframe(
            pd.DataFrame(
                details["normalized_matrix"],
                index=criteria,
                columns=criteria,
            ).style.format("{:.4f}"),
            use_container_width=True,
        )

# --------------------------------------------------
# 3. Database decision matrix
# --------------------------------------------------

st.header("3. Database performance scores")

st.write(
    "Enter comparable scores for each database. "
    "Use the same scale for a given criterion across all databases."
)

database_text = st.text_input(
    "Databases to compare (comma-separated)",
    value="PostgreSQL, MySQL, MongoDB",
)

databases = [
    item.strip()
    for item in database_text.split(",")
    if item.strip()
]

if not databases:
    st.warning("Enter at least one database.")
    st.stop()

if len(databases) != len(set(databases)):
    st.error("Database names must be unique.")
    st.stop()

st.caption(
    "For cost criteria, lower values are better. "
    "For benefit criteria, higher values are better."
)

# Use editable data for scores.
if (
    "score_data" not in st.session_state
    or st.session_state.get("score_criteria") != criteria_key
    or st.session_state.get("score_databases") != tuple(databases)
):
    st.session_state["score_criteria"] = criteria_key
    st.session_state["score_databases"] = tuple(databases)
    st.session_state["score_data"] = pd.DataFrame(
        np.ones((len(databases), n), dtype=float),
        index=databases,
        columns=criteria,
    )

score_data = st.session_state["score_data"]

st.write("Edit the score table:")

edited_scores = st.data_editor(
    score_data,
    use_container_width=True,
    key=f"scores_{criteria_key}_{tuple(databases)}",
    num_rows="fixed",
    column_config={
        criterion: st.column_config.NumberColumn(
            criterion,
            min_value=0.000001,
            step=1.0,
        )
        for criterion in criteria
    },
)

st.session_state["score_data"] = edited_scores

criteria_types = []

cols = st.columns(n)

for i, criterion in enumerate(criteria):
    with cols[i]:
        criterion_type = st.selectbox(
            f"{criterion}: criterion type",
            options=["benefit", "cost"],
            index=0,
            key=f"type_{criteria_key}_{criterion}",
        )
        criteria_types.append(criterion_type)

# --------------------------------------------------
# 4. Save configuration and rank databases
# --------------------------------------------------

st.header("4. Generate recommendations")

config_name = st.text_input(
    "Configuration name",
    value="my_database_selection",
)

if st.button("Rank databases and save configuration", type="primary"):
    if details is None:
        st.error("Calculate AHP weights for the current criteria first.")
    elif not details["is_consistent"]:
        st.error(
            "Your AHP comparisons are inconsistent. "
            "Review them before generating recommendations."
        )
    elif not config_name.strip():
        st.error("Enter a configuration name.")
    else:
        try:
            decision_matrix = edited_scores[criteria].to_numpy(dtype=float)

            if not np.all(np.isfinite(decision_matrix)):
                raise ValueError("All scores must be finite numbers.")

            if np.any(decision_matrix <= 0):
                raise ValueError("All scores must be greater than zero.")

            result = recommend_databases(
                pairwise_matrix=details["matrix"],
                decision_matrix=decision_matrix,
                criteria_types=criteria_types,
                alternatives=databases,
                config_name=config_name.strip(),
                preferences={
                    "criteria": criteria,
                    "criteria_types": criteria_types,
                    "databases": databases,
                },
            )

            st.session_state["recommendation_result"] = result
            st.success(
                f"Configuration saved successfully. "
                f"Version: {result['config_version']}"
            )

        except (ValueError, TypeError) as error:
            st.error(str(error))

# --------------------------------------------------
# 5. Display rankings
# --------------------------------------------------

result = st.session_state.get("recommendation_result")

if result:
    st.header("5. Database rankings")

    ranking_df = pd.DataFrame(result["rankings"])

    st.dataframe(
        ranking_df,
        use_container_width=True,
        hide_index=True,
    )

    winner = result["rankings"][0]

    st.success(
        f"Recommended database: {winner['database']} "
        f"(TOPSIS score: {winner['score']:.4f})"
    )

    st.caption(
        f"Configuration: {result['config_name']} | "
        f"Version: {result['config_version']}"
    )
