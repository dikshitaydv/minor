
import json
from pathlib import Path

SCORING_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "application_scores.json"
)


def load_application_scores(application_id, path=SCORING_FILE):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    try:
        return data["applications"][application_id]
    except KeyError as exc:
        raise ValueError(
            f"No scoring data found for application: {application_id}"
        ) from exc


def apply_application_scores(
    databases, application_id, path=SCORING_FILE
):
    application_scores = load_application_scores(application_id, path)
    result = []

    for database in databases:
        updated_database = dict(database)
        database_scores = application_scores.get(database["id"], {})

        updated_database["scores"] = {
            criterion: details.get("score")
            for criterion, details in database_scores.items()
        }

        updated_database["score_evidence"] = {
            criterion: {
                "evidence_url": details.get("evidence_url"),
                "verified_on": details.get("verified_on"),
            }
            for criterion, details in database_scores.items()
        }

        result.append(updated_database)

    return result
