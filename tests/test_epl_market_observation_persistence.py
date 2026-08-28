import pandas as pd
import pytest

import persist_epl_market_observations as module


def valid_shadow():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "epl-live-1",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "commence_time_utc":
                    "2030-08-03T15:00:00Z",
                "snapshot_time_utc":
                    "2030-08-03T10:00:00Z",
                "market_home_probability":
                    0.50,
                "market_draw_probability":
                    0.30,
                "market_away_probability":
                    0.20,
                "market_argmax": "H",
                "market_shadow_status": "OK",
                "market_only": True,
            }
        ]
    )


def test_market_only_observation_contract():
    result = (
        module
        .build_market_only_observations(
            valid_shadow()
        )
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row["prediction_source"]
        == "MARKET_ONLY"
    )

    assert not bool(
        row["structural_ready"]
    )

    assert not bool(
        row["correction_enabled"]
    )

    assert (
        row[
            "realized_correction_weight"
        ]
        == 0.0
    )

    assert (
        row[
            "market_home_probability"
        ]
        ==
        row[
            "shadow_home_probability"
        ]
    )

    assert (
        row[
            "market_draw_probability"
        ]
        ==
        row[
            "shadow_draw_probability"
        ]
    )

    assert (
        row[
            "market_away_probability"
        ]
        ==
        row[
            "shadow_away_probability"
        ]
    )

    assert (
        row["market_argmax"]
        == row["shadow_argmax"]
    )

    assert bool(
        row["pre_kickoff_valid"]
    )

    assert bool(
        row["research_only"]
    )


def test_rejects_post_kickoff_shadow():
    frame = valid_shadow()

    frame.loc[
        0,
        "snapshot_time_utc",
    ] = (
        "2030-08-03T16:00:00Z"
    )

    with pytest.raises(
        ValueError
    ):
        module.build_market_only_observations(
            frame
        )


def test_rejects_foreign_league():
    frame = valid_shadow()

    frame.loc[
        0,
        "league",
    ] = "LA_LIGA"

    with pytest.raises(
        ValueError
    ):
        module.build_market_only_observations(
            frame
        )


def test_rejects_non_market_only_state():
    frame = valid_shadow()

    frame.loc[
        0,
        "market_only",
    ] = False

    with pytest.raises(
        ValueError
    ):
        module.build_market_only_observations(
            frame
        )


def test_rejects_non_normalized_probabilities():
    frame = valid_shadow()

    frame.loc[
        0,
        "market_home_probability",
    ] = 0.70

    with pytest.raises(
        ValueError
    ):
        module.build_market_only_observations(
            frame
        )
