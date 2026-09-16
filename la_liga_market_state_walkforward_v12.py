"""V12: expanding walk-forward robustness of V11 interpretable market-state components.
Research-only; every fold trains on earlier seasons and evaluates the next season once.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from la_liga_market_movement_regimes_v7 import MOVEMENT_QUANTILE,movement_magnitude,classification_metrics,baseline_metrics
from la_liga_market_state_decomposition_v11 import add_market_geometry,FEATURE_VARIANTS
from la_liga_standard_to_close_signal_v6 import load_history,prepare_frame
EXPERIMENT_ID='LA_LIGA_MARKET_STATE_WALKFORWARD_V12'; C=.1
FOCUS=('FULL_PROBS','DRAW_LEVEL','ENTROPY','FAVORITE_STRENGTH','TOP_TWO_GAP')
def fit(x,y,v):
 m=Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]);m.fit(x[FEATURE_VARIANTS[v]],y);return m
def evaluate_frame(frame):
 frame,coverage=prepare_frame(frame);frame=add_market_geometry(frame);seasons=sorted(frame.season.unique());folds=[]
 for i in range(2,len(seasons)):
  tr=frame[frame.season.isin(seasons[:i])].copy();te=frame[frame.season==seasons[i]].copy();threshold=float(np.quantile(movement_magnitude(tr),MOVEMENT_QUANTILE));yt=(movement_magnitude(tr)>=threshold).astype(int);y=(movement_magnitude(te)>=threshold).astype(int);base=baseline_metrics(y,float(yt.mean()));variants={}
  for v in FOCUS:
   p=fit(tr,yt,v).predict_proba(te[FEATURE_VARIANTS[v]])[:,1];m=classification_metrics(y,p);m['delta_brier_vs_constant']=m['brier']-base['brier'];m['delta_log_loss_vs_constant']=m['log_loss']-base['log_loss'];m['beats_constant_both']=bool(m['delta_brier_vs_constant']<0 and m['delta_log_loss_vs_constant']<0);variants[v]=m
  folds.append({'test_season':seasons[i],'train_seasons':seasons[:i],'train_n':len(tr),'test_n':len(te),'threshold':threshold,'baseline':base,'variants':variants})
 counts={v:sum(f['variants'][v]['beats_constant_both'] for f in folds) for v in FOCUS}; mean_delta={v:{'mean_delta_brier':float(np.mean([f['variants'][v]['delta_brier_vs_constant'] for f in folds])),'mean_delta_log_loss':float(np.mean([f['variants'][v]['delta_log_loss_vs_constant'] for f in folds]))} for v in FOCUS}
 return {'experiment_id':EXPERIMENT_ID,'league':'LA_LIGA','research_only':True,'production_promotion':False,'betting_enabled':False,'result':'NO_BET','match_outcome_used':False,'opened_2026_27_data_used':False,'v7_target_unchanged':True,'movement_quantile':MOVEMENT_QUANTILE,'focus_variants':list(FOCUS),'coverage':coverage,'fold_count':len(folds),'folds':folds,'beats_constant_both_count':counts,'mean_fold_deltas':mean_delta,'all_fold_robust_variants':[v for v in FOCUS if counts[v]==len(folds)],'note':'Threshold, imputer, scaler and classifier are fit from prior seasons only in every fold.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/la_liga_market_state_walkforward_v12/work'));p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_market_state_walkforward_v12/report.json'));a=p.parse_args();r=evaluate_frame(load_history(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
