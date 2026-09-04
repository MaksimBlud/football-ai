import pandas as pd

from prospective_market_path_coverage import (
    STATUS_CONFLICT,
    STATUS_IRRECOVERABLE,
    STATUS_READY,
    STATUS_RECOVERABLE,
    build_fixture_coverage,
    summarize_fixture_coverage,
)


def _row(event, kickoff, observed, league="EPL"):
    return {
        "league": league,
        "event_id": event,
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "commence_time_utc": kickoff,
        "snapshot_time_utc": observed,
    }


def test_ready_fixture_meets_frozen_requirements():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [
        _row("e1", kickoff, "2026-09-11T18:00:00Z"),
        _row("e1", kickoff, "2026-09-12T00:00:00Z"),
        _row("e1", kickoff, "2026-09-12T12:00:00Z"),
    ]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T10:00:00Z"))
    assert coverage.iloc[0].status == STATUS_READY
    assert coverage.iloc[0].snapshot_count_before_cutoff == 3
    assert coverage.iloc[0].path_span_hours >= 12


def test_recoverable_fixture_has_enough_time_left():
    kickoff = "2026-09-13T18:00:00Z"
    rows = [_row("e1", kickoff, "2026-09-12T18:00:00Z")]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T20:00:00Z"))
    assert coverage.iloc[0].status == STATUS_RECOVERABLE


def test_late_first_snapshot_is_irrecoverable_even_before_cutoff():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [_row("e1", kickoff, "2026-09-12T06:30:00Z")]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T07:00:00Z"))
    assert coverage.iloc[0].status == STATUS_IRRECOVERABLE
    assert coverage.iloc[0].reason == "INSUFFICIENT_REMAINING_SPAN_BEFORE_CUTOFF"


def test_passed_cutoff_is_irrecoverable_if_not_ready():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [
        _row("e1", kickoff, "2026-09-12T08:00:00Z"),
        _row("e1", kickoff, "2026-09-12T10:00:00Z"),
    ]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T13:00:00Z"))
    assert coverage.iloc[0].status == STATUS_IRRECOVERABLE
    assert coverage.iloc[0].reason == "CUTOFF_ALREADY_PASSED"


def test_conflicting_kickoffs_are_fail_closed():
    rows = [
        _row("e1", "2026-09-12T18:00:00Z", "2026-09-11T18:00:00Z", league="SERIE_A"),
        _row("e1", "2026-09-13T18:00:00Z", "2026-09-12T00:00:00Z", league="SERIE_A"),
    ]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T01:00:00Z"))
    assert coverage.iloc[0].status == STATUS_CONFLICT


def test_summary_keeps_all_three_research_leagues():
    coverage = pd.DataFrame([{
        "league": "EPL",
        "status": STATUS_READY,
    }])
    summary = summarize_fixture_coverage(coverage)
    assert summary["league"].tolist() == ["EPL", "LA_LIGA", "SERIE_A"]
    assert summary.loc[summary["league"] == "EPL", "ready"].iloc[0] == 1
