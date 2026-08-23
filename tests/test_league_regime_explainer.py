import pandas as pd

import league_regime_explainer as explainer


def test_min_stable_folds_is_not_one():
    assert (
        explainer.MIN_STABLE_FOLDS
        >= 2
    )


def test_features_include_elo_and_form():
    assert (
        "elo_difference"
        in explainer.FEATURES
    )

    assert (
        "form_difference"
        in explainer.FEATURES
    )


def test_standardized_difference_positive():
    regime = pd.Series([
        2.0,
        2.2,
        2.4,
        2.6,
    ])

    baseline = pd.Series([
        1.0,
        1.2,
        1.4,
        1.6,
    ])

    result = (
        explainer.standardized_difference(
            regime,
            baseline,
        )
    )

    assert result > 0


def test_standardized_difference_zero_variance_safe():
    regime = pd.Series([
        1.0,
        1.0,
    ])

    baseline = pd.Series([
        1.0,
        1.0,
    ])

    result = (
        explainer.standardized_difference(
            regime,
            baseline,
        )
    )

    assert result == 0.0


def test_no_production_write_api_present():
    forbidden = {
        "joblib",
        "pickle",
        "supabase",
    }

    module_names = set(
        explainer.__dict__
    )

    assert not (
        forbidden
        & module_names
    )
