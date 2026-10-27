import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.catalogue import load_databases
from core.filtering import filter_databases
from core.explanations import explain_database

ROOT = Path(__file__).resolve().parent
with open(ROOT / "data" / "applications.json", encoding="utf-8") as f:
    applications = json.load(f)

st.set_page_config(page_title="Database Recommendation System", page_icon="🗄️", layout="wide")
st.title("Database Selection & Recommendation System")
st.caption("Prototype: mandatory filtering + transparent catalogue comparison")

databases = load_databases()
application_name = st.selectbox("Choose your application type", [a["name"] for a in applications])
application = next(a for a in applications if a["name"] == application_name)

st.write(application["description"])
eligible, excluded = filter_databases(databases, application["mandatory_requirements"])

left, right = st.columns(2)
left.metric("Eligible databases", len(eligible))
right.metric("Excluded databases", len(excluded))

if eligible:
    rows = []
    for db in eligible:
        row = {"Database": db["name"], "Type": db["type"]}
        row.update({k.replace("_", " ").title(): v for k, v in db.get("scores", {}).items()})
        rows.append(row)
    st.subheader("Eligible database catalogue")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if len(rows) > 1:
        score_cols = [c for c in rows[0] if c not in ("Database", "Type")]
        chosen = st.selectbox("Inspect a database", [d["name"] for d in eligible])
        selected = next(d for d in eligible if d["name"] == chosen)
        explanation = explain_database(selected, eligible, [c.lower().replace(" ", "_") for c in score_cols])
        st.subheader(f"Explanation: {chosen}")
        st.markdown("**Strengths**")
        for item in explanation["strengths"]:
            st.write(f"- {item}")
        st.markdown("**Weaknesses**")
        for item in explanation["weaknesses"]:
            st.write(f"- {item}")
        st.info(explanation["caveat"])
else:
    st.warning("No database satisfies all selected mandatory requirements. Review the requirements or catalogue.")

if excluded:
    with st.expander("View excluded databases and reasons"):
        for item in excluded:
            st.write(f"**{item['database']['name']}** — " + ", ".join(item["reasons"]))

st.caption("Prototype notice: catalogue scores are illustrative, not validated research results. AHP/TOPSIS integration is pending.")
