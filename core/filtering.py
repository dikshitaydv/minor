
"""Filter databases by mandatory requirements."""

def filter_databases(databases, mandatory_requirements):
    eligible = []
    excluded = []

    for database in databases:
        failed = []
        unknown = []

        for requirement in mandatory_requirements:
            value = database.get(requirement)

            if value is False:
                failed.append(requirement)
            elif value is not True:
                unknown.append(requirement)

        if failed:
            excluded.append({
                "database": database,
                "reasons": failed,
            })
        else:
            candidate = database.copy()

            if unknown:
                candidate["_filter_status"] = "needs_verification"
                candidate["_verification_requirements"] = unknown
            else:
                candidate["_filter_status"] = "eligible"
                candidate["_verification_requirements"] = []

            eligible.append(candidate)

    return eligible, excluded

