
import numpy as np

from topsis.topsis import rank_databases


def evaluate_ranking_reliability(
    decision_matrix,
    weights,
    criteria_types,
    alternatives,
    criteria_names=None,
    score_min=1,
    score_mid=3,
    score_max=5,
):
    """
    Test TOPSIS ranking stability under uncertain criterion scores.

    Each database-criterion score is replaced individually with the
    low, middle, and high scenario values. TOPSIS is recalculated for
    every scenario.

    These are what-if scenarios, not predictions or probabilities.
    """

    matrix = np.asarray(decision_matrix, dtype=float)
    weights = np.asarray(weights, dtype=float)
    alternatives = list(alternatives)
    criteria_types = list(criteria_types)

    if matrix.ndim != 2 or matrix.size == 0:
        raise ValueError("Decision matrix must be a non-empty 2D matrix.")

    rows, cols = matrix.shape

    if rows < 2:
        raise ValueError("At least two databases are required.")

    if cols < 1:
        raise ValueError("At least one criterion is required.")

    if len(alternatives) != rows:
        raise ValueError("Database names must match matrix rows.")

    if len(criteria_types) != cols:
        raise ValueError("Criterion types must match matrix columns.")

    if len(weights) != cols:
        raise ValueError("Weights must match matrix columns.")

    if not np.all(np.isfinite(matrix)):
        raise ValueError(
            "Baseline scores must be complete and finite. "
            "Do not replace missing scores silently."
        )

    if not np.all((matrix >= score_min) & (matrix <= score_max)):
        raise ValueError(
            f"Scores must be between {score_min} and {score_max}."
        )

    if not (score_min <= score_mid <= score_max):
        raise ValueError("Scenario values must be in ascending order.")

    if criteria_names is None:
        criteria_names = [
            f"Criterion {i + 1}" for i in range(cols)
        ]

    criteria_names = list(criteria_names)

    if len(criteria_names) != cols:
        raise ValueError("Criterion names must match matrix columns.")

    # Original ranking used as the reference.
    baseline = rank_databases(
        decision_matrix=matrix,
        weights=weights,
        criteria_types=criteria_types,
        alternatives=alternatives,
    )

    baseline_order = [
        item["database"] for item in baseline
    ]

    baseline_ranks = {
        item["database"]: item["rank"] for item in baseline
    }

    original_winner = baseline_order[0]

    scenario_rows = []
    exact_order_matches = 0
    winner_retained = 0
    total_rank_movement = 0
    total_rank_observations = 0

    scenario_values = [
        ("Low", score_min),
        ("Middle", score_mid),
        ("High", score_max),
    ]

    # Test every score independently at low, middle and high values.
    for row_index, database in enumerate(alternatives):
        for col_index, criterion in enumerate(criteria_names):
            original_value = matrix[row_index, col_index]

            for scenario_name, scenario_value in scenario_values:
                changed_matrix = matrix.copy()
                changed_matrix[row_index, col_index] = scenario_value

                changed_ranking = rank_databases(
                    decision_matrix=changed_matrix,
                    weights=weights,
                    criteria_types=criteria_types,
                    alternatives=alternatives,
                )

                changed_order = [
                    item["database"] for item in changed_ranking
                ]

                changed_ranks = {
                    item["database"]: item["rank"]
                    for item in changed_ranking
                }

                same_order = changed_order == baseline_order
                same_winner = changed_order[0] == original_winner

                if same_order:
                    exact_order_matches += 1

                if same_winner:
                    winner_retained += 1

                rank_movements = {
                    name: baseline_ranks[name] - changed_ranks[name]
                    for name in alternatives
                }

                total_rank_movement += sum(
                    abs(change) for change in rank_movements.values()
                )
                total_rank_observations += len(alternatives)

                scenario_rows.append({
                    "database_tested": database,
                    "criterion_tested": criterion,
                    "scenario": scenario_name,
                    "original_score": float(original_value),
                    "scenario_score": float(scenario_value),
                    "original_winner": original_winner,
                    "new_winner": changed_order[0],
                    "winner_retained": same_winner,
                    "ranking_order_unchanged": same_order,
                    "new_ranking": " > ".join(changed_order),
                    "rank_changes": rank_movements,
                })

    total_scenarios = len(scenario_rows)

    return {
        "baseline_ranking": baseline,
        "baseline_order": baseline_order,
        "original_winner": original_winner,
        "scenario_count": total_scenarios,
        "ranking_order_stability_percent": round(
            exact_order_matches / total_scenarios * 100, 2
        ),
        "top_recommendation_retention_percent": round(
            winner_retained / total_scenarios * 100, 2
        ),
        "average_absolute_rank_movement": round(
            total_rank_movement / total_rank_observations, 3
        ),
        "scenarios": scenario_rows,
        "interpretation": (
            "Higher stability percentages mean the ranking changed "
            "less often in the tested scenarios. These results describe "
            "only the tested score changes and are not probabilities "
            "of real-world database performance."
        ),
    }
