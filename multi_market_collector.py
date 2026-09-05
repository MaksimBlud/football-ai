"""Quota-safe append-only Multi-Market V1 collector."""
from __future__ import annotations
import hashlib, json, os
from datetime import UTC, datetime, timedelta
import pandas as pd
from database import supabase
from league_config import get_league_config
from multi_market_card import build_multi_market_card
from multi_market_odds import EVENT_MARKETS, fetch_event_markets, fetch_quota_status
from multi_market_policy import (
    DEFAULT_MAX_CREDITS_PER_MANUAL_CYCLE,
    EVENT_REQUEST_MAX_CREDITS,
    HARD_RESERVE_CREDITS,
    MIN_COLLECTION_REMAINING_CREDITS,
)

TABLE = "league_multi_market_snapshots"
SOURCE_TABLE = "odds_snapshots"
LOOKAHEAD_HOURS = 24
MIN_INTERVAL_HOURS = 6
PAGE_SIZE = 1000
EVENT_ID_BATCH_SIZE = 100


def _utc(value): return pd.to_datetime(value, utc=True, errors="coerce")


def _request_cap(explicit=None):
    value = explicit if explicit is not None else os.getenv("MULTI_MARKET_MAX_PAID_REQUESTS")
    if value in (None, ""):
        return None
    cap = int(value)
    if cap < 1:
        raise ValueError("max paid requests must be >= 1")
    return cap


def _credit_cap(explicit=None):
    value = explicit if explicit is not None else os.getenv("MULTI_MARKET_MAX_PAID_CREDITS")
    if value in (None, ""):
        return DEFAULT_MAX_CREDITS_PER_MANUAL_CYCLE
    cap = int(value)
    if cap < 1:
        raise ValueError("max paid credits must be >= 1")
    return cap


def _int_quota(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
    """Return latest stored collection time for every requested event."""
    latest = {}
    for i in range(0, len(event_ids), EVENT_ID_BATCH_SIZE):
        event_id_batch = event_ids[i:i + EVENT_ID_BATCH_SIZE]
        start = 0
        while True:
            r = (supabase.table(TABLE).select("league,event_id,snapshot_time_utc").in_("event_id", event_id_batch)
                 .order("snapshot_time_utc", desc=True).range(start, start + PAGE_SIZE - 1).execute())
            rows = r.data or []
            for row in rows:
                ts = _utc(row["snapshot_time_utc"])
                if pd.isna(ts): continue
                key, pyts = (str(row["league"]), str(row["event_id"])), ts.to_pydatetime()
                if key not in latest or pyts > latest[key]: latest[key] = pyts
            if len(rows) < PAGE_SIZE:
                break
            start += PAGE_SIZE
    return latest


def _key(league, event_id, ts):
    return hashlib.sha256(f"{league}|{event_id}|{ts.isoformat()}|MULTI_MARKET_V1".encode()).hexdigest()


def collect(now_utc=None, *, max_paid_requests=None, max_paid_credits=None):
    now_utc = now_utc or datetime.now(UTC)
    request_cap = _request_cap(max_paid_requests)
    credit_cap = _credit_cap(max_paid_credits)
    quota_before = fetch_quota_status()  # /sports is zero-cost at the provider.
    remaining = _int_quota(quota_before.get("remaining"))
    if remaining is None or remaining < MIN_COLLECTION_REMAINING_CREDITS:
        return {
            "quota_blocked": True,
            "quota_before": quota_before,
            "provider_paid_requests": 0,
            "provider_paid_credits": 0,
            "max_paid_requests": request_cap,
            "max_paid_credits": credit_cap,
            "reason": f"remaining<{MIN_COLLECTION_REMAINING_CREDITS}",
        }

    events = load_future_events(now_utc)
    latest = load_latest_collection_times([str(e["event_id"]) for e in events])
    summary = {
        "quota_blocked": False,
        "quota_before": quota_before,
        "eligible_events": len(events),
        "fetched": 0,
        "provider_paid_requests": 0,
        "provider_paid_credits": 0,
        "inserted": 0,
        "skipped_recent": 0,
        "skipped_unsupported": 0,
        "quota_stop": False,
        "max_paid_requests": request_cap,
        "max_paid_credits": credit_cap,
        "request_cap_stop": False,
        "credit_cap_stop": False,
        "event_request_max_credits": EVENT_REQUEST_MAX_CREDITS,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
    }
    current_remaining = remaining
    for event in events:
        league, event_id = str(event["league"]), str(event["event_id"])
        config = get_league_config(league)
        if not config.odds_api_sport_key:
            summary["skipped_unsupported"] += 1; continue
        previous = latest.get((league, event_id))
        if previous and now_utc - previous < timedelta(hours=MIN_INTERVAL_HOURS):
            summary["skipped_recent"] += 1; continue
        if request_cap is not None and summary["provider_paid_requests"] >= request_cap:
            summary["request_cap_stop"] = True; break
        if summary["provider_paid_credits"] + EVENT_REQUEST_MAX_CREDITS > credit_cap:
            summary["credit_cap_stop"] = True; break
        if current_remaining - EVENT_REQUEST_MAX_CREDITS < HARD_RESERVE_CREDITS:
            summary["quota_stop"] = True; break

        payload, quota = fetch_event_markets(config.odds_api_sport_key, event_id, regions="eu", markets=EVENT_MARKETS)
        summary["fetched"] += 1
        summary["provider_paid_requests"] += 1
        last_cost = _int_quota(quota.get("last_cost"))
        if last_cost is None:
            # Fail conservatively if the provider omits billing headers.
            last_cost = EVENT_REQUEST_MAX_CREDITS
        summary["provider_paid_credits"] += last_cost
        after = _int_quota(quota.get("remaining"))
        if after is not None:
            current_remaining = after
        else:
            current_remaining -= last_cost

        snapshot_time, kickoff = datetime.now(UTC), _utc(event["commence_time_utc"])
        if not pd.isna(kickoff) and snapshot_time < kickoff.to_pydatetime():
            card = build_multi_market_card(payload)
            stored = {"schema_version": "MULTI_MARKET_V1", "research_only": True, "card": card,
                      "provider_market_keys": sorted({m.get("key") for b in payload.get("bookmakers", []) for m in b.get("markets", []) if m.get("key")}),
                      "bookmakers": payload.get("bookmakers", []), "quota": quota}
            row = {"snapshot_key": _key(league, event_id, snapshot_time), "league": league, "event_id": event_id,
                   "home_team": str(event.get("home_team") or payload.get("home_team") or ""),
                   "away_team": str(event.get("away_team") or payload.get("away_team") or ""),
                   "kickoff_utc": kickoff.isoformat(), "snapshot_time_utc": snapshot_time.isoformat(),
                   "payload": stored, "provider": "THE_ODDS_API"}
            supabase.table(TABLE).insert(row).execute(); summary["inserted"] += 1

        if current_remaining < HARD_RESERVE_CREDITS:
            summary["quota_stop"] = True; break
    return summary


def main(): print(json.dumps(collect(), indent=2, default=str))
if __name__ == "__main__": main()
