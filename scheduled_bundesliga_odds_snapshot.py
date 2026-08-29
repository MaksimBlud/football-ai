"""Adaptive scheduler for Bundesliga h2h snapshots."""
from datetime import datetime,timezone
from database import supabase
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
import save_bundesliga_odds_snapshot as collector
TABLE="odds_snapshots"; NO_FUTURE_MATCH_COOLDOWN_HOURS=24
def parse_dt(value):
    if not value:return None
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00")); return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
def required_interval_hours(hours_to_match):
    if hours_to_match>72:return 12
    if hours_to_match>24:return 6
    if hours_to_match>6:return 4
    return 2
def should_collect(rows,now):
    if not rows:return True,"NO_EXISTING_BUNDESLIGA_SNAPSHOTS"
    times=[parse_dt(r.get("snapshot_time_utc")) for r in rows if r.get("snapshot_time_utc")]; times=[x for x in times if x]
    if not times:return True,"NO_VALID_BUNDESLIGA_SNAPSHOT_TIMES"
    since=(now-max(times)).total_seconds()/3600
    future=[parse_dt(r.get("commence_time_utc")) for r in rows if r.get("commence_time_utc")]; future=[x for x in future if x and x>now]
    if not future:return since>=24,"NO_FUTURE_FIXTURES"
    interval=required_interval_hours((min(future)-now).total_seconds()/3600); return since>=interval,f"NEAREST_KICKOFF_INTERVAL_{interval}H"
def fetch_recent_bundesliga_snapshots():
    r=supabase.table(TABLE).select("snapshot_time_utc,commence_time_utc,league").eq("league","BUNDESLIGA").order("snapshot_time_utc",desc=True).limit(500).execute(); return list(r.data or [])
def main():
    now=datetime.now(timezone.utc); rows=fetch_recent_bundesliga_snapshots(); due,reason=should_collect(rows,now)
    print("decision:",reason); print("snapshot required:",due)
    if due: collector.main()
    else: print("The Odds API not called.")
if __name__=="__main__": main()
