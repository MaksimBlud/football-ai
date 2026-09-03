"""Evaluate whether CORNERS10 adds predictive information beyond market probabilities.

Research only. The market columns in Football-Data are historical bookmaker prices and
are not assumed to be available at the same operational timestamp as live predictions.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from historical_football_signal_lab import add_difference_features, RESULT_TO_INT

MARKET=["market_home","market_draw","market_away"]
CORNERS10=["diff_points_10","diff_points_venue5","diff_goals_for_10","diff_goals_against_10","diff_corners_for_10","diff_corners_against_10","diff_corners_for_venue5","diff_corners_against_venue5"]


def _score(y,p):
    one=np.eye(3)[y]
    return {
        "accuracy":float((p.argmax(1)==y).mean()),
        "brier":float(np.mean(np.sum((p-one)**2,axis=1))),
        "log_loss":float(log_loss(y,p,labels=[0,1,2])),
    }


def run_market_incremental(frame:pd.DataFrame,min_train_seasons:int=3)->pd.DataFrame:
    frame=add_difference_features(frame); rows=[]
    for league,g in frame.groupby("league"):
        seasons=sorted(g.season.unique())
        for i in range(min_train_seasons,len(seasons)):
            tr=g[g.season.isin(seasons[:i])].dropna(subset=MARKET+["result"])
            te=g[g.season==seasons[i]].dropna(subset=MARKET+["result"])
            ytr=tr.result.map(RESULT_TO_INT).to_numpy(); y=te.result.map(RESULT_TO_INT).to_numpy()
            raw=te[MARKET].to_numpy(float); raw=raw/raw.sum(axis=1,keepdims=True)
            rows.append({"league":league,"test_season":seasons[i],"feature_set":"MARKET_RAW","matches":len(y),**_score(y,raw)})
            for name,cols in (("MARKET_MODEL",MARKET),("MARKET_CORNERS10",MARKET+CORNERS10)):
                model=Pipeline([("imputer",SimpleImputer(strategy="median")),("scale",StandardScaler()),("model",LogisticRegression(max_iter=1000))])
                model.fit(tr[cols],ytr); p=model.predict_proba(te[cols])
                rows.append({"league":league,"test_season":seasons[i],"feature_set":name,"matches":len(y),**_score(y,p)})
    return pd.DataFrame(rows)


def summarize(results:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for (league,fs),g in results.groupby(["league","feature_set"]):
        rows.append({"league":league,"feature_set":fs,"matches":int(g.matches.sum()),"seasons":len(g),**{m:float(np.average(g[m],weights=g.matches)) for m in ("accuracy","brier","log_loss")}})
    return pd.DataFrame(rows).sort_values(["league","brier"])


def paired_incremental(results:pd.DataFrame,baseline:str="MARKET_MODEL",candidate:str="MARKET_CORNERS10")->pd.DataFrame:
    a=results[results.feature_set==baseline]
    b=results[results.feature_set==candidate]
    m=b.merge(a,on=["league","test_season"],suffixes=("_candidate","_baseline"),validate="one_to_one")
    if len(m)!=len(b): raise ValueError("incomplete paired market coverage")
    out=pd.DataFrame({
        "league":m.league,"test_season":m.test_season,"candidate":candidate,"baseline":baseline,"matches":m.matches_candidate.astype(int),
        "delta_accuracy":m.accuracy_candidate-m.accuracy_baseline,
        "delta_brier":m.brier_candidate-m.brier_baseline,
        "delta_log_loss":m.log_loss_candidate-m.log_loss_baseline,
    })
    out["brier_win"]=out.delta_brier<0; out["log_loss_win"]=out.delta_log_loss<0
    return out.sort_values(["league","test_season"])


def summarize_incremental(paired:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for league,g in paired.groupby("league"):
        w=g.matches.to_numpy()
        rows.append({"league":league,"matches":int(g.matches.sum()),"seasons":len(g),
            "mean_delta_accuracy":float(np.average(g.delta_accuracy,weights=w)),
            "mean_delta_brier":float(np.average(g.delta_brier,weights=w)),
            "mean_delta_log_loss":float(np.average(g.delta_log_loss,weights=w)),
            "brier_wins":int(g.brier_win.sum()),"log_loss_wins":int(g.log_loss_win.sum()),
            "brier_win_rate":float(g.brier_win.mean()),"log_loss_win_rate":float(g.log_loss_win.mean())})
    return pd.DataFrame(rows).sort_values("league")


def write_market_incremental_reports(frame:pd.DataFrame,output_dir:Path):
    output_dir.mkdir(parents=True,exist_ok=True)
    detail=run_market_incremental(frame); summary=summarize(detail); paired=paired_incremental(detail); paired_summary=summarize_incremental(paired)
    detail.to_csv(output_dir/"market_incremental.csv",index=False)
    summary.to_csv(output_dir/"market_incremental_summary.csv",index=False)
    paired.to_csv(output_dir/"market_incremental_paired.csv",index=False)
    paired_summary.to_csv(output_dir/"market_incremental_paired_summary.csv",index=False)
    return summary,paired_summary
