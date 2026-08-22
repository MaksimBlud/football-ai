from pathlib import Path

import pandas as pd
import pytest

import league_config

from fixture_identity import (
    CANONICAL_FIXTURE_IDENTITY,
    CANONICAL_SNAPSHOT_FIELDS,
    normalize_snapshot_rows,
    normalize_upcoming_fixtures,
)

from generate_upcoming_challenger_shadow import (
    match_odds_to_upcoming,
)

from analyze_challenger_shadow_history import (
    build_movement_summary,
)

from track_challenger_signal_transitions import (
    build_signal_transitions,
    build_fixture_state_summary,
)

from derive_challenger_decision_states import (
    derive_decision_states,
)


def fixture(league):
    return pd.DataFrame([
        {
            "league": league,
            "match_datetime_uk":
                "2030-01-01T15:00:00Z",
            "home_team": "Arsenal",
            "away_team": "Example",
        }
    ])


def snapshot(league, odds):
    return pd.DataFrame([
        {
            "league": league,
            "event_id": league,
            "snapshot_time_utc":
                "2030-01-01T12:00:00Z",
            "commence_time_utc":
                "2030-01-01T15:00:00Z",
            "home_team": "Arsenal",
            "away_team": "Example",
            "home_odds": odds,
            "draw_odds": 3.0,
            "away_odds": 4.0,
        }
    ])


def test_league_configuration_is_inert_for_la_liga():
    assert (
        league_config.EPL.odds_api_sport_key
        == "soccer_epl"
    )

    assert (
        league_config.LA_LIGA.odds_api_sport_key
        == "soccer_spain_la_liga"
    )

    assert (
        league_config.LA_LIGA.name
        == "La Liga"
    )

    assert (
        league_config.LA_LIGA.timezone
        == "Europe/Madrid"
    )

    assert (
        league_config.LA_LIGA.collection_enabled
        is False
    )

    assert (
        league_config.is_collection_ready(
            "LA_LIGA"
        )
        is False
    )

    assert [
        x.identifier
        for x in league_config.configured_leagues()
    ] == [
        "EPL",
        "LA_LIGA",
    ]


def test_canonical_schemas_and_strict_legacy_adapters():
    assert (
        CANONICAL_FIXTURE_IDENTITY[0]
        == "league"
    )

    assert (
        "league"
        in CANONICAL_SNAPSHOT_FIELDS
    )

    legacy_fixture = (
        fixture("EPL")
        .drop(columns="league")
    )

    normalized = normalize_upcoming_fixtures(
        legacy_fixture,
        source_path=Path(
            "data/upcoming_matches.csv"
        ),
    )

    assert normalized[
        "league"
    ].eq(
        "EPL"
    ).all()

    with pytest.raises(
        ValueError
    ):
        normalize_upcoming_fixtures(
            legacy_fixture
        )

    legacy_snapshot = (
        snapshot(
            "EPL",
            2.0,
        )
        .drop(
            columns=[
                "league",
                "event_id",
            ]
        )
    )

    normalized_snapshot = (
        normalize_snapshot_rows(
            legacy_snapshot,
            legacy_epl=True,
        )
    )

    assert normalized_snapshot[
        "league"
    ].eq(
        "EPL"
    ).all()

    with pytest.raises(
        ValueError
    ):
        normalize_snapshot_rows(
            legacy_snapshot
        )


def test_same_fixture_in_different_leagues_never_cross_matches():
    upcoming = pd.concat(
        [
            fixture("EPL"),
            fixture("LA_LIGA"),
        ],
        ignore_index=True,
    )

    snapshots = pd.concat(
        [
            snapshot(
                "EPL",
                2.0,
            ),
            snapshot(
                "LA_LIGA",
                9.0,
            ),
        ],
        ignore_index=True,
    )

    matched = match_odds_to_upcoming(
        upcoming,
        snapshots,
        legacy_epl=False,
    )

    assert (
        matched
        .set_index("league")[
            "home_odds"
        ]
        .to_dict()
        == {
            "EPL": 2.0,
            "LA_LIGA": 9.0,
        }
    )


def test_research_layers_keep_cross_league_fixtures_separate():
    rows = []

    for league in (
        "EPL",
        "LA_LIGA",
    ):
        for hour, home in (
            (
                10,
                0.40,
            ),
            (
                11,
                0.42,
            ),
        ):
            rows.append({
                "league":
                    league,

                "home_team":
                    "Arsenal",

                "away_team":
                    "Example",

                "commence_time_utc":
                    "2030-01-01T15:00:00Z",

                "generated_at_utc":
                    f"2030-01-01T{hour}:00:00Z",

                "shadow_status":
                    "OK",

                "hours_before_kickoff":
                    15 - hour,

                "market_home_probability":
                    home,

                "market_draw_probability":
                    0.30,

                "market_away_probability":
                    0.30,

                "ai_home_probability":
                    0.50,

                "ai_draw_probability":
                    0.25,

                "ai_away_probability":
                    0.25,
            })

    history = pd.DataFrame(
        rows
    )

    movement = build_movement_summary(
        history
    )

    assert len(
        movement
    ) == 2

    assert set(
        movement["league"]
    ) == {
        "EPL",
        "LA_LIGA",
    }

    transitions = (
        build_signal_transitions(
            history
        )
    )

    assert len(
        transitions
    ) == 2

    states = derive_decision_states(
        build_fixture_state_summary(
            transitions
        )
    )

    assert set(
        states["league"]
    ) == {
        "EPL",
        "LA_LIGA",
    }
