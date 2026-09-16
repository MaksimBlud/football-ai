"""V15: can cross-bookmaker disagreement predict Bet365 repricing direction?
EPL historical research only. Uses STANDARD Bet365 + Pinnacle prices as features and
explicit Bet365 closing only for target/regime labels. No match outcomes, NO_BET.
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
EXPERIMENT_ID='EPL_CROSS_BOOK_DIRECTION_V15';Q=.75;C=.1
SEASONS={'1617':'2016-2017','1718':'2017-2018','1819':'2018-2019','1920':'2019-2020','2021':'2020-2021','2122':'2021-2022','2223':'2022-2023','2324':'2023-2024','2425':'2024-2025','2526':'2025-2026'}
FEATURES=['b365_home_prob','b365_draw_prob','b365_away_prob','ps_home_prob','ps_draw_prob','ps_away_prob','disagree_home','disagree_draw','disagree_away','favorite_gap']
def load(work):
 work.mkdir(parents=True,exist_ok=True);out=[]
 for code,s in SEASONS.items():
  p=work/f'{code}.csv'
  if not p.exists():
   r=requests.get(f'https://www.football-data.co.uk/mmz4281/{code}/E0.csv',timeout=30);r.raise_for_status();p.write_bytes(r.content)
  x=pd.read_csv(p);x['season']=s;out.append(x)
 return pd.concat(out,ignore_index=True)
def prepare(raw):
 cols=['B365H','B365D','B365A','B365CH','B365CD','B365CA','PSH','PSD','PSA'];x=raw.dropna(subset=cols).copy();b=power(1/x[['B365H','B365D','B365A']].to_numpy(float));c=power(1/x[['B365CH','B365CD','B365CA']].to_numpy(float));p=power(1/x[['PSH','PSD','PSA']].to_numpy(float));
 for a,z in [('b365',b),('ps',p)]: x[[f'{a}_home_prob',f'{a}_draw_prob',f'{a}_away_prob']]=z
 d=p-b;x[['disagree_home','disagree_draw','disagree_away']]=d;x['favorite_gap']=np.max(np.abs(d),axis=1);x['move_home']=np.log(c[:,0]/c[:,1])-np.log(b[:,0]/b[:,1]);x['move_away']=np.log(c[:,2]/c[:,1])-np.log(b[:,2]/b[:,1]);x['movement']=np.sqrt(x.move_home**2+x.move_away**2);return x,{'total':len(raw),'valid':len(x),'coverage':float(len(x)/len(raw))}
def met(y,p):
 p=np.clip(p,1e-12,1-1e-12);return {'n':len(y),'prevalence':float(np.mean(y)),'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}
def evaluate(raw):
 x,cov=prepare(raw);ss=list(SEASONS.values());folds=[]
 for i in range(2,len(ss)):
  tr=x[x.season.isin(ss[:i])].copy();te=x[x.season==ss[i]].copy();thr=float(np.quantile(tr.movement,Q));tr=tr[tr.movement>=thr];te=te[te.movement>=thr]
  yt=(tr.move_home>0).astype(int).to_numpy();y=(te.move_home>0).astype(int).to_numpy();prev=float(yt.mean());base=met(y,np.full(len(y),prev));model=Pipeline([('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]).fit(tr[FEATURES],yt);cand=met(y,model.predict_proba(te[FEATURES])[:,1]);cand['delta_brier']=cand['brier']-base['brier'];cand['delta_log_loss']=cand['log_loss']-base['log_loss'];cand['beats_both']=cand['delta_brier']<0 and cand['delta_log_loss']<0;folds.append({'season':ss[i],'threshold':thr,'train_material_n':len(tr),'test_material_n':len(te),'baseline':base,'candidate':cand})
 wins=sum(f['candidate']['beats_both'] for f in folds);return {'experiment_id':EXPERIMENT_ID,'league':'EPL','research_only':True,'result':'NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'feature_timing':'STANDARD_ONLY','target_timing':'EXPLICIT_B365_CLOSING','features':FEATURES,'coverage':cov,'fold_count':len(folds),'folds':folds,'beats_constant_both_count':wins,'all_fold_robust':wins==len(folds),'mean_delta_brier':float(np.mean([f['candidate']['delta_brier'] for f in folds])),'mean_delta_log_loss':float(np.mean([f['candidate']['delta_log_loss'] for f in folds]))}
def main():
 a=argparse.ArgumentParser();a.add_argument('--work-dir',type=Path,default=Path('artifacts/epl_cross_book_direction_v15/work'));a.add_argument('--output',type=Path,default=Path('artifacts/epl_cross_book_direction_v15/report.json'));z=a.parse_args();r=evaluate(load(z.work_dir));z.output.parent.mkdir(parents=True,exist_ok=True);z.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
