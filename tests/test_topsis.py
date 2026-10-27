
import pytest

from topsis.topsis import rank_databases


def test_benefit_criteria_ranking():
    results = rank_databases(
        decision_matrix=[[9, 2], [5, 8], [7, 5]],
        weights=[0.5, 0.5],
        criteria_types=["benefit", "benefit"],
        alternatives=["PostgreSQL", "MySQL", "MongoDB"],
    )
    #print(results)

    assert results[0]["database"] == "MySQL"
    assert results[0]["rank"] == 1
    assert all(0 <= result["score"] <= 1 for result in results)


def test_cost_criterion_prefers_lower_value():
    results = rank_databases(
        decision_matrix=[[10], [5], [2]],
        weights=[1.0],
        criteria_types=["cost"],
        alternatives=["A", "B", "C"],
    )

    assert results[0]["database"] == "C"


def test_invalid_weights_rejected():
    with pytest.raises(ValueError):
        rank_databases([[1, 2], [3, 4]], [0.5], ["benefit", "cost"])


def test_invalid_criterion_type_rejected():
    with pytest.raises(ValueError):
        rank_databases([[1], [2]], [1.0], ["unknown"])


def test_alternative_count_must_match():
    with pytest.raises(ValueError):
        rank_databases(
            [[1], [2]], [1.0], ["benefit"], alternatives=["Only one"]
        )
