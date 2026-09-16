"""V19: diagnose the synchronized 2025/26 cross-book direction failure.
Research-only descriptive audit. No outcomes, betting, production promotion, or live writes.
STANDARD Bet365/Pinnacle prices are not called opening prices; B365 closing is target-only.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,requests
from sklearn.metrics import brier_score_loss,log_loss,roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from bookmaker_reconstruction_devig_v1 import power
EXPERIMENT_ID='CROSS_LEAGUE_STRUCTURAL_BREAK_V19';Q=.75;C=.1
SEASONS={'1617':'2016-2017','1718':'2017-2018','1819':'2018-2019','1920':'2019-2020','2021':'2020-2021','2122':'2021-2022','2223':'2022-2023','2324':'2023-2024','2425':'2024-2025','2526':'2025-2026'}
LEAGUES={'EPL':'E0','SERIE_A':'I1','LA_LIGA':'SP1'};FEATURES=['disagree_home','disagree_draw','disagree_away']
def load(code,work):
 out=[];work.mkdir(parents=True,exist_ok=True)
 for sc,s in SEASONS.items():
  p=work/f'{code}_{sc}.csv'
  if not p.exists():
   r=requests.get(f'https://www.football-data.co.uk/mmz4281/{sc}/{code}.csv',timeout=30);r.raise_for_status();p.write_bytes(r.content)
  x=pd.read_csv(p);x['season']=s;out.append(x)
 return pd.concat(out,ignore_index=True)
def prepare(raw):
 cols=['B365H','B365D','B365A','B365CH','B365CD','B365CA','PSH','PSD','PSA'];x=raw.dropna(subset=cols).copy()
 b=power(1/x[['B365H','B365D','B365A']].to_numpy(float));cl=power(1/x[['B365CH','B365CD','B365CA']].to_numpy(float));ps=power(1/x[['PSH','PSD','PSA']].to_numpy(float));d=ps-b
 x[FEATURES]=d;x['disagreement_norm']=np.linalg.norm(d,axis=1);x['move_home']=np.log(cl[:,0]/cl[:,1])-np.log(b[:,0]/b[:,1]);x['move_away']=np.log(cl[:,2]/cl[:,1])-np.log(b[:,2]/b[:,1]);x['movement']=np.sqrt(x.move_home**2+x.move_away**2);x['direction']=(x.move_home>0).astype(int);return x

def metric(y,p):
 y=np.asarray(y,int);p=np.clip(np.asarray(p,float),1e-12,1-1e-12);return {'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}
def summarize(raw):
 x=prepare(raw);ss=[s for s in SEASONS.values() if len(x[x.season==s])];rows=[]
 for i in range(2,len(ss)):
  tr=x[x.season.isin(ss[:i])].copy();te=x[x.season==ss[i]].copy();thr=float(np.quantile(tr.movement,Q));tm=tr[tr.movement>=thr];em=te[te.movement>=thr]
  yt=tm.direction.to_numpy();y=em.direction.to_numpy();base_p=float(yt.mean());model=Pipeline([('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]).fit(tm[FEATURES],yt);p=model.predict_proba(em[FEATURES])[:,1];base=metric(y,np.full(len(y),base_p));cand=metric(y,p)
  rows.append({'season':ss[i],'valid_n':int(len(te)),'material_n':int(len(em)),'material_rate':float(len(em)/len(te)),'train_threshold':thr,'movement_mean':float(te.movement.mean()),'movement_p75':float(te.movement.quantile(.75)),'disagreement_norm_mean':float(te.disagreement_norm.mean()),'disagreement_norm_p75':float(te.disagreement_norm.quantile(.75)),'direction_prevalence_material':float(y.mean()),'train_direction_prevalence_material':base_p,'prevalence_shift':float(y.mean()-base_p),'candidate_auc':cand['auc'],'delta_brier':cand['brier']-base['brier'],'delta_log_loss':cand['log_loss']-base['log_loss'],'beats_both':bool(cand['brier']<base['brier'] and cand['log_loss']<base['log_loss'])})
 return {'total_n':int(len(raw)),'valid_n':int(len(x)),'coverage':float(len(x)/len(raw)),'seasons':rows}
def evaluate(work):
 leagues={k:summarize(load(v,work)) for k,v in LEAGUES.items()};latest={k:v['seasons'][-1] for k,v in leagues.items()};prior={k:v['seasons'][:-1] for k,v in leagues.items()};
 return {'experiment_id':EXPERIMENT_ID,'research_only':True,'result':'DIAGNOSTIC_ONLY_NO_BET','production_promotion':False,'betting_enabled':False,'match_outcome_used':False,'standard_is_labeled_opening':False,'movement_quantile':Q,'logistic_c':C,'features':FEATURES,'leagues':leagues,'latest_2025_26':latest,'prior_fold_beats_both':{k:sum(r['beats_both'] for r in rs) for k,rs in prior.items()},'latest_all_fail_both':all(not r['beats_both'] for r in latest.values()),'latest_mean_prevalence_shift':float(np.mean([r['prevalence_shift'] for r in latest.values()])),'latest_mean_auc':float(np.mean([r['candidate_auc'] for r in latest.values()]))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/cross_league_structural_break_v19/work'));p.add_argument('--output',type=Path,default=Path('artifacts/cross_league_structural_break_v19/report.json'));a=p.parse_args();r=evaluate(a.work_dir);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
