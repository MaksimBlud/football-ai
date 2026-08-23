import pandas as pd

import analyze_la_liga_temporal_behavior as behavior


def fixture(
    states,
):
    rows = []

    for index in range(
        len(states) - 1
    ):
        rows.append({
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

            "observation_count":
                len(states) + 1,

            "previous_pair_index":
                index + 1,

            "latest_pair_index":
                index + 2,

            "previous_state":
                states[index],

            "latest_state":
                states[index + 1],

            "previous_direction":
                behavior._direction_for_state(
                    states[index]
                ),

            "latest_direction":
                behavior._direction_for_state(
                    states[index + 1]
                ),

            "previous_market_argmax":
                "H",

            "latest_market_argmax":
                "H",

            "transition":
                (
                    states[index]
                    + " -> "
                    + states[index + 1]
                ),
        })

    return pd.DataFrame(
        rows
    )


def test_fade():
    result = behavior.analyze_fixture(
        fixture([
            "HOME_STEAM",
            "NO_CHANGE",
        ])
    )

    assert result["has_fade"] is True
    assert (
        result["behavior_state"]
        == "FADE"
    )


def test_persistence():
    result = behavior.analyze_fixture(
        fixture([
            "HOME_STEAM",
            "HOME_STEAM",
            "HOME_STEAM",
        ])
    )

    assert (
        result[
            "has_persistence"
        ]
        is True
    )

    assert (
        result[
            "persistent_direction"
        ]
        == "H"
    )


def test_reversal():
    result = behavior.analyze_fixture(
        fixture([
            "HOME_STEAM",
            "AWAY_STEAM",
        ])
    )

    assert (
        result["has_reversal"]
        is True
    )

    assert (
        result["behavior_state"]
        == "REVERSAL"
    )


def test_stable():
    result = behavior.analyze_fixture(
        fixture([
            "NO_CHANGE",
            "NO_CHANGE",
        ])
    )

    assert (
        result["behavior_state"]
        == "STABLE"
    )


def test_output_schema():
    summary = (
        behavior.build_behavior_summary(
            fixture([
                "DRAW_STEAM",
                "NO_CHANGE",
            ])
        )
    )

    assert list(
        summary.columns
    ) == behavior.OUTPUT_COLUMNS
