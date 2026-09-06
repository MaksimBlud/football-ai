from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from epl_ai_market_pair_evaluation import (
    FROZEN_MODEL_SHA256,
    select_frozen_evaluation_pairs,
)


def _row(pair_key: str, snapshot: str, *, event_id: str = "evt-1", kickoff: str = "2026-09-12T14:00:00Z", home: str = "Arsenal", away: str = "Chelsea", model_sha: str = FROZEN_MODEL_SHA256):
    return {
        "pair_key": pair_key,
        "experiment_id": "EPL_AI_MARKET_PAIR_V1",
        "league": "EPL",
        "event_id": event_id,
        "provider_home_team": home,
        "provider_away_team": away,
        "kickoff_utc": kickoff,
        "market_snapshot_time_utc": snapshot,
        "model_generated_at_utc": "2026-09-06T12:16:54Z",
        "model_artifact_sha256": model_sha,
        "market_home_prob": 0.50,
        "market_draw_prob": 0.25,
        "market_away_prob": 0.25,
        "model_home_prob": 0.55,
        "model_draw_prob": 0.23,
        "model_away_prob": 0.22,
    }


def test_selector_uses_latest_snapshot_before_any_outcome_join():
    frame = pd.DataFrame([
        _row("old", "2026-09-04T04:00:00Z"),
        _row("latest", "2026-09-06T09:00:00Z"),
    ])
    selected, excluded = select_frozen_evaluation_pairs(frame)
    assert excluded == []
    assert selected["pair_key"].tolist() == ["latest"]


def test_selector_resolves_exact_timestamp_tie_by_pair_key_ascending():
    frame = pd.DataFrame([
        _row("z-key", "2026-09-06T09:00:00Z"),
        _row("a-key", "2026-09-06T09:00:00Z"),
    ])
    selected, excluded = select_frozen_evaluation_pairs(frame)
    assert excluded == []
    assert selected["pair_key"].tolist() == ["a-key"]


def test_selector_excludes_nonfrozen_model_hash():
    frame = pd.DataFrame([
        _row("frozen", "2026-09-06T09:00:00Z"),
        _row("other", "2026-09-06T10:00:00Z", model_sha="b" * 64),
    ])
    selected, excluded = select_frozen_evaluation_pairs(frame)
    assert excluded == []
    assert selected["pair_key"].tolist() == ["frozen"]


def test_selector_excludes_ambiguous_event_identity_fail_closed():
    frame = pd.DataFrame([
        _row("one", "2026-09-06T09:00:00Z", kickoff="2026-09-12T14:00:00Z"),
        _row("two", "2026-09-06T10:00:00Z", kickoff="2026-09-12T16:00:00Z"),
    ])
    selected, excluded = select_frozen_evaluation_pairs(frame)
    assert selected.empty
    assert excluded == [{"event_id": "evt-1", "reason": "AMBIGUOUS_EVENT_IDENTITY"}]


def test_frozen_contract_hash_live_provenance_and_readiness_gate_are_machine_readable():
    contract = json.loads(Path("research/epl_ai_market_pair_v1.json").read_text(encoding="utf-8"))
    assert contract["collection"]["frozen_model_artifact_sha256"] == FROZEN_MODEL_SHA256
    assert contract["activation_evidence"]["first_successful_run_id"] == 34032610966
    assert contract["activation_evidence"]["first_successful_pairs"] == 12
    evaluation = contract["evaluation"]
    assert evaluation["row_selection_timing"] == "frozen_before_target_outcomes_are_used_for_this_experiment"
    gate = evaluation["readiness_gate"]
    assert gate["minimum_unique_selected_events"] == 100
    assert gate["minimum_elapsed_calendar_days_from_first_live_collection"] == 56
    assert gate["first_permitted_outcome_read_utc"] == "2026-11-01T12:16:54.672903+00:00"
    assert gate["outcome_free_event_maturity_buffer_hours_after_kickoff"] == 6
    assert evaluation["audit_parameters"] == {"bootstrap_simulations": 20000, "bootstrap_seed": 20260901}
    assert evaluation["primary_decision_rule"]["PASS"].startswith("both Brier and log-loss")
    assert evaluation["primary_decision_rule"]["FAIL"].startswith("both Brier and log-loss")
    assert evaluation["threshold_search"] is False
    assert evaluation["optional_stopping"] is False
    assert evaluation["interim_outcome_scoring_before_gate"] is False
    assert evaluation["production_activation"] is False


def test_cycle_enforces_same_frozen_model_hash_and_stays_outcome_free():
    source = Path("epl_ai_market_pair_cycle.py").read_text(encoding="utf-8")
    assert FROZEN_MODEL_SHA256 in source
    for forbidden in ("league_finished_results", "la_liga_finished_results", "league_corner_results"):
        assert forbidden not in source
