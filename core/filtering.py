
"""Filter databases by mandatory requirements."""

def filter_databases(databases, mandatory_requirements):
    eligible = []
    excluded = []

    for database in databases:
        capabilities = database.get("capabilities", database)
        failed = []
        unknown = []

        for requirement in mandatory_requirements:
            value = capabilities.get(requirement)

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
            candidate["_filter_status"] = (
                "needs_verification" if unknown else "eligible"
            )
            candidate["_verification_requirements"] = unknown
            eligible.append(candidate)

    return eligible, excluded

