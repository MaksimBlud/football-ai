from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from epl_ai_market_pair_evaluation import (
    EVALUATION_DELAY_HOURS,
    FROZEN_MODEL_SHA256,
    PRIMARY_COHORT_SIZE,
    primary_evaluation_gate,
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


def _cohort_rows(count: int = PRIMARY_COHORT_SIZE):
    rows = []
    base_kickoff = pd.Timestamp("2026-09-10T12:00:00Z")
    for index in range(count):
        kickoff = base_kickoff + pd.Timedelta(hours=index)
        rows.append(_row(
            f"pair-{index:03d}",
            "2026-09-06T09:00:00Z",
            event_id=f"evt-{index:03d}",
            kickoff=kickoff.isoformat(),
        ))
    return rows


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


def test_primary_gate_stays_closed_below_preregistered_sample_without_outcomes():
    gate, cohort, excluded = primary_evaluation_gate(
        pd.DataFrame(_cohort_rows(PRIMARY_COHORT_SIZE - 1)),
        now_utc="2027-01-01T00:00:00Z",
    )
    assert excluded == []
    assert len(cohort) == PRIMARY_COHORT_SIZE - 1
    assert gate == {
        "open": False,
        "reason": "INSUFFICIENT_PREREGISTERED_EVENTS",
        "required_events": PRIMARY_COHORT_SIZE,
        "eligible_events": PRIMARY_COHORT_SIZE - 1,
        "outcome_reads_allowed": False,
    }


def test_primary_gate_stays_closed_until_24h_after_last_cohort_kickoff():
    frame = pd.DataFrame(_cohort_rows())
    last_kickoff = pd.to_datetime(frame["kickoff_utc"], utc=True).max()
    gate, cohort, excluded = primary_evaluation_gate(
        frame,
        now_utc=last_kickoff + pd.Timedelta(hours=EVALUATION_DELAY_HOURS) - pd.Timedelta(seconds=1),
    )
    assert excluded == []
    assert len(cohort) == PRIMARY_COHORT_SIZE
    assert gate["open"] is False
    assert gate["reason"] == "COHORT_NOT_MATURE"
    assert gate["outcome_reads_allowed"] is False


def test_primary_gate_opens_deterministically_after_preregistered_cohort_matures():
    rows = _cohort_rows(PRIMARY_COHORT_SIZE + 5)
    frame = pd.DataFrame(list(reversed(rows)))
    first_hundred_last_kickoff = pd.to_datetime(rows[PRIMARY_COHORT_SIZE - 1]["kickoff_utc"], utc=True)
    gate, cohort, excluded = primary_evaluation_gate(
        frame,
        now_utc=first_hundred_last_kickoff + pd.Timedelta(hours=EVALUATION_DELAY_HOURS),
    )
    assert excluded == []
    assert gate["open"] is True
    assert gate["reason"] == "PREREGISTERED_GATE_OPEN"
    assert gate["outcome_reads_allowed"] is True
    assert cohort["event_id"].tolist() == [f"evt-{index:03d}" for index in range(PRIMARY_COHORT_SIZE)]


def test_frozen_contract_hash_live_provenance_and_gate_are_machine_readable():
    contract = json.loads(Path("research/epl_ai_market_pair_v1.json").read_text(encoding="utf-8"))
    assert contract["collection"]["frozen_model_artifact_sha256"] == FROZEN_MODEL_SHA256
    assert contract["activation_evidence"]["first_successful_run_id"] == 34032610966
    assert contract["activation_evidence"]["first_successful_pairs"] == 12
    assert contract["evaluation"]["row_selection_timing"] == "frozen_before_target_outcomes_are_used_for_this_experiment"
    assert contract["evaluation"]["primary_cohort_size"] == PRIMARY_COHORT_SIZE
    assert contract["evaluation"]["evaluation_delay_hours_after_last_cohort_kickoff"] == EVALUATION_DELAY_HOURS
    assert contract["evaluation"]["outcome_read_gate"] == "closed_until_primary_cohort_exists_and_is_mature"
    assert contract["evaluation"]["interim_primary_evaluation"] is False
    assert contract["evaluation"]["threshold_search"] is False
    assert contract["evaluation"]["production_activation"] is False


def test_cycle_enforces_same_frozen_model_hash_and_stays_outcome_free():
    source = Path("epl_ai_market_pair_cycle.py").read_text(encoding="utf-8")
    assert FROZEN_MODEL_SHA256 in source
    for forbidden in ("league_finished_results", "la_liga_finished_results", "league_corner_results"):
        assert forbidden not in source
