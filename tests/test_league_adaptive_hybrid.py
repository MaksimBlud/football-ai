import numpy as np
import pandas as pd

import league_adaptive_hybrid as adaptive


def test_alpha_zero_is_allowed():
    assert 0.0 in adaptive.ALPHAS


def test_alpha_grid_is_bounded():
    assert min(
        adaptive.ALPHAS
    ) == 0.0

    assert max(
        adaptive.ALPHAS
    ) <= 0.30


def test_segments_use_confidence_and_agreement():
    frame = pd.DataFrame({
        "ai_home_probability": [0.50],
        "ai_draw_probability": [0.30],
        "ai_away_probability": [0.20],
        "market_home_probability": [0.60],
        "market_draw_probability": [0.25],
        "market_away_probability": [0.15],
    })

    result = (
        adaptive.add_segments(
            frame
        )
    )

    assert (
        "confidence_bucket"
        in result.columns
    )

    assert (
        "agreement_bucket"
        in result.columns
    )

    assert (
        "segment"
        in result.columns
    )


def test_apply_policy_can_preserve_market():
    frame = pd.DataFrame({
        "target": [0],
        "segment": ["X"],
        "ai_home_probability": [0.30],
        "ai_draw_probability": [0.30],
        "ai_away_probability": [0.40],
        "market_home_probability": [0.60],
        "market_draw_probability": [0.25],
        "market_away_probability": [0.15],
    })

    result = (
        adaptive.apply_policy(
            frame,
            {"X": 0.0},
        )
    )

    expected = np.array([
        [0.60, 0.25, 0.15],
    ])

    assert np.allclose(
        result,
        expected,
    )


def test_next_true_holdout_not_encoded_as_selection():
    assert (
        "2025-2026"
        not in
        adaptive.sweep.SELECTION_TEST_SEASONS
    )
