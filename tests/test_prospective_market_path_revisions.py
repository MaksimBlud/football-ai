import pandas as pd

from prospective_market_path_revisions import STATUS_SUPERSEDED, mark_superseded_revisions


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
