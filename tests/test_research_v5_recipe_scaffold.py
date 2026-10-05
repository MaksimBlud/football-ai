from pathlib import Path

import pytest

from research_v5_recipe_scaffold import ScaffoldError, build_scaffold, render_markdown


def _issue(family: str, number: int = 9001) -> dict:
    return {
        "number": number,
        "title": "[AGENT-RESEARCH] deterministic scaffold test",
        "body": (
            "research_question: Can this independent family add OOS information?\n"
            f"hypothesis_family: {family}\n"
            "independent_information_justification: This is a separate preregistered "
            "feature family, not a retune of a seen threshold.\n"
        ),
    }


def test_scaffold_for_unknown_family_is_no_api_and_reviewable():
    payload = build_scaffold(_issue("v5_scaffold_unregistered_family"), root=Path("."))
    assert payload["decision"] == "NEEDS_DETERMINISTIC_RECIPE"
    assert payload["engine"] == "V5_DETERMINISTIC_NO_API"
    assert payload["hypothesis_family"] == "v5_scaffold_unregistered_family"
    assert payload["safety"]["model_api"] is False
    assert payload["safety"]["outcomes_read_during_scaffold"] is False
    assert payload["safety"]["production_operations"] is False
    assert "evaluator" in payload["required_implementation"]
    assert payload["expected_lifecycle"][-1] == "DONE"

    markdown = render_markdown(payload)
    assert "Required deterministic implementation" in markdown
    assert "model API: forbidden by default" in markdown
    assert "does not claim" in markdown


def test_scaffold_rejects_family_already_supported_by_v5():
    with pytest.raises(ScaffoldError, match="already supported"):
        build_scaffold(_issue("kickoff_calendar_context"), root=Path("."))


def test_scaffold_rejects_invalid_issue_number():
    issue = _issue("v5_scaffold_another_family", number=0)
    with pytest.raises(ScaffoldError, match="positive integer"):
        build_scaffold(issue, root=Path("."))
