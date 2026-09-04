from pathlib import Path

import pandas as pd
import pytest

from prospective_market_path import (
    FREEZE_UTC,
    MIN_PATH_SPAN_HOURS,
    PATH_FEATURES,
    build_market_paths,
    evaluate_ready_league,
    readiness_for_league,
    settle_market_paths,
)


def _snapshot(event, kickoff, observed, home_odds, draw_odds=3.4, away_odds=4.0, league="EPL"):
    return {
        "league": league,
        "event_id": event,
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "commence_time_utc": kickoff,
        "snapshot_time_utc": observed,
        "home_odds": home_odds,
        "draw_odds": draw_odds,
        "away_odds": away_odds,
    }


def test_pre_freeze_kickoffs_are_never_eligible():
    rows = [
        _snapshot("old", "2026-09-04T12:00:00Z", "2026-09-03T10:00:00Z", 2.0),
        _snapshot("old", "2026-09-04T12:00:00Z", "2026-09-03T22:00:00Z", 1.9),
        _snapshot("old", "2026-09-04T12:00:00Z", "2026-09-04T05:00:00Z", 1.8),
    ]
    assert FREEZE_UTC > pd.Timestamp("2026-09-04T12:00:00Z")
    assert build_market_paths(pd.DataFrame(rows)).empty


def test_path_uses_only_snapshots_at_or_before_six_hour_cutoff():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [
        _snapshot("e1", kickoff, "2026-09-11T18:00:00Z", 2.20),
        _snapshot("e1", kickoff, "2026-09-12T06:00:00Z", 2.10),
        _snapshot("e1", kickoff, "2026-09-12T12:00:00Z", 2.00),
        # after the -6h cutoff and therefore forbidden from features
        _snapshot("e1", kickoff, "2026-09-12T14:00:00Z", 1.40),
    ]
    path = build_market_paths(pd.DataFrame(rows))
    assert len(path) == 1
    row = path.iloc[0]
    assert row.path_snapshot_count == 3
    assert row.cutoff_snapshot_time_utc == pd.Timestamp("2026-09-12T12:00:00Z")
    assert row.path_span_hours >= MIN_PATH_SPAN_HOURS


def test_path_requires_three_snapshots_and_twelve_hour_span():
    kickoff = "2026-09-12T18:00:00Z"
    too_few = [
        _snapshot("few", kickoff, "2026-09-11T18:00:00Z", 2.2),
        _snapshot("few", kickoff, "2026-09-12T12:00:00Z", 2.0),
    ]
    too_short = [
        _snapshot("short", kickoff, "2026-09-12T08:00:00Z", 2.2),
        _snapshot("short", kickoff, "2026-09-12T10:00:00Z", 2.1),
        _snapshot("short", kickoff, "2026-09-12T12:00:00Z", 2.0),
    ]
    assert build_market_paths(pd.DataFrame(too_few)).empty
    assert build_market_paths(pd.DataFrame(too_short)).empty


def test_path_feature_family_is_exactly_frozen():
    assert PATH_FEATURES == [
        "net_home_prob_move",
        "net_draw_prob_move",
        "net_away_prob_move",
        "total_home_prob_path",
        "total_draw_prob_path",
        "total_away_prob_path",
    ]


def test_settlement_uses_canonical_local_date_and_team_keys():
    kickoff = "2026-09-12T18:00:00Z"
    paths = build_market_paths(pd.DataFrame([
        _snapshot("e1", kickoff, "2026-09-11T18:00:00Z", 2.2),
        _snapshot("e1", kickoff, "2026-09-12T00:00:00Z", 2.1),
        _snapshot("e1", kickoff, "2026-09-12T12:00:00Z", 2.0),
    ]))
    results = pd.DataFrame([{
        "league": "EPL",
        "match_date": "2026-09-12",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "result": "H",
    }])
    settled = settle_market_paths(paths, results, "EPL")
    assert len(settled) == 1
    assert settled.iloc[0].actual_result == "H"


def test_unready_sample_refuses_outcome_scoring():
    settled = pd.DataFrame(columns=["league", "event_id", "month", "kickoff_utc"])
    state = readiness_for_league(settled, "EPL")
    assert state.ready is False
    with pytest.raises(RuntimeError, match="not ready"):
        evaluate_ready_league(settled, "EPL")


def test_cycle_checks_all_league_readiness_before_evaluation():
    source = Path("prospective_market_path_cycle.py").read_text()
    readiness_check = 'if not bool(readiness["ready"].all()):'
    evaluation = "evaluate_ready_league(settled_all, league)"
    assert readiness_check in source
    assert evaluation in source
    assert source.index(readiness_check) < source.index(evaluation)
