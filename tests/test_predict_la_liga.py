from pathlib import Path

import pandas as pd
import pytest

import predict_la_liga as predictor


def market_frame():
    return pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "event-1",
            "commence_time_utc":
                "2030-01-02T20:00:00Z",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "market_home_probability": 0.55,
            "market_draw_probability": 0.25,
            "market_away_probability": 0.20,
            "market_argmax": "H",
            "market_shadow_status": "OK",
        },
        {
            "league": "LA_LIGA",
            "event_id": "event-2",
            "commence_time_utc":
                "2030-01-03T20:00:00Z",
            "home_team": "Valencia",
            "away_team": "Sevilla",
            "market_home_probability": 0.25,
            "market_draw_probability": 0.30,
            "market_away_probability": 0.45,
            "market_argmax": "A",
            "market_shadow_status": "OK",
        },
    ])


def test_prediction_contract():
    result = (
        predictor.build_predictions(
            market_frame()
        )
    )

    assert len(result) == 2

    assert list(
        result.columns
    ) == predictor.OUTPUT_COLUMNS


def test_predictions_use_market_argmax():
    result = (
        predictor.build_predictions(
            market_frame()
        )
    )

    first = result.iloc[0]
    second = result.iloc[1]

    assert (
        first["prediction"]
        == "HOME"
    )

    assert (
        second["prediction"]
        == "AWAY"
    )


def test_source_is_explicit():
    result = (
        predictor.build_predictions(
            market_frame()
        )
    )

    assert set(
        result[
            "prediction_source"
        ]
    ) == {
        "MARKET_BASELINE"
    }

    assert not result[
        "ai_model_used"
    ].astype(bool).any()

    assert result[
        "market_only"
    ].astype(bool).all()


def test_non_ok_rows_are_ignored():
    frame = market_frame()

    frame.loc[
        0,
        "market_shadow_status",
    ] = "NO_MARKET_ODDS"

    result = (
        predictor.build_predictions(
            frame
        )
    )

    assert len(result) == 1


def test_output_restricted_to_experiments(
    tmp_path,
):
    result = (
        predictor.build_predictions(
            market_frame()
        )
    )

    outside = (
        tmp_path
        / "predictions.csv"
    )

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        predictor.write_predictions(
            result,
            outside,
        )


def test_no_epl_model_usage():
    source = Path(
        "predict_la_liga.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        "football_model_xgboost_elo.pkl",
        "football_model_no_odds.pkl",
        "predict_match_no_odds",
        "goal_prediction_no_odds",
        "joblib",
        "train_model",
        "--production",
    ]

    for token in forbidden:
        assert token not in source
