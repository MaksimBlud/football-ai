"""Quota-safe append-only Multi-Market V1 collector.

Reads canonical future event identities from existing odds_snapshots, fetches only
additional event-level markets, and inserts immutable snapshots into the dedicated
research table. It never updates/deletes rows and never touches prediction models.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pandas as pd

from database import supabase
from league_config import get_league_config
from multi_market_card import build_multi_market_card
from multi_market_odds import EVENT_MARKETS, fetch_event_markets

TABLE = "league_multi_market_snapshots"
SOURCE_TABLE = "odds_snapshots"
LOOKAHEAD_HOURS = 24
MIN_INTERVAL_HOURS = 6
MIN_REQUESTS_REMAINING = 500
PAGE_SIZE = 1000


def _parse_utc(value):
    return pd.to_datetime(value, utc=True, errors="coerce")


def load_future_events(now_utc: datetime) -> list[dict]:
    rows = []
    start = 0
    while True:
        response = (
            supabase.table(SOURCE_TABLE)
            .select("league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc")
            .gte("commence_time_utc", now_utc.isoformat())
            .lte("commence_time_utc", (now_utc + timedelta(hours=LOOKAHEAD_HOURS)).isoformat())
            .order("snapshot_time_utc", desc=True)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    frame["snapshot_time_utc"] = pd.to_datetime(frame["snapshot_time_utc"], utc=True, errors="coerce")
    frame["commence_time_utc"] = pd.to_datetime(frame["commence_time_utc"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["league", "event_id", "commence_time_utc", "snapshot_time_utc"])
    # Latest canonical source row for each provider event id. A rescheduled event is
    # represented by the most recently observed kickoff revision.
    frame = frame.sort_values("snapshot_time_utc").groupby(["league", "event_id"], as_index=False).tail(1)
    frame = frame[(frame["commence_time_utc"] > pd.Timestamp(now_utc)) & (frame["commence_time_utc"] <= pd.Timestamp(now_utc + timedelta(hours=LOOKAHEAD_HOURS)))]
    return frame.sort_values("commence_time_utc").to_dict("records")


def load_latest_collection_times(event_ids: list[str]) -> dict[tuple[str, str], datetime]:
    if not event_ids:
        return {}
    latest = {}
    # PostgREST IN lists are intentionally chunked.
    for i in range(0, len(event_ids), 100):
        chunk = event_ids[i:i + 100]
        response = (
            supabase.table(TABLE)
            .select("league,event_id,snapshot_time_utc")
            .in_("event_id", chunk)
            .order("snapshot_time_utc", desc=True)
            .execute()
        )
        for row in response.data or []:
            key = (str(row["league"]), str(row["event_id"]))
            ts = _parse_utc(row["snapshot_time_utc"])
            if pd.isna(ts):
                continue
            current = latest.get(key)
            pyts = ts.to_pydatetime()
            if current is None or pyts > current:
                latest[key] = pyts
    return latest


def _snapshot_key(league: str, event_id: str, snapshot_time_utc: datetime) -> str:
    raw = f"{league}|{event_id}|{snapshot_time_utc.isoformat()}|MULTI_MARKET_V1"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def collect(now_utc: datetime | None = None) -> dict:
    now_utc = now_utc or datetime.now(UTC)
    events = load_future_events(now_utc)
    try:
        latest = load_latest_collection_times([str(e["event_id"]) for e in events])
    except Exception as exc:
        # Missing dedicated schema is an activation blocker, not a reason to spend API quota.
        raise RuntimeError(f"Multi-market schema not ready: {exc}") from exc

    summary = {"eligible_events": len(events), "fetched": 0, "inserted": 0, "skipped_recent": 0, "skipped_unsupported": 0, "quota_stop": False}
    for event in events:
        league = str(event["league"])
        event_id = str(event["event_id"])
        config = get_league_config(league)
        if not config.odds_api_sport_key:
            summary["skipped_unsupported"] += 1
            continue
        previous = latest.get((league, event_id))
        if previous is not None and now_utc - previous < timedelta(hours=MIN_INTERVAL_HOURS):
            summary["skipped_recent"] += 1
            continue

        payload, quota = fetch_event_markets(config.odds_api_sport_key, event_id, regions="eu", markets=EVENT_MARKETS)
        summary["fetched"] += 1
        remaining = quota.get("remaining")
        if remaining is not None and int(remaining) < MIN_REQUESTS_REMAINING:
            summary["quota_stop"] = True
            break

        snapshot_time = datetime.now(UTC)
        kickoff = _parse_utc(event["commence_time_utc"])
        if pd.isna(kickoff) or snapshot_time >= kickoff.to_pydatetime():
            continue
        card = build_multi_market_card(payload)
        stored_payload = {
            "schema_version": "MULTI_MARKET_V1",
            "research_only": True,
            "card": card,
            "provider_market_keys": sorted({m.get("key") for b in payload.get("bookmakers", []) for m in b.get("markets", []) if m.get("key")}),
            "bookmakers": payload.get("bookmakers", []),
            "quota": quota,
        }
        row = {
            "snapshot_key": _snapshot_key(league, event_id, snapshot_time),
            "league": league,
            "event_id": event_id,
            "home_team": str(event.get("home_team") or payload.get("home_team") or ""),
            "away_team": str(event.get("away_team") or payload.get("away_team") or ""),
            "kickoff_utc": kickoff.isoformat(),
            "snapshot_time_utc": snapshot_time.isoformat(),
            "payload": stored_payload,
            "provider": "THE_ODDS_API",
        }
        supabase.table(TABLE).insert(row).execute()
        summary["inserted"] += 1
    return summary


def main():
    print(json.dumps(collect(), indent=2, default=str))


if __name__ == "__main__":
    main()
