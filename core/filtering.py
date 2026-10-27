"""Filter databases by mandatory requirements, preserving exclusion reasons."""

def filter_databases(databases, mandatory_requirements):
    eligible, excluded = [], []
    for database in databases:
        reasons = [
            requirement
            for requirement in mandatory_requirements
            if database.get(requirement) is not True
        ]
        if reasons:
            excluded.append({
                "database": database,
                "reasons": reasons,
            })
        else:
            eligible.append(database)
    return eligible, excluded
