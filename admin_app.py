"""Administrator interface for maintaining catalogue and application data.

Administrators can edit the source JSON files used by the recommendation workflow.
No AHP, pairwise-comparison, recommendation, or TOPSIS workflow is exposed here.
"""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATABASES_FILE = DATA_DIR / "databases.json"
APPLICATIONS_FILE = DATA_DIR / "applications.json"
APPLICATION_SCORES_FILE = DATA_DIR / "application_scores.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    """Atomically replace a JSON data file after validating serialization."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    temp_name = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent,
            prefix=path.name + ".", suffix=".tmp", delete=False
        ) as temp:
            temp.write(serialized)
            temp.flush()
            os.fsync(temp.fileno())
            temp_name = temp.name
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def parse_lines(value):
    return [line.strip() for line in value.splitlines() if line.strip()]


def score_input(label, value, key):
    value = st.number_input(
        label, min_value=1.0, max_value=5.0, value=float(value),
        step=1.0, key=key,
    )
    return int(value) if value.is_integer() else value


def render_admin_page():
    st.title("Administrator Dashboard")
    st.caption("Manage database catalogue information, application details, and application-specific scores.")

    try:
        databases = load_json(DATABASES_FILE)
        applications = load_json(APPLICATIONS_FILE)
        score_data = load_json(APPLICATION_SCORES_FILE)
    except (OSError, json.JSONDecodeError) as error:
        st.error(f"Could not load project data: {error}")
        st.stop()

    if not isinstance(databases, list) or not isinstance(applications, list):
        st.error("The database or application data file has an unexpected structure.")
        st.stop()
    score_data.setdefault("applications", {})

    overview, database_tab, application_tab, scores_tab = st.tabs(
        ["Overview", "Databases", "Applications", "Application Scores"]
    )

    with overview:
        st.subheader("Project data overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Databases", len(databases))
        c2.metric("Applications", len(applications))
        c3.metric(
            "Application score sets",
            len(score_data.get("applications", {})),
        )
        if databases:
            st.subheader("All databases")
            st.dataframe(
                pd.DataFrame([
                    {"Database": item.get("name", ""), "ID": item.get("id", ""),
                     "Type": item.get("type", "")}
                    for item in databases
                ]),
                use_container_width=True, hide_index=True,
            )
        if applications:
            st.subheader("All applications")
            st.dataframe(
                pd.DataFrame([
                    {"Application": item.get("name", ""), "ID": item.get("id", ""),
                     "Description": item.get("description", "")}
                    for item in applications
                ]),
                use_container_width=True, hide_index=True,
            )

    with database_tab:
        st.subheader("View and modify database information")
        if not databases:
            st.info("No databases are currently configured.")
        else:
            labels = {
                f"{item.get('name', item.get('id'))} ({item.get('id')})": item
                for item in databases
            }
            selected_label = st.selectbox("Select a database", list(labels), key="admin_database")
            selected = labels[selected_label]
            db_index = databases.index(selected)

            with st.expander("Database details", expanded=True):
                st.write(f"**Database ID:** `{selected.get('id', '')}`")
                st.write(f"**Name:** {selected.get('name', '')}")
                st.write(f"**Type:** {selected.get('type', '')}")
                st.write(f"**Notes:** {selected.get('notes', '') or 'No notes'}")
                st.write("**Capabilities and other catalogue fields**")
                st.json({
                    key: value for key, value in selected.items()
                    if key not in {"id", "name", "type", "scores", "evidence_urls", "verified_on", "notes"}
                })
                st.write("**Catalogue scores**")
                if selected.get("scores"):
                    st.dataframe(
                        pd.DataFrame(
                            [{"Criterion": key, "Score": value}
                             for key, value in selected["scores"].items()]
                        ),
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.info("No general catalogue scores are stored.")

            with st.form("edit_database_form"):
                st.markdown("**Edit database profile**")
                new_name = st.text_input("Database name", value=selected.get("name", ""))
                new_type = st.text_input("Database type", value=selected.get("type", ""))
                new_notes = st.text_area("Notes", value=selected.get("notes", ""))
                new_evidence = st.text_area(
                    "Catalogue evidence URLs (one per line)",
                    value="\n".join(selected.get("evidence_urls", [])),
                )
                new_verified = st.text_input(
                    "Catalogue verified date (YYYY-MM-DD or blank)",
                    value=selected.get("verified_on") or "",
                )
                st.caption("Edit capability flags and other existing fields as JSON. Keep the field names and valid JSON types.")
                excluded = {"id", "name", "type", "scores", "evidence_urls", "verified_on", "notes"}
                other_fields = {k: v for k, v in selected.items() if k not in excluded}
                other_json = st.text_area(
                    "Other database information (JSON)",
                    value=json.dumps(other_fields, indent=2, ensure_ascii=False),
                    height=180,
                )
                st.markdown("**Edit catalogue scores (1–5; blank means unknown)**")
                new_catalogue_scores = {}
                invalid_catalogue_scores = []
                score_columns = st.columns(3)
                for idx, (criterion, old_score) in enumerate(selected.get("scores", {}).items()):
                    with score_columns[idx % 3]:
                        raw = st.text_input(
                            criterion.replace("_", " ").title(),
                            value="" if old_score is None else str(old_score),
                            key=f"catalogue_{selected['id']}_{criterion}",
                        )
                    if raw.strip():
                        try:
                            number = float(raw)
                            if not 1 <= number <= 5:
                                raise ValueError
                            new_catalogue_scores[criterion] = int(number) if number.is_integer() else number
                        except ValueError:
                            st.error(f"{criterion}: enter a number from 1 to 5 or leave blank.")
                            invalid_catalogue_scores.append(criterion)
                            new_catalogue_scores[criterion] = old_score
                    else:
                        new_catalogue_scores[criterion] = None
                submitted = st.form_submit_button("Save database changes", type="primary")
            if submitted:
                try:
                    if invalid_catalogue_scores:
                        raise ValueError("Correct invalid catalogue scores before saving.")
                    other = json.loads(other_json or "{}")
                    if not isinstance(other, dict):
                        raise ValueError("Other database information must be a JSON object.")
                    if not new_name.strip() or not new_type.strip():
                        raise ValueError("Database name and type are required.")
                    if new_verified.strip():
                        from datetime import date
                        date.fromisoformat(new_verified.strip())
                    updated = {
                        **other,
                        "id": selected["id"],
                        "name": new_name.strip(),
                        "type": new_type.strip(),
                        "scores": new_catalogue_scores,
                        "evidence_urls": parse_lines(new_evidence),
                        "verified_on": new_verified.strip() or None,
                        "notes": new_notes.strip(),
                    }
                    databases[db_index] = updated
                    save_json(DATABASES_FILE, databases)
                    st.success("Database information saved to data/databases.json.")
                    st.rerun()
                except (ValueError, TypeError, json.JSONDecodeError) as error:
                    st.error(f"Could not save database changes: {error}")

    with application_tab:
        st.subheader("View and modify application details")
        if not applications:
            st.info("No applications are currently configured.")
        else:
            app_labels = {
                f"{item.get('name', item.get('id'))} ({item.get('id')})": item
                for item in applications
            }
            selected_app_label = st.selectbox(
                "Select an application", list(app_labels), key="admin_application"
            )
            selected_app = app_labels[selected_app_label]
            app_index = applications.index(selected_app)
            st.write(f"**Application ID:** `{selected_app.get('id', '')}`")
            with st.form("edit_application_form"):
                app_name = st.text_input("Application name", value=selected_app.get("name", ""))
                app_description = st.text_area(
                    "Application description", value=selected_app.get("description", "")
                )
                mandatory = st.text_area(
                    "Mandatory requirements (one per line)",
                    value="\n".join(selected_app.get("mandatory_requirements", [])),
                )
                default_criteria = st.text_area(
                    "Default evaluation criteria (one per line)",
                    value="\n".join(selected_app.get("default_criteria", [])),
                )
                save_app = st.form_submit_button("Save application details", type="primary")
            if save_app:
                if not app_name.strip():
                    st.error("Application name is required.")
                else:
                    applications[app_index] = {
                        **selected_app,
                        "name": app_name.strip(),
                        "description": app_description.strip(),
                        "mandatory_requirements": parse_lines(mandatory),
                        "default_criteria": parse_lines(default_criteria),
                    }
                    save_json(APPLICATIONS_FILE, applications)
                    st.success("Application details saved to data/applications.json.")
                    st.rerun()

    with scores_tab:
        st.subheader("Manage application-specific database scores")
        app_options = {
            f"{item.get('name', item.get('id'))} ({item.get('id')})": item
            for item in applications
        }
        if not app_options:
            st.info("Add application details before editing application scores.")
        else:
            score_app_label = st.selectbox(
                "Application", list(app_options), key="scores_application"
            )
            score_app = app_options[score_app_label]
            app_id = score_app["id"]
            per_app = score_data["applications"].setdefault(app_id, {})
            db_options = {
                f"{item.get('name', item.get('id'))} ({item.get('id')})": item
                for item in databases
            }
            if not db_options:
                st.info("Add databases before editing scores.")
            else:
                score_db_label = st.selectbox(
                    "Database", list(db_options), key=f"scores_database_{app_id}"
                )
                score_db = db_options[score_db_label]
                db_id = score_db["id"]
                current_scores = per_app.setdefault(db_id, {})
                if current_scores:
                    st.markdown("**Current saved scores for this application and database**")
                    current_rows = []
                    for criterion, details in current_scores.items():
                        details = details if isinstance(details, dict) else {"score": details}
                        current_rows.append({
                            "Criterion": criterion.replace("_", " ").title(),
                            "Score": details.get("score"),
                            "Evidence URL": details.get("evidence_url") or "",
                            "Verified on": details.get("verified_on") or "",
                        })
                    st.dataframe(
                        pd.DataFrame(current_rows),
                        use_container_width=True, hide_index=True,
                    )
                criteria = list(dict.fromkeys(
                    list(score_app.get("default_criteria", [])) + list(current_scores.keys())
                ))
                if not criteria:
                    st.info("This application has no default criteria. Add criteria in Applications first.")
                else:
                    st.caption("Scores use the project's 1–5 scale. Leave a score blank to mark it unknown.")
                    with st.form(f"application_score_form_{app_id}_{db_id}"):
                        edited = {}
                        invalid_application_scores = []
                        columns = st.columns(2)
                        for index, criterion in enumerate(criteria):
                            current = current_scores.get(criterion, {})
                            current = current if isinstance(current, dict) else {"score": current}
                            with columns[index % 2]:
                                st.markdown(f"**{criterion.replace('_', ' ').title()}**")
                                raw_score = st.text_input(
                                    "Score (1–5; blank = unknown)",
                                    value="" if current.get("score") is None else str(current.get("score")),
                                    key=f"appscore_{app_id}_{db_id}_{criterion}",
                                )
                                evidence = st.text_input(
                                    "Evidence URL",
                                    value=current.get("evidence_url") or "",
                                    key=f"appevidence_{app_id}_{db_id}_{criterion}",
                                )
                                verified = st.text_input(
                                    "Verified on",
                                    value=current.get("verified_on") or "",
                                    key=f"appverified_{app_id}_{db_id}_{criterion}",
                                )
                            if raw_score.strip():
                                try:
                                    number = float(raw_score)
                                    if not 1 <= number <= 5:
                                        raise ValueError
                                    parsed_score = int(number) if number.is_integer() else number
                                except ValueError:
                                    st.error(f"{criterion}: enter a number from 1 to 5 or leave blank.")
                                    invalid_application_scores.append(criterion)
                                    parsed_score = current.get("score")
                            else:
                                parsed_score = None
                            edited[criterion] = {
                                "score": parsed_score,
                                "evidence_url": evidence.strip() or None,
                                "verified_on": verified.strip() or None,
                            }
                        save_scores = st.form_submit_button("Save application scores", type="primary")
                    if save_scores:
                        try:
                            if invalid_application_scores:
                                raise ValueError("Correct invalid application scores before saving.")
                            for criterion, details in edited.items():
                                if details["evidence_url"] and not details["evidence_url"].startswith(("http://", "https://")):
                                    raise ValueError(f"{criterion}: evidence URL must start with http:// or https://.")
                            per_app[db_id] = edited
                            score_data["applications"][app_id] = per_app
                            save_json(APPLICATION_SCORES_FILE, score_data)
                            st.success("Application-specific scores saved to data/application_scores.json.")
                            st.rerun()
                        except (ValueError, TypeError) as error:
                            st.error(f"Could not save application scores: {error}")


render_admin_page()
