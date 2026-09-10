from __future__ import annotations

import numpy as np
import pandas as pd

import league_model_diagnostics as diagnostics


def test_hybrid_alpha_grid_is_ai_increment_only() -> None:
    assert 0.0 not in diagnostics.ALPHAS
    assert diagnostics.ALPHAS == (
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
    )


def test_hybrid_probability_is_normalized_convex_mix() -> None:
    market = np.array(
        [
            [0.55, 0.25, 0.20],
            [0.20, 0.30, 0.50],
        ]
    )
    ai = np.array(
        [
            [0.45, 0.35, 0.20],
            [0.25, 0.35, 0.40],
        ]
    )

    result = diagnostics.hybrid_probability(
        market,
        ai,
        alpha=0.20,
    )

    expected = 0.80 * market + 0.20 * ai

    assert np.allclose(result, expected)
    assert np.allclose(result.sum(axis=1), 1.0)


def test_alpha_search_uses_only_frozen_grid() -> None:
    selection = pd.DataFrame(
        {
            "target": [0, 1, 2, 0],
            "ai_home_probability": [0.60, 0.25, 0.15, 0.55],
            "ai_draw_probability": [0.25, 0.50, 0.25, 0.25],
            "ai_away_probability": [0.15, 0.25, 0.60, 0.20],
            "market_home_probability": [0.50, 0.30, 0.20, 0.45],
            "market_draw_probability": [0.30, 0.40, 0.30, 0.30],
            "market_away_probability": [0.20, 0.30, 0.50, 0.25],
        }
    )

    result = diagnostics.alpha_search(selection)

    assert set(result["alpha"].tolist()) == set(diagnostics.ALPHAS)
    assert len(result) == len(diagnostics.ALPHAS)
    assert result.iloc[0]["rank"] == 1
