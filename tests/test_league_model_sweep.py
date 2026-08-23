import numpy as np

import league_model_sweep as sweep


def test_sweep_has_multiple_variants():
    assert (
        len(sweep.FEATURE_SETS)
        >= 3
    )

    assert (
        len(sweep.MODEL_VARIANTS)
        >= 4
    )

    assert (
        len(sweep.FEATURE_SETS)
        * len(sweep.MODEL_VARIANTS)
        >= 12
    )


def test_holdout_not_in_selection():
    assert (
        sweep.FINAL_HOLDOUT_SEASON
        not in
        sweep.SELECTION_TEST_SEASONS
    )


def test_feature_sets_have_no_odds():
    for features in (
        sweep.FEATURE_SETS.values()
    ):
        assert "home_odds" not in features
        assert "draw_odds" not in features
        assert "away_odds" not in features


def test_market_probabilities_normalize():
    import pandas as pd

    frame = pd.DataFrame({
        "home_odds": [2.0],
        "draw_odds": [4.0],
        "away_odds": [4.0],
    })

    result = (
        sweep.market_probabilities(
            frame
        )
    )

    assert np.isclose(
        result.sum(),
        1.0,
    )


def test_no_production_training_variant():
    names = set(
        sweep.MODEL_VARIANTS
    )

    assert (
        "production"
        not in names
    )
