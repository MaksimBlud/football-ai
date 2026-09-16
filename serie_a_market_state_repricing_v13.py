"""V13: independent Serie A replication of the La Liga V7/V12 repricing-risk test.

Research-only. Football-Data standard Bet365 1X2 is deliberately called STANDARD,
not opening. Explicit B365 closing columns define subsequent repricing. No match
outcomes are used. Fixed V7 movement quantile=.75 and logistic C=.1 are transferred
without tuning on Serie A. Expanding folds train only on earlier seasons.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import brier_score_loss,log_loss,roc_auc_score,average_precision_score
from bookmaker_reconstruction_devig_v1 import power

EXPERIMENT_ID='SERIE_A_MARKET_STATE_REPRICING_V13'; MOVEMENT_QUANTILE=.75; C=.1
SEASONS={'1617':'2016-2017','1718':'2017-2018','1819':'2018-2019','1920':'2019-2020','2021':'2020-2021','2122':'2021-2022','2223':'2022-2023','2324':'2023-2024','2425':'2024-2025','2526':'2025-2026'}
FEATURES={'FULL_PROBS':['standard_home_prob','standard_draw_prob','standard_away_prob'],'DRAW_LEVEL':['standard_draw_prob'],'ENTROPY':['market_entropy'],'FAVORITE_STRENGTH':['favorite_prob'],'TOP_TWO_GAP':['top_two_gap']}
def load_history(work):
 work.mkdir(parents=True,exist_ok=True);frames=[]
 for code,season in SEASONS.items():
  p=work/f'{code}.csv'
  if not p.exists():
   r=requests.get(f'https://www.football-data.co.uk/mmz4281/{code}/I1.csv',timeout=30);r.raise_for_status();p.write_bytes(r.content)
  x=pd.read_csv(p);x['season']=season;frames.append(x)
 return pd.concat(frames,ignore_index=True)
def prep(raw):
 need=['B365H','B365D','B365A','B365CH','B365CD','B365CA'];x=raw.dropna(subset=need).copy()
 so=x[['B365H','B365D','B365A']].to_numpy(float);co=x[['B365CH','B365CD','B365CA']].to_numpy(float)
 sp=power(1.0/so);cp=power(1.0/co);x[['standard_home_prob','standard_draw_prob','standard_away_prob']]=sp
 x['target_home_vs_draw']=np.log(cp[:,0]/cp[:,1])-np.log(sp[:,0]/sp[:,1]);x['target_away_vs_draw']=np.log(cp[:,2]/cp[:,1])-np.log(sp[:,2]/sp[:,1]);x['movement_magnitude']=np.sqrt(x.target_home_vs_draw**2+x.target_away_vs_draw**2)
 ps=np.sort(sp,axis=1);x['favorite_prob']=sp.max(axis=1);x['market_entropy']=-np.sum(sp*np.log(np.clip(sp,1e-12,1)),axis=1);x['top_two_gap']=ps[:,-1]-ps[:,-2]
 return x,{'total_rows':len(raw),'paired_valid_rows':len(x),'paired_coverage':float(len(x)/len(raw))}
def metrics(y,p):
 y=np.asarray(y,int);p=np.clip(np.asarray(p,float),1e-12,1-1e-12);return {'n':len(y),'prevalence':float(y.mean()),'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,'average_precision':float(average_precision_score(y,p)) if y.sum() else None}
def fit(x,y,cols): return Pipeline([('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]).fit(x[cols],y)
def evaluate(raw):
 x,cov=prep(raw);available=[s for s in SEASONS.values() if len(x[x.season==s])];folds=[]
 for i in range(2,len(available)):
  tr=x[x.season.isin(available[:i])];te=x[x.season==available[i]];threshold=float(np.quantile(tr.movement_magnitude,MOVEMENT_QUANTILE));yt=(tr.movement_magnitude>=threshold).astype(int);y=(te.movement_magnitude>=threshold).astype(int);base=metrics(y,np.full(len(y),yt.mean()));variants={}
  for v,cols in FEATURES.items():
   p=fit(tr,yt,cols).predict_proba(te[cols])[:,1];m=metrics(y,p);m['delta_brier_vs_constant']=m['brier']-base['brier'];m['delta_log_loss_vs_constant']=m['log_loss']-base['log_loss'];m['beats_constant_both']=bool(m['delta_brier_vs_constant']<0 and m['delta_log_loss_vs_constant']<0);variants[v]=m
  folds.append({'test_season':available[i],'train_seasons':available[:i],'train_n':len(tr),'test_n':len(te),'threshold':threshold,'baseline':base,'variants':variants})
 counts={v:sum(f['variants'][v]['beats_constant_both'] for f in folds) for v in FEATURES};means={v:{'mean_delta_brier':float(np.mean([f['variants'][v]['delta_brier_vs_constant'] for f in folds])),'mean_delta_log_loss':float(np.mean([f['variants'][v]['delta_log_loss_vs_constant'] for f in folds]))} for v in FEATURES}
 return {'experiment_id':EXPERIMENT_ID,'league':'SERIE_A','research_only':True,'production_promotion':False,'betting_enabled':False,'result':'NO_BET','match_outcome_used':False,'standard_is_labeled_opening':False,'la_liga_parameters_transferred_without_tuning':True,'movement_quantile':MOVEMENT_QUANTILE,'logistic_c':C,'coverage':cov,'available_seasons':available,'fold_count':len(folds),'folds':folds,'beats_constant_both_count':counts,'mean_fold_deltas':means,'all_fold_robust_variants':[v for v in FEATURES if counts[v]==len(folds)]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/serie_a_market_state_repricing_v13/work'));p.add_argument('--output',type=Path,default=Path('artifacts/serie_a_market_state_repricing_v13/report.json'));a=p.parse_args();r=evaluate(load_history(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
