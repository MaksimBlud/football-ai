from pathlib import Path

import pandas as pd
import pytest

import classify_la_liga_market_movements as classifier


def test_no_change():
    state, direction = (
        classifier.classify_movements(
            0.0,
            0.0,
            0.0,
            previous_argmax="H",
            latest_argmax="H",
        )
    )

    assert state == "NO_CHANGE"
    assert direction == "NONE"


def test_home_steam():
    state, direction = (
        classifier.classify_movements(
            0.02,
            -0.01,
            -0.01,
            previous_argmax="H",
            latest_argmax="H",
        )
    )

    assert state == "HOME_STEAM"
    assert direction == "H"


def test_draw_steam():
    state, direction = (
        classifier.classify_movements(
            -0.01,
            0.02,
            -0.01,
            previous_argmax="H",
            latest_argmax="H",
        )
    )

    assert state == "DRAW_STEAM"
    assert direction == "D"


def test_away_steam():
    state, direction = (
        classifier.classify_movements(
            -0.01,
            -0.01,
            0.02,
            previous_argmax="A",
            latest_argmax="A",
        )
    )

    assert state == "AWAY_STEAM"
    assert direction == "A"


def test_argmax_flip_has_precedence():
    state, direction = (
        classifier.classify_movements(
            0.001,
            -0.001,
            0.0,
            previous_argmax="A",
            latest_argmax="H",
        )
    )

    assert state == "ARGMAX_FLIP"
    assert direction == "H"


def test_tied_positive_movement_is_mixed():
    state, direction = (
        classifier.classify_movements(
            0.01,
            0.01,
            -0.02,
            previous_argmax="H",
            latest_argmax="H",
        )
    )

    assert state == "MIXED"
    assert direction == "NONE"


def history_fixture():
    return pd.DataFrame([
        {
            "league":
                "LA_LIGA",

            "event_id":
                "event-1",

            "home_team":
                "Barcelona",

            "away_team":
                "Real Madrid",

            "commence_time_utc":
                "2030-01-02T20:00:00Z",

            "snapshot_time_utc":
                "2030-01-01T18:00:00Z",

            "hours_before_kickoff":
                26.0,

            "market_home_probability":
                0.50,

            "market_draw_probability":
                0.25,

            "market_away_probability":
                0.25,

            "market_argmax":
                "H",

            "market_shadow_status":
                "OK",
        },
        {
            "league":
                "LA_LIGA",

            "event_id":
                "event-1",

            "home_team":
                "Barcelona",

            "away_team":
                "Real Madrid",

            "commence_time_utc":
                "2030-01-02T20:00:00Z",

            "snapshot_time_utc":
                "2030-01-01T20:00:00Z",

            "hours_before_kickoff":
                24.0,

            "market_home_probability":
                0.52,

            "market_draw_probability":
                0.24,

            "market_away_probability":
                0.24,

            "market_argmax":
                "H",

            "market_shadow_status":
                "OK",
        },
    ])


def test_build_states_uses_latest_two_observations():
    history = history_fixture()

    history[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        history[
            "snapshot_time_utc"
        ],
        utc=True,
    )

    history[
        "commence_time_utc"
    ] = pd.to_datetime(
        history[
            "commence_time_utc"
        ],
        utc=True,
    )

    states = classifier.build_states(
        history
    )

    assert len(states) == 1

    row = states.iloc[0]

    assert (
        row[
            "observation_count"
        ]
        == 2
    )

    assert (
        row[
            "movement_state"
        ]
        == "HOME_STEAM"
    )

    assert (
        row[
            "movement_magnitude"
        ]
        == pytest.approx(
            0.02
        )
    )


def test_single_observation_is_hold():
    history = history_fixture().iloc[
        :1
    ].copy()

    history[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        history[
            "snapshot_time_utc"
        ],
        utc=True,
    )

    history[
        "commence_time_utc"
    ] = pd.to_datetime(
        history[
            "commence_time_utc"
        ],
        utc=True,
    )

    states = classifier.build_states(
        history
    )

    assert states.empty


def test_output_restricted_to_experiments(
    tmp_path,
):
    frame = pd.DataFrame(
        columns=classifier.OUTPUT_COLUMNS
    )

    with pytest.raises(
        ValueError
    ):
        classifier.write_states(
            frame,
            tmp_path
            / "outside.csv",
        )


def test_no_ai_columns():
    assert not any(
        column.startswith("ai_")
        for column
        in classifier.OUTPUT_COLUMNS
    )
