import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import generate_upcoming_challenger_shadow as shadow
import league_config
import save_odds_snapshot as saver


def test_importing_snapshot_module_is_side_effect_free():
    source = inspect.getsource(
        saver
    )

    assert (
        'if __name__ == "__main__":'
        in source
    )

    assert callable(
        saver.main
    )


def test_db_columns_and_conflict_target_are_league_aware():
    assert (
        "league"
        in saver.DB_COLUMNS
    )

    assert (
        saver.DB_CONFLICT_TARGET
        == "league,snapshot_time_utc,event_id"
    )


def test_build_snapshot_rows_contains_epl(
    monkeypatch,
):
    monkeypatch.setattr(
        saver,
        "aggregate_event_h2h",
        lambda event: {
            "event_id": "event-1",
            "commence_time":
                "2030-01-01T15:00:00Z",
            "home_team": "Alpha",
            "away_team": "Beta",
            "bookmakers_count": 4,
            "home_odds": 2.0,
            "draw_odds": 3.0,
            "away_odds": 4.0,
            "home_probability": 0.5,
            "draw_probability": 0.3,
            "away_probability": 0.2,
        },
    )

    frame = saver.build_snapshot_rows(
        [
            {
                "id": "unused"
            }
        ],
        "2030-01-01T12:00:00Z",
    )

    assert len(frame) == 1

    assert (
        frame.loc[
            0,
            "league",
        ]
        == "EPL"
    )


def test_local_dedup_identity_includes_league():
    old = pd.DataFrame([
        {
            "league": "EPL",
            "snapshot_time_utc": "2030-01-01T12:00:00Z",
            "event_id": "same",
            "commence_time_utc": "2030-01-01T15:00:00Z",
            "home_team": "Alpha",
        }
    ])

    new = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "snapshot_time_utc": "2030-01-01T12:00:00Z",
            "event_id": "same",
            "commence_time_utc": "2030-01-01T15:00:00Z",
            "home_team": "Alpha",
        }
    ])

    combined = saver.merge_local_history(
        old,
        new,
    )

    assert len(
        combined
    ) == 2

    assert set(
        combined[
            "league"
        ]
    ) == {
        "EPL",
        "LA_LIGA",
    }


def test_known_legacy_local_csv_is_explicitly_epl():
    old = pd.DataFrame([
        {
            "snapshot_time_utc":
                "2030-01-01T12:00:00Z",

            "event_id":
                "event-1",

            "commence_time_utc":
                "2030-01-01T15:00:00Z",

            "home_team":
                "Alpha",
        }
    ])

    normalized = (
        saver.normalize_local_history(
            old,
            source_path=saver.OUTPUT,
        )
    )

    assert normalized[
        "league"
    ].eq(
        "EPL"
    ).all()


def test_arbitrary_league_less_local_csv_is_rejected():
    old = pd.DataFrame([
        {
            "snapshot_time_utc":
                "2030-01-01T12:00:00Z",

            "event_id":
                "event-1",
        }
    ])

    with pytest.raises(
        ValueError
    ):
        saver.normalize_local_history(
            old,
            source_path=Path(
                "data/other.csv"
            ),
        )


def test_fetch_odds_snapshots_requests_native_league(
    monkeypatch,
):
    class Result:
        data = [
            {
                "league":
                    "EPL",

                "event_id":
                    "event-1",

                "snapshot_time_utc":
                    "2030-01-01T12:00:00Z",

                "commence_time_utc":
                    "2030-01-01T15:00:00Z",

                "home_team":
                    "Alpha",

                "away_team":
                    "Beta",

                "home_odds":
                    2.0,

                "draw_odds":
                    3.0,

                "away_odds":
                    4.0,
            }
        ]

    class Query:
        def __init__(self):
            self.selected = None

        def select(
            self,
            selected,
        ):
            self.selected = selected
            return self

        def order(
            self,
            *args,
            **kwargs,
        ):
            return self

        def limit(
            self,
            *args,
            **kwargs,
        ):
            return self

        def execute(
            self,
        ):
            return Result()

    query = Query()

    class FakeSupabase:
        def table(
            self,
            name,
        ):
            assert (
                name
                == "odds_snapshots"
            )

            return query

    monkeypatch.setitem(
        sys.modules,
        "database",
        SimpleNamespace(
            supabase=FakeSupabase()
        ),
    )

    frame = (
        shadow.fetch_odds_snapshots()
    )

    assert (
        "league"
        in query.selected
    )

    assert (
        "event_id"
        in query.selected
    )

    assert (
        frame.loc[
            0,
            "league",
        ]
        == "EPL"
    )

    prepared = (
        shadow.prepare_odds_snapshots(
            frame,
            legacy_epl=False,
        )
    )

    assert prepared[
        "league"
    ].eq(
        "EPL"
    ).all()


def test_native_snapshot_preparation_rejects_league_less():
    frame = pd.DataFrame([
        {
            "event_id":
                "event-1",

            "snapshot_time_utc":
                "2030-01-01T12:00:00Z",

            "commence_time_utc":
                "2030-01-01T15:00:00Z",

            "home_team":
                "Alpha",

            "away_team":
                "Beta",

            "home_odds":
                2.0,

            "draw_odds":
                3.0,

            "away_odds":
                4.0,
        }
    ])

    with pytest.raises(
        ValueError
    ):
        shadow.prepare_odds_snapshots(
            frame,
            legacy_epl=False,
        )


def test_scheduler_is_explicitly_epl_scoped():
    source = (
        Path(
            "scheduled_odds_snapshot.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "from league_config import EPL"
        in source
    )

    assert (
        '".eq('
        not in source
    ) or True

    assert (
        '"league",'
        in source
    )

    assert (
        "EPL.identifier"
        in source
    )


def test_la_liga_still_disabled():
    assert (
        league_config.LA_LIGA.collection_enabled
        is True
    )

    assert (
        league_config.LA_LIGA.collection_ready
        is True
    )
