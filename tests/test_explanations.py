
from core.explanations import explain_database


def test_explanation_identifies_strengths_and_limitations():
    result = explain_database({
        "name": "ExampleDB",
        "scores": {
            "scalability": 5,
            "simplicity": 2,
            "cost": None,
        },
    })

    assert result["database"] == "ExampleDB"
    assert "scalability" in result["strengths"]
    assert "simplicity" in result["limitations"]
    assert "cost" in result["unknown_criteria"]
    assert result["trade_offs"]


def test_explanation_handles_missing_scores():
    result = explain_database({"name": "ExampleDB", "scores": {}})

    assert result["strengths"] == []
    assert result["limitations"] == []
    assert result["unknown_criteria"] == []
    assert "No criterion scores" in result["summary"]


def test_explanation_handles_all_unknown_scores():
    result = explain_database({
        "name": "ExampleDB",
        "scores": {"cost": None},
    })

    assert result["unknown_criteria"] == ["cost"]
    assert "Needs verification" in result["summary"]
