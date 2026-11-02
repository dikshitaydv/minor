
import storage.database as database


def test_save_and_retrieve_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "test.db"
    )

    version = database.save_configuration(
        "balanced",
        {"performance": 0.5, "cost": 0.5},
        {"engine": "relational"},
    )

    result = database.get_configuration("balanced")

    assert version == 1
    assert result["criteria_weights"] == {
        "performance": 0.5,
        "cost": 0.5,
    }
    assert result["preferences"]["engine"] == "relational"


def test_configuration_versions_are_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "test.db"
    )

    database.save_configuration(
        "balanced", {"performance": 0.5, "cost": 0.5}
    )
    database.save_configuration(
        "balanced", {"performance": 0.7, "cost": 0.3}
    )

    latest = database.get_configuration("balanced")
    previous = database.get_configuration("balanced", version=1)
    history = database.get_configuration_history("balanced")

    assert latest["version"] == 2
    assert latest["criteria_weights"]["performance"] == 0.7
    assert previous["criteria_weights"]["performance"] == 0.5
    assert [item["version"] for item in history] == [1, 2]


def test_empty_configuration_name_rejected():
    import pytest

    with pytest.raises(ValueError):
        database.save_configuration(
            "", {"performance": 1.0}
        )
