from core.catalogue import load_databases

def test_catalogue_has_seven_databases():
    databases = load_databases()
    assert len(databases) == 7