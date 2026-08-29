import pandas as pd
import pytest

from league_prediction_ledger import (
    build_market_only_predictions,
    prediction_key,
)


def _shadow():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "event-1",
                "home_team": "Home",
                "away_team": "Away",
                "commence_time_utc":
                    "2026-08-30T15:00:00+00:00",
                "snapshot_time_utc":
                    "2026-08-30T12:00:00+00:00",
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


def test_market_only_prediction_contract():
    result = build_market_only_predictions(
        _shadow()
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert row["prediction_mode"] == "MARKET_ONLY"
    assert row["market_pick"] == "H"
    assert row["structural_applied"] == False

    assert pd.isna(
        row["structural_home_prob"]
    )

    assert row[
        "structural_status"
    ] == "CALIBRATION_REQUIRED"


def test_prediction_identity_is_deterministic():
    first = build_market_only_predictions(
        _shadow()
    )

    second = build_market_only_predictions(
        _shadow()
    )

    assert (
        first.iloc[0]["prediction_key"]
        ==
        second.iloc[0]["prediction_key"]
    )


def test_prediction_identity_changes_with_snapshot():
    first = build_market_only_predictions(
        _shadow()
    )

    changed = _shadow()

    changed.loc[
        0,
        "snapshot_time_utc",
    ] = "2026-08-30T13:00:00+00:00"

    second = build_market_only_predictions(
        changed
    )

    assert (
        first.iloc[0]["prediction_key"]
        !=
        second.iloc[0]["prediction_key"]
    )


def test_prediction_must_be_pre_kickoff():
    frame = _shadow()

    frame.loc[
        0,
        "snapshot_time_utc",
    ] = "2026-08-30T16:00:00+00:00"

    with pytest.raises(
        ValueError,
        match="pre-kickoff",
    ):
        build_market_only_predictions(
            frame
        )


def test_market_argmax_must_match_probabilities():
    frame = _shadow()

    frame.loc[
        0,
        "market_argmax",
    ] = "A"

    with pytest.raises(
        ValueError,
        match="market_argmax",
    ):
        build_market_only_predictions(
            frame
        )


def test_observation_key_link_is_preserved():
    frame = _shadow()

    result = build_market_only_predictions(
        frame,
        observation_keys={
            (
                "event-1",
                "2026-08-30T12:00:00+00:00",
            ):
                "EPL:test-observation",
        },
    )

    assert (
        result.iloc[0][
            "observation_key"
        ]
        ==
        "EPL:test-observation"
    )
