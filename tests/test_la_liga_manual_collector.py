import inspect

import pandas as pd

import league_config
import save_la_liga_odds_snapshot as collector
import the_odds_service


def test_generic_odds_service_exists():
    assert callable(
        the_odds_service.get_h2h_odds
    )

    source = inspect.getsource(
        the_odds_service.get_epl_h2h_odds
    )

    assert (
        "get_h2h_odds"
        in source
    )


def test_la_liga_collector_is_import_safe():
    assert callable(
        collector.main
    )

    source = inspect.getsource(
        collector
    )

    assert (
        'if __name__ == "__main__":'
        in source
    )


def test_la_liga_build_rows(
    monkeypatch,
):
    monkeypatch.setattr(
        collector,
        "aggregate_event_h2h",
        lambda event: {
            "event_id": "laliga-1",
            "commence_time":
                "2030-01-01T20:00:00Z",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "bookmakers_count": 10,
            "home_odds": 2.0,
            "draw_odds": 3.5,
            "away_odds": 3.4,
            "home_probability": 0.48,
            "draw_probability": 0.27,
            "away_probability": 0.25,
        },
    )

    frame = collector.build_snapshot_rows(
        [{}],
        "2030-01-01T12:00:00Z",
    )

    assert len(frame) == 1

    assert (
        frame.loc[
            0,
            "league",
        ]
        == "LA_LIGA"
    )


def test_la_liga_uses_shared_conflict_target():
    assert (
        collector.DB_CONFLICT_TARGET
        == "league,snapshot_time_utc,event_id"
    )


def test_la_liga_history_keeps_cross_league_identity():
    old = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "snapshot_time_utc":
                "2030-01-01T12:00:00Z",
            "event_id": "same",
            "commence_time_utc":
                "2030-01-01T20:00:00Z",
            "home_team": "Barcelona",
        }
    ])

    new = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "snapshot_time_utc":
                "2030-01-01T13:00:00Z",
            "event_id": "same",
            "commence_time_utc":
                "2030-01-01T20:00:00Z",
            "home_team": "Barcelona",
        }
    ])

    merged = collector.merge_local_history(
        old,
        new,
    )

    assert len(
        merged
    ) == 2


def test_la_liga_remains_not_scheduled():
    assert (
        league_config.LA_LIGA.collection_enabled
        is False
    )

    assert (
        league_config.LA_LIGA.collection_ready
        is False
    )
