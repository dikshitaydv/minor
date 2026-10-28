"""Import only rows marked VERIFIED from workbook into application_scores.json."""
import json
from datetime import date
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "database_criteria_scoring_workbook.xlsx"
JSON_FILE = ROOT / "data" / "application_scores.json"

def main():
    df = pd.read_excel(WORKBOOK, sheet_name="Scoring Review")
    required = {"application_id","criterion_id","database_id","proposed_score_1_to_5","evidence_url","verified_on","review_status"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Workbook missing columns: {sorted(missing)}")
    approved = df[df["review_status"].astype(str).str.strip().str.upper() == "VERIFIED"]
    if approved.empty:
        print("No rows marked VERIFIED. JSON was not changed.")
        return
    data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    for _, row in approved.iterrows():
        score = row["proposed_score_1_to_5"]
        if pd.isna(score) or int(score) not in range(1,6):
            raise ValueError(f"Invalid score for {row['application_id']}/{row['database_id']}/{row['criterion_id']}")
        app_id, db_id, cid = str(row["application_id"]).strip(), str(row["database_id"]).strip(), str(row["criterion_id"]).strip()
        try:
            entry = data["applications"][app_id][db_id][cid]
        except KeyError as exc:
            raise ValueError(f"ID mismatch in workbook: {app_id}/{db_id}/{cid}") from exc
        entry["score"] = int(score)
        entry["evidence_url"] = None if pd.isna(row["evidence_url"]) else str(row["evidence_url"]).strip()
        verified = row["verified_on"]
        entry["verified_on"] = date.today().isoformat() if pd.isna(verified) or not str(verified).strip() else str(verified)[:10]
    backup = JSON_FILE.with_suffix(".json.bak")
    backup.write_text(JSON_FILE.read_text(encoding="utf-8"),encoding="utf-8")
    JSON_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Imported {len(approved)} verified rows. Backup created at {backup}")

if __name__ == "__main__":
    main()
