"""V16: fixed decomposition of V15 EPL cross-book repricing-direction evidence.
No feature selection on 2025/26. Same material-movement target, q=.75 and C=.1.
Closing Bet365 is target-only; features use STANDARD Bet365/Pinnacle only. NO_BET.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss,log_loss,roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from epl_cross_book_direction_v15 import load,prepare,SEASONS,Q,C
EXPERIMENT_ID='EPL_CROSS_BOOK_DIRECTION_DECOMPOSITION_V16'
FEATURE_VARIANTS={
 'B365_ONLY':['b365_home_prob','b365_draw_prob','b365_away_prob'],
 'PINNACLE_ONLY':['ps_home_prob','ps_draw_prob','ps_away_prob'],
 'DISAGREEMENT_ONLY':['disagree_home','disagree_draw','disagree_away'],
 'DISAGREEMENT_MAGNITUDE':['favorite_gap'],
 'B365_PLUS_DISAGREEMENT':['b365_home_prob','b365_draw_prob','b365_away_prob','disagree_home','disagree_draw','disagree_away'],
 'V15_FULL':['b365_home_prob','b365_draw_prob','b365_away_prob','ps_home_prob','ps_draw_prob','ps_away_prob','disagree_home','disagree_draw','disagree_away','favorite_gap'],
}
def met(y,p):
 p=np.clip(np.asarray(p,float),1e-12,1-1e-12);y=np.asarray(y,int)
 return {'n':len(y),'prevalence':float(y.mean()),'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}
def evaluate(raw):
 x,cov=prepare(raw);ss=[s for s in SEASONS.values() if len(x[x.season==s])];folds=[]
 for i in range(2,len(ss)):
  tr=x[x.season.isin(ss[:i])].copy();te=x[x.season==ss[i]].copy();thr=float(np.quantile(tr.movement,Q));tr=tr[tr.movement>=thr];te=te[te.movement>=thr]
  if not len(te): continue
  yt=(tr.move_home>0).astype(int).to_numpy();y=(te.move_home>0).astype(int).to_numpy();base=met(y,np.full(len(y),yt.mean()));variants={}
  for name,cols in FEATURE_VARIANTS.items():
   model=Pipeline([('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]).fit(tr[cols],yt);m=met(y,model.predict_proba(te[cols])[:,1]);m['delta_brier']=m['brier']-base['brier'];m['delta_log_loss']=m['log_loss']-base['log_loss'];m['beats_both']=bool(m['delta_brier']<0 and m['delta_log_loss']<0);variants[name]=m
  folds.append({'season':ss[i],'threshold':thr,'train_material_n':len(tr),'test_material_n':len(te),'baseline':base,'variants':variants})
 counts={v:sum(f['variants'][v]['beats_both'] for f in folds) for v in FEATURE_VARIANTS};means={v:{'mean_delta_brier':float(np.mean([f['variants'][v]['delta_brier'] for f in folds])),'mean_delta_log_loss':float(np.mean([f['variants'][v]['delta_log_loss'] for f in folds]))} for v in FEATURE_VARIANTS}
 return {'experiment_id':EXPERIMENT_ID,'league':'EPL','research_only':True,'result':'NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'v15_target_unchanged':True,'feature_selection_on_2025_26':False,'movement_quantile':Q,'logistic_c':C,'coverage':cov,'available_seasons':ss,'fold_count':len(folds),'feature_variants':FEATURE_VARIANTS,'folds':folds,'beats_constant_both_count':counts,'mean_fold_deltas':means,'all_fold_robust_variants':[v for v in FEATURE_VARIANTS if counts[v]==len(folds)]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/epl_cross_book_direction_decomposition_v16/work'));p.add_argument('--output',type=Path,default=Path('artifacts/epl_cross_book_direction_decomposition_v16/report.json'));a=p.parse_args();r=evaluate(load(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
