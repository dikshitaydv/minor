
import numpy as np
import pytest

from core.ahp import compute_weights, get_ahp_details


def test_single_criterion():
    weights, cr = compute_weights([[1]])

    assert np.allclose(weights, [1.0])
    assert cr == 0.0


def test_equal_importance():
    matrix = np.ones((3, 3))

    weights, cr = compute_weights(matrix)

    assert np.allclose(weights, [1 / 3] * 3)
    assert cr == pytest.approx(0.0, abs=1e-8)


def test_weights_sum_to_one():
    matrix = [
        [1, 3, 4],
        [1 / 3, 1, 2],
        [1 / 4, 1 / 2, 1],
    ]

    weights, cr = compute_weights(matrix)

    assert np.isclose(weights.sum(), 1.0)
    assert np.all(weights > 0)
    assert cr >= 0


def test_inconsistent_matrix_is_flagged():
    matrix = [
        [1, 9, 1 / 9],
        [1 / 9, 1, 9],
        [9, 1 / 9, 1],
    ]

    details = get_ahp_details(matrix)

    assert details["cr"] > 0.10
    assert details["is_consistent"] is False


def test_invalid_matrix_rejected():
    with pytest.raises(ValueError):
        compute_weights([[1, 2], [2, 1]])


def test_non_square_matrix_rejected():
    with pytest.raises(ValueError):
        compute_weights([[1, 2, 3], [1, 1, 2]])
