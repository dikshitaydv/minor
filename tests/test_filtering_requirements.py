
import pytest

from core.filtering import filter_databases


def test_explicit_failure_is_excluded():
    databases = [{"name": "A", "supports_documents": False}]

    eligible, excluded = filter_databases(
        databases, ["supports_documents"]
    )

    assert eligible == []
    assert excluded[0]["reasons"] == ["supports_documents"]


def test_unknown_requirement_needs_verification():
    databases = [{"name": "A", "supports_documents": None}]

    eligible, excluded = filter_databases(
        databases, ["supports_documents"]
    )

    assert len(eligible) == 1
    assert eligible[0]["_filter_status"] == "needs_verification"
    assert excluded == []


def test_missing_requirement_needs_verification():
    eligible, excluded = filter_databases(
        [{"name": "A"}], ["supports_documents"]
    )

    assert eligible[0]["_filter_status"] == "needs_verification"
    assert excluded == []


def test_all_requirements_must_pass():
    databases = [{
        "name": "A",
        "supports_documents": True,
        "supports_sql": True,
    }]

    eligible, excluded = filter_databases(
        databases, ["supports_documents", "supports_sql"]
    )

    assert eligible[0]["_filter_status"] == "eligible"
    assert excluded == []


def test_empty_requirements_keep_all():
    eligible, excluded = filter_databases(
        [{"name": "A"}], []
    )

    assert len(eligible) == 1
    assert eligible[0]["_filter_status"] == "eligible"
    assert excluded == []
