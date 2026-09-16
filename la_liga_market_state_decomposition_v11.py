"""V11: decompose the robust La Liga V7 repricing-risk market-state signal.

Research-only. Uses only the standard Bet365 1X2 POWER probabilities available
before the explicit closing prices. The V7 target and 75th-percentile definition
are unchanged. Feature families are fixed, interpretable transforms of the three
standard probabilities; 2024-25 is validation and 2025-26 remains temporal OOT.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from la_liga_market_movement_regimes_v7 import MOVEMENT_QUANTILE,movement_magnitude,classification_metrics,baseline_metrics
from la_liga_standard_to_close_signal_v6 import TRAIN_SEASONS,VALIDATION_SEASON,TEST_SEASON,load_history,prepare_frame

EXPERIMENT_ID='LA_LIGA_MARKET_STATE_DECOMPOSITION_V11'; C=.1
FEATURE_VARIANTS={
 'FULL_PROBS':['standard_home_prob','standard_draw_prob','standard_away_prob'],
 'FAVORITE_STRENGTH':['favorite_prob'],
 'DRAW_LEVEL':['standard_draw_prob'],
 'ENTROPY':['market_entropy'],
 'TOP_TWO_GAP':['top_two_gap'],
 'FAVORITE_PLUS_ENTROPY':['favorite_prob','market_entropy'],
 'GEOMETRY':['favorite_prob','market_entropy','top_two_gap','standard_draw_prob'],
}

def add_market_geometry(frame):
 out=frame.copy(); p=out[['standard_home_prob','standard_draw_prob','standard_away_prob']].to_numpy(float); ps=np.sort(p,axis=1)
 out['favorite_prob']=p.max(axis=1); out['market_entropy']=-np.sum(p*np.log(np.clip(p,1e-12,1)),axis=1); out['top_two_gap']=ps[:,-1]-ps[:,-2]
 return out

def fit(train,y,variant):
 m=Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))]);m.fit(train[FEATURE_VARIANTS[variant]],y);return m

def evaluate_frame(frame):
 frame,coverage=prepare_frame(frame); frame=add_market_geometry(frame); tr=frame[frame.season.isin(TRAIN_SEASONS)].copy(); va=frame[frame.season==VALIDATION_SEASON].copy(); te=frame[frame.season==TEST_SEASON].copy()
 threshold=float(np.quantile(movement_magnitude(tr),MOVEMENT_QUANTILE)); yt=(movement_magnitude(tr)>=threshold).astype(int); yv=(movement_magnitude(va)>=threshold).astype(int); yo=(movement_magnitude(te)>=threshold).astype(int); prevalence=float(yt.mean()); vb=baseline_metrics(yv,prevalence); ob=baseline_metrics(yo,prevalence)
 candidates=[]; models={}
 for v in FEATURE_VARIANTS:
  models[v]=fit(tr,yt,v); p=models[v].predict_proba(va[FEATURE_VARIANTS[v]])[:,1]; m=classification_metrics(yv,p); candidates.append({'feature_variant':v,**m,'delta_brier_vs_constant':m['brier']-vb['brier'],'delta_log_loss_vs_constant':m['log_loss']-vb['log_loss']})
 admissible=[x for x in candidates if x['brier']<vb['brier'] and x['log_loss']<vb['log_loss']]; selected=min(admissible,key=lambda x:(x['log_loss'],x['brier'],x['feature_variant'])) if admissible else None
 oot=[]
 for v in FEATURE_VARIANTS:
  p=models[v].predict_proba(te[FEATURE_VARIANTS[v]])[:,1]; m=classification_metrics(yo,p); oot.append({'feature_variant':v,**m,'delta_brier_vs_constant':m['brier']-ob['brier'],'delta_log_loss_vs_constant':m['log_loss']-ob['log_loss']})
 selected_oot=next((x for x in oot if selected and x['feature_variant']==selected['feature_variant']),None); accepted=bool(selected_oot and selected_oot['brier']<ob['brier'] and selected_oot['log_loss']<ob['log_loss'])
 return {'experiment_id':EXPERIMENT_ID,'league':'LA_LIGA','research_only':True,'production_promotion':False,'betting_enabled':False,'result':'NO_BET','match_outcome_used':False,'opened_2026_27_data_used':False,'standard_is_labeled_opening':False,'v7_target_unchanged':True,'movement_quantile':MOVEMENT_QUANTILE,'threshold_fit_on_train_only':threshold,'train_n':len(tr),'validation_n':len(va),'test_n':len(te),'coverage':coverage,'feature_variants':FEATURE_VARIANTS,'validation_baseline':vb,'validation_candidates':candidates,'validation_selected':selected,'oot_baseline':ob,'oot_variants':oot,'selected_oot':selected_oot,'selected_signal_accepted':accepted,'active_mode':'INTERPRETABLE_MARKET_STATE_SIGNAL' if accepted else 'V7_MARKET_STATE_UNCHANGED','acceptance_rule':'validation-selected interpretable component must beat constant prevalence on both Brier and LogLoss on untouched OOT'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,default=Path('artifacts/la_liga_market_state_decomposition_v11/work'));p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_market_state_decomposition_v11/report.json'));a=p.parse_args();r=evaluate_frame(load_history(a.work_dir));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
