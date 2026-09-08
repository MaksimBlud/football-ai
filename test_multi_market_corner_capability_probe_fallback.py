import json
from pathlib import Path

import multi_market_corner_capability_probe as probe


FALLBACK_PATH = Path("research/multi_market_corner_capability_probe_fallback_v1.json")
ROLLOVER_PATH = Path("research/multi_market_corner_capability_probe_rollover_v2.json")
PROBE_PATH = Path("multi_market_corner_capability_probe.py")
WORKFLOW_PATH = Path(".github/workflows/multi-market-corner-capability-probe.yml")


def load_fallback():
    return json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))


def load_rollover():
    return json.loads(ROLLOVER_PATH.read_text(encoding="utf-8"))


def test_historical_fallback_activation_provenance_is_preserved():
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
    assert p["target"] == {
        "league": "LA_LIGA",
        "event_id": "0817220a8e0794e15ecba51338bb6cf8",
        "home_team": "Getafe",
        "away_team": "Celta Vigo",
        "commence_time_utc": "2026-09-07T17:00:00+00:00",
    }


def test_rollover_v2_is_inactive_preregistration_with_durable_zero_cost_proof():
    p = load_rollover()
    expected = {
        "league": "BUNDESLIGA",
        "event_id": "115c6679a72c5a360640b6baaa16e78c",
        "home_team": "Union Berlin",
        "away_team": "FC Schalke 04",
        "commence_time_utc": "2026-09-11T18:30:00+00:00",
    }
    assert p["schema_version"] == "MULTI_MARKET_CORNER_CAPABILITY_PROBE_ROLLOVER_V2"
    assert p["research_only"] is True
    assert p["preregistered"] is True
    assert p["active"] is False
    assert p["selected_before_corner_response"] is True
    assert p["automatic_activation_allowed"] is False
    assert p["automatic_target_switching_allowed"] is False
    assert p["paid_request_allowed_by_this_file"] is False
    assert p["requires_separate_activation_pr"] is True
    assert p["requires_explicit_manual_paid_action"] is True
    assert p["requires_fresh_zero_cost_quota_preflight"] is True
    assert p["hard_reserve_credits"] == 100
    assert p["max_paid_requests"] == 1
    assert p["max_paid_credits"] == 2
    assert p["target"] == expected

    proof = p["scheduled_zero_cost_rollover_proof"]
    assert proof["workflow_run_id"] == 34112118221
    assert proof["artifact_id"] == 10014773586
    assert proof["artifact_zip_sha256"] == "6b34164dc659bf438eea66d989890d0bfb12c8429a18f9d677af3fea4455aa7e"
    assert proof["head_sha"] == "9265d90bb7c1eca806a86be874832517d694c35f"
    assert proof["proposed_candidate_matches_target"] is True
    assert proof["paid_provider_requests"] == 0
    assert proof["paid_provider_credits"] == 0
    assert proof["writes_performed"] is False

    live = p["live_identity_recheck"]
    assert live["read_only"] is True
    assert live["event_snapshot_count"] == 17
    assert live["distinct_event_identity_count"] == 1
    assert live["identity_conflict"] is False
    assert live["paid_provider_requests"] == 0
    assert live["writes_performed"] is False


def test_preregistration_does_not_change_active_probe_target():
    historical = load_fallback()
    rollover = load_rollover()
    assert probe.TARGET == historical["target"]
    assert probe.TARGET != rollover["target"]
    assert rollover["active"] is False
    assert rollover["requires_separate_activation_pr"] is True


def test_rollover_activation_conditions_preserve_paid_safety_boundary():
    p = load_rollover()["activation_conditions"]
    assert p["current_active_target_must_be_expired"] is True
    assert p["current_active_probe_must_have_zero_provider_request_attempts"] is True
    assert p["fresh_zero_cost_quota_preflight_required"] is True
    assert p["hard_reserve_credits"] == 100
    assert p["max_paid_requests"] == 1
    assert p["max_paid_credits"] == 2
    assert p["target_must_still_be_prospective"] is True


def test_stale_quota_cannot_authorize_paid_action():
    quota = load_rollover()["quota_state_at_preregistration"]
    assert quota["fresh_quota_confirmed"] is False
    assert quota["last_stored_remaining"] == 193
    assert quota["stale_value_authorizes_paid_action"] is False


def test_paid_probe_cannot_read_or_auto_activate_provenance_files():
    probe_source = PROBE_PATH.read_text(encoding="utf-8")
    workflow_source = WORKFLOW_PATH.read_text(encoding="utf-8")
    for provenance_name in (FALLBACK_PATH.name, ROLLOVER_PATH.name):
        assert provenance_name not in probe_source
        assert provenance_name not in workflow_source
    assert "workflow_dispatch:" in workflow_source
    assert "schedule:" not in workflow_source
    assert "push:" not in workflow_source
