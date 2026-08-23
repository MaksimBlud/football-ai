import numpy as np

import league_model_diagnostics as diag


def test_alpha_grid_has_no_pure_market_candidate():
    assert 0.0 not in diag.ALPHAS

    assert min(
        diag.ALPHAS
    ) > 0.0


def test_alpha_grid_has_no_pure_ai_candidate():
    assert max(
        diag.ALPHAS
    ) < 1.0


def test_hybrid_probability_normalized():
    market = np.array([
        [0.50, 0.30, 0.20],
    ])

    ai = np.array([
        [0.40, 0.35, 0.25],
    ])

    result = (
        diag.hybrid_probability(
            market,
            ai,
            0.25,
        )
    )

    assert np.isclose(
        result.sum(),
        1.0,
    )


def test_alpha_zero_equivalent_math():
    market = np.array([
        [0.50, 0.30, 0.20],
    ])

    ai = np.array([
        [0.40, 0.35, 0.25],
    ])

    result = (
        diag.hybrid_probability(
            market,
            ai,
            0.0,
        )
    )

    assert np.allclose(
        result,
        market,
    )


def test_production_artifacts_are_read_only_names():
    assert (
        "football_model_xgboost_elo.pkl"
        in diag.PRODUCTION_ARTIFACTS
    )
