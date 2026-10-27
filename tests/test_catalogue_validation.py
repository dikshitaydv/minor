
import pytest

from core.catalogue import validate_databases


def valid_database():
    return {
        "id": "test_db",
        "name": "Test DB",
        "type": "relational",
        "scores": {"cost": 3, "scalability": None},
        "evidence_urls": ["https://example.com/docs"],
        "verified_on": None,
    }


def test_valid_database_is_accepted():
    data = [valid_database()]
    assert validate_databases(data) == data


def test_duplicate_ids_are_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_databases([valid_database(), valid_database()])


def test_scores_outside_scale_are_rejected():
    db = valid_database()
    db["scores"]["cost"] = 6
    with pytest.raises(ValueError, match="between 1 and 5"):
        validate_databases([db])


def test_unknown_scores_are_allowed():
    db = valid_database()
    db["scores"]["cost"] = None
    assert validate_databases([db])[0]["scores"]["cost"] is None


def test_invalid_verification_date_is_rejected():
    db = valid_database()
    db["verified_on"] = "not-a-date"
    with pytest.raises(ValueError, match="verified_on"):
        validate_databases([db])
