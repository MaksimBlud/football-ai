import pandas as pd
import pytest
from historical_football_market_incremental import paired_incremental, summarize_incremental


def _row(league,season,feature_set,brier,log_loss,accuracy=0.5,matches=100):
    return {"league":league,"test_season":season,"feature_set":feature_set,"matches":matches,"accuracy":accuracy,"brier":brier,"log_loss":log_loss}


def test_paired_incremental_matches_same_season():
    frame=pd.DataFrame([
        _row("EPL","s1","MARKET_MODEL",0.55,0.95,0.54),
        _row("EPL","s1","MARKET_CORNERS10",0.54,0.94,0.55),
        _row("EPL","s2","MARKET_MODEL",0.56,0.96,0.53),
        _row("EPL","s2","MARKET_CORNERS10",0.565,0.965,0.53),
    ])
    out=paired_incremental(frame)
    assert len(out)==2
    assert out.iloc[0].delta_brier==pytest.approx(-0.01)
    assert bool(out.iloc[0].brier_win)
    assert not bool(out.iloc[1].brier_win)


def test_incremental_summary_is_match_weighted():
    paired=pd.DataFrame([
        {"league":"EPL","test_season":"s1","candidate":"MARKET_CORNERS10","baseline":"MARKET_MODEL","matches":100,"delta_accuracy":0.02,"delta_brier":-0.02,"delta_log_loss":-0.03,"brier_win":True,"log_loss_win":True},
        {"league":"EPL","test_season":"s2","candidate":"MARKET_CORNERS10","baseline":"MARKET_MODEL","matches":300,"delta_accuracy":-0.01,"delta_brier":0.01,"delta_log_loss":0.02,"brier_win":False,"log_loss_win":False},
    ])
    out=summarize_incremental(paired).iloc[0]
    assert out.seasons==2
    assert out.mean_delta_brier==pytest.approx(0.0025)
    assert out.brier_wins==1
    assert out.brier_win_rate==0.5


def test_paired_incremental_rejects_incomplete_coverage():
    frame=pd.DataFrame([
        _row("EPL","s1","MARKET_MODEL",0.55,0.95),
        _row("EPL","s1","MARKET_CORNERS10",0.54,0.94),
        _row("EPL","s2","MARKET_CORNERS10",0.56,0.96),
    ])
    with pytest.raises(ValueError,match="incomplete paired market coverage"):
        paired_incremental(frame)
