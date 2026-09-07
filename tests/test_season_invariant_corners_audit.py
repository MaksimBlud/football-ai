import pandas as pd
import pytest

from season_invariant_corners_audit import (
    league_invariant_report,
    overall_portability,
    window_robustness_report,
)


def _row(league,season,feature_set,brier,log_loss,accuracy=0.5,matches=100):
    return {"league":league,"test_season":season,"feature_set":feature_set,"matches":matches,"accuracy":accuracy,"brier":brier,"log_loss":log_loss}


def _strong_frame():
    rows=[]
    seasons=["2021-2022","2022-2023","2023-2024","2024-2025","2025-2026"]
    for league in ("EPL","LA_LIGA","SERIE_A"):
        for i,season in enumerate(seasons):
            base_brier=0.60+i*0.001
            base_log=1.00+i*0.001
            for window in (5,10,15):
                rows.append(_row(league,season,f"GOALS{window}",base_brier,base_log,0.50))
                rows.append(_row(league,season,f"CORNERS{window}",base_brier-0.01,base_log-0.02,0.52))
    return pd.DataFrame(rows)


def test_strong_classification_requires_repeated_unseen_season_wins():
    report=league_invariant_report(_strong_frame())
    assert set(report.classification)=={"STRONG"}
    assert overall_portability(report)=="PORTABLE_STRONG"
    assert (report.brier_win_rate==1.0).all()
    assert (report.log_loss_win_rate==1.0).all()


def test_one_unstable_league_blocks_portability():
    frame=_strong_frame()
    mask=(frame.league=="SERIE_A") & (frame.feature_set=="CORNERS10")
    frame.loc[mask,"brier"] += 0.03
    frame.loc[mask,"log_loss"] += 0.05
    report=league_invariant_report(frame)
    assert report.loc[report.league=="SERIE_A","classification"].iloc[0]=="UNSTABLE"
    assert overall_portability(report)=="NOT_PORTABLE"


def test_window_report_is_fixed_to_5_10_15_only():
    out=window_robustness_report(_strong_frame())
    assert set(out.candidate)=={"CORNERS5","CORNERS10","CORNERS15"}
    assert len(out)==9


def test_current_season_outcomes_are_rejected():
    frame=_strong_frame()
    extra=_row("EPL","2026-2027","CORNERS10",0.59,0.99)
    frame=pd.concat([frame,pd.DataFrame([extra])],ignore_index=True)
    with pytest.raises(ValueError,match="must not read 2026-2027"):
        league_invariant_report(frame)


def test_incomplete_candidate_baseline_pairing_is_rejected():
    frame=_strong_frame()
    frame=frame[~((frame.league=="EPL") & (frame.test_season=="2025-2026") & (frame.feature_set=="GOALS10"))]
    with pytest.raises(ValueError,match="incomplete paired coverage"):
        league_invariant_report(frame)
