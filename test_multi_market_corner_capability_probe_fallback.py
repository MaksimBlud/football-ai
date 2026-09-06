import json
from pathlib import Path


FALLBACK_PATH = Path("research/multi_market_corner_capability_probe_fallback_v1.json")
PROBE_PATH = Path("multi_market_corner_capability_probe.py")
WORKFLOW_PATH = Path(".github/workflows/multi-market-corner-capability-probe.yml")


def load_fallback():
    return json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))


def test_fallback_is_inert_preregistered_research_evidence():
    p = load_fallback()
    assert p["schema_version"] == "MULTI_MARKET_CORNER_CAPABILITY_PROBE_FALLBACK_V1"
    assert p["research_only"] is True
    assert p["active"] is False
    assert p["automatic_activation_allowed"] is False
    assert p["automatic_target_switching_allowed"] is False
    assert p["paid_request_allowed_by_this_file"] is False
    assert p["requires_separate_activation_pr"] is True
    assert p["selected_before_corner_response"] is True


def test_fallback_target_matches_zero_cost_rollover_proof():
    p = load_fallback()
    assert p["target"] == {
        "league": "LA_LIGA",
        "event_id": "0817220a8e0794e15ecba51338bb6cf8",
        "home_team": "Getafe",
        "away_team": "Celta Vigo",
        "commence_time_utc": "2026-09-07T17:00:00+00:00",
    }
    proof = p["source_rollover_proof"]
    assert proof["workflow_run_id"] == 34013842380
    assert proof["artifact_id"] == 9983294632
    assert proof["artifact_zip_sha256"] == "72b573aedbbad340d5e7809b3b007e0842880ec12ffd26f45eed8bedf55da0ca"
    assert proof["head_sha"] == "e7ef5e355862bc1cf21ab23b06952244aec16d2d"
    assert proof["paid_provider_requests"] == 0
    assert proof["paid_provider_credits"] == 0
    assert proof["writes_performed"] is False


def test_activation_conditions_preserve_one_request_and_hard_reserve_contract():
    p = load_fallback()["activation_conditions"]
    assert p["primary_target_must_be_expired"] is True
    assert p["primary_probe_must_have_zero_provider_request_attempts"] is True
    assert p["fresh_zero_cost_quota_preflight_required"] is True
    assert p["hard_reserve_credits"] == 100
    assert p["max_paid_requests"] == 1
    assert p["max_paid_credits"] == 2
    assert p["target_must_still_be_prospective"] is True


def test_paid_probe_cannot_read_or_auto_activate_fallback():
    fallback_name = FALLBACK_PATH.name
    probe_source = PROBE_PATH.read_text(encoding="utf-8")
    workflow_source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert fallback_name not in probe_source
    assert fallback_name not in workflow_source
    assert "workflow_dispatch:" in workflow_source
    assert "schedule:" not in workflow_source
    assert "push:" not in workflow_source
