
from core.filtering import filter_databases
from core.explanations import explain_database


def test_filtering_and_explanation_work_together():
    databases = [
        {
            "id": "postgresql",
            "name": "PostgreSQL",
            "capabilities": {"supports_sql": True},
            "scores": {
                "scalability": 4,
                "simplicity": 3,
                "cost": None,
            },
        },
        {
            "id": "example_db",
            "name": "Example DB",
            "capabilities": {"supports_sql": False},
            "scores": {},
        },
    ]

    eligible, excluded = filter_databases(
        databases, ["supports_sql"]
    )

    assert len(eligible) == 1
    assert eligible[0]["name"] == "PostgreSQL"
    assert len(excluded) == 1
    assert excluded[0]["database"]["name"] == "Example DB"

    explanation = explain_database(eligible[0])

    assert explanation["database"] == "PostgreSQL"
    assert "cost" in explanation["unknown_criteria"]
