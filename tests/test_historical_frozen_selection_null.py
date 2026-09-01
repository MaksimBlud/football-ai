import math

import numpy as np
import pandas as pd

from historical_frozen_selection_null import (
    Candidate,
    _simulate_candidate_metrics,
    familywise_null_summary,
    selection_aware_null,
)


def sample_frame():
    rows = []
    seasons = ["2016-2017", "2017-2018", "2018-2019", "2019-2020"]
    for season_index, season in enumerate(seasons):
        for pick, confidence, odds, count in [
            ("H", 0.65, 1.50, 40),
            ("A", 0.45, 2.20, 40),
        ]:
            if season_index < 3:
                wins = 30 if pick == "H" else 18
            else:
                wins = 30 if pick == "H" else 16
            for index in range(count):
                won = index < wins
                rows.append({
                    "league": "LA_LIGA",
                    "season": season,
                    "market_pick": pick,
                    "market_confidence": confidence,
                    "selected_odds": odds,
                    "won": won,
                    "profit": odds - 1.0 if won else -1.0,
                })
    return pd.DataFrame(rows)


def test_selection_aware_null_is_deterministic_for_fixed_seed():
    first_summary, first_simulations = selection_aware_null(
        sample_frame(), simulations=300, seed=123, batch_size=75
    )
    second_summary, second_simulations = selection_aware_null(
        sample_frame(), simulations=300, seed=123, batch_size=75
    )
    pd.testing.assert_frame_equal(first_summary, second_summary)
    pd.testing.assert_frame_equal(first_simulations, second_simulations)


def test_observed_rule_and_plus_one_tail_are_reported():
    summary, simulations = selection_aware_null(
        sample_frame(), simulations=400, seed=7, batch_size=100
    )
    row = summary.iloc[0]
    assert row["league"] == "LA_LIGA"
    assert row["observed_market_pick"] == "H"
    assert row["observed_confidence_bucket"] == "60–70%"
    assert row["observed_test_matches"] == 40
    assert math.isclose(row["observed_test_roi"], 0.125)
    assert len(simulations) == 400
    exceedances = int(row["selection_aware_roi_exceedances"])
    assert math.isclose(
        row["selection_aware_roi_upper_tail"],
        (exceedances + 1) / 401,
    )
    assert 0.0 < row["selection_aware_roi_upper_tail"] <= 1.0
    assert 0.0 <= row["same_rule_selection_share"] <= 1.0


def test_familywise_null_uses_maximum_across_leagues_per_simulation():
    observed = pd.DataFrame([
        {
            "league": "EPL",
            "observed_market_pick": "H",
            "observed_confidence_bucket": "50–60%",
            "observed_test_roi": 0.04,
        },
        {
            "league": "LA_LIGA",
            "observed_market_pick": "H",
            "observed_confidence_bucket": "60–70%",
            "observed_test_roi": 0.10,
        },
    ])
    simulations = pd.DataFrame([
        {"simulation": 0, "league": "EPL", "test_roi": 0.02},
        {"simulation": 0, "league": "LA_LIGA", "test_roi": 0.08},
        {"simulation": 1, "league": "EPL", "test_roi": 0.12},
        {"simulation": 1, "league": "LA_LIGA", "test_roi": 0.01},
        {"simulation": 2, "league": "EPL", "test_roi": 0.03},
        {"simulation": 2, "league": "LA_LIGA", "test_roi": 0.11},
    ])
    row = familywise_null_summary(observed, simulations).iloc[0]
    assert row["leagues_tested"] == 2
    assert row["observed_best_league"] == "LA_LIGA"
    assert row["familywise_roi_exceedances"] == 2
    assert math.isclose(row["familywise_roi_upper_tail"], 3 / 4)
    assert math.isclose(row["null_global_max_roi_q99"], np.quantile([0.08, 0.12, 0.11], 0.99))


def test_positive_season_share_ignores_absent_training_seasons_like_original_selector():
    candidate = Candidate(
        market_pick="H",
        confidence_bucket="60–70%",
        training_matches=4,
        training_indices_by_season=(
            np.array([0, 1], dtype=int),
            np.array([], dtype=int),
            np.array([2, 3], dtype=int),
        ),
        test_indices=np.array([], dtype=int),
    )
    train_roi, positive_share, *_ = _simulate_candidate_metrics(
        candidate,
        np.ones(4, dtype=float),
        np.full(4, 2.0, dtype=float),
        simulations=5,
        rng=np.random.default_rng(1),
        batch_size=5,
    )
    assert np.allclose(train_roi, 1.0)
    assert np.allclose(positive_share, 1.0)


def test_missing_columns_are_rejected():
    frame = sample_frame().drop(columns=["market_confidence"])
    try:
        selection_aware_null(frame, simulations=10, seed=1)
    except ValueError as exc:
        assert "market_confidence" in str(exc)
    else:
        raise AssertionError("expected ValueError")
