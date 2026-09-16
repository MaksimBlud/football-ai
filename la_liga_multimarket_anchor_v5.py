"""La Liga V5: test whether additional bookmaker markets explain 1X2 market error.

Research-only diagnostic. The goal is not another football residual search. It asks
whether pre-match totals/Asian-handicap prices contain incremental information about
realized 1X2 outcomes after the fixed POWER 1X2 prior. Selection is on 2024-25 and
2025-26 is untouched temporal OOT. No 2026-27 outcomes are used.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from historical_football_signal_lab import RESULT_TO_INT
from historical_football_signal_runner import BASE, LEAGUES
from la_liga_power_anchor_v3 import LEAGUE, TRAIN_SEASONS, VALIDATION_SEASON, TEST_SEASON, LATEST_ALLOWED_DATE, _power_market
from market_anchor_1x2_v1 import score_probabilities

EXPERIMENT_ID='LA_LIGA_MULTIMARKET_ANCHOR_V5'
# Football-Data commonly exposes these historical bookmaker market columns when available.
TOTAL_PAIRS=(('B365>2.5','B365<2.5'),('P>2.5','P<2.5'),('Avg>2.5','Avg<2.5'))
AH_PAIRS=(('B365AHH','B365AHA'),('PAHH','PAHA'),('AvgAHH','AvgAHA'))
AH_LINE=('AHh','B365AH')


def _first_pair(row,pairs):
    for a,b in pairs:
        x,y=pd.to_numeric(row.get(a),errors='coerce'),pd.to_numeric(row.get(b),errors='coerce')
        if np.isfinite(x) and np.isfinite(y) and x>1 and y>1: return float(x),float(y),f'{a}/{b}'
    return None

def load_raw():
    cfg=LEAGUES[LEAGUE]; frames=[]; allowed=set(TRAIN_SEASONS)|{VALIDATION_SEASON,TEST_SEASON}
    for code,season in cfg.historical_source.season_codes.items():
        if season not in allowed: continue
        r=requests.get(BASE.format(code=code,comp=cfg.historical_source.competition_code),timeout=60); r.raise_for_status()
        f=pd.read_csv(pd.io.common.BytesIO(r.content)); f['season']=season; frames.append(f)
    raw=pd.concat(frames,ignore_index=True); raw['match_date']=pd.to_datetime(raw['Date'],dayfirst=True,errors='coerce')
    raw=raw[(raw.match_date<=LATEST_ALLOWED_DATE)&raw.FTR.isin(RESULT_TO_INT)].copy()
    rows=[]
    from bookmaker_reconstruction_devig_v1 import _market_odds
    for _,r in raw.iterrows():
        one=_market_odds(r); total=_first_pair(r,TOTAL_PAIRS); ah=_first_pair(r,AH_PAIRS)
        if one is None: continue
        line=np.nan
        for c in AH_LINE:
            v=pd.to_numeric(r.get(c),errors='coerce')
            if np.isfinite(v): line=float(v); break
        rows.append({'season':r.season,'match_date':r.match_date,'result':r.FTR,
          'market_home_odds':one[0],'market_draw_odds':one[1],'market_away_odds':one[2],
          'total_over_odds':total[0] if total else np.nan,'total_under_odds':total[1] if total else np.nan,
          'ah_home_odds':ah[0] if ah else np.nan,'ah_away_odds':ah[1] if ah else np.nan,'ah_line':line})
    return pd.DataFrame(rows).sort_values('match_date').reset_index(drop=True)

def _binary_devig(a,b):
    ia,ib=1/a,1/b; s=ia+ib; return ia/s

def _features(f):
    m=_power_market(f); out=pd.DataFrame({'m_home':m[:,0],'m_draw':m[:,1],'m_away':m[:,2]})
    out['market_entropy']=-(m*np.log(np.clip(m,1e-15,1))).sum(axis=1)
    out['over25']=np.where(f.total_over_odds.notna()&f.total_under_odds.notna(),_binary_devig(f.total_over_odds,f.total_under_odds),np.nan)
    out['ah_home']=np.where(f.ah_home_odds.notna()&f.ah_away_odds.notna(),_binary_devig(f.ah_home_odds,f.ah_away_odds),np.nan)
    out['ah_line']=f.ah_line.to_numpy()
    return out

def evaluate(frame):
    tr=frame[frame.season.isin(TRAIN_SEASONS)].copy(); va=frame[frame.season==VALIDATION_SEASON].copy(); te=frame[frame.season==TEST_SEASON].copy()
    ytr=tr.result.map(RESULT_TO_INT).to_numpy(); yv=va.result.map(RESULT_TO_INT).to_numpy(); yt=te.result.map(RESULT_TO_INT).to_numpy()
    mv,mt=_power_market(va),_power_market(te); basev,baset=score_probabilities(yv,mv),score_probabilities(yt,mt)
    feature_sets={'ONE_X_TWO':['m_home','m_draw','m_away','market_entropy'], 'ONE_X_TWO_PLUS_TOTAL':['m_home','m_draw','m_away','market_entropy','over25'], 'ONE_X_TWO_PLUS_AH':['m_home','m_draw','m_away','market_entropy','ah_home','ah_line'], 'ONE_X_TWO_PLUS_TOTAL_AH':['m_home','m_draw','m_away','market_entropy','over25','ah_home','ah_line']}
    xtr,xv,xt=_features(tr),_features(va),_features(te); candidates=[]; models={}
    for name,cols in feature_sets.items():
        model=Pipeline([('imp',SimpleImputer(strategy='median')),('scale',StandardScaler()),('clf',LogisticRegression(C=0.1,max_iter=2000))])
        model.fit(xtr[cols],ytr); p=model.predict_proba(xv[cols]); s=score_probabilities(yv,p); candidates.append({'variant':name,**s}); models[name]=(model,cols)
    admiss=[c for c in candidates if c['brier']<basev['brier'] and c['log_loss']<basev['log_loss']]
    selected=min(admiss,key=lambda c:(c['log_loss'],c['brier'],c['variant'])) if admiss else None
    if selected:
        model,cols=models[selected['variant']]; pt=model.predict_proba(xt[cols]); st=score_probabilities(yt,pt)
    else: pt=mt.copy(); st=baset
    accepted=selected is not None and st['brier']<baset['brier'] and st['log_loss']<baset['log_loss']
    coverage={'total_train':int(tr.total_over_odds.notna().sum()),'total_validation':int(va.total_over_odds.notna().sum()),'total_test':int(te.total_over_odds.notna().sum()),'ah_train':int(tr.ah_home_odds.notna().sum()),'ah_validation':int(va.ah_home_odds.notna().sum()),'ah_test':int(te.ah_home_odds.notna().sum())}
    return {'experiment_id':EXPERIMENT_ID,'evidence_class':'HISTORICAL_TEMPORAL_OOT','research_only':True,'production_promotion':False,'betting_enabled':False,'result':'NO_BET','opened_2026_27_outcomes_used':False,'train_n':len(tr),'validation_n':len(va),'test_n':len(te),'coverage':coverage,'validation_power_market':basev,'validation_candidates':candidates,'selected_variant':selected,'test_power_market':baset,'test_candidate':st,'test_delta_brier':st['brier']-baset['brier'],'test_delta_log_loss':st['log_loss']-baset['log_loss'],'multimarket_accepted':bool(accepted),'active_mode':'MULTIMARKET' if accepted else 'POWER_MARKET_FALLBACK'}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=Path('artifacts/la_liga_multimarket_anchor_v5/report.json')); a=p.parse_args(); r=evaluate(load_raw()); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__': main()
