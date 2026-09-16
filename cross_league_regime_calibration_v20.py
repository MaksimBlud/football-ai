"""V20: test whether recent-history calibration repairs cross-book direction drift.
Research only. Uses STANDARD Bet365/Pinnacle disagreement as predictors and explicit
B365 closing only as target. No match outcomes, betting, production promotion or live writes.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss,log_loss,roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from cross_league_structural_break_v19 import LEAGUES,SEASONS,FEATURES,Q,C,load,prepare
EXPERIMENT_ID='CROSS_LEAGUE_REGIME_CALIBRATION_V20';RECENT_SEASONS=2

def metrics(y,p):
 p=np.clip(np.asarray(p,float),1e-12,1-1e-12);y=np.asarray(y,int)
 return {'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}
def fit_predict(train,test):
 m=Pipeline([('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]).fit(train[FEATURES],train.direction.to_numpy())
 return m.predict_proba(test[FEATURES])[:,1]
def fold_rows(raw):
 x=prepare(raw);ss=[s for s in SEASONS.values() if len(x[x.season==s])];rows=[]
 for i in range(2,len(ss)):
  train_seasons=ss[:i];recent_seasons=train_seasons[-RECENT_SEASONS:];tr=x[x.season.isin(train_seasons)].copy();te=x[x.season==ss[i]].copy();thr=float(np.quantile(tr.movement,Q));tm=tr[tr.movement>=thr];em=te[te.movement>=thr];recent=tm[tm.season.isin(recent_seasons)]
  y=em.direction.to_numpy();global_p=float(tm.direction.mean());recent_p=float(recent.direction.mean())
  global_model=metrics(y,fit_predict(tm,em));recent_model=metrics(y,fit_predict(recent,em));global_base=metrics(y,np.full(len(y),global_p));recent_base=metrics(y,np.full(len(y),recent_p))
  rows.append({'season':ss[i],'material_n':int(len(em)),'recent_train_seasons':recent_seasons,'global_prevalence':global_p,'recent_prevalence':recent_p,'actual_prevalence':float(y.mean()),'global_baseline':global_base,'recent_baseline':recent_base,'global_model':global_model,'recent_model':recent_model,'recent_model_vs_global_model_delta_brier':recent_model['brier']-global_model['brier'],'recent_model_vs_global_model_delta_log_loss':recent_model['log_loss']-global_model['log_loss'],'recent_model_beats_global_both':bool(recent_model['brier']<global_model['brier'] and recent_model['log_loss']<global_model['log_loss']),'recent_base_beats_global_base_both':bool(recent_base['brier']<global_base['brier'] and recent_base['log_loss']<global_base['log_loss'])})
 return rows
def evaluate(work):
 leagues={k:fold_rows(load(code,work)) for k,code in LEAGUES.items()};latest={k:v[-1] for k,v in leagues.items()}
 return {'experiment_id':EXPERIMENT_ID,'research_only':True,'result':'DIAGNOSTIC_ONLY_NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'movement_quantile':Q,'logistic_c':C,'recent_seasons':RECENT_SEASONS,'features':FEATURES,'leagues':leagues,'latest_2025_26':latest,'latest_recent_model_beats_global_both_count':sum(r['recent_model_beats_global_both'] for r in latest.values()),'latest_recent_base_beats_global_base_both_count':sum(r['recent_base_beats_global_base_both'] for r in latest.values()),'all_fold_recent_model_beats_global_both':{k:sum(r['recent_model_beats_global_both'] for r in rows) for k,rows in leagues.items()}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/cross_league_regime_calibration_v20/work'));p.add_argument('--output',type=Path,default=Path('artifacts/cross_league_regime_calibration_v20/report.json'));a=p.parse_args();r=evaluate(a.work_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
