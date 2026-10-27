
import numpy as np


def rank_databases(decision_matrix, weights, criteria_types, alternatives=None):
    """
    Rank database alternatives using TOPSIS.

    Args:
        decision_matrix: 2D array; rows = databases, columns = criteria.
        weights: AHP weights, one per criterion, summing to 1.
        criteria_types: One value per criterion: "benefit" or "cost".
        alternatives: Optional database names matching matrix rows.

    Returns:
        List of dictionaries sorted by closeness coefficient (descending).
    """
    matrix = np.asarray(decision_matrix, dtype=float)
    weights = np.asarray(weights, dtype=float)
    criteria_types = [c.lower() for c in criteria_types]

    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("Decision matrix must be a non-empty 2D matrix.")

    rows, cols = matrix.shape

    if weights.ndim != 1 or len(weights) != cols:
        raise ValueError("Number of weights must match the criteria count.")

    if len(criteria_types) != cols:
        raise ValueError("Criteria types must match the criteria count.")

    if not np.all(np.isfinite(matrix)):
        raise ValueError("Decision matrix values must be finite.")

    if not np.all(np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("Weights must be finite and non-negative.")

    if not np.isclose(weights.sum(), 1.0):
        raise ValueError("Weights must sum to 1.")

    if any(c not in {"benefit", "cost"} for c in criteria_types):
        raise ValueError("Each criterion type must be 'benefit' or 'cost'.")

    if alternatives is None:
        alternatives = [f"Alternative {i + 1}" for i in range(rows)]

    if len(alternatives) != rows:
        raise ValueError("Alternative names must match the row count.")

    if any(not str(name).strip() for name in alternatives):
        raise ValueError("Alternative names cannot be empty.")

    # Vector normalization.
    norms = np.linalg.norm(matrix, axis=0)
    if np.any(norms == 0):
        raise ValueError("A criterion column cannot contain only zeros.")

    normalized = matrix / norms

    # Apply AHP criterion weights.
    weighted = normalized * weights

    # Determine ideal best and ideal worst for each criterion.
    ideal_best = np.empty(cols)
    ideal_worst = np.empty(cols)

    for j, criterion_type in enumerate(criteria_types):
        if criterion_type == "benefit":
            ideal_best[j] = weighted[:, j].max()
            ideal_worst[j] = weighted[:, j].min()
        else:
            ideal_best[j] = weighted[:, j].min()
            ideal_worst[j] = weighted[:, j].max()

    # Euclidean distances from the ideal best and worst.
    distance_best = np.linalg.norm(weighted - ideal_best, axis=1)
    distance_worst = np.linalg.norm(weighted - ideal_worst, axis=1)

    denominator = distance_best + distance_worst
    closeness = np.divide(
        distance_worst,
        denominator,
        out=np.full(rows, 0.5),
        where=denominator != 0,
    )

    results = [
        {
            "database": str(alternatives[i]),
            "score": float(closeness[i]),
            "rank": 0,
        }
        for i in range(rows)
    ]

    results.sort(key=lambda item: item["score"], reverse=True)

    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    return results
