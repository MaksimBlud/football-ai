import pandas as pd

from prospective_market_path_revisions import (
    STATUS_QUARANTINED_REVISION,
    STATUS_SUPERSEDED,
    mark_superseded_revisions,
)


def test_older_provider_event_for_same_pair_is_superseded():
    snapshots = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "old",
            "home_team": "Real Racing Club de Santander",
            "away_team": "Alavés",
            "snapshot_time_utc": "2026-08-31T08:00:00Z",
        },
        {
            "league": "LA_LIGA",
            "event_id": "new",
            "home_team": "Real Racing Club de Santander",
            "away_team": "Alavés",
            "snapshot_time_utc": "2026-09-04T11:00:00Z",
        },
    ])
    coverage = pd.DataFrame([
        {"league": "LA_LIGA", "event_id": "old", "status": "RECOVERABLE", "reason": "x"},
        {"league": "LA_LIGA", "event_id": "new", "status": "READY", "reason": "y"},
    ])
    result = mark_superseded_revisions(coverage, snapshots)
    assert result.loc[result["event_id"] == "old", "status"].iloc[0] == STATUS_SUPERSEDED
    assert result.loc[result["event_id"] == "new", "status"].iloc[0] == "READY"


def test_internal_event_conflict_is_not_hidden_by_superseded_marker():
    snapshots = pd.DataFrame([
        {
            "league": "SERIE_A",
            "event_id": "old",
            "home_team": "Cagliari",
            "away_team": "Lecce",
            "snapshot_time_utc": "2026-08-31T08:00:00Z",
        },
        {
            "league": "SERIE_A",
            "event_id": "new",
            "home_team": "Cagliari",
            "away_team": "Lecce",
            "snapshot_time_utc": "2026-09-04T11:00:00Z",
        },
    ])
    coverage = pd.DataFrame([
        {"league": "SERIE_A", "event_id": "old", "status": "CONFLICT", "reason": "MULTIPLE_KICKOFFS_FOR_EVENT_ID"},
        {"league": "SERIE_A", "event_id": "new", "status": "READY", "reason": "ok"},
    ])
    result = mark_superseded_revisions(coverage, snapshots)
    assert result.loc[result["event_id"] == "old", "status"].iloc[0] == "CONFLICT"


def test_monotonic_same_event_schedule_revision_is_quarantined_not_resolved():
    snapshots = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Celta Vigo",
            "away_team": "Málaga",
            "commence_time_utc": "2026-09-13T19:00:00Z",
            "snapshot_time_utc": "2026-09-04T12:00:00Z",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Celta Vigo",
            "away_team": "Málaga",
            "commence_time_utc": "2026-09-13T19:00:00Z",
            "snapshot_time_utc": "2026-09-04T16:00:00Z",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Celta Vigo",
            "away_team": "Málaga",
            "commence_time_utc": "2026-09-13T12:00:00Z",
            "snapshot_time_utc": "2026-09-04T20:00:00Z",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Celta Vigo",
            "away_team": "Málaga",
            "commence_time_utc": "2026-09-13T12:00:00Z",
            "snapshot_time_utc": "2026-09-05T10:00:00Z",
        },
    ])
    coverage = pd.DataFrame([{
        "league": "LA_LIGA",
        "event_id": "event-1",
        "status": "CONFLICT",
        "reason": "MULTIPLE_KICKOFFS_FOR_EVENT_ID",
        "operationally_active": True,
        "refresh_due": False,
        "refresh_reason": "CONFLICTING_KICKOFF_IDENTITY",
    }])
    result = mark_superseded_revisions(coverage, snapshots)
    row = result.iloc[0]
    assert row.status == STATUS_QUARANTINED_REVISION
    assert row.reason == "MONOTONIC_PROVIDER_SCHEDULE_REVISION_RESEARCH_EXCLUDED"
    assert not bool(row.operationally_active)
    assert not bool(row.refresh_due)
    assert row.refresh_reason == "RESEARCH_QUARANTINED_PROVIDER_REVISION"


def test_reappearing_kickoff_remains_hard_conflict():
    snapshots = pd.DataFrame([
        {
            "league": "SERIE_A",
            "event_id": "event-2",
            "home_team": "Cagliari",
            "away_team": "Lecce",
            "commence_time_utc": "2026-09-07T16:00:00Z",
            "snapshot_time_utc": "2026-09-01T08:00:00Z",
        },
        {
            "league": "SERIE_A",
            "event_id": "event-2",
            "home_team": "Cagliari",
            "away_team": "Lecce",
            "commence_time_utc": "2026-09-07T16:30:00Z",
            "snapshot_time_utc": "2026-09-01T10:00:00Z",
        },
        {
            "league": "SERIE_A",
            "event_id": "event-2",
            "home_team": "Cagliari",
            "away_team": "Lecce",
            "commence_time_utc": "2026-09-07T16:00:00Z",
            "snapshot_time_utc": "2026-09-01T12:00:00Z",
        },
    ])
    coverage = pd.DataFrame([{
        "league": "SERIE_A",
        "event_id": "event-2",
        "status": "CONFLICT",
        "reason": "MULTIPLE_KICKOFFS_FOR_EVENT_ID",
        "operationally_active": True,
        "refresh_due": False,
        "refresh_reason": "CONFLICTING_KICKOFF_IDENTITY",
    }])
    result = mark_superseded_revisions(coverage, snapshots)
    assert result.iloc[0].status == "CONFLICT"
    assert bool(result.iloc[0].operationally_active)
