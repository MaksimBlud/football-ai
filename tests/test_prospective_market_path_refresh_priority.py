import pandas as pd

from prospective_market_path_refresh_priority import build_league_refresh_priority


def test_priority_prefers_earliest_active_due_cutoff():
    coverage = pd.DataFrame([
        {
            "league": "EPL",
            "event_id": "e1",
            "status": "READY",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 100.0,
            "hours_since_last_snapshot": 24.0,
            "refresh_interval_hours": 12.0,
        },
        {
            "league": "LA_LIGA",
            "event_id": "l1",
            "status": "READY",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 8.0,
            "hours_since_last_snapshot": 20.0,
            "refresh_interval_hours": 2.0,
        },
        {
            "league": "SERIE_A",
            "event_id": "s1",
            "status": "READY",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 10.0,
            "hours_since_last_snapshot": 16.0,
            "refresh_interval_hours": 4.0,
        },
    ])
    result = build_league_refresh_priority(coverage).set_index("league")
    assert result.loc["LA_LIGA", "refresh_priority_rank"] == 1
    assert result.loc["SERIE_A", "refresh_priority_rank"] == 2
    assert result.loc["EPL", "refresh_priority_rank"] == 3
    assert result.loc["LA_LIGA", "earliest_due_cutoff_hours"] == 8.0
    assert result.loc["LA_LIGA", "max_due_staleness_ratio"] == 10.0


def test_quarantined_and_superseded_rows_do_not_create_paid_priority():
    coverage = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "q",
            "status": "QUARANTINED_REVISION",
            "operationally_active": False,
            "refresh_due": True,
            "hours_until_cutoff": 1.0,
            "hours_since_last_snapshot": 100.0,
            "refresh_interval_hours": 2.0,
        },
        {
            "league": "SERIE_A",
            "event_id": "x",
            "status": "SUPERSEDED",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 2.0,
            "hours_since_last_snapshot": 100.0,
            "refresh_interval_hours": 2.0,
        },
    ])
    result = build_league_refresh_priority(coverage).set_index("league")
    assert result.loc["LA_LIGA", "priority_due_paths"] == 0
    assert result.loc["SERIE_A", "priority_due_paths"] == 0
    assert pd.isna(result.loc["LA_LIGA", "refresh_priority_rank"])
    assert pd.isna(result.loc["SERIE_A", "refresh_priority_rank"])


def test_tie_breaks_by_more_due_paths_then_staleness():
    coverage = pd.DataFrame([
        {
            "league": "EPL",
            "event_id": "e1",
            "status": "READY",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 12.0,
            "hours_since_last_snapshot": 12.0,
            "refresh_interval_hours": 6.0,
        },
        {
            "league": "SERIE_A",
            "event_id": "s1",
            "status": "READY",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 12.0,
            "hours_since_last_snapshot": 8.0,
            "refresh_interval_hours": 4.0,
        },
        {
            "league": "SERIE_A",
            "event_id": "s2",
            "status": "READY",
            "operationally_active": True,
            "refresh_due": True,
            "hours_until_cutoff": 20.0,
            "hours_since_last_snapshot": 12.0,
            "refresh_interval_hours": 4.0,
        },
    ])
    result = build_league_refresh_priority(coverage).set_index("league")
    assert result.loc["SERIE_A", "priority_due_paths"] == 2
    assert result.loc["SERIE_A", "refresh_priority_rank"] == 1
    assert result.loc["EPL", "refresh_priority_rank"] == 2
