
import json
from pathlib import Path

path = Path("data/databases.json")

new_criteria = [
    "transaction_support",
    "availability",
    "security",
    "backup_recovery",
    "concurrency_support",
    "ecosystem_support",
    "document_model_support",
    "schema_flexibility",
    "indexing_support",
    "aggregation_support",
    "replication_support",
    "read_latency",
    "write_latency",
    "throughput",
    "persistence",
    "eviction_policy_support",
    "replication_failover",
    "write_throughput",
    "read_throughput",
    "horizontal_scaling",
    "fault_tolerance",
    "consistency_options"
]

with path.open("r", encoding="utf-8") as file:
    databases = json.load(file)

if not isinstance(databases, list):
    raise ValueError(
        "databases.json must contain a list. Restore the original database profiles first."
    )

for database in databases:
    scores = database.setdefault("scores", {})
    for criterion in new_criteria:
        scores.setdefault(criterion, None)

with path.open("w", encoding="utf-8") as file:
    json.dump(databases, file, indent=2, ensure_ascii=False)
    file.write("\n")

print(f"Updated {len(databases)} database profiles.")
print("Existing scores preserved; new scores marked unknown.")
