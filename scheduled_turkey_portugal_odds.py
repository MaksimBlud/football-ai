"""Adaptive, quota-safe h2h snapshot scheduler for Turkey and Portugal."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import requests
from config import THE_ODDS_API_KEY
from database import supabase
from the_odds_service import BASE_URL
from turkey_portugal_market_only import collect_snapshot, config_for

QUOTA_START_FLOOR=500
NO_FUTURE_MATCH_COOLDOWN_HOURS=24

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

def should_collect(rows, now):
    if not rows:return True,"NO_EXISTING_SNAPSHOTS"
    times=[parse_dt(r.get("snapshot_time_utc")) for r in rows if r.get("snapshot_time_utc")]; times=[x for x in times if x]
    if not times:return True,"NO_VALID_SNAPSHOT_TIMES"
    since=(now-max(times)).total_seconds()/3600.0
    starts=[parse_dt(r.get("commence_time_utc")) for r in rows if r.get("commence_time_utc")]; future=[x for x in starts if x and x>now]
    if not future:
        due=since>=NO_FUTURE_MATCH_COOLDOWN_HOURS; return due,"NO_FUTURE_FIXTURES_COOLDOWN_EXPIRED" if due else "NO_FUTURE_FIXTURES_COOLDOWN"
    hours=(min(future)-now).total_seconds()/3600.0; interval=required_interval_hours(hours)
    return since>=interval,f"NEAREST_KICKOFF_INTERVAL_{interval}H"

def zero_cost_quota():
    if not THE_ODDS_API_KEY: raise RuntimeError("THE_ODDS_API_KEY missing")
    r=requests.get(f"{BASE_URL}/sports",params={"apiKey":THE_ODDS_API_KEY},timeout=30); r.raise_for_status()
    return {"remaining":int(r.headers.get("x-requests-remaining") or 0),"last_cost":int(r.headers.get("x-requests-last") or 0)}

def recent_rows(league):
    r=supabase.table("odds_snapshots").select("snapshot_time_utc,commence_time_utc,league").eq("league",league).order("snapshot_time_utc",desc=True).limit(500).execute()
    return list(r.data or [])

def run(league):
    config_for(league); quota=zero_cost_quota()
    if quota["last_cost"]!=0: raise RuntimeError("Expected zero-cost sports quota preflight")
    if quota["remaining"]<QUOTA_START_FLOOR:
        print(f"{league}=BLOCKED_LOW_QUOTA remaining={quota['remaining']} floor={QUOTA_START_FLOOR}; paid requests=0"); return {"status":"BLOCKED_LOW_QUOTA","quota":quota}
    now=datetime.now(timezone.utc); due,reason=should_collect(recent_rows(league),now)
    print("decision:",reason,"required:",due)
    if not due:return {"status":"NOT_DUE","quota":quota}
    out=collect_snapshot(league,persist=True); print(f"{league} MARKET_ONLY snapshot rows={out['rows']} persisted={out['persisted']}"); return {"status":"COLLECTED","quota":out["quota"]}

def main():
    p=argparse.ArgumentParser(); p.add_argument("league",choices=["TURKEY_SUPER_LIG","PRIMEIRA_LIGA"]); a=p.parse_args(); run(a.league)
if __name__=="__main__": main()
