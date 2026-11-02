
from core.ahp import get_ahp_details
from topsis.topsis import rank_databases
from storage.database import save_configuration


def recommend_databases(
    pairwise_matrix,
    decision_matrix,
    criteria_types,
    alternatives,
    config_name,
    preferences=None,
    allow_inconsistent=False,
):
    """
    Calculate AHP weights, rank database alternatives using TOPSIS,
    and save the configuration in SQLite.

    Args:
        pairwise_matrix: AHP pairwise comparison matrix for criteria.
        decision_matrix: Rows are databases; columns are criteria.
        criteria_types: "benefit" or "cost" for each criterion.
        alternatives: Database names corresponding to decision matrix rows.
        config_name: Name used to identify configuration history.
        preferences: Optional dictionary of additional preferences.
        allow_inconsistent: Whether to continue when AHP CR > 0.10.

    Returns:
        Dictionary containing AHP details, rankings, and saved version.
    """

    # 1. Calculate criteria weights and consistency information.
    ahp_details = get_ahp_details(pairwise_matrix)

    consistency_ratio = ahp_details["cr"]
    is_consistent = ahp_details["is_consistent"]

    # 2. Do not recommend using inconsistent comparisons by default.
    if not is_consistent and not allow_inconsistent:
        raise ValueError(
            f"AHP comparisons are inconsistent (CR={consistency_ratio:.4f}). "
            "Review the comparisons or explicitly allow inconsistency."
        )

    weights = ahp_details["weights"]

    # 3. Rank database alternatives using the AHP weights.
    rankings = rank_databases(
        decision_matrix=decision_matrix,
        weights=weights,
        criteria_types=criteria_types,
        alternatives=alternatives,
    )

    # 4. Save the weights and preferences as a new configuration version.
    version = save_configuration(
        config_name=config_name,
        criteria_weights={
            f"criterion_{i + 1}": float(weight)
            for i, weight in enumerate(weights)
        },
        preferences=preferences or {},
    )

    # 5. Return the results to the caller or UI.
    return {
        "config_name": config_name,
        "config_version": version,
        "criteria_weights": weights.tolist(),
        "consistency_ratio": consistency_ratio,
        "is_consistent": is_consistent,
        "rankings": rankings,
    }
