from datetime import datetime, timezone

import pandas as pd
import pytest

import export_la_liga_upcoming_matches as exporter


def sample_snapshots():
    return pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "snapshot_time_utc": "2030-08-23T10:00:00Z",
            "commence_time_utc": "2030-08-24T19:00:00Z",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "snapshot_time_utc": "2030-08-23T11:00:00Z",
            "commence_time_utc": "2030-08-24T19:00:00Z",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
        },
    ])


def test_exporter_keeps_latest_representation_per_fixture():
    result = exporter.prepare_upcoming_fixtures(
        sample_snapshots(),
        now=datetime(
            2030,
            8,
            23,
            tzinfo=timezone.utc,
        ),
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert row["league"] == "LA_LIGA"
    assert row["event_id"] == "event-1"
    assert row["home_team"] == "Barcelona"
    assert row["away_team"] == "Real Madrid"

    # 19:00 UTC -> 21:00 Madrid during summer time.
    assert row["match_time"] == "21:00"


def test_exporter_rejects_other_leagues():
    frame = sample_snapshots()
    frame.loc[0, "league"] = "EPL"

    with pytest.raises(ValueError):
        exporter.prepare_upcoming_fixtures(
            frame,
            now=datetime(
                2030,
                8,
                23,
                tzinfo=timezone.utc,
            ),
        )


def test_exporter_excludes_past_fixtures():
    result = exporter.prepare_upcoming_fixtures(
        sample_snapshots(),
        now=datetime(
            2030,
            8,
            25,
            tzinfo=timezone.utc,
        ),
    )

    assert result.empty


def test_exporter_schema_is_explicitly_league_aware():
    result = exporter.prepare_upcoming_fixtures(
        sample_snapshots(),
        now=datetime(
            2030,
            8,
            23,
            tzinfo=timezone.utc,
        ),
    )

    assert list(result.columns) == [
        "league",
        "event_id",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_team_model",
        "away_team_model",
        "commence_time_utc",
        "match_datetime_local",
    ]
