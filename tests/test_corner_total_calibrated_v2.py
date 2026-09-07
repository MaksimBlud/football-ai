import pandas as pd
import pytest

from corner_total_calibrated_v2 import EXPECTED_SEASONS, summarize


def _frame(delta=-0.01, slope=0.10):
    return pd.DataFrame([
        {
            "season": season,
            "matches": 300,
            "train_matches": 900 + i*300,
            "slope": slope,
            "intercept": 9.0,
            "calibrated_mae": 2.70,
            "baseline_mae": 2.70 - delta,
            "delta_mae": delta,
            "auc_9_5": 0.53,
            "hit_rate_9_5": 0.56,
        }
        for i, season in enumerate(EXPECTED_SEASONS)
    ])


def test_portable_requires_negative_weighted_delta_and_five_wins():
    out = summarize(_frame())
    assert out["status"] == "PORTABLE_CALIBRATED_TOTAL_SIGNAL"
    assert out["mae_season_wins"] == 7


def test_positive_average_error_is_not_portable():
    out = summarize(_frame(delta=0.02))
    assert out["status"] == "NOT_PORTABLE_CALIBRATED_TOTAL_SIGNAL"


def test_only_four_winning_seasons_is_not_portable():
    frame = _frame()
    frame.loc[4:, "delta_mae"] = 0.05
    out = summarize(frame)
    assert out["mae_season_wins"] == 4
    assert out["status"] == "NOT_PORTABLE_CALIBRATED_TOTAL_SIGNAL"


def test_missing_held_out_season_is_rejected():
    with pytest.raises(ValueError, match="unexpected held-out seasons"):
        summarize(_frame().iloc[:-1].copy())


def test_current_season_cannot_replace_frozen_held_out_season():
    frame = _frame()
    frame.loc[len(frame)-1, "season"] = "2026/2027"
    with pytest.raises(ValueError, match="unexpected held-out seasons"):
        summarize(frame)
