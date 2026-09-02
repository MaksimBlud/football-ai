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

def write_window_reports(frame:pd.DataFrame,output_dir:Path):
 output_dir.mkdir(parents=True,exist_ok=True); detail=run_window_ablation(frame); summary=summarize(detail)
 detail.to_csv(output_dir/"window_ablation.csv",index=False); summary.to_csv(output_dir/"window_ablation_summary.csv",index=False)
 return summary
