"""Persist Eredivisie MARKET_ONLY observations to generic durable storage."""
import numpy as np
import pandas as pd
from database import supabase
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from league_supabase_persistence import persist_observations

MARKET_COLUMNS=("market_home_probability","market_draw_probability","market_away_probability")

def load_market_shadow(): return pd.read_csv(EREDIVISIE_RUNTIME_CONFIG.paths.market_shadow)

def build_market_only_observations(shadow):
    required={"league","event_id","home_team","away_team","commence_time_utc","snapshot_time_utc","market_home_probability","market_draw_probability","market_away_probability","market_argmax","market_shadow_status","market_only"}
    missing=required-set(shadow.columns)
    if missing: raise ValueError("Market shadow missing columns: "+", ".join(sorted(missing)))
    work=shadow.copy()
    if not (work["league"].astype(str)=="EREDIVISIE").all(): raise ValueError("Market shadow contains non-Eredivisie rows")
    market_only=work["market_only"].astype(str).str.lower().map({"true":True,"false":False})
    if market_only.isna().any() or not market_only.all(): raise ValueError("Non-market-only Eredivisie shadow supplied")
    work=work.loc[work["market_shadow_status"]=="OK"].copy()
    if work.empty: raise ValueError("No valid Eredivisie market observations")
    work["snapshot_time_utc"]=pd.to_datetime(work["snapshot_time_utc"],utc=True,errors="coerce"); work["commence_time_utc"]=pd.to_datetime(work["commence_time_utc"],utc=True,errors="coerce")
    if work[["snapshot_time_utc","commence_time_utc"]].isna().any().any() or not (work["snapshot_time_utc"]<work["commence_time_utc"]).all(): raise ValueError("Invalid Eredivisie pre-kickoff timestamps")
    probability=work[list(MARKET_COLUMNS)].apply(pd.to_numeric,errors="coerce"); matrix=probability.to_numpy(dtype=float)
    if not np.isfinite(matrix).all() or not np.allclose(matrix.sum(axis=1),1.0,atol=1e-12): raise ValueError("Invalid Eredivisie market probabilities")
    result=pd.DataFrame({
        "league":work["league"].astype(str),"event_id":work["event_id"].astype(str),"home_team":work["home_team"].astype(str),"away_team":work["away_team"].astype(str),
        "snapshot_time_utc":work["snapshot_time_utc"],"commence_time_utc":work["commence_time_utc"],
        "market_home_probability":probability["market_home_probability"].astype(float),"market_draw_probability":probability["market_draw_probability"].astype(float),"market_away_probability":probability["market_away_probability"].astype(float),
        "shadow_home_probability":probability["market_home_probability"].astype(float),"shadow_draw_probability":probability["market_draw_probability"].astype(float),"shadow_away_probability":probability["market_away_probability"].astype(float),
        "market_argmax":work["market_argmax"].astype(str),"shadow_argmax":work["market_argmax"].astype(str),"structural_ready":False,"structural_score":None,"correction_enabled":False,"realized_correction_weight":0.0,"prediction_source":"MARKET_ONLY","pre_kickoff_valid":True,"research_only":True,
    })
    if result["event_id"].duplicated().any(): raise ValueError("Duplicate Eredivisie event_id in current market shadow")
    return result.reset_index(drop=True)

def persist_current_market_observations(): return persist_observations(supabase,build_market_only_observations(load_market_shadow()),EREDIVISIE_RUNTIME_CONFIG)
def main():
    metrics=persist_current_market_observations(); print("Eredivisie observations:",metrics); print("AI model used:",False); print("Structural V2 used:",False)
if __name__=="__main__": main()
