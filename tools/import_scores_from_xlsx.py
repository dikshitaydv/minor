"""Import VERIFIED rows from the scoring workbook into application_scores.json.

Creates missing database and criterion entries for known applications while
preserving all existing scores. Only rows marked VERIFIED are imported.
"""
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "database_criteria_scoring_workbook.xlsx"
JSON_FILE = ROOT / "data" / "application_scores.json"


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_verified_date(value):
    if pd.isna(value) or not clean_text(value):
        return date.today().isoformat()
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.date().isoformat() if isinstance(value, pd.Timestamp) else value.isoformat()
    return clean_text(value)[:10]


def main():
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")
    if not JSON_FILE.exists():
        raise FileNotFoundError(f"Scoring JSON not found: {JSON_FILE}")

    df = pd.read_excel(WORKBOOK, sheet_name="Scoring Review")
    required = {
        "application_id",
        "criterion_id",
        "database_id",
        "proposed_score_1_to_5",
        "evidence_url",
        "verified_on",
        "review_status",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Workbook missing columns: {sorted(missing)}")

    approved = df[
        df["review_status"].astype(str).str.strip().str.upper() == "VERIFIED"
    ].copy()

    if approved.empty:
        print("No rows marked VERIFIED. JSON was not changed.")
        return

    data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    applications = data.setdefault("applications", {})

    # Use the existing databases' criterion IDs as the allowed criteria for
    # each application. This prevents a typo in a workbook criterion ID from
    # silently creating an unrelated criterion.
    criteria_by_app = {}
    for app_id, databases in applications.items():
        allowed = set()
        for db_entries in databases.values():
            if isinstance(db_entries, dict):
                allowed.update(db_entries.keys())
        criteria_by_app[app_id] = allowed

    updates = []
    seen = set()

    for _, row in approved.iterrows():
        app_id = clean_text(row["application_id"])
        db_id = clean_text(row["database_id"])
        cid = clean_text(row["criterion_id"])

        if not app_id or not db_id or not cid:
            raise ValueError("Workbook contains a VERIFIED row with a blank application_id, database_id, or criterion_id.")

        if app_id not in applications:
            raise ValueError(f"Unknown application_id in workbook: {app_id}")

        if cid not in criteria_by_app.get(app_id, set()):
            raise ValueError(
                f"Unknown criterion_id for application {app_id}: {cid}. "
                "Check the criterion ID against the existing application definitions."
            )

        key = (app_id, db_id, cid)
        if key in seen:
            raise ValueError(f"Duplicate VERIFIED workbook row: {app_id}/{db_id}/{cid}")
        seen.add(key)

        score_value = row["proposed_score_1_to_5"]
        if pd.isna(score_value):
            raise ValueError(f"Missing score for {app_id}/{db_id}/{cid}")
        try:
            score = int(score_value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid score for {app_id}/{db_id}/{cid}: {score_value}")
        if score not in range(1, 6) or float(score_value) != score:
            raise ValueError(f"Score must be a whole number from 1 to 5 for {app_id}/{db_id}/{cid}")

        evidence_url = clean_text(row["evidence_url"])
        if not evidence_url:
            raise ValueError(f"Missing evidence_url for VERIFIED row {app_id}/{db_id}/{cid}")

        updates.append({
            "application_id": app_id,
            "database_id": db_id,
            "criterion_id": cid,
            "score": score,
            "evidence_url": evidence_url,
            "verified_on": normalize_verified_date(row["verified_on"]),
        })

    # Apply updates only after all VERIFIED rows pass validation.
    for item in updates:
        app_scores = applications[item["application_id"]]
        db_scores = app_scores.setdefault(item["database_id"], {})
        entry = db_scores.setdefault(item["criterion_id"], {})
        entry["score"] = item["score"]
        entry["evidence_url"] = item["evidence_url"]
        entry["verified_on"] = item["verified_on"]

    backup = JSON_FILE.with_suffix(JSON_FILE.suffix + ".bak")
    backup.write_text(JSON_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    JSON_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    new_pairs = sorted({
        (item["application_id"], item["database_id"])
        for item in updates
    })
    print(f"Imported {len(updates)} VERIFIED rows.")
    print("Database/application entries updated:")
    for app_id, db_id in new_pairs:
        print(f"  - {app_id}/{db_id}")
    print(f"Backup created at: {backup}")


if __name__ == "__main__":
    main()
