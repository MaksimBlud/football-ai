import numpy as np
import pandas as pd

import league_residual_edge as residual


def sample_frame():
    return pd.DataFrame({
        "target": [0, 1, 2, 0],
        "season": ["X"] * 4,
        "match_date": ["2030-01-01"] * 4,
        "home_team": ["A"] * 4,
        "away_team": ["B"] * 4,

        "ai_home_probability":
            [0.55, 0.30, 0.20, 0.60],
        "ai_draw_probability":
            [0.25, 0.40, 0.30, 0.25],
        "ai_away_probability":
            [0.20, 0.30, 0.50, 0.15],

        "market_home_probability":
            [0.50, 0.32, 0.25, 0.70],
        "market_draw_probability":
            [0.30, 0.38, 0.30, 0.20],
        "market_away_probability":
            [0.20, 0.30, 0.45, 0.10],
    })


def test_fixed_alpha_is_small():
    assert (
        residual.FIXED_ALPHA
        > 0.0
    )

    assert (
        residual.FIXED_ALPHA
        <= 0.10
    )


def test_residual_segments_created():
    result = (
        residual.add_residual_segments(
            sample_frame()
        )
    )

    assert (
        "residual_magnitude"
        in result.columns
    )

    assert (
        "residual_bucket"
        in result.columns
    )

    assert (
        "regime"
        in result.columns
    )


def test_no_eligible_regime_preserves_market():
    frame = (
        residual.add_residual_segments(
            sample_frame()
        )
    )

    result, metadata = (
        residual.apply_gate(
            frame,
            set(),
        )
    )

    market = frame[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy()

    assert np.allclose(
        result,
        market,
    )

    assert not metadata[
        "ai_correction_enabled"
    ].any()


def test_enabled_regime_changes_probability():
    frame = (
        residual.add_residual_segments(
            sample_frame()
        )
    )

    enabled = {
        str(
            frame.iloc[0][
                "regime"
            ]
        )
    }

    result, metadata = (
        residual.apply_gate(
            frame,
            enabled,
        )
    )

    market = frame[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy()

    assert not np.allclose(
        result[0],
        market[0],
    )

    assert bool(
        metadata.iloc[0][
            "ai_correction_enabled"
        ]
    )


def test_minimum_regime_rows_prevents_tiny_segment():
    assert (
        residual.MIN_TRAIN_ROWS
        >= 50
    )


def test_2025_2026_is_not_true_future_gate():
    assert (
        residual.WALKFORWARD_TEST_SEASONS[
            -1
        ]
        == "2025-2026"
    )
