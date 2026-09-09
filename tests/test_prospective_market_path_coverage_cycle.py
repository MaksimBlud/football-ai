import pandas as pd

import prospective_market_path_coverage_cycle as cycle
from prospective_market_path_revisions import STATUS_SUPERSEDED


def test_coverage_cycle_writes_revision_safe_market_status_and_live_priority(monkeypatch, tmp_path):
    rows_by_league = {
        "LA_LIGA": [
            {
                "league": "LA_LIGA",
                "event_id": "old",
                "home_team": "Real Racing Club de Santander",
                "away_team": "Alavés",
                "commence_time_utc": "2027-01-10T18:00:00Z",
                "snapshot_time_utc": "2026-09-05T12:00:00Z",
            },
            {
                "league": "LA_LIGA",
                "event_id": "new",
                "home_team": "Real Racing Club de Santander",
                "away_team": "Alavés",
                "commence_time_utc": "2027-01-10T18:00:00Z",
                "snapshot_time_utc": "2026-09-06T12:00:00Z",
            },
        ],
        "EPL": [
            {
                "league": "EPL",
                "event_id": "epl-live",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "commence_time_utc": "2027-01-11T18:00:00Z",
                "snapshot_time_utc": "2026-09-06T12:00:00Z",
            }
        ],
        "SERIE_A": [],
    }

    monkeypatch.setattr(cycle, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(cycle, "_fetch_snapshots", lambda league: rows_by_league[league])

    result = cycle.run()

    coverage_path = tmp_path / "fixture_coverage_monitor.csv"
    summary_path = tmp_path / "fixture_coverage_summary.csv"
    priority_path = tmp_path / "live_refresh_priority.csv"
    assert coverage_path.exists()
    assert summary_path.exists()
    assert priority_path.exists()

    coverage = pd.read_csv(coverage_path)
    priority = pd.read_csv(priority_path)
    old = coverage.loc[coverage["event_id"] == "old"].iloc[0]

    assert old.status == STATUS_SUPERSEDED
    assert not bool(old.operationally_active)
    assert not bool(old.refresh_due)
    assert "old" not in set(priority["event_id"])
    assert priority["event_id"].tolist() == ["new", "epl-live"]
    assert result["actionable_refresh_due"] == 2
    assert [row["event_id"] for row in result["live_refresh_queue"]] == ["new", "epl-live"]
