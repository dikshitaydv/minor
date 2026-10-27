"""Simple, transparent rule-based explanations for prototype rankings."""

def explain_database(database, all_databases, criteria=None):
    criteria = criteria or []
    strengths = []
    weaknesses = []
    for criterion in criteria:
        value = database.get("scores", {}).get(criterion)
        if value is None:
            continue
        peers = [
            other.get("scores", {}).get(criterion)
            for other in all_databases
            if other.get("scores", {}).get(criterion) is not None
        ]
        if peers and value == max(peers):
            strengths.append(f"Highest catalogue score for {criterion.replace('_', ' ')} ({value}/5).")
        if peers and value == min(peers):
            weaknesses.append(f"Lowest catalogue score for {criterion.replace('_', ' ')} ({value}/5).")
    return {
        "strengths": strengths or ["No standout strength identified from the selected criteria."],
        "weaknesses": weaknesses or ["No standout weakness identified from the selected criteria."],
        "caveat": "Explanations reflect the current catalogue values; verify evidence and scores before relying on the recommendation."
    }
