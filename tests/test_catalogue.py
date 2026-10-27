from core.catalogue import load_databases

def test_catalogue_has_five_databases():
    databases = load_databases()
    assert len(databases) == 5
    assert {d["name"] for d in databases} == {
        "PostgreSQL", "MySQL", "MongoDB", "Apache Cassandra", "Redis"
    }
