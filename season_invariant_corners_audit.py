"""Preregistered season-invariant CORNERS10 audit. Research only."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

PRIMARY_LEAGUES=("EPL","LA_LIGA","SERIE_A")
PRIMARY_CANDIDATE="CORNERS10"
PRIMARY_BASELINE="GOALS10"
MIN_TEST_SEASONS=5
STRONG_WIN_RATE=0.70
SUPPORTIVE_WIN_RATE=0.55
FROZEN_LAST_HISTORICAL_SEASON="2025-2026"
WINDOW_PAIRS=(("CORNERS5","GOALS5"),("CORNERS10","GOALS10"),("CORNERS15","GOALS15"))


def _reject_future(seasons:pd.Series)->None:
    if (seasons.astype(str)>FROZEN_LAST_HISTORICAL_SEASON).any():
        raise ValueError("SEASON_INVARIANT_CORNERS_V1 must not read 2026-2027 or later outcomes")


def _validate(results:pd.DataFrame)->None:
    required={"league","test_season","feature_set","matches","accuracy","brier","log_loss"}
    missing=required-set(results.columns)
    if missing:
        raise ValueError(f"missing invariant-audit columns: {sorted(missing)}")
    _reject_future(results["test_season"])


def _validate_reference(reference:pd.DataFrame)->None:
    required={"league","test_season","window","matches","delta_accuracy","delta_brier","delta_log_loss"}
    missing=required-set(reference.columns)
    if missing:
        raise ValueError(f"missing invariant-reference columns: {sorted(missing)}")
    _reject_future(reference["test_season"])
    if not set(reference["window"].astype(int)).issubset({5,10,15}):
        raise ValueError("only preregistered 5/10/15 windows are allowed")


def _paired(results:pd.DataFrame,candidate:str,baseline:str)->pd.DataFrame:
    cand=results[results.feature_set==candidate].copy()
    base=results[results.feature_set==baseline].copy()
    merged=cand.merge(base,on=["league","test_season"],suffixes=("_candidate","_baseline"),validate="one_to_one")
    if len(merged)!=len(cand) or len(merged)!=len(base):
        raise ValueError(f"incomplete paired coverage for {candidate} vs {baseline}")
    merged["delta_brier"]=merged.brier_candidate-merged.brier_baseline
    merged["delta_log_loss"]=merged.log_loss_candidate-merged.log_loss_baseline
    merged["delta_accuracy"]=merged.accuracy_candidate-merged.accuracy_baseline
    merged["brier_win"]=merged.delta_brier<0
    merged["log_loss_win"]=merged.delta_log_loss<0
    return merged


def classify_league(mean_brier:float,mean_log_loss:float,brier_win_rate:float,log_loss_win_rate:float,seasons:int)->str:
    if seasons<MIN_TEST_SEASONS:
        return "UNSTABLE"
    if mean_brier<0 and mean_log_loss<0 and brier_win_rate>=STRONG_WIN_RATE and log_loss_win_rate>=STRONG_WIN_RATE:
        return "STRONG"
    if mean_brier<0 and mean_log_loss<0 and brier_win_rate>=SUPPORTIVE_WIN_RATE and log_loss_win_rate>=SUPPORTIVE_WIN_RATE:
        return "SUPPORTIVE"
    return "UNSTABLE"


def _league_rows_from_deltas(deltas:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for league in PRIMARY_LEAGUES:
        g=deltas[deltas.league==league]
        if g.empty:
            rows.append({"league":league,"candidate":PRIMARY_CANDIDATE,"baseline":PRIMARY_BASELINE,"matches":0,"seasons":0,"mean_delta_accuracy":np.nan,"mean_delta_brier":np.nan,"mean_delta_log_loss":np.nan,"brier_win_rate":0.0,"log_loss_win_rate":0.0,"classification":"UNSTABLE"})
            continue
        w=g.matches.to_numpy()
        mean_brier=float(np.average(g.delta_brier,weights=w))
        mean_log=float(np.average(g.delta_log_loss,weights=w))
        brier_rate=float((g.delta_brier<0).mean())
        log_rate=float((g.delta_log_loss<0).mean())
        rows.append({
            "league":league,"candidate":PRIMARY_CANDIDATE,"baseline":PRIMARY_BASELINE,
            "matches":int(g.matches.sum()),"seasons":len(g),
            "mean_delta_accuracy":float(np.average(g.delta_accuracy,weights=w)),
            "mean_delta_brier":mean_brier,"mean_delta_log_loss":mean_log,
            "brier_win_rate":brier_rate,"log_loss_win_rate":log_rate,
            "classification":classify_league(mean_brier,mean_log,brier_rate,log_rate,len(g)),
        })
    return pd.DataFrame(rows)


def league_invariant_report(results:pd.DataFrame)->pd.DataFrame:
    _validate(results)
    paired=_paired(results,PRIMARY_CANDIDATE,PRIMARY_BASELINE)
    deltas=pd.DataFrame({
        "league":paired.league,
        "test_season":paired.test_season,
        "matches":paired.matches_candidate.astype(int),
        "delta_accuracy":paired.delta_accuracy,
        "delta_brier":paired.delta_brier,
        "delta_log_loss":paired.delta_log_loss,
    })
    return _league_rows_from_deltas(deltas)


def league_invariant_from_reference(reference:pd.DataFrame)->pd.DataFrame:
    _validate_reference(reference)
    primary=reference[reference.window.astype(int)==10].copy()
    return _league_rows_from_deltas(primary)


def overall_portability(league_report:pd.DataFrame)->str:
    by_league={row.league:row.classification for row in league_report.itertuples()}
    if any(league not in by_league for league in PRIMARY_LEAGUES):
        return "NOT_PORTABLE"
    states=[by_league[league] for league in PRIMARY_LEAGUES]
    if all(state=="STRONG" for state in states):
        return "PORTABLE_STRONG"
    if all(state in {"STRONG","SUPPORTIVE"} for state in states):
        return "PORTABLE_SUPPORTIVE"
    return "NOT_PORTABLE"


def window_robustness_report(results:pd.DataFrame)->pd.DataFrame:
    _validate(results)
    rows=[]
    for candidate,baseline in WINDOW_PAIRS:
        paired=_paired(results,candidate,baseline)
        for league in PRIMARY_LEAGUES:
            g=paired[paired.league==league]
            if g.empty:
                continue
            w=g.matches_candidate.to_numpy()
            rows.append({
                "league":league,"candidate":candidate,"baseline":baseline,
                "seasons":len(g),"matches":int(g.matches_candidate.sum()),
                "mean_delta_brier":float(np.average(g.delta_brier,weights=w)),
                "mean_delta_log_loss":float(np.average(g.delta_log_loss,weights=w)),
                "brier_win_rate":float(g.brier_win.mean()),
                "log_loss_win_rate":float(g.log_loss_win.mean()),
            })
    return pd.DataFrame(rows).sort_values(["league","candidate"])


def window_robustness_from_reference(reference:pd.DataFrame)->pd.DataFrame:
    _validate_reference(reference)
    rows=[]
    for (league,window),g in reference.groupby(["league","window"]):
        w=g.matches.to_numpy()
        rows.append({
            "league":league,"window":int(window),"seasons":len(g),"matches":int(g.matches.sum()),
            "mean_delta_brier":float(np.average(g.delta_brier,weights=w)),
            "mean_delta_log_loss":float(np.average(g.delta_log_loss,weights=w)),
            "brier_win_rate":float((g.delta_brier<0).mean()),
            "log_loss_win_rate":float((g.delta_log_loss<0).mean()),
        })
    return pd.DataFrame(rows).sort_values(["league","window"])


def _write(league:pd.DataFrame,windows:pd.DataFrame,output_dir:Path):
    output_dir.mkdir(parents=True,exist_ok=True)
    status=overall_portability(league)
    overall=pd.DataFrame([{"research_block":"SEASON_INVARIANT_CORNERS_V1","status":status}])
    league.to_csv(output_dir/"season_invariant_corners_leagues.csv",index=False)
    windows.to_csv(output_dir/"season_invariant_corners_windows.csv",index=False)
    overall.to_csv(output_dir/"season_invariant_corners_overall.csv",index=False)
    return league,windows,overall


def write_invariant_reports(window_results:pd.DataFrame,output_dir:Path):
    return _write(league_invariant_report(window_results),window_robustness_report(window_results),output_dir)


def write_reference_reports(reference:pd.DataFrame,output_dir:Path):
    return _write(league_invariant_from_reference(reference),window_robustness_from_reference(reference),output_dir)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,default=Path("artifacts/season_invariant_corners_v1"))
    a=p.parse_args()
    reference=pd.read_csv(a.reference)
    league,windows,overall=write_reference_reports(reference,a.output_dir)
    print("SEASON_INVARIANT_CORNERS_V1")
    print(league.to_string(index=False))
    print(windows.to_string(index=False))
    print(overall.to_string(index=False))

if __name__=="__main__": main()
