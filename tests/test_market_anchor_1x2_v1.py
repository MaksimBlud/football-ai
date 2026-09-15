import numpy as np
import pandas as pd

from market_anchor_1x2_v1 import (
    FEATURE_VARIANTS,
    LAMBDA_GRID,
    TEST_SEASON,
    TRAIN_SEASONS,
    VALIDATION_SEASON,
    devig_market_probabilities,
    dual_metric_improvement,
    fit_residual_model,
    market_anchored_probabilities,
    score_probabilities,
)


def test_devig_is_valid_probability_matrix():
    p = devig_market_probabilities(np.array([[0.50, 0.30, 0.25], [2.0, 1.0, 1.0]]))
    assert np.allclose(p.sum(axis=1), 1.0)
    assert np.isfinite(p).all()
    assert (p > 0).all()


def test_lambda_zero_is_exact_market_identity():
    market = devig_market_probabilities(np.array([[0.55, 0.28, 0.22], [0.25, 0.35, 0.50]]))
    residual = np.array([[10.0, -5.0, 3.0], [-7.0, 1.0, 9.0]])
    anchored = market_anchored_probabilities(market, residual, 0.0)
    assert np.array_equal(anchored, market)


def test_residual_outputs_valid_probabilities():
    market = devig_market_probabilities(np.array([[0.50, 0.30, 0.25], [0.25, 0.35, 0.50]]))
    residual = np.array([[0.3, 0.0, -0.2], [-0.1, 0.0, 0.4]])
    p = market_anchored_probabilities(market, residual, 0.5)
    assert np.allclose(p.sum(axis=1), 1.0)
    assert (p > 0).all() and (p < 1).all()


def test_dual_metric_gate_fails_closed_if_either_metric_loses():
    market = {"brier": 0.60, "log_loss": 1.00, "accuracy": 0.50}
    assert not dual_metric_improvement({"brier": 0.59, "log_loss": 1.01, "accuracy": 0.60}, market)
    assert not dual_metric_improvement({"brier": 0.61, "log_loss": 0.99, "accuracy": 0.60}, market)
    assert dual_metric_improvement({"brier": 0.59, "log_loss": 0.99, "accuracy": 0.40}, market)


def test_residual_fit_can_learn_signal_without_touching_market_identity():
    rng = np.random.default_rng(7)
    n = 180
    x = rng.normal(size=n)
    X = pd.DataFrame({"signal": x})
    market = np.tile(np.array([0.40, 0.30, 0.30]), (n, 1))
    y = np.where(x > 0.7, 0, np.where(x < -0.7, 2, 1))
    model = fit_residual_model(X, y, market, l2_penalty=0.2)
    residual = model.residual_logits(X)
    p = market_anchored_probabilities(market, residual, 1.0)
    assert score_probabilities(y, p)["log_loss"] < score_probabilities(y, market)["log_loss"]
    assert np.array_equal(market_anchored_probabilities(market, residual, 0.0), market)


def test_temporal_contract_excludes_opened_september_2026_outcomes():
    assert TRAIN_SEASONS[-1] == "2023-2024"
    assert VALIDATION_SEASON == "2024-2025"
    assert TEST_SEASON == "2025-2026"
    assert all("2026-2027" != season for season in (*TRAIN_SEASONS, VALIDATION_SEASON, TEST_SEASON))
    assert 0.0 in LAMBDA_GRID
    assert set(FEATURE_VARIANTS) == {"FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL"}
