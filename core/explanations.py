
"""Generate understandable explanations for database candidates."""

def explain_database(database, criteria_weights=None):
    scores = database.get("scores", {})
    strengths = []
    limitations = []
    unknowns = []

    for criterion, score in scores.items():
        if score is None:
            unknowns.append(criterion)
        elif score >= 4:
            strengths.append(criterion)
        elif score <= 2:
            limitations.append(criterion)

    return {
        "database": database.get("name", database.get("id", "Unknown")),
        "strengths": strengths,
        "limitations": limitations,
        "unknown_criteria": unknowns,
        "trade_offs": [
            f"Strong on {strengths[0]} but weaker on {limitations[0]}"
        ] if strengths and limitations else [],
        "summary": _make_summary(strengths, limitations, unknowns),
    }


def _make_summary(strengths, limitations, unknowns):
    parts = []

    if strengths:
        parts.append("Higher-scoring areas: " + ", ".join(strengths))
    if limitations:
        parts.append("Lower-scoring areas: " + ", ".join(limitations))
    if unknowns:
        parts.append("Needs verification: " + ", ".join(unknowns))
    if not parts:
        parts.append("No criterion scores are available to explain.")

    return ". ".join(parts) + "."

