from pathlib import Path

import pandas as pd

from prospective_market_path_coverage import (
    REFRESH_CUTOFF_PASSED,
    REFRESH_DEFER,
    REFRESH_DUE,
    STATUS_CONFLICT,
    STATUS_IRRECOVERABLE,
    STATUS_READY,
    STATUS_RECOVERABLE,
    build_fixture_coverage,
    refresh_interval_hours,
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
    assert bool(coverage.iloc[0].operationally_active)


def test_recoverable_fixture_has_enough_time_left():
    kickoff = "2026-09-13T18:00:00Z"
    rows = [_row("e1", kickoff, "2026-09-12T18:00:00Z")]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T20:00:00Z"))
    assert coverage.iloc[0].status == STATUS_RECOVERABLE
    assert bool(coverage.iloc[0].operationally_active)


def test_late_first_snapshot_is_irrecoverable_even_before_cutoff():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [_row("e1", kickoff, "2026-09-12T06:30:00Z")]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T07:00:00Z"))
    assert coverage.iloc[0].status == STATUS_IRRECOVERABLE
    assert coverage.iloc[0].reason == "INSUFFICIENT_REMAINING_SPAN_BEFORE_CUTOFF"
    assert bool(coverage.iloc[0].operationally_active)


def test_passed_cutoff_is_irrecoverable_if_not_ready():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [
        _row("e1", kickoff, "2026-09-12T08:00:00Z"),
        _row("e1", kickoff, "2026-09-12T10:00:00Z"),
    ]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T13:00:00Z"))
    assert coverage.iloc[0].status == STATUS_IRRECOVERABLE
    assert coverage.iloc[0].reason == "CUTOFF_ALREADY_PASSED"
    assert not bool(coverage.iloc[0].operationally_active)
    assert not bool(coverage.iloc[0].refresh_due)
    assert coverage.iloc[0].refresh_reason == REFRESH_CUTOFF_PASSED


def test_conflicting_kickoffs_are_fail_closed_and_active_until_latest_candidate_cutoff():
    rows = [
        _row("e1", "2026-09-12T18:00:00Z", "2026-09-11T18:00:00Z", league="SERIE_A"),
        _row("e1", "2026-09-13T18:00:00Z", "2026-09-12T00:00:00Z", league="SERIE_A"),
    ]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-12T01:00:00Z"))
    assert coverage.iloc[0].status == STATUS_CONFLICT
    assert bool(coverage.iloc[0].operationally_active)
    assert not bool(coverage.iloc[0].refresh_due)


def test_historical_conflict_stays_visible_but_is_not_active_health_risk():
    rows = [
        _row("e1", "2026-09-12T18:00:00Z", "2026-09-11T18:00:00Z", league="LA_LIGA"),
        _row("e1", "2026-09-13T18:00:00Z", "2026-09-12T00:00:00Z", league="LA_LIGA"),
    ]
    coverage = build_fixture_coverage(pd.DataFrame(rows), now_utc=pd.Timestamp("2026-09-13T13:00:00Z"))
    assert coverage.iloc[0].status == STATUS_CONFLICT
    assert not bool(coverage.iloc[0].operationally_active)


def test_ready_path_can_be_refresh_due_without_changing_frozen_status():
    kickoff = "2026-09-14T18:00:00Z"
    rows = [
        _row("e1", kickoff, "2026-09-12T18:00:00Z"),
        _row("e1", kickoff, "2026-09-13T00:00:00Z"),
        _row("e1", kickoff, "2026-09-13T12:00:00Z"),
    ]
    coverage = build_fixture_coverage(
        pd.DataFrame(rows),
        now_utc=pd.Timestamp("2026-09-14T06:00:00Z"),
    )
    row = coverage.iloc[0]
    assert row.status == STATUS_READY
    assert row.refresh_interval_hours == 4.0
    assert row.hours_since_last_snapshot == 18.0
    assert bool(row.refresh_due)
    assert row.refresh_reason == REFRESH_DUE


def test_recent_ready_path_defers_paid_refresh():
    kickoff = "2026-09-14T18:00:00Z"
    rows = [
        _row("e1", kickoff, "2026-09-12T18:00:00Z", league="SERIE_A"),
        _row("e1", kickoff, "2026-09-13T00:00:00Z", league="SERIE_A"),
        _row("e1", kickoff, "2026-09-14T04:00:00Z", league="SERIE_A"),
    ]
    coverage = build_fixture_coverage(
        pd.DataFrame(rows),
        now_utc=pd.Timestamp("2026-09-14T06:00:00Z"),
    )
    row = coverage.iloc[0]
    assert row.status == STATUS_READY
    assert row.refresh_interval_hours == 4.0
    assert row.hours_since_last_snapshot == 2.0
    assert not bool(row.refresh_due)
    assert row.refresh_reason == REFRESH_DEFER


def test_refresh_policy_mirrors_existing_league_collector_cadence():
    assert refresh_interval_hours("EPL", 80) == 12.0
    assert refresh_interval_hours("EPL", 48) == 6.0
    assert refresh_interval_hours("SERIE_A", 12) == 4.0
    assert refresh_interval_hours("SERIE_A", 4) == 2.0
    assert refresh_interval_hours("LA_LIGA", 100) == 2.0


def test_summary_keeps_all_three_research_leagues_and_refresh_due_count():
    coverage = pd.DataFrame([{
        "league": "EPL",
        "status": STATUS_READY,
        "refresh_due": True,
    }])
    summary = summarize_fixture_coverage(coverage)
    assert summary["league"].tolist() == ["EPL", "LA_LIGA", "SERIE_A"]
    assert summary.loc[summary["league"] == "EPL", "ready"].iloc[0] == 1
    assert summary.loc[summary["league"] == "EPL", "manual_refresh_due"].iloc[0] == 1


def test_superseded_refresh_due_is_not_counted_as_manual_advice():
    coverage = pd.DataFrame([{
        "league": "LA_LIGA",
        "status": "SUPERSEDED",
        "refresh_due": True,
    }])
    summary = summarize_fixture_coverage(coverage)
    assert summary.loc[summary["league"] == "LA_LIGA", "manual_refresh_due"].iloc[0] == 0


def test_workflow_uploads_diagnostics_before_fail_closed_active_health_gate():
    text = Path(".github/workflows/prospective-market-path-coverage.yml").read_text()
    upload = "name: Upload coverage artifacts"
    gate = "name: Enforce active coverage health"
    assert upload in text
    assert gate in text
    assert text.index(upload) < text.index(gate)
    assert "operationally_active" in text
    assert "['IRRECOVERABLE','CONFLICT']" in text
    assert "if: always()" in text
