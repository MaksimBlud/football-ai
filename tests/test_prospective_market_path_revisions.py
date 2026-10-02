import pandas as pd

from prospective_market_path_revisions import (
    REFRESH_QUARANTINED_PAIR_REVISION,
    REFRESH_SUPERSEDED_PROVIDER_REVISION,
    STATUS_QUARANTINED_REVISION,
    STATUS_SUPERSEDED,
    filter_research_paths_for_provider_revisions,
    mark_superseded_revisions,
)


def test_older_provider_event_for_same_pair_is_superseded_and_deactivated():
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
        {
            "league": "LA_LIGA",
            "event_id": "old",
            "status": "RECOVERABLE",
            "reason": "x",
            "operationally_active": True,
            "refresh_due": True,
            "refresh_reason": "MANUAL_REFRESH_DUE_BY_EXISTING_CADENCE",
        },
        {
            "league": "LA_LIGA",
            "event_id": "new",
            "status": "READY",
            "reason": "y",
            "operationally_active": True,
            "refresh_due": True,
            "refresh_reason": "MANUAL_REFRESH_DUE_BY_EXISTING_CADENCE",
        },
    ])
    result = mark_superseded_revisions(coverage, snapshots)
    old = result.loc[result["event_id"] == "old"].iloc[0]
    new = result.loc[result["event_id"] == "new"].iloc[0]

    assert old.status == STATUS_SUPERSEDED
    assert old.reason == "OLDER_PROVIDER_REVISION_FOR_SAME_FIXTURE_PAIR"
    assert not bool(old.operationally_active)
    assert not bool(old.refresh_due)
    assert old.refresh_reason == REFRESH_SUPERSEDED_PROVIDER_REVISION

    assert new.status == "READY"
    assert bool(new.operationally_active)
    assert bool(new.refresh_due)


def test_tied_current_event_ids_for_same_pair_are_all_quarantined():
    snapshots = pd.DataFrame([
        {
            "league": "SERIE_A",
            "event_id": "old-kickoff-id",
            "home_team": "Torino",
            "away_team": "AS Roma",
            "commence_time_utc": "2026-09-13T10:30:00Z",
            "snapshot_time_utc": "2026-09-05T15:08:05Z",
        },
        {
            "league": "SERIE_A",
            "event_id": "new-kickoff-id",
            "home_team": "Torino",
            "away_team": "AS Roma",
            "commence_time_utc": "2026-09-14T16:30:00Z",
            "snapshot_time_utc": "2026-09-05T15:08:05Z",
        },
    ])
    coverage = pd.DataFrame([
        {
            "league": "SERIE_A",
            "event_id": "old-kickoff-id",
            "status": "READY",
            "reason": "ok",
            "operationally_active": True,
            "refresh_due": True,
            "refresh_reason": "MANUAL_REFRESH_DUE_BY_EXISTING_CADENCE",
        },
        {
            "league": "SERIE_A",
            "event_id": "new-kickoff-id",
            "status": "RECOVERABLE",
            "reason": "ok",
            "operationally_active": True,
            "refresh_due": True,
            "refresh_reason": "MANUAL_REFRESH_DUE_BY_EXISTING_CADENCE",
        },
    ])

    result = mark_superseded_revisions(coverage, snapshots)

    assert set(result["status"]) == {STATUS_QUARANTINED_REVISION}
    assert set(result["reason"]) == {"AMBIGUOUS_ACTIVE_PROVIDER_EVENT_REVISIONS_RESEARCH_EXCLUDED"}
    assert not result["operationally_active"].astype(bool).any()
    assert not result["refresh_due"].astype(bool).any()
    assert set(result["refresh_reason"]) == {REFRESH_QUARANTINED_PAIR_REVISION}


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


def test_research_path_filter_excludes_superseded_provider_id_and_keeps_latest():
    snapshots = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "old",
            "home_team": "Athletic Bilbao",
            "away_team": "Elche CF",
            "commence_time_utc": "2026-09-13T19:00:00Z",
            "snapshot_time_utc": "2026-09-04T16:29:24Z",
        },
        {
            "league": "LA_LIGA",
            "event_id": "new",
            "home_team": "Athletic Bilbao",
            "away_team": "Elche CF",
            "commence_time_utc": "2026-09-12T16:30:00Z",
            "snapshot_time_utc": "2026-09-11T15:45:28Z",
        },
    ])
    paths = pd.DataFrame([
        {"league": "LA_LIGA", "event_id": "old", "kickoff_utc": "2026-09-13T19:00:00Z"},
        {"league": "LA_LIGA", "event_id": "new", "kickoff_utc": "2026-09-12T16:30:00Z"},
    ])

    filtered, audit = filter_research_paths_for_provider_revisions(
        paths,
        snapshots,
    )

    assert filtered["event_id"].tolist() == ["new"]
    old = audit.loc[audit["event_id"] == "old"].iloc[0]
    new = audit.loc[audit["event_id"] == "new"].iloc[0]
    assert old.status == STATUS_SUPERSEDED
    assert not bool(old.research_path_eligible)
    assert new.status == "READY"
    assert bool(new.research_path_eligible)


def test_research_path_filter_quarantines_tied_current_pair_revisions():
    snapshots = pd.DataFrame([
        {
            "league": "SERIE_A",
            "event_id": "a",
            "home_team": "Torino",
            "away_team": "AS Roma",
            "commence_time_utc": "2026-09-13T10:30:00Z",
            "snapshot_time_utc": "2026-09-05T15:08:05Z",
        },
        {
            "league": "SERIE_A",
            "event_id": "b",
            "home_team": "Torino",
            "away_team": "AS Roma",
            "commence_time_utc": "2026-09-14T16:30:00Z",
            "snapshot_time_utc": "2026-09-05T15:08:05Z",
        },
    ])
    paths = pd.DataFrame([
        {"league": "SERIE_A", "event_id": "a"},
        {"league": "SERIE_A", "event_id": "b"},
    ])

    filtered, audit = filter_research_paths_for_provider_revisions(
        paths,
        snapshots,
    )

    assert filtered.empty
    assert set(audit["status"]) == {STATUS_QUARANTINED_REVISION}
    assert not audit["research_path_eligible"].astype(bool).any()
