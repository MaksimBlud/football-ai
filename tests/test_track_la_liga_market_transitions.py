from pathlib import Path

import pandas as pd
import pytest

import track_la_liga_market_transitions as tracker


def history_frame():
    return pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "commence_time_utc":
                "2030-01-02T20:00:00Z",
            "snapshot_time_utc":
                "2030-01-01T10:00:00Z",
            "hours_before_kickoff": 34.0,
            "market_home_probability": 0.50,
            "market_draw_probability": 0.25,
            "market_away_probability": 0.25,
            "market_argmax": "H",
            "market_shadow_status": "OK",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "commence_time_utc":
                "2030-01-02T20:00:00Z",
            "snapshot_time_utc":
                "2030-01-01T11:00:00Z",
            "hours_before_kickoff": 33.0,
            "market_home_probability": 0.52,
            "market_draw_probability": 0.24,
            "market_away_probability": 0.24,
            "market_argmax": "H",
            "market_shadow_status": "OK",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "commence_time_utc":
                "2030-01-02T20:00:00Z",
            "snapshot_time_utc":
                "2030-01-01T12:00:00Z",
            "hours_before_kickoff": 32.0,
            "market_home_probability": 0.52,
            "market_draw_probability": 0.24,
            "market_away_probability": 0.24,
            "market_argmax": "H",
            "market_shadow_status": "OK",
        },
    ])


def prepared_history():
    frame = history_frame()

    frame[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        frame["snapshot_time_utc"],
        utc=True,
    )

    frame[
        "commence_time_utc"
    ] = pd.to_datetime(
        frame["commence_time_utc"],
        utc=True,
    )

    return frame


def test_build_pair_states_uses_all_adjacent_pairs():
    pairs = tracker.build_pair_states(
        prepared_history()
    )

    assert len(pairs) == 2

    assert pairs[
        "pair_index"
    ].tolist() == [1, 2]

    assert (
        pairs.iloc[0][
            "movement_state"
        ]
        == "HOME_STEAM"
    )

    assert (
        pairs.iloc[1][
            "movement_state"
        ]
        == "NO_CHANGE"
    )


def test_three_observations_create_one_transition():
    result = tracker.build_transitions(
        prepared_history()
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row["observation_count"]
        == 3
    )

    assert (
        row["movement_pair_count"]
        == 2
    )

    assert (
        row["transition_count"]
        == 1
    )

    assert (
        row["previous_state"]
        == "HOME_STEAM"
    )

    assert (
        row["latest_state"]
        == "NO_CHANGE"
    )

    assert (
        row["transition"]
        == "HOME_STEAM -> NO_CHANGE"
    )

    assert bool(
        row["state_changed"]
    ) is True


def test_two_observations_are_not_enough_for_transition():
    frame = prepared_history().iloc[
        :2
    ].copy()

    result = tracker.build_transitions(
        frame
    )

    assert result.empty


def test_argmax_flip_is_preserved():
    frame = prepared_history()

    frame.loc[
        frame.index[2],
        "market_home_probability",
    ] = 0.30

    frame.loc[
        frame.index[2],
        "market_away_probability",
    ] = 0.46

    frame.loc[
        frame.index[2],
        "market_argmax",
    ] = "A"

    result = tracker.build_transitions(
        frame
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row["latest_state"]
        == "ARGMAX_FLIP"
    )

    assert (
        row["latest_market_argmax"]
        == "A"
    )


def test_duplicate_observation_does_not_create_fake_transition():
    frame = history_frame()

    duplicate = frame.iloc[
        [1]
    ].copy()

    frame = pd.concat(
        [
            frame,
            duplicate,
        ],
        ignore_index=True,
    )

    frame[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        frame["snapshot_time_utc"],
        utc=True,
    )

    frame[
        "commence_time_utc"
    ] = pd.to_datetime(
        frame["commence_time_utc"],
        utc=True,
    )

    frame = frame.drop_duplicates(
        subset=[
            "league",
            "event_id",
            "snapshot_time_utc",
        ],
        keep="last",
    )

    pairs = tracker.build_pair_states(
        frame
    )

    assert len(pairs) == 2


def test_write_rejects_output_outside_experiments(
    tmp_path,
):
    frame = tracker.build_transitions(
        prepared_history()
    )

    outside = tmp_path / "states.csv"

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        tracker.write_transitions(
            frame,
            outside,
        )


def test_tracker_is_la_liga_research_only():
    source = Path(
        "track_la_liga_market_transitions.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        "football_model_xgboost_elo.pkl",
        "football_model_no_odds.pkl",
        "home_goals_model_no_odds.pkl",
        "away_goals_model_no_odds.pkl",
        "over_2_5_calibrator.pkl",
        "btts_calibrator.pkl",
    ]

    for token in forbidden:
        assert token not in source


def test_four_observations_create_two_transitions():
    frame = prepared_history()

    fourth = frame.iloc[
        [-1]
    ].copy()

    fourth[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        ["2030-01-01T13:00:00Z"],
        utc=True,
    )

    fourth[
        "hours_before_kickoff"
    ] = 31.0

    fourth[
        "market_home_probability"
    ] = 0.50

    fourth[
        "market_draw_probability"
    ] = 0.25

    fourth[
        "market_away_probability"
    ] = 0.25

    fourth[
        "market_argmax"
    ] = "H"

    frame = pd.concat(
        [
            frame,
            fourth,
        ],
        ignore_index=True,
    )

    result = tracker.build_transitions(
        frame
    )

    assert len(result) == 2

    assert (
        result[
            "observation_count"
        ]
        == 4
    ).all()

    assert (
        result[
            "movement_pair_count"
        ]
        == 3
    ).all()

    assert (
        result[
            "transition_count"
        ]
        == 2
    ).all()

    assert result[
        "previous_pair_index"
    ].tolist() == [1, 2]

    assert result[
        "latest_pair_index"
    ].tolist() == [2, 3]


def test_transition_identity_is_unique():
    frame = prepared_history()

    result = tracker.build_transitions(
        frame
    )

    duplicates = result.duplicated(
        subset=[
            "league",
            "event_id",
            "previous_pair_index",
            "latest_pair_index",
        ],
        keep=False,
    )

    assert not duplicates.any()
