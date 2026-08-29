"""Persist Ligue 1 MARKET_ONLY observations to the generic durable store."""
import numpy as np
import pandas as pd
from database import supabase
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from league_supabase_persistence import persist_observations
MARKET_COLUMNS=("market_home_probability","market_draw_probability","market_away_probability")
def load_market_shadow():return pd.read_csv(LIGUE1_RUNTIME_CONFIG.paths.market_shadow)
def build_market_only_observations(shadow):
    work=shadow.copy();required={"league","event_id","home_team","away_team","commence_time_utc","snapshot_time_utc","market_home_probability","market_draw_probability","market_away_probability","market_argmax","market_shadow_status","market_only"};missing=required-set(work.columns)
    if missing:raise ValueError("Market shadow missing columns: "+", ".join(sorted(missing)))
    if not (work["league"].astype(str)=="LIGUE_1").all():raise ValueError("Foreign league in Ligue 1 shadow")
    mo=work["market_only"].astype(str).str.lower().map({"true":True,"false":False})
    if mo.isna().any() or not mo.all():raise ValueError("Ligue 1 shadow must be MARKET_ONLY")
    work=work.loc[work["market_shadow_status"]=="OK"].copy()
    if work.empty:raise ValueError("No valid Ligue 1 market observations")
    work["snapshot_time_utc"]=pd.to_datetime(work["snapshot_time_utc"],utc=True,errors="coerce");work["commence_time_utc"]=pd.to_datetime(work["commence_time_utc"],utc=True,errors="coerce")
    if work[["snapshot_time_utc","commence_time_utc"]].isna().any().any() or not (work["snapshot_time_utc"]<work["commence_time_utc"]).all():raise ValueError("Ligue 1 observation must be pre-kickoff")
    p=work[list(MARKET_COLUMNS)].apply(pd.to_numeric,errors="coerce");m=p.to_numpy(dtype=float)
    if not np.isfinite(m).all() or not np.allclose(m.sum(axis=1),1.0,atol=1e-12):raise ValueError("Invalid Ligue 1 market probabilities")
    out=pd.DataFrame({"league":work["league"].astype(str),"event_id":work["event_id"].astype(str),"home_team":work["home_team"].astype(str),"away_team":work["away_team"].astype(str),"snapshot_time_utc":work["snapshot_time_utc"],"commence_time_utc":work["commence_time_utc"],"market_home_probability":p[MARKET_COLUMNS[0]].astype(float),"market_draw_probability":p[MARKET_COLUMNS[1]].astype(float),"market_away_probability":p[MARKET_COLUMNS[2]].astype(float),"shadow_home_probability":p[MARKET_COLUMNS[0]].astype(float),"shadow_draw_probability":p[MARKET_COLUMNS[1]].astype(float),"shadow_away_probability":p[MARKET_COLUMNS[2]].astype(float),"market_argmax":work["market_argmax"].astype(str),"shadow_argmax":work["market_argmax"].astype(str),"structural_ready":False,"structural_score":None,"correction_enabled":False,"realized_correction_weight":0.0,"prediction_source":"MARKET_ONLY","pre_kickoff_valid":True,"research_only":True})
    if out["event_id"].duplicated().any():raise ValueError("Duplicate Ligue 1 event_id")
    return out.reset_index(drop=True)
def persist_current_market_observations():return persist_observations(supabase,build_market_only_observations(load_market_shadow()),LIGUE1_RUNTIME_CONFIG)
def main():print("Ligue 1 observations:",persist_current_market_observations());print("Structural V2 used:",False)
if __name__=="__main__":main()
