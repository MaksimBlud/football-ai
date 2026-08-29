"""Adaptive scheduler for Eredivisie h2h snapshots."""
from datetime import datetime,timezone
from database import supabase
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
import save_eredivisie_odds_snapshot as collector

TABLE="odds_snapshots"; NO_FUTURE_MATCH_COOLDOWN_HOURS=24

def parse_dt(value):
    if not value:return None
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def required_interval_hours(hours_to_match):
    if hours_to_match>72:return 12
    if hours_to_match>24:return 6
    if hours_to_match>6:return 4
    return 2

def should_collect(rows,now):
    if not rows:return True,"NO_EXISTING_EREDIVISIE_SNAPSHOTS"
    snapshot_times=[parse_dt(r.get("snapshot_time_utc")) for r in rows if r.get("snapshot_time_utc")]; snapshot_times=[d for d in snapshot_times if d]
    if not snapshot_times:return True,"NO_VALID_EREDIVISIE_SNAPSHOT_TIMES"
    last=max(snapshot_times); since=(now-last).total_seconds()/3600.0
    commence=[parse_dt(r.get("commence_time_utc")) for r in rows if r.get("commence_time_utc")]; future=[d for d in commence if d and d>now]
    if not future:
        due=since>=NO_FUTURE_MATCH_COOLDOWN_HOURS; return due,"NO_FUTURE_FIXTURES_COOLDOWN_EXPIRED" if due else "NO_FUTURE_FIXTURES_COOLDOWN"
    hours=(min(future)-now).total_seconds()/3600.0; interval=required_interval_hours(hours); return since>=interval,f"NEAREST_KICKOFF_INTERVAL_{interval}H"

def fetch_recent_eredivisie_snapshots():
    r=supabase.table(TABLE).select("snapshot_time_utc,commence_time_utc,league").eq("league","EREDIVISIE").order("snapshot_time_utc",desc=True).limit(500).execute(); return list(r.data or [])
def main():
    now=datetime.now(timezone.utc); rows=fetch_recent_eredivisie_snapshots(); due,reason=should_collect(rows,now)
    print("UTC now:",now.isoformat()); print("Eredivisie snapshot rows inspected:",len(rows)); print("decision:",reason); print("snapshot required:",due)
    if not due:print("The Odds API not called."); return
    collector.main()
if __name__=="__main__": main()
