from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from epl_ai_market_pair_evaluation import (
    AUDIT_BOOTSTRAP_SEED,
    AUDIT_BOOTSTRAP_SIMULATIONS,
    EVALUATION_DELAY_HOURS,
    FIRST_PERMITTED_OUTCOME_READ_UTC,
    FROZEN_MODEL_SHA256,
    PRIMARY_COHORT_SIZE,
    primary_decision_from_audit,
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


def test_primary_gate_stays_closed_after_cohort_maturity_until_fixed_wall_clock_gate():
    frame = pd.DataFrame(_cohort_rows())
    last_kickoff = pd.to_datetime(frame["kickoff_utc"], utc=True).max()
    assert last_kickoff + pd.Timedelta(hours=EVALUATION_DELAY_HOURS) < FIRST_PERMITTED_OUTCOME_READ_UTC
    gate, cohort, excluded = primary_evaluation_gate(
        frame,
        now_utc=FIRST_PERMITTED_OUTCOME_READ_UTC - pd.Timedelta(seconds=1),
    )
    assert excluded == []
    assert len(cohort) == PRIMARY_COHORT_SIZE
    assert gate["open"] is False
    assert gate["reason"] == "PREREGISTERED_GATE_NOT_REACHED"
    assert gate["gate_opens_at_utc"] == FIRST_PERMITTED_OUTCOME_READ_UTC.isoformat()
    assert gate["outcome_reads_allowed"] is False


def test_primary_gate_uses_later_cohort_maturity_when_cohort_finishes_after_fixed_date():
    rows = _cohort_rows()
    shift = pd.Timedelta(days=70)
    for row in rows:
        row["kickoff_utc"] = (pd.Timestamp(row["kickoff_utc"]) + shift).isoformat()
    frame = pd.DataFrame(rows)
    last_kickoff = pd.to_datetime(frame["kickoff_utc"], utc=True).max()
    expected = last_kickoff + pd.Timedelta(hours=EVALUATION_DELAY_HOURS)
    gate, _, _ = primary_evaluation_gate(frame, now_utc=expected - pd.Timedelta(seconds=1))
    assert gate["open"] is False
    assert gate["gate_opens_at_utc"] == expected.isoformat()


def test_primary_gate_opens_deterministically_after_both_preregistered_gates_pass():
    rows = _cohort_rows(PRIMARY_COHORT_SIZE + 5)
    frame = pd.DataFrame(list(reversed(rows)))
    gate, cohort, excluded = primary_evaluation_gate(
        frame,
        now_utc=FIRST_PERMITTED_OUTCOME_READ_UTC,
    )
    assert excluded == []
    assert gate["open"] is True
    assert gate["reason"] == "PREREGISTERED_GATE_OPEN"
    assert gate["outcome_reads_allowed"] is True
    assert cohort["event_id"].tolist() == [f"evt-{index:03d}" for index in range(PRIMARY_COHORT_SIZE)]


def test_primary_decision_requires_both_metrics_to_clear_same_direction():
    pass_result = {
        "brier_delta_model_minus_market": {"ci95_low": -0.10, "ci95_high": -0.01},
        "logloss_delta_model_minus_market": {"ci95_low": -0.08, "ci95_high": -0.001},
    }
    fail_result = {
        "brier_delta_model_minus_market": {"ci95_low": 0.001, "ci95_high": 0.10},
        "logloss_delta_model_minus_market": {"ci95_low": 0.01, "ci95_high": 0.20},
    }
    mixed_result = {
        "brier_delta_model_minus_market": {"ci95_low": -0.10, "ci95_high": -0.01},
        "logloss_delta_model_minus_market": {"ci95_low": -0.02, "ci95_high": 0.03},
    }
    assert primary_decision_from_audit(pass_result) == "PASS"
    assert primary_decision_from_audit(fail_result) == "FAIL"
    assert primary_decision_from_audit(mixed_result) == "INCONCLUSIVE"


def test_frozen_contract_hash_live_provenance_readiness_and_decision_are_machine_readable():
    contract = json.loads(Path("research/epl_ai_market_pair_v1.json").read_text(encoding="utf-8"))
    assert contract["collection"]["frozen_model_artifact_sha256"] == FROZEN_MODEL_SHA256
    assert contract["activation_evidence"]["first_successful_run_id"] == 34032610966
    assert contract["activation_evidence"]["first_successful_pairs"] == 12
    evaluation = contract["evaluation"]
    assert evaluation["row_selection_timing"] == "frozen_before_target_outcomes_are_used_for_this_experiment"
    assert evaluation["primary_cohort_size"] == PRIMARY_COHORT_SIZE
    assert evaluation["evaluation_delay_hours_after_last_cohort_kickoff"] == EVALUATION_DELAY_HOURS
    assert evaluation["minimum_elapsed_calendar_days_from_first_live_collection"] == 56
    assert evaluation["first_permitted_outcome_read_utc"] == "2026-11-01T12:16:54.672903+00:00"
    assert evaluation["audit_parameters"] == {
        "bootstrap_simulations": AUDIT_BOOTSTRAP_SIMULATIONS,
        "bootstrap_seed": AUDIT_BOOTSTRAP_SEED,
    }
    assert evaluation["primary_decision_rule"]["PASS"].startswith("both Brier and log-loss")
    assert evaluation["primary_decision_rule"]["FAIL"].startswith("both Brier and log-loss")
    assert evaluation["interim_primary_evaluation"] is False
    assert evaluation["optional_stopping_on_primary_metrics"] is False
    assert evaluation["threshold_search"] is False
    assert evaluation["production_activation"] is False


def test_cycle_enforces_same_frozen_model_hash_and_stays_outcome_free():
    source = Path("epl_ai_market_pair_cycle.py").read_text(encoding="utf-8")
    assert FROZEN_MODEL_SHA256 in source
    for forbidden in ("league_finished_results", "la_liga_finished_results", "league_corner_results"):
        assert forbidden not in source
