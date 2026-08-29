"""Export future Bundesliga fixtures from existing odds snapshots."""
from datetime import datetime
import pandas as pd
from database import supabase
from league_fixture_export import prepare_upcoming_fixtures as prepare_generic
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
OUTPUT_PATH=BUNDESLIGA_RUNTIME_CONFIG.paths.upcoming_fixtures
DB_COLUMNS="league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team"
def normalize_bundesliga_team(value):
    value=str(value).strip(); return BUNDESLIGA_RUNTIME_CONFIG.aliases.get(value,value)
def fetch_bundesliga_snapshots():
    r=supabase.table("odds_snapshots").select(DB_COLUMNS).eq("league","BUNDESLIGA").order("snapshot_time_utc",desc=True).limit(10000).execute(); return pd.DataFrame(r.data or [])
def prepare_upcoming_fixtures(snapshots,now:datetime|None=None):
    return prepare_generic(snapshots,BUNDESLIGA_RUNTIME_CONFIG,normalize_team=normalize_bundesliga_team,now=now)
def main():
    s=BUNDESLIGA_RUNTIME_CONFIG.structural_v2
    if s.calibration_status!="CALIBRATION_REQUIRED" or s.structural_alpha is not None or s.edge_threshold is not None: raise RuntimeError("Unexpected Bundesliga Structural V2 state")
    upcoming=prepare_upcoming_fixtures(fetch_bundesliga_snapshots())
    if upcoming.empty: raise RuntimeError("No future Bundesliga fixtures found")
    OUTPUT_PATH.parent.mkdir(parents=True,exist_ok=True); upcoming.to_csv(OUTPUT_PATH,index=False)
    print("Bundesliga fixtures:",len(upcoming)); print("Structural V2 used:",False)
if __name__=="__main__": main()
