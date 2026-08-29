"""Bundesliga h2h odds snapshot collector using The Odds API EU region."""
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from fixture_identity import require_league
from save_odds_snapshot import DB_COLUMNS,DB_CONFLICT_TARGET,SUPABASE_TABLE
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from the_odds_service import aggregate_event_h2h,get_h2h_odds

REGION="eu"; LEAGUE="BUNDESLIGA"; SPORT_KEY=BUNDESLIGA_RUNTIME_CONFIG.identity.odds_sport_key
OUTPUT=Path("data/odds_snapshots/bundesliga_h2h_snapshots.csv")

def build_snapshot_rows(events,snapshot_time_utc):
    rows=[]
    for event in events:
        a=aggregate_event_h2h(event)
        if a is None: continue
        rows.append({"league":LEAGUE,"snapshot_time_utc":snapshot_time_utc,"event_id":a["event_id"],"commence_time_utc":a["commence_time"],"home_team":a["home_team"],"away_team":a["away_team"],"bookmakers_count":a["bookmakers_count"],"home_odds":a["home_odds"],"draw_odds":a["draw_odds"],"away_odds":a["away_odds"],"home_probability":a["home_probability"],"draw_probability":a["draw_probability"],"away_probability":a["away_probability"]})
    return pd.DataFrame(rows,columns=DB_COLUMNS)

def merge_local_history(old_df,new_df):
    old_df=require_league(old_df,legacy_epl=False); new_df=require_league(new_df,legacy_epl=False)
    for frame in (old_df,new_df):
        if not frame.empty and not frame["league"].eq(LEAGUE).all(): raise ValueError("Bundesliga snapshot contains foreign league")
    return pd.concat([old_df,new_df],ignore_index=True,sort=False).drop_duplicates(subset=["league","snapshot_time_utc","event_id"],keep="last").sort_values(["snapshot_time_utc","commence_time_utc","home_team"]).reset_index(drop=True)

def save_local_history(new_df,output_path=OUTPUT):
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    old=pd.read_csv(output_path) if output_path.exists() else pd.DataFrame(columns=DB_COLUMNS)
    combined=merge_local_history(old,new_df); combined.to_csv(output_path,index=False); return combined

def build_db_rows(frame):
    frame=require_league(frame,legacy_epl=False)
    if not frame.empty and not frame["league"].eq(LEAGUE).all(): raise ValueError("Foreign Bundesliga payload")
    return frame[DB_COLUMNS].where(pd.notna(frame[DB_COLUMNS]),None).to_dict(orient="records")

def save_supabase(frame,supabase_client=None):
    if supabase_client is None:
        from database import supabase as supabase_client
    response=supabase_client.table(SUPABASE_TABLE).upsert(build_db_rows(frame),on_conflict=DB_CONFLICT_TARGET).execute()
    return len(response.data or [])

def main():
    result=get_h2h_odds(SPORT_KEY,regions=REGION); now=datetime.now(timezone.utc).isoformat(); frame=build_snapshot_rows(result["events"],now)
    if frame.empty: raise RuntimeError("The Odds API returned no usable Bundesliga h2h odds")
    history=save_local_history(frame); persisted=save_supabase(frame)
    print("BUNDESLIGA ODDS SNAPSHOT SAVED"); print("snapshot rows:",len(frame)); print("local history rows:",len(history)); print("Supabase response rows:",persisted); print("quota:",result["quota"]); print("Structural V2 used:",False); print("production model used:",False)
if __name__=="__main__": main()
