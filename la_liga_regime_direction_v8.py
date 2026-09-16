"""V8: predict direction of closing repricing inside V7's material-movement regime.

Research only. V7's threshold (75th percentile of training movement magnitude) is
recomputed from training data only. Direction models are trained only on training
rows whose eventual movement is material; validation selects one fixed feature
family, then 2025-26 is untouched OOT. Match outcomes are unused.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from la_liga_market_movement_regimes_v7 import MOVEMENT_QUANTILE, movement_magnitude, regime_feature_columns
from la_liga_standard_to_close_signal_v6 import TEST_SEASON, TRAIN_SEASONS, VALIDATION_SEASON, load_history, prepare_frame

EXPERIMENT_ID = "LA_LIGA_REGIME_DIRECTION_V8"
FEATURE_VARIANTS = ("MARKET_STATE", "FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL")
C = 0.1


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y=np.asarray(y,dtype=int); p=np.clip(np.asarray(p,float),1e-12,1-1e-12)
    return {"brier":float(brier_score_loss(y,p)),"log_loss":float(log_loss(y,np.column_stack([1-p,p]),labels=[0,1])),"roc_auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else float('nan'),"prevalence":float(y.mean())}


def baseline(y: np.ndarray, prevalence: float) -> dict[str,float]:
    return metrics(y,np.full(len(y),prevalence))


def fit(train, y, variant):
    m=Pipeline([("imputer",SimpleImputer(strategy="median")),("scale",StandardScaler()),("logit",LogisticRegression(C=C,max_iter=2000))])
    m.fit(train[regime_feature_columns(variant)],y)
    return m


def evaluate_frame(frame):
    frame,coverage=prepare_frame(frame)
    train=frame[frame.season.isin(TRAIN_SEASONS)].copy(); val=frame[frame.season==VALIDATION_SEASON].copy(); test=frame[frame.season==TEST_SEASON].copy()
    threshold=float(np.quantile(movement_magnitude(train),MOVEMENT_QUANTILE))
    train=train.loc[movement_magnitude(train)>=threshold].copy(); val=val.loc[movement_magnitude(val)>=threshold].copy(); test=test.loc[movement_magnitude(test)>=threshold].copy()
    if min(len(train),len(val),len(test))==0: raise RuntimeError("no material-movement rows")
    # Direction is whether the home-vs-draw log ratio strengthened by close.
    train_y=(train.target_home_vs_draw.to_numpy(float)>0).astype(int); val_y=(val.target_home_vs_draw.to_numpy(float)>0).astype(int); test_y=(test.target_home_vs_draw.to_numpy(float)>0).astype(int)
    prevalence=float(train_y.mean()); val_base=baseline(val_y,prevalence)
    choices=[]; fitted={}
    for variant in FEATURE_VARIANTS:
        model=fit(train,train_y,variant); fitted[variant]=model
        p=model.predict_proba(val[regime_feature_columns(variant)])[:,1]; choices.append({"feature_variant":variant,**metrics(val_y,p)})
    admissible=[x for x in choices if x['brier']<val_base['brier'] and x['log_loss']<val_base['log_loss']]
    selected=min(admissible,key=lambda x:(x['log_loss'],x['brier'],x['feature_variant'])) if admissible else None
    test_base=baseline(test_y,prevalence)
    if selected:
        variant=selected['feature_variant']; p=fitted[variant].predict_proba(test[regime_feature_columns(variant)])[:,1]; cand=metrics(test_y,p); accepted=cand['brier']<test_base['brier'] and cand['log_loss']<test_base['log_loss']
    else:
        variant='CONSTANT_DIRECTION_BASELINE'; cand=dict(test_base); accepted=False
    return {"experiment_id":EXPERIMENT_ID,"league":"LA_LIGA","evidence_class":"HISTORICAL_TEMPORAL_OOT_REGIME_CONDITIONED_DIRECTION","research_only":True,"production_promotion":False,"betting_enabled":False,"result":"NO_BET","match_outcome_used":False,"opened_2026_27_data_used":False,"standard_is_labeled_opening":False,"v7_movement_quantile":MOVEMENT_QUANTILE,"movement_threshold_fit_on_train_only":threshold,"target":"home_vs_draw_closing_repricing_direction_within_material_movement_rows","train_material_n":len(train),"validation_material_n":len(val),"test_material_n":len(test),"train_positive_n":int(train_y.sum()),"validation_positive_n":int(val_y.sum()),"test_positive_n":int(test_y.sum()),"coverage":coverage,"baseline":"CONSTANT_TRAIN_DIRECTION_PREVALENCE","validation_baseline":val_base,"validation_candidates":choices,"validation_selected":selected,"selected_feature_variant":variant,"test_baseline":test_base,"test_candidate":cand,"test_delta_brier":float(cand['brier']-test_base['brier']),"test_delta_log_loss":float(cand['log_loss']-test_base['log_loss']),"direction_signal_accepted":bool(accepted),"active_mode":"REGIME_DIRECTION_SIGNAL" if accepted else "CONSTANT_DIRECTION_FALLBACK","acceptance_rule":"beat constant train direction prevalence on Brier and LogLoss on validation and untouched OOT"}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-dir',type=Path,default=Path('artifacts/la_liga_regime_direction_v8/work')); p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_regime_direction_v8/report.json')); a=p.parse_args()
    r=evaluate_frame(load_history(a.work_dir)); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__': main()
