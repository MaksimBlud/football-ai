import pandas as pd
import pytest

from corner_pressure_signal_v3 import EXPECTED_SEASONS, summarize


def _frame(primary_auc=0.54, secondary_auc=0.53):
    rows=[]
    for signal,auc in (("SHOTS",primary_auc),("SHOTS_ON_TARGET",secondary_auc)):
        for season in EXPECTED_SEASONS:
            rows.append({"signal":signal,"season":season,"matches":300,"n_pos":160,"n_neg":140,"auc_9_5":auc,"pearson_corr":0.05})
    return pd.DataFrame(rows)


def test_primary_signal_can_pass_only_fixed_rule():
    out=summarize(_frame())
    assert out["status"]=="PORTABLE_PRESSURE_DISCRIMINATOR"
    assert out["primary_seasons_above_0_5"]==7


def test_auc_below_threshold_fails_even_with_season_wins():
    out=summarize(_frame(primary_auc=0.515))
    assert out["status"]=="NOT_PORTABLE_PRESSURE_DISCRIMINATOR"


def test_secondary_signal_cannot_rescue_failed_primary():
    out=summarize(_frame(primary_auc=0.49,secondary_auc=0.70))
    assert out["status"]=="NOT_PORTABLE_PRESSURE_DISCRIMINATOR"
    assert out["secondary_weighted_auc_9_5"]>0.5


def test_missing_season_is_rejected():
    frame=_frame()
    frame=frame[~((frame.signal=="SHOTS")&(frame.season=="2025/2026"))]
    with pytest.raises(ValueError,match="unexpected held-out seasons"):
        summarize(frame)


def test_current_season_cannot_replace_frozen_season():
    frame=_frame()
    mask=(frame.signal=="SHOTS")&(frame.season=="2025/2026")
    frame.loc[mask,"season"]="2026/2027"
    with pytest.raises(ValueError,match="unexpected held-out seasons"):
        summarize(frame)
