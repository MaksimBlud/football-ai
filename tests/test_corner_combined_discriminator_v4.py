import pandas as pd
import pytest

from corner_combined_discriminator_v4 import EXPECTED_SEASONS, summarize


def _frame(auc=0.54):
    return pd.DataFrame([
        {"season":s,"matches":300,"train_matches":900+i*300,"intercept":0.3,
         "b_corner":0.01,"b_shots":0.005,"b_sot":0.01,"auc_9_5":auc}
        for i,s in enumerate(EXPECTED_SEASONS)
    ])


def test_fixed_rule_can_pass():
    out=summarize(_frame())
    assert out["status"]=="PORTABLE_COMBINED_DISCRIMINATOR"
    assert out["seasons_above_0_5"]==7


def test_weak_average_auc_fails():
    out=summarize(_frame(0.515))
    assert out["status"]=="NOT_PORTABLE_COMBINED_DISCRIMINATOR"


def test_only_four_positive_seasons_fails():
    frame=_frame(0.54)
    frame.loc[4:,"auc_9_5"]=0.49
    out=summarize(frame)
    assert out["seasons_above_0_5"]==4
    assert out["status"]=="NOT_PORTABLE_COMBINED_DISCRIMINATOR"


def test_missing_season_rejected():
    with pytest.raises(ValueError,match="unexpected held-out seasons"):
        summarize(_frame().iloc[:-1].copy())


def test_current_season_cannot_replace_frozen_season():
    frame=_frame(); frame.loc[len(frame)-1,"season"]="2026/2027"
    with pytest.raises(ValueError,match="unexpected held-out seasons"):
        summarize(frame)
