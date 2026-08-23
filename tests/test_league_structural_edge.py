import numpy as np
import pandas as pd

import league_structural_edge as structural


def test_structural_features_exclude_market_odds():
    forbidden = {
        "home_odds",
        "draw_odds",
        "away_odds",
    }

    assert not (
        forbidden
        & set(
            structural.STRUCTURAL_FEATURES
        )
    )


def test_structural_features_include_core_signals():
    assert (
        "elo_difference"
        in structural.STRUCTURAL_FEATURES
    )

    assert (
        "form_difference"
        in structural.STRUCTURAL_FEATURES
    )

    assert (
        "venue_win_rate_difference"
        in structural.STRUCTURAL_FEATURES
    )


def test_edge_threshold_positive():
    assert (
        structural.EDGE_THRESHOLD
        > 0
    )


def test_structural_alpha_small():
    assert (
        0
        < structural.STRUCTURAL_ALPHA
        <= 0.10
    )


def test_no_correction_preserves_market():
    market = np.array([
        [0.50, 0.30, 0.20],
    ])

    score = np.array([
        0.0,
    ])

    result, enabled = (
        structural.apply_structural_correction(
            market,
            score,
        )
    )

    assert not enabled[0]

    assert np.allclose(
        result,
        market,
    )


def test_positive_structural_edge_increases_home_probability():
    market = np.array([
        [0.50, 0.30, 0.20],
    ])

    score = np.array([
        1.0,
    ])

    result, enabled = (
        structural.apply_structural_correction(
            market,
            score,
        )
    )

    assert enabled[0]

    assert (
        result[0, 0]
        > market[0, 0]
    )


def test_negative_structural_edge_reduces_home_probability():
    market = np.array([
        [0.50, 0.30, 0.20],
    ])

    score = np.array([
        -1.0,
    ])

    result, enabled = (
        structural.apply_structural_correction(
            market,
            score,
        )
    )

    assert enabled[0]

    assert (
        result[0, 0]
        < market[0, 0]
    )
