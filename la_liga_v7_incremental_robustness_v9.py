"""V9: robustness and incremental decomposition of accepted La Liga V7 signal.

Research-only diagnostic. Replays the frozen V7 definition and fixed logistic C,
then compares MARKET_STATE against FORM on validation and untouched OOT. Includes
paired bootstrap on proper-score loss differences and historical season-by-season
readouts. No thresholds/models are promoted or retuned from OOT results.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score

from la_liga_market_movement_regimes_v7 import MOVEMENT_QUANTILE, movement_magnitude, regime_feature_columns
from la_liga_standard_to_close_signal_v6 import TRAIN_SEASONS, VALIDATION_SEASON, TEST_SEASON, load_history, prepare_frame

EXPERIMENT_ID='LA_LIGA_V7_INCREMENTAL_ROBUSTNESS_V9'
C=0.1
BOOTSTRAP_DRAWS=5000
BOOTSTRAP_SEED=20260916
VARIANTS=('MARKET_STATE','FORM')

def fit_model(frame,y,variant):
    m=Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('logit',LogisticRegression(C=C,max_iter=2000))])
    m.fit(frame[regime_feature_columns(variant)],y); return m

def losses(y,p):
    y=np.asarray(y,int); p=np.clip(np.asarray(p,float),1e-12,1-1e-12)
    return (p-y)**2, -(y*np.log(p)+(1-y)*np.log(1-p))

def scores(y,p):
    b,l=losses(y,p); y=np.asarray(y,int)
    return {'n':int(len(y)),'material_n':int(y.sum()),'prevalence':float(y.mean()),'brier':float(b.mean()),'log_loss':float(l.mean()),'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else float('nan'),'average_precision':float(average_precision_score(y,p)) if y.sum() else float('nan')}

def paired_bootstrap(y,p_form,p_market):
    bf,lf=losses(y,p_form); bm,lm=losses(y,p_market); db=bf-bm; dl=lf-lm
    rng=np.random.default_rng(BOOTSTRAP_SEED); n=len(y); idx=rng.integers(0,n,size=(BOOTSTRAP_DRAWS,n))
    boot_b=db[idx].mean(axis=1); boot_l=dl[idx].mean(axis=1)
    return {'delta_brier':float(db.mean()),'delta_log_loss':float(dl.mean()),'brier_ci95':[float(np.quantile(boot_b,.025)),float(np.quantile(boot_b,.975))],'log_loss_ci95':[float(np.quantile(boot_l,.025)),float(np.quantile(boot_l,.975))],'prob_form_improves_brier':float(np.mean(boot_b<0)),'prob_form_improves_log_loss':float(np.mean(boot_l<0)),'prob_form_improves_both':float(np.mean((boot_b<0)&(boot_l<0)))}

def evaluate_frame(frame):
    frame,coverage=prepare_frame(frame); train=frame[frame.season.isin(TRAIN_SEASONS)].copy(); val=frame[frame.season==VALIDATION_SEASON].copy(); test=frame[frame.season==TEST_SEASON].copy()
    threshold=float(np.quantile(movement_magnitude(train),MOVEMENT_QUANTILE)); train_y=(movement_magnitude(train)>=threshold).astype(int)
    models={v:fit_model(train,train_y,v) for v in VARIANTS}
    def eval_split(x):
        y=(movement_magnitude(x)>=threshold).astype(int); ps={v:models[v].predict_proba(x[regime_feature_columns(v)])[:,1] for v in VARIANTS}
        return {'market_state':scores(y,ps['MARKET_STATE']),'form':scores(y,ps['FORM']),'form_vs_market_state':paired_bootstrap(y,ps['FORM'],ps['MARKET_STATE'])}
    validation=eval_split(val); oot=eval_split(test)
    seasons={}
    for season in list(TRAIN_SEASONS)+[VALIDATION_SEASON,TEST_SEASON]:
        x=frame[frame.season==season].copy()
        if len(x):
            y=(movement_magnitude(x)>=threshold).astype(int); pm=models['MARKET_STATE'].predict_proba(x[regime_feature_columns('MARKET_STATE')])[:,1]; pf=models['FORM'].predict_proba(x[regime_feature_columns('FORM')])[:,1]; bf,lf=losses(y,pf); bm,lm=losses(y,pm)
            seasons[season]={'n':int(len(x)),'material_n':int(y.sum()),'delta_brier_form_minus_market_state':float((bf-bm).mean()),'delta_log_loss_form_minus_market_state':float((lf-lm).mean())}
    return {'experiment_id':EXPERIMENT_ID,'league':'LA_LIGA','research_only':True,'production_promotion':False,'betting_enabled':False,'result':'NO_BET','match_outcome_used':False,'opened_2026_27_data_used':False,'v7_definition_unchanged':True,'movement_quantile':MOVEMENT_QUANTILE,'movement_threshold_fit_on_train_only':threshold,'train_n':int(len(train)),'validation_n':int(len(val)),'test_n':int(len(test)),'coverage':coverage,'validation':validation,'oot_2025_26':oot,'season_by_season_descriptive':seasons,'incremental_form_robust_on_oot':bool(oot['form_vs_market_state']['delta_brier']<0 and oot['form_vs_market_state']['delta_log_loss']<0),'note':'season-by-season training-season rows are descriptive/in-sample; validation and OOT carry the inferential weight'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-dir',type=Path,default=Path('artifacts/la_liga_v7_incremental_robustness_v9/work')); p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_v7_incremental_robustness_v9/report.json')); a=p.parse_args(); r=evaluate_frame(load_history(a.work_dir)); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__': main()
