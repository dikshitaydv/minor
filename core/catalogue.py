
"""Load and validate the database catalogue."""
import json
from datetime import date
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "databases.json"


def validate_databases(data):
    if not isinstance(data, list):
        raise ValueError("databases.json must contain a list")

    seen_ids = set()
    required = {"id", "name", "type", "scores", "evidence_urls", "verified_on"}

    for index, db in enumerate(data):
        location = f"Database entry {index}"

        if not isinstance(db, dict):
            raise ValueError(f"{location} must be an object")

        missing = required - db.keys()
        if missing:
            raise ValueError(f"{location} missing fields: {sorted(missing)}")

        if not isinstance(db["id"], str) or not db["id"].strip():
            raise ValueError(f"{location}: id must be a non-empty string")

        if db["id"] in seen_ids:
            raise ValueError(f"Duplicate database id: {db['id']}")
        seen_ids.add(db["id"])

        if not isinstance(db["name"], str) or not db["name"].strip():
            raise ValueError(f"{location}: name must be a non-empty string")

        if not isinstance(db["scores"], dict):
            raise ValueError(f"{location}: scores must be an object")

        for criterion, score in db["scores"].items():
            if score is None:
                continue
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(f"{location}: {criterion} must be a number or null")
            if not 1 <= score <= 5:
                raise ValueError(f"{location}: {criterion} must be between 1 and 5")

        if not isinstance(db["evidence_urls"], list):
            raise ValueError(f"{location}: evidence_urls must be a list")

        if not all(
            isinstance(url, str) and url.startswith(("https://", "http://"))
            for url in db["evidence_urls"]
        ):
            raise ValueError(f"{location}: evidence URLs must be valid HTTP(S) URLs")

        verified_on = db["verified_on"]
        if verified_on is not None:
            try:
                date.fromisoformat(verified_on)
            except (TypeError, ValueError):
                raise ValueError(
                    f"{location}: verified_on must be YYYY-MM-DD or null"
                )

    return data


def load_databases(path=DATA_FILE):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return validate_databases(data)

