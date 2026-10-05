import numpy as np
import pytest

import kickoff_calendar_league_heterogeneity_v1 as mod


def test_loss_delta_zero_when_predictions_match():
    y = np.array([0, 1, 1, 0])
    p = np.array([0.2, 0.8, 0.7, 0.3])
    delta = mod._loss_delta(y, p, p)
    assert np.allclose(delta, 0.0)


def test_pairwise_bootstrap_detects_clear_difference(monkeypatch):
    monkeypatch.setattr(mod, "BOOTSTRAP_DRAWS", 500)
    a = np.full(40, -0.02)
    b = np.full(40, 0.02)
    report = mod._pairwise_bootstrap(a, b, seed=123)
    assert report["observed_difference"] == pytest.approx(-0.04)
    assert report["excludes_zero"] is True
    assert report["ci_high"] < 0.0


def test_stable_pairwise_heterogeneity_requires_both_splits_same_direction():
    validation = {
        "pairwise_bonferroni_bootstrap": {
            "EPL__minus__LA_LIGA": {
                "observed_difference": -0.02,
                "excludes_zero": True,
            },
            "EPL__minus__SERIE_A": {
                "observed_difference": 0.01,
                "excludes_zero": False,
            },
        }
    }
    test = {
        "pairwise_bonferroni_bootstrap": {
            "EPL__minus__LA_LIGA": {
                "observed_difference": -0.01,
                "excludes_zero": True,
            },
            "EPL__minus__SERIE_A": {
                "observed_difference": -0.01,
                "excludes_zero": True,
            },
        }
    }
    assert mod._stable_pairwise_heterogeneity(validation, test) == [
        "EPL__minus__LA_LIGA"
    ]


def test_stable_pairwise_heterogeneity_rejects_sign_flip():
    validation = {
        "pairwise_bonferroni_bootstrap": {
            "EPL__minus__LA_LIGA": {
                "observed_difference": -0.02,
                "excludes_zero": True,
            }
        }
    }
    test = {
        "pairwise_bonferroni_bootstrap": {
            "EPL__minus__LA_LIGA": {
                "observed_difference": 0.02,
                "excludes_zero": True,
            }
        }
    }
    assert mod._stable_pairwise_heterogeneity(validation, test) == []
