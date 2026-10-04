import json
from pathlib import Path

import pytest

from research_orchestrator_v4 import (
    branch_name,
    classify_model_errors,
    load_state,
    retry_delay_seconds,
    load_usage,
    parse_usage_increment,
    update_usage,
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
    assert classify_model_errors([message]) == "TRANSIENT_QUOTA"


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
    assert classify_model_errors([message]) == "PERMANENT_BLOCKED"


def test_latest_tool_format_error_wins_over_earlier_quota():
    log = """
GROQ_HTTP_ERROR status=429 retry_after='5' body=rate limit quota exceeded
Please retry after 7s.
GROQ_HTTP_ERROR status=400 retry_after=None body={"error":{"code":"tool_use_failed","message":"Failed to parse tool call arguments as JSON"}}
GROQ_TOOL_FORMAT_ERROR retryable=true
"""
    assert classify_model_errors([log]) == "TOOL_FORMAT_RETRY"


def test_latest_permanent_error_wins_over_earlier_quota():
    log = """
429 RESOURCE_EXHAUSTED quota exceeded
Please retry after 5s.
GROQ_API_KEY missing
"""
    assert classify_model_errors([log]) == "PERMANENT_BLOCKED"


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


def test_long_groq_retry_after_does_not_short_redispatch():
    log = (
        "GROQ_HTTP_ERROR status=429 retry_after='2296' body=TPD rate limit\n"
        "GROQ_LONG_QUOTA_WAIT retry_after_seconds=2296.000"
    )
    assert classify_model_errors([log]) == "TRANSIENT_QUOTA"
    assert retry_delay_seconds([log]) is None


def test_minute_quota_retry_wins_when_another_fallback_hit_daily_quota():
    minute = (
        "Quota exceeded for generate_content_free_tier_input_token_count; "
        "Please retry in 58.283537871s."
    )
    daily = (
        "You have exhausted your daily quota on this model. "
        "GenerateRequestsPerDayPerProjectPerModel-FreeTier; "
        "Please retry in 16h2m25s."
    )
    assert retry_delay_seconds([minute, daily]) == 69


def test_retry_delay_uses_largest_hint_across_models():
    assert retry_delay_seconds(
        ["Please retry in 31.1s", "Please retry in 59.97s"]
    ) == 70


def test_usage_accounting_persists_and_accumulates(tmp_path):
    first = update_usage(
        428,
        {"runs_started": 1, "model_passes_attempted": 3, "quota_waits": 1},
        tmp_path,
    )
    assert first["runs_started"] == 1
    assert first["model_passes_attempted"] == 3
    assert first["quota_waits"] == 1
    assert first["last_updated_utc"]

    second = update_usage(
        428,
        {"runs_started": 1, "short_retries_scheduled": 1},
        tmp_path,
    )
    assert second["runs_started"] == 2
    assert second["model_passes_attempted"] == 3
    assert second["short_retries_scheduled"] == 1
    assert load_usage(428, tmp_path) == second


def test_usage_increment_parser_supports_default_one():
    assert parse_usage_increment("runs_started") == ("runs_started", 1)
    assert parse_usage_increment("model_passes_attempted=3") == (
        "model_passes_attempted",
        3,
    )


def test_usage_increment_parser_rejects_unknown_or_negative():
    with pytest.raises(ValueError):
        parse_usage_increment("not_a_counter=1")
    with pytest.raises(ValueError):
        parse_usage_increment("runs_started=-1")


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
