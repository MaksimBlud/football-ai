from datetime import datetime, timezone

import pandas as pd
from pandas.testing import (
    assert_frame_equal,
)

import export_la_liga_upcoming_matches as legacy_fixture

from league_fixture_export import (
    prepare_upcoming_fixtures as generic_prepare,
)
from league_runtime_config import (
    LA_LIGA_RUNTIME_CONFIG,
)
from team_names import (
    normalize_team_name,
)


def test_fixture_export_semantic_parity():
    snapshots = pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "fixture-1",
                "snapshot_time_utc":
                    "2026-08-25T08:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
            },
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "fixture-1",
                "snapshot_time_utc":
                    "2026-08-25T10:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
            },
        ]
    )

    now = datetime(
        2026,
        8,
        25,
        7,
        0,
        tzinfo=timezone.utc,
    )

    legacy = (
        legacy_fixture
        .prepare_upcoming_fixtures(
            snapshots,
            now=now,
        )
    )

    generic = (
        generic_prepare(
            snapshots,
            LA_LIGA_RUNTIME_CONFIG,
            normalize_team=(
                normalize_team_name
            ),
            now=now,
        )
    )

    assert_frame_equal(
        legacy.reset_index(
            drop=True
        ),
        generic.reset_index(
            drop=True
        ),
        check_dtype=False,
        check_like=False,
    )


def test_market_probability_facade_parity():
    import generate_la_liga_market_shadow as legacy_market
    import league_market_shadow as generic_market

    legacy = (
        legacy_market
        .normalized_market_probabilities(
            1.80,
            3.80,
            4.50,
        )
    )

    generic = (
        generic_market
        .normalized_market_probabilities(
            1.80,
            3.80,
            4.50,
        )
    )

    assert legacy == generic

    assert (
        legacy_market
        .probability_argmax(
            *legacy
        )
        ==
        generic_market
        .probability_argmax(
            *generic
        )
    )


def test_market_prepare_snapshot_facade_parity():
    import generate_la_liga_market_shadow as legacy_market
    import league_market_shadow as generic_market

    frame = pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "market-1",
                "snapshot_time_utc":
                    "2026-08-25T10:00:00Z",
                "commence_time_utc":
                    "2026-08-26T20:00:00Z",
                "home_team":
                    "Barcelona",
                "away_team":
                    "Valencia",
                "home_odds":
                    1.80,
                "draw_odds":
                    3.80,
                "away_odds":
                    4.50,
            }
        ]
    )

    legacy = (
        legacy_market
        .prepare_snapshots(
            frame
        )
    )

    generic = (
        generic_market
        .prepare_snapshots(
            frame,
            LA_LIGA_RUNTIME_CONFIG,
        )
    )

    assert_frame_equal(
        legacy,
        generic,
        check_dtype=False,
    )
