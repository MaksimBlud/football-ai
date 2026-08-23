import numpy as np
import pandas as pd

import league_structural_edge_v2 as v2


def test_alpha_small():
    assert (
        0
        < v2.STRUCTURAL_ALPHA
        <= 0.10
    )


def test_threshold_positive():
    assert (
        v2.EDGE_THRESHOLD
        > 0
    )


def test_stats_fit_derived_components_on_training_data():
    frame = pd.DataFrame({
        "elo_difference":
            [1.0, 2.0, 3.0],
        "form_difference":
            [1.0, 0.0, -1.0],
        "venue_win_rate_difference":
            [0.1, 0.2, 0.3],

        "home_goals_scored_last5":
            [2.0, 3.0, 4.0],
        "away_goals_scored_last5":
            [1.0, 1.0, 2.0],

        "home_goals_conceded_last5":
            [1.0, 1.5, 2.0],
        "away_goals_conceded_last5":
            [2.0, 2.0, 3.0],
    })

    stats = v2.fit_stats(
        frame
    )

    assert (
        "attack_difference"
        in stats
    )

    assert (
        "defence_difference"
        in stats
    )


def test_score_uses_external_stats():
    train = pd.DataFrame({
        "elo_difference":
            [0.0, 10.0],
        "form_difference":
            [0.0, 2.0],
        "venue_win_rate_difference":
            [0.0, 0.2],

        "home_goals_scored_last5":
            [1.0, 2.0],
        "away_goals_scored_last5":
            [1.0, 1.0],

        "home_goals_conceded_last5":
            [1.0, 1.0],
        "away_goals_conceded_last5":
            [1.0, 2.0],
    })

    test = train.iloc[
        [1]
    ].copy()

    stats = v2.fit_stats(
        train
    )

    score = v2.structural_score(
        test,
        stats,
    )

    assert len(score) == 1


def test_preservation_keeps_market_winner():
    market = np.array([
        0.40,
        0.35,
        0.25,
    ])

    candidate = np.array([
        0.30,
        0.35,
        0.35,
    ])

    result, weight = (
        v2.preserve_market_argmax(
            market,
            candidate,
        )
    )

    assert (
        np.argmax(result)
        == np.argmax(market)
    )

    assert (
        0.0
        <= weight
        <= 1.0
    )


def test_no_edge_preserves_market_exactly():
    market = np.array([
        [
            0.50,
            0.30,
            0.20,
        ]
    ])

    score = np.array([
        0.0,
    ])

    result, enabled, weights = (
        v2.apply_correction(
            market,
            score,
        )
    )

    assert not enabled[0]

    assert weights[0] == 0.0

    assert np.allclose(
        result,
        market,
    )


def test_enabled_edge_never_changes_argmax():
    market = np.array([
        [
            0.36,
            0.35,
            0.29,
        ],
        [
            0.35,
            0.36,
            0.29,
        ],
        [
            0.35,
            0.29,
            0.36,
        ],
    ])

    score = np.array([
        -2.0,
        2.0,
        2.0,
    ])

    result, _, _ = (
        v2.apply_correction(
            market,
            score,
        )
    )

    assert np.array_equal(
        np.argmax(
            result,
            axis=1,
        ),
        np.argmax(
            market,
            axis=1,
        ),
    )
