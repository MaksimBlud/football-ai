"""V17: independent Serie A replication of the EPL V16 disagreement-only direction signal.
Frozen transfer: material q=.75, LogisticRegression C=.1, STANDARD Pinnacle-Bet365
fair-probability disagreement only. Explicit B365 closing is target-only. NO_BET.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss,log_loss,roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from bookmaker_reconstruction_devig_v1 import power
EXPERIMENT_ID='SERIE_A_CROSS_BOOK_DIRECTION_V17';Q=.75;C=.1
SEASONS={'1617':'2016-2017','1718':'2017-2018','1819':'2018-2019','1920':'2019-2020','2021':'2020-2021','2122':'2021-2022','2223':'2022-2023','2324':'2023-2024','2425':'2024-2025','2526':'2025-2026'}
FEATURES=['disagree_home','disagree_draw','disagree_away']
def load(work):
 work.mkdir(parents=True,exist_ok=True);out=[]
 for code,s in SEASONS.items():
  p=work/f'{code}.csv'
  if not p.exists():
   r=requests.get(f'https://www.football-data.co.uk/mmz4281/{code}/I1.csv',timeout=30);r.raise_for_status();p.write_bytes(r.content)
  x=pd.read_csv(p);x['season']=s;out.append(x)
 return pd.concat(out,ignore_index=True)
def prepare(raw):
 cols=['B365H','B365D','B365A','B365CH','B365CD','B365CA','PSH','PSD','PSA'];x=raw.dropna(subset=cols).copy();b=power(1/x[['B365H','B365D','B365A']].to_numpy(float));cl=power(1/x[['B365CH','B365CD','B365CA']].to_numpy(float));ps=power(1/x[['PSH','PSD','PSA']].to_numpy(float));d=ps-b;x[['disagree_home','disagree_draw','disagree_away']]=d;x['move_home']=np.log(cl[:,0]/cl[:,1])-np.log(b[:,0]/b[:,1]);x['move_away']=np.log(cl[:,2]/cl[:,1])-np.log(b[:,2]/b[:,1]);x['movement']=np.sqrt(x.move_home**2+x.move_away**2);return x,{'total':len(raw),'valid':len(x),'coverage':float(len(x)/len(raw))}
def met(y,p):
 y=np.asarray(y,int);p=np.clip(np.asarray(p,float),1e-12,1-1e-12);return {'n':len(y),'prevalence':float(y.mean()),'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}
def evaluate(raw):
 x,cov=prepare(raw);ss=[s for s in SEASONS.values() if len(x[x.season==s])];folds=[]
 for i in range(2,len(ss)):
  tr=x[x.season.isin(ss[:i])].copy();te=x[x.season==ss[i]].copy();thr=float(np.quantile(tr.movement,Q));tr=tr[tr.movement>=thr];te=te[te.movement>=thr]
  if not len(te):continue
  yt=(tr.move_home>0).astype(int).to_numpy();y=(te.move_home>0).astype(int).to_numpy();base=met(y,np.full(len(y),yt.mean()));model=Pipeline([('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]).fit(tr[FEATURES],yt);m=met(y,model.predict_proba(te[FEATURES])[:,1]);m['delta_brier']=m['brier']-base['brier'];m['delta_log_loss']=m['log_loss']-base['log_loss'];m['beats_both']=bool(m['delta_brier']<0 and m['delta_log_loss']<0);folds.append({'season':ss[i],'threshold':thr,'train_material_n':len(tr),'test_material_n':len(te),'baseline':base,'candidate':m})
 wins=sum(f['candidate']['beats_both'] for f in folds);return {'experiment_id':EXPERIMENT_ID,'league':'SERIE_A','research_only':True,'result':'NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'parameters_transferred_without_serie_a_tuning':True,'source_signal':'EPL_V16_DISAGREEMENT_ONLY','movement_quantile':Q,'logistic_c':C,'features':FEATURES,'coverage':cov,'available_seasons':ss,'fold_count':len(folds),'folds':folds,'beats_constant_both_count':wins,'all_fold_robust':bool(folds) and wins==len(folds),'mean_delta_brier':float(np.mean([f['candidate']['delta_brier'] for f in folds])),'mean_delta_log_loss':float(np.mean([f['candidate']['delta_log_loss'] for f in folds]))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/serie_a_cross_book_direction_v17/work'));p.add_argument('--output',type=Path,default=Path('artifacts/serie_a_cross_book_direction_v17/report.json'));a=p.parse_args();r=evaluate(load(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
