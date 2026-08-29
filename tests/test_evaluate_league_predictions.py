import numpy as np
import pandas as pd
import pytest

import evaluate_league_predictions as evaluator


def ledger_frame():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "event-1",
                "home_team": "Alpha",
                "away_team": "Beta",
                "kickoff_utc":
                    "2026-08-01T14:00:00Z",
                "snapshot_time_utc":
                    "2026-08-01T10:00:00Z",
                "market_home_prob": 0.60,
                "market_draw_prob": 0.25,
                "market_away_prob": 0.15,
                "market_pick": "H",
                "prediction_mode": "MARKET_ONLY",
                "structural_applied": False,
            },
            {
                "league": "EPL",
                "event_id": "event-1",
                "home_team": "Alpha",
                "away_team": "Beta",
                "kickoff_utc":
                    "2026-08-01T14:00:00Z",
                "snapshot_time_utc":
                    "2026-08-01T13:00:00Z",
                "market_home_prob": 0.70,
                "market_draw_prob": 0.20,
                "market_away_prob": 0.10,
                "market_pick": "H",
                "prediction_mode": "MARKET_ONLY",
                "structural_applied": False,
            },
            {
                "league": "EPL",
                "event_id": "event-2",
                "home_team": "Gamma",
                "away_team": "Delta",
                "kickoff_utc":
                    "2026-08-02T14:00:00Z",
                "snapshot_time_utc":
                    "2026-08-02T12:00:00Z",
                "market_home_prob": 0.20,
                "market_draw_prob": 0.30,
                "market_away_prob": 0.50,
                "market_pick": "A",
                "prediction_mode": "MARKET_ONLY",
                "structural_applied": False,
            },
        ]
    )


def result_frame():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "match_date": "2026-08-01",
                "home_team": "Alpha",
                "away_team": "Beta",
                "result": "H",
            },
            {
                "league": "EPL",
                "match_date": "2026-08-02",
                "home_team": "Gamma",
                "away_team": "Delta",
                "result": "H",
            },
        ]
    )


def test_settlement_preserves_all_snapshots():
    settled = evaluator.settle_predictions(
        ledger_frame(),
        result_frame(),
    )

    assert len(settled) == 3
    assert settled["event_id"].nunique() == 2


def test_latest_view_selects_latest_snapshot():
    settled = evaluator.settle_predictions(
        ledger_frame(),
        result_frame(),
    )

    latest = evaluator.latest_pre_kickoff(
        settled
    )

    assert len(latest) == 2

    first = (
        latest
        .loc[
            latest["event_id"]
            == "event-1"
        ]
        .iloc[0]
    )

    assert (
        first[
            "snapshot_time_utc"
        ]
        == pd.Timestamp(
            "2026-08-01T13:00:00Z"
        )
    )

    assert (
        first[
            "market_home_prob"
        ]
        == pytest.approx(
            0.70
        )
    )


def test_multiclass_metrics_are_correct():
    settled = evaluator.settle_predictions(
        ledger_frame(),
        result_frame(),
    )

    latest = evaluator.latest_pre_kickoff(
        settled
    )

    metrics = evaluator.calculate_metrics(
        latest,
        view="LATEST",
    )

    assert metrics.prediction_rows == 2
    assert metrics.fixtures == 2
    assert metrics.correct == 1
    assert metrics.accuracy == pytest.approx(
        0.5
    )

    expected_log_loss = (
        -(
            np.log(0.70)
            + np.log(0.20)
        )
        / 2.0
    )

    assert metrics.log_loss == pytest.approx(
        expected_log_loss
    )

    first_brier = (
        (0.70 - 1.0) ** 2
        + (0.20 - 0.0) ** 2
        + (0.10 - 0.0) ** 2
    )

    second_brier = (
        (0.20 - 1.0) ** 2
        + (0.30 - 0.0) ** 2
        + (0.50 - 0.0) ** 2
    )

    expected_brier = (
        first_brier
        + second_brier
    ) / 2.0

    assert metrics.brier == pytest.approx(
        expected_brier
    )

    assert (
        metrics.mean_actual_probability
        == pytest.approx(
            0.45
        )
    )


def test_full_report_contains_two_views():
    (
        report,
        settled,
        latest,
    ) = evaluator.evaluate_frames(
        "EPL",
        ledger_frame(),
        result_frame(),
    )

    assert len(settled) == 3
    assert len(latest) == 2

    assert (
        report.all_snapshots.prediction_rows
        == 3
    )

    assert (
        report.latest_pre_kickoff.prediction_rows
        == 2
    )

    assert report.market_only_rows == 3
    assert report.structural_rows == 0


def test_post_kickoff_prediction_rejected():
    frame = ledger_frame()

    frame.loc[
        0,
        "snapshot_time_utc",
    ] = "2026-08-01T15:00:00Z"

    with pytest.raises(
        ValueError,
        match="non-pre-kickoff",
    ):
        evaluator.settle_predictions(
            frame,
            result_frame(),
        )


def test_market_pick_must_match_probabilities():
    frame = ledger_frame()

    frame.loc[
        0,
        "market_pick",
    ] = "A"

    with pytest.raises(
        ValueError,
        match="market_pick disagrees",
    ):
        evaluator.settle_predictions(
            frame,
            result_frame(),
        )


def test_empty_results_safe():
    (
        report,
        settled,
        latest,
    ) = evaluator.evaluate_frames(
        "EPL",
        ledger_frame(),
        pd.DataFrame(),
    )

    assert settled.empty
    assert latest.empty

    assert (
        report.all_snapshots.accuracy
        is None
    )

    assert (
        report.latest_pre_kickoff.log_loss
        is None
    )


def test_source_is_read_only():
    source = open(
        "evaluate_league_predictions.py",
        encoding="utf-8",
    ).read()

    forbidden = [
        ".insert(",
        ".upsert(",
        ".update(",
        ".delete(",
        "persist_predictions(",
        "persist_observations(",
        "persist_results(",
    ]

    for token in forbidden:
        assert token not in source


def test_source_does_not_use_model_or_structural_runtime():
    source = open(
        "evaluate_league_predictions.py",
        encoding="utf-8",
    ).read()

    forbidden = [
        "football_model_xgboost_elo",
        "joblib.load",
        "train_model",
        "league_structural_v2_shadow",
    ]

    for token in forbidden:
        assert token not in source
