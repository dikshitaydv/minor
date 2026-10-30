
import numpy as np
import pytest

from core.ranking_reliability import evaluate_ranking_reliability


@pytest.fixture
def example_data():
    return {
        "decision_matrix": [
            [5, 4],
            [3, 3],
            [2, 5],
        ],
        "weights": [0.6, 0.4],
        "criteria_types": ["benefit", "benefit"],
        "alternatives": ["Database A", "Database B", "Database C"],
        "criteria_names": ["Security", "Scalability"],
    }


def test_reliability_generates_expected_scenarios(example_data):
    result = evaluate_ranking_reliability(**example_data)

    # 18 possible scenarios minus 4 unchanged scenarios.
    assert result["scenario_count"] == 14
    assert len(result["scenarios"]) == 14
    assert result["skipped_unchanged_scenarios"] == 4


def test_stability_metrics_are_in_valid_ranges(example_data):
    result = evaluate_ranking_reliability(**example_data)

    assert 0 <= result["ranking_order_stability_percent"] <= 100
    assert 0 <= result["top_recommendation_retention_percent"] <= 100
    assert result["average_absolute_rank_movement"] >= 0


def test_original_ranking_is_preserved(example_data):
    result = evaluate_ranking_reliability(**example_data)

    assert result["baseline_order"] == [
        item["database"] for item in result["baseline_ranking"]
    ]
    assert result["original_winner"] == result["baseline_order"][0]


def test_missing_baseline_score_is_rejected(example_data):
    example_data["decision_matrix"][0][0] = np.nan

    with pytest.raises(ValueError, match="complete and finite"):
        evaluate_ranking_reliability(**example_data)


def test_scores_outside_scale_are_rejected(example_data):
    example_data["decision_matrix"][0][0] = 8

    with pytest.raises(ValueError, match="between"):
        evaluate_ranking_reliability(**example_data)


def test_invalid_weight_count_is_rejected(example_data):
    example_data["weights"] = [1.0]

    with pytest.raises(ValueError, match="Weights must match"):
        evaluate_ranking_reliability(**example_data)
