
import core.recommendation as recommendation
import storage.database as database


def test_pipeline_saves_configuration_to_sqlite(
    tmp_path, monkeypatch
):
    # Use a temporary database, not the project's real database.
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "integration.db"
    )

    # Make the pipeline use the same storage module we are testing.
    monkeypatch.setattr(
        recommendation,
        "save_configuration",
        database.save_configuration,
    )

    result = recommendation.recommend_databases(
        pairwise_matrix=[
            [1, 1],
            [1, 1],
        ],
        decision_matrix=[
            [9, 2],
            [5, 8],
            [7, 5],
        ],
        criteria_types=["benefit", "benefit"],
        alternatives=["PostgreSQL", "MySQL", "MongoDB"],
        config_name="integration_test",
        preferences={"database_type": "relational"},
    )

    saved = database.get_configuration("integration_test")

    assert result["config_version"] == 1
    assert saved is not None
    assert saved["version"] == 1
    assert saved["preferences"]["database_type"] == "relational"
    assert len(saved["criteria_weights"]) == 2
    assert result["rankings"][0]["database"] == "MySQL"
