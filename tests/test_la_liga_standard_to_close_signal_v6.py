import numpy as np
import pandas as pd

from la_liga_standard_to_close_signal_v6 import (
    CLOSING_COLUMNS,
    STANDARD_COLUMNS,
    _power_from_odds,
    _valid_odds,
    movement_metrics,
    movement_targets,
)


def test_standard_is_not_inferred_as_opening_and_closing_is_explicit():
    assert STANDARD_COLUMNS == ("B365H", "B365D", "B365A")
    assert CLOSING_COLUMNS == ("B365CH", "B365CD", "B365CA")


def test_power_probabilities_and_zero_target_for_identical_market():
    odds = np.array([[2.0, 3.5, 4.2], [4.0, 3.2, 1.9]])
    p = _power_from_odds(odds)
    assert p.shape == (2, 3)
    assert np.allclose(p.sum(axis=1), 1.0)
    target = movement_targets(p, p.copy())
    assert np.array_equal(target, np.zeros((2, 2)))


def test_target_direction_tracks_home_vs_draw_market_move():
    standard = _power_from_odds(np.array([[2.5, 3.2, 3.0]]))
    closing = _power_from_odds(np.array([[2.0, 3.5, 4.0]]))
    target = movement_targets(standard, closing)
    assert target[0, 0] > 0.0
    assert target[0, 1] < 0.0


def test_zero_movement_baseline_metrics_are_finite():
    actual = np.array([[0.1, -0.2], [-0.05, 0.03]])
    score = movement_metrics(actual, np.zeros_like(actual))
    assert score["mae"] > 0
    assert score["rmse"] > 0
    assert np.isfinite(list(score.values())).all()


def test_valid_odds_requires_all_three_prices():
    frame = pd.DataFrame({"B365H": [2.0, 2.0], "B365D": [3.0, np.nan], "B365A": [4.0, 4.0]})
    assert _valid_odds(frame, STANDARD_COLUMNS).tolist() == [True, False]
