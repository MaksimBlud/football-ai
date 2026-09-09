import pandas as pd

from prospective_market_path_refresh_priority import EXCLUDED_OPERATIONAL_STATUSES
from prospective_market_path_revisions import (
    STATUS_QUARANTINED_REVISION,
    STATUS_SUPERSEDED,
)
from prospective_market_status import (
    build_live_refresh_queue,
    build_market_status,
    render_market_status,
)


def _coverage_row(
    *,
    league,
    event_id,
    hours_until_cutoff,
    hours_since_last_snapshot,
    refresh_interval_hours,
    status="RECOVERABLE",
    operationally_active=True,
    refresh_due=True,
):
    return {
        "league": league,
        "event_id": event_id,
        "home_team": f"{event_id}-home",
        "away_team": f"{event_id}-away",
        "kickoff_utc": pd.Timestamp("2026-09-12T18:00:00Z"),
        "cutoff_utc": pd.Timestamp("2026-09-12T12:00:00Z"),
        "status": status,
        "snapshot_count_before_cutoff": 1,
        "last_snapshot_utc": pd.Timestamp("2026-09-09T00:00:00Z"),
        "hours_until_cutoff": hours_until_cutoff,
        "hours_since_last_snapshot": hours_since_last_snapshot,
        "refresh_interval_hours": refresh_interval_hours,
        "refresh_due": refresh_due,
        "refresh_reason": "MANUAL_REFRESH_DUE_BY_EXISTING_CADENCE",
        "operationally_active": operationally_active,
    }


def test_live_refresh_queue_excludes_revision_statuses_and_ranks_fixtures():
    coverage = pd.DataFrame([
        _coverage_row(
            league="EPL",
            event_id="later",
            hours_until_cutoff=20.0,
            hours_since_last_snapshot=12.0,
            refresh_interval_hours=6.0,
        ),
        _coverage_row(
            league="LA_LIGA",
            event_id="soon-less-stale",
            hours_until_cutoff=10.0,
            hours_since_last_snapshot=4.0,
            refresh_interval_hours=2.0,
        ),
        _coverage_row(
            league="SERIE_A",
            event_id="soon-more-stale",
            hours_until_cutoff=10.0,
            hours_since_last_snapshot=12.0,
            refresh_interval_hours=4.0,
        ),
        _coverage_row(
            league="LA_LIGA",
            event_id="superseded",
            hours_until_cutoff=1.0,
            hours_since_last_snapshot=100.0,
            refresh_interval_hours=2.0,
            status=STATUS_SUPERSEDED,
        ),
        _coverage_row(
            league="SERIE_A",
            event_id="quarantined",
            hours_until_cutoff=1.0,
            hours_since_last_snapshot=100.0,
            refresh_interval_hours=2.0,
            status=STATUS_QUARANTINED_REVISION,
        ),
        _coverage_row(
            league="EPL",
            event_id="inactive",
            hours_until_cutoff=0.5,
            hours_since_last_snapshot=100.0,
            refresh_interval_hours=2.0,
            operationally_active=False,
        ),
    ])

    queue = build_live_refresh_queue(coverage)

    assert set(EXCLUDED_OPERATIONAL_STATUSES).isdisjoint(set(queue["status"]))
    assert queue["event_id"].tolist() == [
        "soon-more-stale",
        "soon-less-stale",
        "later",
    ]
    assert queue["live_priority_rank"].tolist() == [1, 2, 3]
    assert queue["staleness_ratio"].tolist() == [3.0, 2.0, 2.0]


def test_market_status_applies_revision_safety_and_surfaces_actionable_priority():
    snapshots = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "old",
            "home_team": "Real Racing Club de Santander",
            "away_team": "Alavés",
            "commence_time_utc": "2026-09-08T18:00:00Z",
            "snapshot_time_utc": "2026-09-04T18:00:00Z",
        },
        {
            "league": "LA_LIGA",
            "event_id": "new",
            "home_team": "Real Racing Club de Santander",
            "away_team": "Alavés",
            "commence_time_utc": "2026-09-08T18:00:00Z",
            "snapshot_time_utc": "2026-09-05T15:00:00Z",
        },
        {
            "league": "EPL",
            "event_id": "epl-active",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "commence_time_utc": "2026-09-09T18:00:00Z",
            "snapshot_time_utc": "2026-09-05T12:00:00Z",
        },
    ])
    original = snapshots.copy(deep=True)

    status = build_market_status(
        snapshots,
        now_utc=pd.Timestamp("2026-09-06T00:00:00Z"),
    )

    old = status.coverage.loc[status.coverage["event_id"] == "old"].iloc[0]
    new = status.coverage.loc[status.coverage["event_id"] == "new"].iloc[0]
    la_liga = status.leagues.loc[status.leagues["league"] == "LA_LIGA"].iloc[0]
    epl = status.leagues.loc[status.leagues["league"] == "EPL"].iloc[0]

    assert old.status == STATUS_SUPERSEDED
    assert not bool(old.operationally_active)
    assert not bool(old.refresh_due)
    assert bool(new.operationally_active)

    assert la_liga.superseded == 1
    assert la_liga.actionable_refresh_due == 1
    assert epl.actionable_refresh_due == 1
    assert la_liga.refresh_priority_rank == 1
    assert epl.refresh_priority_rank == 2
    assert status.live_refresh_queue["event_id"].tolist() == ["new", "epl-active"]

    pd.testing.assert_frame_equal(snapshots, original)


def test_market_status_renderer_is_explicitly_read_only():
    snapshots = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Celta Vigo",
            "away_team": "Málaga",
            "commence_time_utc": "2026-09-10T18:00:00Z",
            "snapshot_time_utc": "2026-09-05T12:00:00Z",
        },
    ])
    status = build_market_status(
        snapshots,
        now_utc=pd.Timestamp("2026-09-06T00:00:00Z"),
    )
    rendered = render_market_status(status)

    assert "PROSPECTIVE MARKET STATUS" in rendered
    assert "Read-only. Provider-free. No writes." in rendered
    assert "LA_LIGA:" in rendered
    assert "NEXT:" in rendered
