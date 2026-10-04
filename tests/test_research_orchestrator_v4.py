import json
from pathlib import Path

import pytest

from research_orchestrator_v4 import (
    branch_name,
    classify_model_errors,
    load_state,
    retry_delay_seconds,
)


def _write_state(root: Path, issue: int, payload: dict) -> None:
    path = root / "research" / "agent_runs" / f"issue_{issue}" / "STATE.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_branch_name_is_issue_scoped():
    assert branch_name(428) == "agent/v4-issue-428"


@pytest.mark.parametrize(
    "message",
    [
        "429 RESOURCE_EXHAUSTED quota exceeded",
        "503 UNAVAILABLE high demand",
        "You have exhausted your daily quota on this model",
        "Please retry after 48s",
    ],
)
def test_transient_gemini_failures_wait(message):
    assert classify_model_errors([message]) == "QUOTA_WAIT"


@pytest.mark.parametrize(
    "message",
    [
        "invalid API key",
        "permission denied",
        "unauthenticated",
        "unexpected parser failure",
        "",
    ],
)
def test_non_transient_gemini_failures_block(message):
    assert classify_model_errors([message]) == "BLOCKED"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Please retry in 56.480131123s.", 67),
        ("Suggested retry after 30s.", 45),
        ("Please retry in 560ms.", 45),
        ("503 UNAVAILABLE high demand", 75),
    ],
)
def test_retry_delay_uses_provider_hint_with_bounds(message, expected):
    assert retry_delay_seconds([message]) == expected


def test_daily_quota_does_not_short_retry():
    assert retry_delay_seconds(
        ["GenerateRequestsPerDayPerProjectPerModel-FreeTier daily quota"]
    ) is None


def test_retry_delay_uses_largest_hint_across_models():
    assert retry_delay_seconds(
        ["Please retry in 31.1s", "Please retry in 59.97s"]
    ) == 70


def test_continue_requires_next_step(tmp_path):
    _write_state(tmp_path, 428, {"status": "CONTINUE", "summary": "more work remains"})
    with pytest.raises(ValueError, match="next_step"):
        load_state(428, tmp_path)


def test_done_requires_final_report(tmp_path):
    _write_state(tmp_path, 428, {"status": "DONE", "summary": "complete"})
    with pytest.raises(ValueError, match="FINAL_REPORT"):
        load_state(428, tmp_path)


def test_done_accepts_non_empty_final_report(tmp_path):
    _write_state(tmp_path, 428, {"status": "DONE", "summary": "complete"})
    report = tmp_path / "docs" / "agent_runs" / "issue_428" / "FINAL_REPORT.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Final\nResult.", encoding="utf-8")
    assert load_state(428, tmp_path).status == "DONE"


def test_blocked_requires_reason(tmp_path):
    _write_state(tmp_path, 428, {"status": "BLOCKED", "summary": "cannot continue"})
    with pytest.raises(ValueError, match="blocker"):
        load_state(428, tmp_path)
