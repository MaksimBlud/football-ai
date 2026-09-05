"""Quota-safe append-only Multi-Market V1 collector."""
from __future__ import annotations
import hashlib, json
from datetime import UTC, datetime, timedelta
import pandas as pd
from database import supabase
from league_config import get_league_config
from multi_market_card import build_multi_market_card
from multi_market_odds import EVENT_MARKETS, fetch_event_markets, fetch_quota_status
from multi_market_policy import HARD_RESERVE_REQUESTS, START_MIN_REQUESTS_REMAINING

TABLE = "league_multi_market_snapshots"
SOURCE_TABLE = "odds_snapshots"
LOOKAHEAD_HOURS = 24
MIN_INTERVAL_HOURS = 6
PAGE_SIZE = 1000


def _utc(value): return pd.to_datetime(value, utc=True, errors="coerce")


def load_future_events(now_utc):
    rows, start = [], 0
    while True:
        r = (supabase.table(SOURCE_TABLE).select("league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc")
             .gte("commence_time_utc", now_utc.isoformat()).lte("commence_time_utc", (now_utc + timedelta(hours=LOOKAHEAD_HOURS)).isoformat())
             .order("snapshot_time_utc", desc=True).range(start, start + PAGE_SIZE - 1).execute())
        batch = r.data or []; rows.extend(batch)
        if len(batch) < PAGE_SIZE: break
        start += PAGE_SIZE
    if not rows: return []
    f = pd.DataFrame(rows)
    f["snapshot_time_utc"] = pd.to_datetime(f["snapshot_time_utc"], utc=True, errors="coerce")
    f["commence_time_utc"] = pd.to_datetime(f["commence_time_utc"], utc=True, errors="coerce")
    f = f.dropna(subset=["league", "event_id", "commence_time_utc", "snapshot_time_utc"])
    f = f.sort_values("snapshot_time_utc").groupby(["league", "event_id"], as_index=False).tail(1)
    f = f[(f["commence_time_utc"] > pd.Timestamp(now_utc)) & (f["commence_time_utc"] <= pd.Timestamp(now_utc + timedelta(hours=LOOKAHEAD_HOURS)))]
    return f.sort_values("commence_time_utc").to_dict("records")


def load_latest_collection_times(event_ids):
    latest = {}
    for i in range(0, len(event_ids), 100):
        r = (supabase.table(TABLE).select("league,event_id,snapshot_time_utc").in_("event_id", event_ids[i:i+100])
             .order("snapshot_time_utc", desc=True).execute())
        for row in r.data or []:
            ts = _utc(row["snapshot_time_utc"])
            if pd.isna(ts): continue
            key, pyts = (str(row["league"]), str(row["event_id"])), ts.to_pydatetime()
            if key not in latest or pyts > latest[key]: latest[key] = pyts
    return latest


def _key(league, event_id, ts):
    return hashlib.sha256(f"{league}|{event_id}|{ts.isoformat()}|MULTI_MARKET_V1".encode()).hexdigest()


def collect(now_utc=None):
    now_utc = now_utc or datetime.now(UTC)
    quota = fetch_quota_status()
    remaining = quota.get("remaining")
    if remaining is None:
        raise RuntimeError("Provider quota remaining header unavailable")
    if int(remaining) < START_MIN_REQUESTS_REMAINING:
        return {"status": "BLOCKED_QUOTA", "quota": quota, "inserted": 0, "unchanged": 0, "skipped_recent": 0, "skipped_quota": 0}
    events = load_future_events(now_utc)
    latest = load_latest_collection_times([str(e["event_id"]) for e in events]) if events else {}
    summary = {"status": "OK", "quota_start": quota, "inserted": 0, "unchanged": 0, "skipped_recent": 0, "skipped_quota": 0, "events_considered": len(events)}
    for e in events:
        league, event_id = str(e["league"]), str(e["event_id"])
        last = latest.get((league, event_id))
        if last and now_utc - last < timedelta(hours=MIN_INTERVAL_HOURS):
            summary["skipped_recent"] += 1; continue
        current = fetch_quota_status(); rem = current.get("remaining")
        if rem is None or int(rem) <= HARD_RESERVE_REQUESTS:
            summary["skipped_quota"] += 1; summary["status"] = "STOPPED_HARD_RESERVE"; break
        config = get_league_config(league)
        payload, after = fetch_event_markets(config.identity.odds_sport_key, event_id, regions="eu")
        if int(after.get("remaining") or 0) <= HARD_RESERVE_REQUESTS:
            summary["status"] = "STOPPED_HARD_RESERVE_AFTER_REQUEST"
        card = build_multi_market_card(payload)
        snapshot_time = datetime.now(UTC)
        kickoff = _utc(e["commence_time_utc"])
        if pd.isna(kickoff) or snapshot_time >= kickoff.to_pydatetime():
            continue
        row = {
            "snapshot_key": _key(league, event_id, snapshot_time),
            "league": league,
            "event_id": event_id,
            "home_team": str(e["home_team"]),
            "away_team": str(e["away_team"]),
            "kickoff_utc": kickoff.isoformat(),
            "snapshot_time_utc": snapshot_time.isoformat(),
            "payload": {
                "schema_version": "MULTI_MARKET_V1",
                "research_only": True,
                "quota": after,
                "card": card,
            },
            "provider": "THE_ODDS_API",
        }
        existing = supabase.table(TABLE).select("payload").eq("snapshot_key", row["snapshot_key"]).limit(1).execute().data or []
        if existing:
            if json.dumps(existing[0]["payload"], sort_keys=True) != json.dumps(row["payload"], sort_keys=True):
                raise RuntimeError("Immutable Multi-Market snapshot conflict")
            summary["unchanged"] += 1
        else:
            supabase.table(TABLE).insert(row).execute(); summary["inserted"] += 1
        if summary["status"].startswith("STOPPED_"):
            break
    return summary


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2, default=str))
