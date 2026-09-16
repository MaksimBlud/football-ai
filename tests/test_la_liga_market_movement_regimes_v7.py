import numpy as np
import pandas as pd

from la_liga_market_movement_regimes_v7 import baseline_metrics, classification_metrics, movement_magnitude


def test_movement_magnitude_uses_both_independent_log_ratios():
    frame = pd.DataFrame({"target_home_vs_draw": [3.0, 0.0], "target_away_vs_draw": [4.0, -2.0]})
    assert np.allclose(movement_magnitude(frame), [5.0, 2.0])


def test_constant_prevalence_baseline_is_well_formed():
    y = np.array([0, 0, 1, 1])
    m = baseline_metrics(y, 0.25)
    assert 0 < m["brier"] < 1
    assert m["log_loss"] > 0
    assert m["roc_auc"] == 0.5


def test_better_probabilities_beat_constant_baseline_on_proper_scores():
    y = np.array([0, 0, 1, 1])
    base = baseline_metrics(y, 0.5)
    candidate = classification_metrics(y, np.array([0.1, 0.2, 0.8, 0.9]))
    assert candidate["brier"] < base["brier"]
    assert candidate["log_loss"] < base["log_loss"]
