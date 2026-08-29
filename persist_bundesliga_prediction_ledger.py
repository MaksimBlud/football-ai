"""Persist current Bundesliga MARKET_ONLY predictions to canonical ledger."""
import pandas as pd
from database import supabase
import persist_bundesliga_market_observations as observation_mirror
from league_prediction_ledger import TABLE,build_market_only_predictions,persist_predictions
OBSERVATION_TABLE="league_structural_v2_observations"
def _observation_key_map():
    r=supabase.table(OBSERVATION_TABLE).select("observation_key,event_id,snapshot_time_utc,league").eq("league","BUNDESLIGA").execute(); out={}
    for row in r.data or []:
        ts=pd.to_datetime(row["snapshot_time_utc"],utc=True,errors="coerce")
        if pd.isna(ts): continue
        out[(str(row["event_id"]),ts.isoformat())]=str(row["observation_key"])
    return out
def build_current_predictions():
    shadow=observation_mirror.load_market_shadow()
    if not (shadow["league"].astype(str)=="BUNDESLIGA").all(): raise ValueError("Foreign league in Bundesliga shadow")
    return build_market_only_predictions(shadow,observation_keys=_observation_key_map())
def persist_current_predictions():
    p=build_current_predictions()
    if not (p["prediction_mode"]=="MARKET_ONLY").all(): raise RuntimeError("Unexpected Bundesliga prediction mode")
    if p["structural_applied"].astype(bool).any(): raise RuntimeError("Unexpected Bundesliga Structural V2 activation")
    if p["observation_key"].isna().any(): raise RuntimeError("Unlinked Bundesliga observation_key")
    return persist_predictions(supabase,p)
def main(): print("Bundesliga prediction ledger:",persist_current_predictions()); print("Structural V2 used:",False)
if __name__=="__main__": main()
