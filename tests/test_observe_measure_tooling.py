import pandas as pd
import pytest

from advanced_oos_evaluator import bootstrap_metrics, confidence_bucket, segment_latest
from analyze_multi_league_market_movement import analyze_snapshots
from trace_canonical_prediction import build_lineage, observation_table
from validate_research_experiments import validate_registry


def _settled_frame():
    return pd.DataFrame([
        {"event_id": "e1", "market_home_prob": 0.60, "market_draw_prob": 0.25, "market_away_prob": 0.15, "market_pick": "H", "actual_result": "H", "prediction_correct": True, "actual_result_probability": 0.60},
        {"event_id": "e2", "market_home_prob": 0.30, "market_draw_prob": 0.30, "market_away_prob": 0.40, "market_pick": "A", "actual_result": "D", "prediction_correct": False, "actual_result_probability": 0.30},
    ])


def test_advanced_oos_metrics_are_deterministic_and_descriptive_only():
    frame = _settled_frame()
    assert confidence_bucket(0.44) == "LT_045"
    assert confidence_bucket(0.60) == "060_075"
    first = bootstrap_metrics(frame, samples=50, seed=7)
    second = bootstrap_metrics(frame, samples=50, seed=7)
    assert first == second
    assert set(segment_latest(frame)) == {"market_pick", "confidence", "actual_result"}


def test_registry_rejects_threshold_and_duplicate_id():
    base = {
        "experiment_id": "X",
        "status": "FROZEN",
        "research_only": True,
        "prediction_source": "ledger",
        "prediction_mode": "MARKET_ONLY",
        "eligible_leagues": ["EPL"],
        "start_time_utc": "2026-08-30T00:00:00Z",
        "code_sha": "a" * 40,
        "parameters": {},
        "evaluation_view": "LATEST_PRE_KICKOFF_PER_FIXTURE",
        "readiness_threshold": None,
    }
    assert len(validate_registry({"schema_version": 1, "experiments": [base]})) == 1
    bad = dict(base, readiness_threshold=50)
    with pytest.raises(ValueError, match="readiness threshold"):
        validate_registry({"schema_version": 1, "experiments": [bad]})
    with pytest.raises(ValueError, match="unique"):
        validate_registry({"schema_version": 1, "experiments": [base, dict(base)]})


def test_market_movement_is_league_scoped_and_pre_kickoff_only():
    frame = pd.DataFrame([
        {"league": "EPL", "event_id": "e1", "home_team": "A", "away_team": "B", "snapshot_time_utc": "2026-08-30T10:00:00Z", "commence_time_utc": "2026-08-30T14:00:00Z", "home_odds": 2.0, "draw_odds": 3.5, "away_odds": 4.0},
        {"league": "EPL", "event_id": "e1", "home_team": "A", "away_team": "B", "snapshot_time_utc": "2026-08-30T13:00:00Z", "commence_time_utc": "2026-08-30T14:00:00Z", "home_odds": 1.8, "draw_odds": 3.7, "away_odds": 4.5},
        {"league": "EPL", "event_id": "e1", "home_team": "A", "away_team": "B", "snapshot_time_utc": "2026-08-30T14:01:00Z", "commence_time_utc": "2026-08-30T14:00:00Z", "home_odds": 1.7, "draw_odds": 3.8, "away_odds": 4.8},
    ])
    movement = analyze_snapshots(frame, league="EPL")
    assert len(movement) == 1
    assert movement.iloc[0]["snapshots"] == 2
    assert movement.iloc[0]["latest_hours_to_kickoff"] == pytest.approx(1.0)
    foreign = frame.copy()
    foreign.loc[0, "league"] = "LA_LIGA"
    with pytest.raises(ValueError, match="league mismatch"):
        analyze_snapshots(foreign, league="EPL")


def test_lineage_traces_canonical_settlement_without_activation():
    ledger = pd.DataFrame([{
        "league": "EPL", "event_id": "e1", "home_team": "Arsenal", "away_team": "Chelsea",
        "kickoff_utc": "2026-08-30T14:00:00Z", "snapshot_time_utc": "2026-08-30T12:00:00Z",
        "market_home_prob": 0.6, "market_draw_prob": 0.25, "market_away_prob": 0.15,
        "market_pick": "H", "prediction_mode": "MARKET_ONLY", "structural_applied": False,
    }])
    results = pd.DataFrame([{
        "league": "EPL", "match_date": "2026-08-30", "home_team": "Arsenal", "away_team": "Chelsea", "result": "H"
    }])
    snapshots = pd.DataFrame([{"league": "EPL", "event_id": "e1", "snapshot_time_utc": "2026-08-30T12:00:00Z"}])
    observations = pd.DataFrame([{"league": "EPL", "event_id": "e1"}])
    lineage = build_lineage(league="EPL", event_id="e1", snapshots=snapshots, observations=observations, ledger=ledger, results=results)
    assert lineage["settled_rows"] == 1
    assert lineage["actual_result"] == "H"
    assert lineage["ledger_pre_kickoff"] is True
    assert lineage["structural_applied"] is False
    assert observation_table("LA_LIGA") == "la_liga_structural_v2_observations"
