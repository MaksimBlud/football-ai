"""V10: expanding walk-forward robustness for V7 repricing-risk signal.

For each eligible season, all earlier paired seasons train the fixed V7 MARKET_STATE
and FORM logistic models; the 75th-percentile movement threshold is re-estimated
from that fold's training history only. The next season is evaluated once. This is
historical robustness, not prospective evidence or production promotion.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from la_liga_market_movement_regimes_v7 import MOVEMENT_QUANTILE,movement_magnitude,regime_feature_columns
from la_liga_standard_to_close_signal_v6 import load_history,prepare_frame
from la_liga_v7_incremental_robustness_v9 import losses,scores

EXPERIMENT_ID='LA_LIGA_V7_WALKFORWARD_V10'; C=.1; VARIANTS=('MARKET_STATE','FORM')

def fit(x,y,v):
 m=Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]);m.fit(x[regime_feature_columns(v)],y);return m

def evaluate_frame(frame):
 frame,coverage=prepare_frame(frame); seasons=sorted(frame.season.unique()); folds=[]
 for i in range(2,len(seasons)):
  test_season=seasons[i]; train_seasons=seasons[:i]; tr=frame[frame.season.isin(train_seasons)].copy(); te=frame[frame.season==test_season].copy()
  threshold=float(np.quantile(movement_magnitude(tr),MOVEMENT_QUANTILE)); ytr=(movement_magnitude(tr)>=threshold).astype(int); y=(movement_magnitude(te)>=threshold).astype(int); prevalence=float(ytr.mean())
  pb=np.full(len(te),prevalence); fold={'test_season':test_season,'train_seasons':train_seasons,'train_n':len(tr),'test_n':len(te),'threshold':threshold,'baseline':scores(y,pb),'variants':{}}
  for v in VARIANTS:
   m=fit(tr,ytr,v); p=m.predict_proba(te[regime_feature_columns(v)])[:,1]; s=scores(y,p); bb,ll=losses(y,p); b0,l0=losses(y,pb); s['delta_brier_vs_constant']=float((bb-b0).mean());s['delta_log_loss_vs_constant']=float((ll-l0).mean());fold['variants'][v]=s
  bf,lf=losses(y,fit(tr,ytr,'FORM').predict_proba(te[regime_feature_columns('FORM')])[:,1]); bm,lm=losses(y,fit(tr,ytr,'MARKET_STATE').predict_proba(te[regime_feature_columns('MARKET_STATE')])[:,1]);fold['form_delta_brier_vs_market_state']=float((bf-bm).mean());fold['form_delta_log_loss_vs_market_state']=float((lf-lm).mean());fold['form_beats_market_state_both']=bool(fold['form_delta_brier_vs_market_state']<0 and fold['form_delta_log_loss_vs_market_state']<0);folds.append(fold)
 return {'experiment_id':EXPERIMENT_ID,'league':'LA_LIGA','research_only':True,'production_promotion':False,'betting_enabled':False,'result':'NO_BET','match_outcome_used':False,'opened_2026_27_data_used':False,'movement_quantile':MOVEMENT_QUANTILE,'coverage':coverage,'folds':folds,'fold_count':len(folds),'form_beats_market_state_both_count':sum(f['form_beats_market_state_both'] for f in folds),'form_beats_market_state_both_fraction':float(np.mean([f['form_beats_market_state_both'] for f in folds])) if folds else 0.0,'market_state_beats_constant_both_count':sum(f['variants']['MARKET_STATE']['delta_brier_vs_constant']<0 and f['variants']['MARKET_STATE']['delta_log_loss_vs_constant']<0 for f in folds),'form_beats_constant_both_count':sum(f['variants']['FORM']['delta_brier_vs_constant']<0 and f['variants']['FORM']['delta_log_loss_vs_constant']<0 for f in folds),'note':'Each fold trains only on earlier seasons and evaluates the next season; no fold uses future rows for threshold or model fit.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/la_liga_v7_walkforward_v10/work'));p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_v7_walkforward_v10/report.json'));a=p.parse_args();r=evaluate_frame(load_history(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
