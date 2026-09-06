import pandas as pd
import pytest
from prekickoff_observability import analyze_market_movement, build_prekickoff_lineage


def test_market_movement_excludes_post_kickoff_snapshots():
    rows = pd.DataFrame([
        {"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T10:00:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":2.0,"draw_odds":3.0,"away_odds":4.0},
        {"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T11:00:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":1.8,"draw_odds":3.2,"away_odds":4.5},
        {"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T12:01:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":1.2,"draw_odds":8.0,"away_odds":15.0},
    ])
    out = analyze_market_movement(rows, league="EPL")
    assert len(out) == 1
    assert out.iloc[0]["snapshots"] == 2
    assert str(out.iloc[0]["latest_pre_kickoff_utc"]) == "2026-09-01 11:00:00+00:00"


def test_market_movement_rejects_cross_league_input():
    rows = pd.DataFrame([{"league":"LA_LIGA","event_id":"e1","snapshot_time_utc":"2026-09-01T10:00:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":2.0,"draw_odds":3.0,"away_odds":4.0}])
    with pytest.raises(ValueError, match="league mismatch"):
        analyze_market_movement(rows, league="EPL")


def test_lineage_is_outcome_free_and_checks_point_in_time():
    snapshots = pd.DataFrame([{"league":"EPL","event_id":"e1"}])
    ledger = pd.DataFrame([{"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T11:00:00Z","kickoff_utc":"2026-09-01T12:00:00Z","prediction_mode":"MARKET_ONLY"}])
    out = build_prekickoff_lineage(league="EPL", event_id="e1", snapshots=snapshots, ledger=ledger)
    assert out["ledger_pre_kickoff"] is True
    assert out["outcome_reads"] == 0
    assert out["prediction_modes"] == ["MARKET_ONLY"]


def test_lineage_flags_post_kickoff_ledger_row():
    snapshots = pd.DataFrame([{"league":"EPL","event_id":"e1"}])
    ledger = pd.DataFrame([{"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T12:01:00Z","kickoff_utc":"2026-09-01T12:00:00Z"}])
    assert build_prekickoff_lineage(league="EPL", event_id="e1", snapshots=snapshots, ledger=ledger)["ledger_pre_kickoff"] is False
