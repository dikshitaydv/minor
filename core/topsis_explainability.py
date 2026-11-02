
import numpy as np


def explain_topsis(
    decision_matrix,
    weights,
    criteria_types,
    criteria_names,
    alternatives=None,
    sensitivity_percent=20,
):
    """
    Explain the ranking produced by the project's TOPSIS method.

    decision_matrix: rows = databases, columns = criteria
    weights: AHP weights, summing to 1
    criteria_types: "benefit" or "cost"
    criteria_names: names in the same order as matrix columns
    alternatives: database names in matrix row order

    Sensitivity analysis increases one criterion's weight at a time,
    then renormalizes all weights and recalculates TOPSIS.
    """

    matrix = np.asarray(decision_matrix, dtype=float)
    weights = np.asarray(weights, dtype=float)
    types = [c.lower() for c in criteria_types]
    names = list(criteria_names)

    if matrix.ndim != 2 or matrix.shape[0] < 2:
        raise ValueError("At least two databases are required.")

    rows, cols = matrix.shape

    if cols < 2:
        raise ValueError("At least two criteria are required.")

    if len(weights) != cols or len(types) != cols or len(names) != cols:
        raise ValueError("Criteria, types, weights and matrix columns must match.")

    if not np.all(np.isfinite(matrix)):
        raise ValueError("All criterion scores must be numeric and finite.")

    if not np.all(np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("Weights must be finite and non-negative.")

    if not np.isclose(weights.sum(), 1.0):
        raise ValueError("AHP weights must sum to 1.")

    if any(t not in {"benefit", "cost"} for t in types):
        raise ValueError("Criterion types must be benefit or cost.")

    if len(set(names)) != len(names):
        raise ValueError("Criterion names must be unique.")

    if alternatives is None:
        alternatives = [f"Alternative {i + 1}" for i in range(rows)]

    if len(alternatives) != rows:
        raise ValueError("Database names must match matrix rows.")

    if sensitivity_percent < 0:
        raise ValueError("Sensitivity percentage cannot be negative.")

    # Same vector normalization as rank_databases().
    norms = np.linalg.norm(matrix, axis=0)

    if np.any(norms == 0):
        raise ValueError("A criterion column cannot contain only zeros.")

    normalized = matrix / norms

    def calculate_topisis(current_weights):
        """Repeat the existing TOPSIS calculation with supplied weights."""
        weighted = normalized * current_weights

        ideal_best = np.empty(cols)
        ideal_worst = np.empty(cols)

        for j, criterion_type in enumerate(types):
            if criterion_type == "benefit":
                ideal_best[j] = weighted[:, j].max()
                ideal_worst[j] = weighted[:, j].min()
            else:
                ideal_best[j] = weighted[:, j].min()
                ideal_worst[j] = weighted[:, j].max()

        distance_best = np.linalg.norm(
            weighted - ideal_best, axis=1
        )
        distance_worst = np.linalg.norm(
            weighted - ideal_worst, axis=1
        )

        denominator = distance_best + distance_worst

        scores = np.divide(
            distance_worst,
            denominator,
            out=np.full(rows, 0.5),
            where=denominator != 0,
        )

        order = np.argsort(-scores, kind="stable")
        ranks = np.empty(rows, dtype=int)

        for rank, index in enumerate(order, start=1):
            ranks[index] = rank

        return {
            "weighted": weighted,
            "ideal_best": ideal_best,
            "ideal_worst": ideal_worst,
            "distance_best": distance_best,
            "distance_worst": distance_worst,
            "scores": scores,
            "ranks": ranks,
        }

    baseline = calculate_topisis(weights)
    weighted = baseline["weighted"]
    ideal_best = baseline["ideal_best"]
    ideal_worst = baseline["ideal_worst"]

    # Criterion-level differences from the ideal solutions.
    best_parts = (weighted - ideal_best) ** 2
    worst_parts = (weighted - ideal_worst) ** 2

    best_totals = best_parts.sum(axis=1)
    worst_totals = worst_parts.sum(axis=1)

    # Sensitivity: increase each criterion weight independently.
    sensitivity = {}

    for j, criterion in enumerate(names):
        changed_weights = weights.copy()
        changed_weights[j] *= 1 + sensitivity_percent / 100

        if changed_weights.sum() == 0:
            continue

        changed_weights /= changed_weights.sum()
        changed = calculate_topisis(changed_weights)

        sensitivity[criterion] = {
            str(alternatives[i]): {
                "original_rank": int(baseline["ranks"][i]),
                "new_rank": int(changed["ranks"][i]),
                "rank_change": int(
                    baseline["ranks"][i] - changed["ranks"][i]
                ),
                "new_score": round(float(changed["scores"][i]), 4),
            }
            for i in range(rows)
        }

    results = []

    for i, database in enumerate(alternatives):
        criterion_details = {}

        for j, criterion in enumerate(names):
            # Relative position among the available alternatives.
            column = normalized[:, j]

            if types[j] == "cost":
                column = -column

            low = column.min()
            high = column.max()

            if np.isclose(high, low):
                relative_position = 0.5
            else:
                relative_position = (
                    (column[i] - low) / (high - low)
                )

            # Share of this database's squared distance.
            best_share = (
                best_parts[i, j] / best_totals[i] * 100
                if best_totals[i] else 0.0
            )
            worst_share = (
                worst_parts[i, j] / worst_totals[i] * 100
                if worst_totals[i] else 0.0
            )

            if np.isclose(high, low):
                position = "same as other databases"
            elif relative_position >= 0.8:
                position = "strong relative performance"
            elif relative_position <= 0.2:
                position = "weak relative performance"
            else:
                position = "middle relative performance"

            criterion_details[criterion] = {
                "raw_score": float(matrix[i, j]),
                "ahp_weight": round(float(weights[j]), 4),
                "weight_percent": round(float(weights[j] * 100), 2),
                "weighted_value": round(float(weighted[i, j]), 4),
                "ideal_best_value": round(float(ideal_best[j]), 4),
                "ideal_worst_value": round(float(ideal_worst[j]), 4),
                "relative_position": round(float(relative_position), 3),
                "performance_description": position,
                "distance_from_ideal_share_percent": round(
                    float(best_share), 2
                ),
                "distance_from_worst_share_percent": round(
                    float(worst_share), 2
                ),
            }

        strong = [
            c for c, d in criterion_details.items()
            if d["performance_description"] == "strong relative performance"
        ]
        weak = [
            c for c, d in criterion_details.items()
            if d["performance_description"] == "weak relative performance"
        ]

        results.append({
            "database": str(database),
            "rank": int(baseline["ranks"][i]),
            "topsis_score": round(float(baseline["scores"][i]), 4),
            "distance_from_ideal": round(
                float(baseline["distance_best"][i]), 4
            ),
            "distance_from_worst": round(
                float(baseline["distance_worst"][i]), 4
            ),
            "strong_criteria": strong,
            "weak_criteria": weak,
            "criteria": criterion_details,
            "sensitivity": {
                c: sensitivity[c][str(database)]
                for c in names
            },
        })

    results.sort(key=lambda item: item["rank"])
    return results
