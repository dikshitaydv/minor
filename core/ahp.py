
import numpy as np


# Saaty's Random Index values
RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


def validate_matrix(matrix):
    """Validate an AHP pairwise comparison matrix."""
    matrix = np.asarray(matrix, dtype=float)

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Pairwise matrix must be square.")

    n = matrix.shape[0]

    if n == 0:
        raise ValueError("Pairwise matrix cannot be empty.")

    if not np.all(np.isfinite(matrix)) or np.any(matrix <= 0):
        raise ValueError("Matrix values must be finite and positive.")

    if not np.allclose(np.diag(matrix), 1.0):
        raise ValueError("Diagonal elements must all equal 1.")

    if not np.allclose(matrix * matrix.T, 1.0, atol=1e-8):
        raise ValueError("Matrix must be reciprocal: a[j,i] = 1/a[i,j].")

    return matrix


def compute_weights(matrix):
    """
    Calculate AHP criteria weights and consistency ratio.

    Returns:
        weights: NumPy array of criteria weights.
        cr: Consistency ratio.
    """
    matrix = validate_matrix(matrix)
    n = matrix.shape[0]

    # A single criterion has weight 1 and no inconsistency.
    if n == 1:
        return np.array([1.0]), 0.0

    # Step 1: Normalize each column.
    column_sums = matrix.sum(axis=0)
    normalized = matrix / column_sums

    # Step 2: Average each row to obtain criteria weights.
    weights = normalized.mean(axis=1)

    # Ensure weights sum to 1 despite floating-point rounding.
    weights = weights / weights.sum()

    # Step 3: Calculate lambda max.
    weighted_sum = matrix @ weights
    lambda_max = float(np.mean(weighted_sum / weights))

    # Step 4: Calculate Consistency Index.
    ci = (lambda_max - n) / (n - 1)

    # Small negative values can occur due to floating-point error.
    ci = max(0.0, ci)

    # Step 5: Calculate Consistency Ratio.
    ri = RANDOM_INDEX.get(n)

    if ri is None:
        raise ValueError(
            f"Random Index is unavailable for {n} criteria."
        )

    cr = 0.0 if ri == 0 else ci / ri

    return weights, float(cr)


def get_ahp_details(matrix):
    """Return intermediate AHP calculations for display in the UI."""
    matrix = validate_matrix(matrix)
    weights, cr = compute_weights(matrix)

    normalized = matrix / matrix.sum(axis=0)

    n = matrix.shape[0]
    if n == 1:
        lambda_max = 1.0
        ci = 0.0
    else:
        lambda_max = float(np.mean((matrix @ weights) / weights))
        ci = max(0.0, (lambda_max - n) / (n - 1))

    return {
        "normalized_matrix": normalized,
        "weights": weights,
        "lambda_max": lambda_max,
        "ci": ci,
        "cr": cr,
        "is_consistent": cr <= 0.10,
    }
