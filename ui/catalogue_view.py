
"""Dikshita's UI module for database selection and filtering."""

import pandas as pd
import streamlit as st

from core.filtering import filter_databases
from core.explanations import explain_database


def _get_name(item):
    return item.get("name", item.get("id", "Unnamed"))


def _get_requirements(application):
    requirements = application.get(
        "mandatory_requirements",
        application.get("requirements", []),
    )

    # Support either a list of strings or a list of requirement objects.
    return [
        item if isinstance(item, str) else item.get("key", item.get("id"))
        for item in requirements
        if isinstance(item, str)
        or isinstance(item, dict)
    ]


def render_catalogue_view(databases, applications):
    st.header("Database Selection")

    if not databases:
        st.warning("No databases are available in the catalogue.")
        return

    if not applications:
        st.warning("No application types are configured.")
        return

    app_names = [_get_name(app) for app in applications]
    selected_name = st.selectbox(
        "Select application type",
        app_names,
    )

    application = applications[app_names.index(selected_name)]
    requirements = _get_requirements(application)

    st.subheader("Mandatory requirements")

    if requirements:
        selected_requirements = st.multiselect(
            "Select requirements to check",
            options=requirements,
            default=requirements,
        )
    else:
        selected_requirements = []
        st.info(
            "No mandatory requirements are configured for this "
            "application yet."
        )

    eligible, excluded = filter_databases(
        databases,
        selected_requirements,
    )

    st.subheader("Eligible candidates")

    if eligible:
        rows = []

        for database in eligible:
            rows.append({
                "Database": _get_name(database),
                "Status": database["_filter_status"],
                "Needs verification": ", ".join(
                    database["_verification_requirements"]
                ) or "None",
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Database explanations")

        for database in eligible:
            explanation = explain_database(database)

            with st.expander(explanation["database"]):
                st.write(explanation["summary"])

                if explanation["strengths"]:
                    st.write(
                        "**Strengths:**",
                        ", ".join(explanation["strengths"]),
                    )

                if explanation["limitations"]:
                    st.write(
                        "**Limitations:**",
                        ", ".join(explanation["limitations"]),
                    )

                if explanation["unknown_criteria"]:
                    st.write(
                        "**Unknown criteria:**",
                        ", ".join(explanation["unknown_criteria"]),
                    )
    else:
        st.info("No candidates remain for the selected requirements.")

    st.subheader("Excluded databases")

    if excluded:
        for item in excluded:
            st.write(
                f"**{_get_name(item['database'])}** — "
                f"Confirmed failures: {', '.join(item['reasons'])}"
            )
    else:
        st.write("No databases were excluded.")
