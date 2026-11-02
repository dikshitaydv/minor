
import pytest

import core.recommendation as recommendation


def test_recommendation_pipeline_saves_and_ranks(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        recommendation,
        "save_configuration",
        lambda config_name, criteria_weights, preferences=None: 1,
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
        config_name="test_config",
        preferences={"database_type": "relational"},
    )

    assert result["config_version"] == 1
    assert result["is_consistent"] is True
    assert len(result["criteria_weights"]) == 2
    assert result["rankings"][0]["database"] == "MySQL"


def test_inconsistent_ahp_matrix_stops_pipeline(monkeypatch):
    def unexpected_save(*args, **kwargs):
        pytest.fail("Inconsistent configuration should not be saved")

    monkeypatch.setattr(
        recommendation, "save_configuration", unexpected_save
    )

    with pytest.raises(ValueError, match="inconsistent"):
        recommendation.recommend_databases(
            pairwise_matrix=[
                [1, 9, 1],
                [1 / 9, 1, 9],
                [1, 1 / 9, 1],
            ],
            decision_matrix=[
                [9, 2, 8],
                [5, 8, 4],
            ],
            criteria_types=["benefit", "benefit", "benefit"],
            alternatives=["PostgreSQL", "MySQL"],
            config_name="inconsistent_config",
        )
