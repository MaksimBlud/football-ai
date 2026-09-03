import pandas as pd
import pytest
from historical_football_window_audit import paired_robustness, summarize_paired_robustness


def _row(league,season,feature_set,brier,log_loss,accuracy=0.5,matches=100):
    return {"league":league,"test_season":season,"feature_set":feature_set,"matches":matches,"accuracy":accuracy,"brier":brier,"log_loss":log_loss}


def test_paired_robustness_uses_same_league_and_season():
    rows=[]
    for season in ("2023-2024","2024-2025"):
        rows += [
            _row("EPL",season,"CORNERS10",0.59,0.99,0.53),
            _row("EPL",season,"GOALS10",0.61,1.02,0.51),
            _row("EPL",season,"FORM10",0.62,1.03,0.50),
        ]
    out=paired_robustness(pd.DataFrame(rows))
    assert len(out)==4
    assert set(out.baseline)=={"GOALS10","FORM10"}
    assert (out.delta_brier<0).all()
    assert out.candidate_brier_win.all()


def test_paired_summary_counts_season_wins_and_weighted_delta():
    paired=pd.DataFrame([
        {"league":"EPL","test_season":"s1","candidate":"CORNERS10","baseline":"GOALS10","matches":100,"delta_accuracy":0.02,"delta_brier":-0.02,"delta_log_loss":-0.03,"candidate_brier_win":True,"candidate_log_loss_win":True},
        {"league":"EPL","test_season":"s2","candidate":"CORNERS10","baseline":"GOALS10","matches":300,"delta_accuracy":-0.01,"delta_brier":0.01,"delta_log_loss":0.02,"candidate_brier_win":False,"candidate_log_loss_win":False},
    ])
    out=summarize_paired_robustness(paired).iloc[0]
    assert out.seasons==2
    assert out.brier_wins==1
    assert out.brier_win_rate==0.5
    assert out.mean_delta_brier==pytest.approx(0.0025)


def test_paired_robustness_rejects_incomplete_baseline_coverage():
    frame=pd.DataFrame([
        _row("EPL","s1","CORNERS10",0.59,0.99),
        _row("EPL","s2","CORNERS10",0.60,1.00),
        _row("EPL","s1","GOALS10",0.61,1.02),
        _row("EPL","s1","FORM10",0.62,1.03),
        _row("EPL","s2","FORM10",0.61,1.01),
    ])
    with pytest.raises(ValueError,match="incomplete paired coverage"):
        paired_robustness(frame)
