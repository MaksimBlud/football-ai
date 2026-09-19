import numpy as np
import pandas as pd

from market_anchor_ou25_v1 import (
    FEATURE_VARIANTS,
    LAMBDA_GRID,
    MARKET_ODDS_PAIRS,
    TEST_SEASON,
    TRAIN_SEASONS,
    VALIDATION_SEASON,
    _extract_ou25_odds,
    devig_ou25_odds,
    dual_metric_improvement,
    fit_residual_model,
    market_anchored_probability,
    score_probabilities,
)


def test_devig_ou25_is_valid_probability():
    p = devig_ou25_odds(np.array([2.0, 1.80]), np.array([2.0, 2.10]))
    assert np.all((p > 0) & (p < 1))
    assert abs(p[0] - 0.5) < 1e-12


def test_market_source_priority_prefers_consensus_and_supports_old_name():
    modern = pd.Series(
        {
            "Avg>2.5": 1.91,
            "Avg<2.5": 1.99,
            "B365>2.5": 1.90,
            "B365<2.5": 2.00,
        }
    )
    assert _extract_ou25_odds(modern) == (1.91, 1.99, "AVG_STANDARD")

    old = pd.Series(
        {
            "BbAv>2.5": 1.88,
            "BbAv<2.5": 2.02,
            "B365>2.5": 1.85,
            "B365<2.5": 2.05,
        }
    )
    assert _extract_ou25_odds(old) == (1.88, 2.02, "BBAV_STANDARD")


def test_market_contract_contains_no_closing_columns():
    fields = [column for over, under, _ in MARKET_ODDS_PAIRS for column in (over, under)]
    assert fields == [
        "Avg>2.5",
        "Avg<2.5",
        "BbAv>2.5",
        "BbAv<2.5",
        "B365>2.5",
        "B365<2.5",
        "P>2.5",
        "P<2.5",
    ]
    assert not any("C>2.5" in field or "C<2.5" in field for field in fields)


def test_lambda_zero_is_exact_market_identity():
    market = np.array([0.42, 0.55, 0.63])
    residual = np.array([10.0, -7.0, 3.0])
    anchored = market_anchored_probability(market, residual, 0.0)
    assert np.array_equal(anchored, market)


def test_dual_metric_gate_fails_closed_if_either_metric_loses():
    market = {"brier": 0.24, "log_loss": 0.68}
    assert not dual_metric_improvement({"brier": 0.23, "log_loss": 0.69}, market)
    assert not dual_metric_improvement({"brier": 0.25, "log_loss": 0.67}, market)
    assert dual_metric_improvement({"brier": 0.23, "log_loss": 0.67}, market)


def test_residual_fit_can_learn_binary_signal_without_touching_market_identity():
    rng = np.random.default_rng(11)
    n = 240
    signal = rng.normal(size=n)
    X = pd.DataFrame({"signal": signal})
    market = np.full(n, 0.50)
    y = (signal > 0.0).astype(int)
    model = fit_residual_model(X, y, market, l2_penalty=0.2)
    residual = model.residual_logit(X)
    candidate = market_anchored_probability(market, residual, 1.0)
    assert score_probabilities(y, candidate)["log_loss"] < score_probabilities(y, market)["log_loss"]
    assert np.array_equal(market_anchored_probability(market, residual, 0.0), market)


def test_temporal_and_feature_contract_is_frozen_before_oot():
    assert TRAIN_SEASONS[-1] == "2023-2024"
    assert VALIDATION_SEASON == "2024-2025"
    assert TEST_SEASON == "2025-2026"
    assert all("2026-2027" != season for season in (*TRAIN_SEASONS, VALIDATION_SEASON, TEST_SEASON))
    assert LAMBDA_GRID == (0.0, 0.10, 0.25, 0.50, 0.75, 1.0)
    assert set(FEATURE_VARIANTS) == {"GOALS10", "GOALS_CORNERS10"}
