"""Ligue 1 MARKET_ONLY live shadow."""
from pathlib import Path
import pandas as pd
from database import supabase
from league_market_shadow import MARKET_SHADOW_OUTPUT_COLUMNS,build_market_shadow as build_generic_market_shadow,prepare_snapshots as prepare_generic_snapshots,write_market_shadow_outputs
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
UPCOMING_PATH=LIGUE1_RUNTIME_CONFIG.paths.upcoming_fixtures;LATEST_OUTPUT=LIGUE1_RUNTIME_CONFIG.paths.market_shadow;HISTORY_OUTPUT=LIGUE1_RUNTIME_CONFIG.paths.market_history;OUTPUT_COLUMNS=MARKET_SHADOW_OUTPUT_COLUMNS
def fetch_ligue1_snapshots():
    r=supabase.table("odds_snapshots").select("league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team,home_odds,draw_odds,away_odds").eq("league","LIGUE_1").order("snapshot_time_utc",desc=False).limit(10000).execute();return pd.DataFrame(r.data or [])
def prepare_snapshots(snapshots):return prepare_generic_snapshots(snapshots,LIGUE1_RUNTIME_CONFIG)
def load_upcoming(path:Path=UPCOMING_PATH):
    f=pd.read_csv(path)
    if not (f["league"]=="LIGUE_1").all():raise ValueError("Upcoming file contains foreign league")
    f=f.copy();f["commence_time_utc"]=pd.to_datetime(f["commence_time_utc"],utc=True,errors="coerce");return f.dropna(subset=["event_id","home_team","away_team","commence_time_utc"])
def load_previous_history(path:Path=HISTORY_OUTPUT):
    if not path.exists():return pd.DataFrame(columns=OUTPUT_COLUMNS)
    f=pd.read_csv(path)
    if f.empty:return pd.DataFrame(columns=OUTPUT_COLUMNS)
    if not (f["league"]=="LIGUE_1").all():raise ValueError("History contains foreign league")
    for c in ("generated_at_utc","snapshot_time_utc"):f[c]=pd.to_datetime(f[c],utc=True,errors="coerce")
    return f
def build_market_shadow(upcoming,snapshots,previous_history=None):return build_generic_market_shadow(upcoming,snapshots,LIGUE1_RUNTIME_CONFIG,previous_history=previous_history)
def main():
    latest=build_market_shadow(load_upcoming(),fetch_ligue1_snapshots(),previous_history=load_previous_history());history=write_market_shadow_outputs(latest,latest_path=LATEST_OUTPUT,history_path=HISTORY_OUTPUT);print("Ligue 1 market shadow rows:",len(latest));print("history rows:",len(history));print("AI model used:",False);print("Structural V2 used:",False)
if __name__=="__main__":main()
