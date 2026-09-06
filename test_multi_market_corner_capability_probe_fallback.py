import json
from pathlib import Path

import multi_market_corner_capability_probe as probe


FALLBACK_PATH = Path("research/multi_market_corner_capability_probe_fallback_v1.json")
PROBE_PATH = Path("multi_market_corner_capability_probe.py")
WORKFLOW_PATH = Path(".github/workflows/multi-market-corner-capability-probe.yml")


def load_fallback():
    return json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))


def test_fallback_is_separately_activated_research_evidence():
    p = load_fallback()
    assert p["schema_version"] == "MULTI_MARKET_CORNER_CAPABILITY_PROBE_FALLBACK_V1"
    assert p["research_only"] is True
    assert p["active"] is True
    assert p["automatic_activation_allowed"] is False
    assert p["automatic_target_switching_allowed"] is False
    assert p["paid_request_allowed_by_this_file"] is False
    assert p["requires_separate_activation_pr"] is True
    assert p["activated_by_separate_pr"] is True
    assert p["activation_pr"] == 200
    assert p["activation_merge_sha"] == "b387551319ae94e0dcfbdc0f7afbd8cf39e8edec"
    assert p["selected_before_corner_response"] is True


def test_active_fallback_target_matches_zero_cost_rollover_proof_and_probe_target():
    p = load_fallback()
    expected = {
        "league": "LA_LIGA",
        "event_id": "0817220a8e0794e15ecba51338bb6cf8",
        "home_team": "Getafe",
        "away_team": "Celta Vigo",
        "commence_time_utc": "2026-09-07T17:00:00+00:00",
    }
    assert p["target"] == expected
    assert probe.TARGET == expected
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


def test_activation_proof_satisfies_frozen_conditions_without_paid_call():
    proof = load_fallback()["activation_proof"]
    assert proof["primary_target_expired_before_activation"] is True
    assert proof["primary_probe_workflow_dispatch_runs_observed"] == 0
    assert proof["primary_provider_request_attempts_observed"] == 0
    assert proof["fresh_zero_cost_readiness_run_id"] == 34039051536
    assert proof["fresh_zero_cost_readiness_artifact_id"] == 9991098557
    assert proof["fresh_zero_cost_readiness_artifact_zip_sha256"] == "65e885e9ce2e44d9eb47817e27c380363946c7aa4e52f6d888ed72f1c89db988"
    assert proof["quota_remaining"] == 193
    assert proof["quota_last_cost"] == 0
    assert proof["quota_ready"] is True
    assert proof["provider_corner_capability_ready"] is False
    assert proof["provider_corner_capability_blocker"] == "PROVIDER_CORNER_CAPABILITY_UNPROVEN"
    assert proof["paid_provider_requests"] == 0
    assert proof["paid_provider_credits"] == 0
    assert proof["writes_performed"] is False


def test_paid_probe_cannot_read_or_auto_activate_fallback():
    fallback_name = FALLBACK_PATH.name
    probe_source = PROBE_PATH.read_text(encoding="utf-8")
    workflow_source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert fallback_name not in probe_source
    assert fallback_name not in workflow_source
    assert "workflow_dispatch:" in workflow_source
    assert "schedule:" not in workflow_source
    assert "push:" not in workflow_source
