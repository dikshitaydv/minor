from core.filtering import filter_databases

def test_filter_returns_eligible_and_exclusion_reasons():
    databases = [
        {"name": "A", "supports_documents": True},
        {"name": "B", "supports_documents": False},
    ]
    eligible, excluded = filter_databases(databases, ["supports_documents"])
    assert [d["name"] for d in eligible] == ["A"]
    assert excluded[0]["database"]["name"] == "B"
    assert excluded[0]["reasons"] == ["supports_documents"]

def test_empty_requirements_keeps_all():
    eligible, excluded = filter_databases([{"name": "A"}], [])
    assert len(eligible) == 1
    assert excluded == []
