"""Fixed Form-5 vs Form-10 football-signal ablation. Research only."""
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

WINDOW_SETS={
 "FORM5":["diff_points_5","diff_points_venue5"],
 "FORM10":["diff_points_10","diff_points_venue5"],
 "GOALS5":["diff_points_5","diff_points_venue5","diff_goals_for_5","diff_goals_against_5","diff_goals_for_venue5","diff_goals_against_venue5"],
 "GOALS10":["diff_points_10","diff_points_venue5","diff_goals_for_10","diff_goals_against_10","diff_goals_for_venue5","diff_goals_against_venue5"],
 "CORNERS5":["diff_points_5","diff_points_venue5","diff_goals_for_5","diff_goals_against_5","diff_corners_for_5","diff_corners_against_5","diff_corners_for_venue5","diff_corners_against_venue5"],
 "CORNERS10":["diff_points_10","diff_points_venue5","diff_goals_for_10","diff_goals_against_10","diff_corners_for_10","diff_corners_against_10","diff_corners_for_venue5","diff_corners_against_venue5"],
}
ROBUSTNESS_BASELINES=("GOALS10","FORM10")

def run_window_ablation(frame:pd.DataFrame,min_train_seasons:int=3)->pd.DataFrame:
 frame=add_difference_features(frame); rows=[]
 for league,g in frame.groupby("league"):
  seasons=sorted(g.season.unique())
  for i in range(min_train_seasons,len(seasons)):
   tr=g[g.season.isin(seasons[:i])]; te=g[g.season==seasons[i]]
   ytr=tr.result.map(RESULT_TO_INT).to_numpy(); y=te.result.map(RESULT_TO_INT).to_numpy(); one=np.eye(3)[y]
   for name,cols in WINDOW_SETS.items():
    model=Pipeline([("imputer",SimpleImputer(strategy="median")),("scale",StandardScaler()),("model",LogisticRegression(max_iter=1000))])
    model.fit(tr[cols],ytr); p=model.predict_proba(te[cols])
    rows.append({"league":league,"test_season":seasons[i],"feature_set":name,"matches":len(y),"accuracy":float((p.argmax(1)==y).mean()),"brier":float(np.mean(np.sum((p-one)**2,axis=1))),"log_loss":float(log_loss(y,p,labels=[0,1,2]))})
 return pd.DataFrame(rows)

def summarize(results:pd.DataFrame)->pd.DataFrame:
 rows=[]
 for (league,fs),g in results.groupby(["league","feature_set"]):
  rows.append({"league":league,"feature_set":fs,"matches":int(g.matches.sum()),"seasons":len(g),**{m:float(np.average(g[m],weights=g.matches)) for m in ("accuracy","brier","log_loss")}})
 return pd.DataFrame(rows).sort_values(["league","brier"])

def paired_robustness(results:pd.DataFrame,candidate:str="CORNERS10",baselines=ROBUSTNESS_BASELINES)->pd.DataFrame:
 required={"league","test_season","feature_set","matches","accuracy","brier","log_loss"}
 missing=required-set(results.columns)
 if missing: raise ValueError(f"missing window-ablation columns: {sorted(missing)}")
 rows=[]
 for baseline in baselines:
  cand=results[results.feature_set==candidate].copy()
  base=results[results.feature_set==baseline].copy()
  merged=cand.merge(base,on=["league","test_season"],suffixes=("_candidate","_baseline"),validate="one_to_one")
  if len(merged)!=len(cand): raise ValueError(f"incomplete paired coverage for {candidate} vs {baseline}")
  for _,r in merged.iterrows():
   rows.append({
    "league":r.league,"test_season":r.test_season,"candidate":candidate,"baseline":baseline,
    "matches":int(r.matches_candidate),
    "delta_accuracy":float(r.accuracy_candidate-r.accuracy_baseline),
    "delta_brier":float(r.brier_candidate-r.brier_baseline),
    "delta_log_loss":float(r.log_loss_candidate-r.log_loss_baseline),
    "candidate_brier_win":bool(r.brier_candidate<r.brier_baseline),
    "candidate_log_loss_win":bool(r.log_loss_candidate<r.log_loss_baseline),
   })
 return pd.DataFrame(rows).sort_values(["baseline","league","test_season"])

def summarize_paired_robustness(paired:pd.DataFrame)->pd.DataFrame:
 rows=[]
 for (league,baseline),g in paired.groupby(["league","baseline"]):
  w=g.matches.to_numpy()
  rows.append({
   "league":league,"candidate":g.candidate.iloc[0],"baseline":baseline,
   "matches":int(g.matches.sum()),"seasons":len(g),
   "mean_delta_accuracy":float(np.average(g.delta_accuracy,weights=w)),
   "mean_delta_brier":float(np.average(g.delta_brier,weights=w)),
   "mean_delta_log_loss":float(np.average(g.delta_log_loss,weights=w)),
   "brier_wins":int(g.candidate_brier_win.sum()),
   "log_loss_wins":int(g.candidate_log_loss_win.sum()),
   "brier_win_rate":float(g.candidate_brier_win.mean()),
   "log_loss_win_rate":float(g.candidate_log_loss_win.mean()),
  })
 return pd.DataFrame(rows).sort_values(["baseline","league"])

def write_window_reports(frame:pd.DataFrame,output_dir:Path):
 output_dir.mkdir(parents=True,exist_ok=True); detail=run_window_ablation(frame); summary=summarize(detail)
 paired=paired_robustness(detail); paired_summary=summarize_paired_robustness(paired)
 detail.to_csv(output_dir/"window_ablation.csv",index=False); summary.to_csv(output_dir/"window_ablation_summary.csv",index=False)
 paired.to_csv(output_dir/"window_paired_robustness.csv",index=False); paired_summary.to_csv(output_dir/"window_paired_robustness_summary.csv",index=False)
 return summary,paired_summary
