import numpy as np
import pandas as pd

from la_liga_power_anchor_v3 import LAMBDA_GRID, _power_market
from market_anchor_1x2_v1 import market_anchored_probabilities


def test_lambda_zero_is_exact_power_market_identity():
    frame = pd.DataFrame({
        "market_home_odds": [2.0, 4.0],
        "market_draw_odds": [3.5, 3.2],
        "market_away_odds": [4.2, 1.9],
    })
    market = _power_market(frame)
    residual = np.array([[0.5, 0.0, -0.2], [-0.3, 0.0, 0.4]])
    actual = market_anchored_probabilities(market, residual, 0.0)
    assert np.array_equal(actual, market)
    assert np.allclose(market.sum(axis=1), 1.0)


def test_v3_lambda_grid_preserves_market_fallback():
    assert LAMBDA_GRID[0] == 0.0
    assert all(0.0 <= value <= 1.0 for value in LAMBDA_GRID)


def test_power_market_requires_raw_decimal_odds():
    frame = pd.DataFrame({
        "market_home_odds": [2.0],
        "market_draw_odds": [3.5],
        "market_away_odds": [4.2],
    })
    p = _power_market(frame)
    assert p.shape == (1, 3)
    assert np.isfinite(p).all()
    assert (p > 0).all() and (p < 1).all()
