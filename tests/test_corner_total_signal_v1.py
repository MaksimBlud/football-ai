import pandas as pd
import pytest

from corner_total_signal_v1 import EXPECTED_SEASONS, summarize


def _frame(delta=-0.05, auc=0.56):
    return pd.DataFrame([
        {
            "season": season,
            "matches": 300,
            "signal_mae": 2.7,
            "baseline_mae": 2.7 - delta,
            "delta_mae": delta,
            "auc_9_5": auc,
            "hit_rate_9_5": 0.56,
        }
        for season in EXPECTED_SEASONS
    ])


def test_portable_requires_negative_mae_and_five_season_wins():
    out = summarize(_frame())
    assert out["status"] == "PORTABLE_TOTAL_SIGNAL"
    assert out["mae_season_wins"] == 7


def test_positive_average_error_is_not_portable():
    frame = _frame(delta=0.03)
    out = summarize(frame)
    assert out["status"] == "NOT_PORTABLE_TOTAL_SIGNAL"


def test_only_four_winning_seasons_is_not_portable():
    frame = _frame()
    frame.loc[4:, "delta_mae"] = 0.08
    out = summarize(frame)
    assert out["mae_season_wins"] == 4
    assert out["status"] == "NOT_PORTABLE_TOTAL_SIGNAL"


def test_missing_held_out_season_is_rejected():
    with pytest.raises(ValueError, match="unexpected held-out seasons"):
        summarize(_frame().iloc[:-1].copy())


def test_current_season_outcomes_are_rejected():
    frame = _frame()
    frame.loc[len(frame)] = frame.iloc[-1].to_dict()
    frame.loc[len(frame)-1, "season"] = "2026/2027"
    with pytest.raises(ValueError, match="unexpected held-out seasons|forbidden"):
        summarize(frame)
