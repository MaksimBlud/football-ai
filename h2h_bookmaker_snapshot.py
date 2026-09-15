"""Research-only bookmaker-level H2H snapshot persistence.

This module never calls The Odds API. It only persists bookmaker quotes already
present in an H2H response fetched by an existing collector, so enabling this
capture adds zero provider requests and zero provider credits.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from the_odds_service import aggregate_event_h2h


TABLE = "league_h2h_bookmaker_snapshots"
SCHEMA_VERSION = "H2H_BOOKMAKER_V1"
PROVIDER = "THE_ODDS_API"


def _utc(value) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_json(payload: dict) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _snapshot_key(league: str, event_id: str, snapshot_time: datetime) -> str:
    identity = f"{league}|{event_id}|{snapshot_time.isoformat()}|{SCHEMA_VERSION}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _normalized_bookmakers(aggregated: dict) -> list[dict]:
    rows = []
    for bookmaker in aggregated.get("bookmakers") or []:
        rows.append(
            {
                "bookmaker_key": bookmaker.get("bookmaker_key"),
                "bookmaker_title": bookmaker.get("bookmaker_title"),
                "last_update": bookmaker.get("last_update"),
                "home_odds": float(bookmaker["home_odds"]),
                "draw_odds": float(bookmaker["draw_odds"]),
                "away_odds": float(bookmaker["away_odds"]),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("bookmaker_key") or ""),
            str(row.get("bookmaker_title") or ""),
            str(row.get("last_update") or ""),
        ),
    )


def build_h2h_bookmaker_rows(
    events,
    *,
    league: str,
    snapshot_time_utc: str,
) -> list[dict]:
    """Build strict pre-kickoff bookmaker-level rows without external writes."""

    league = str(league or "").strip()
    if not league:
        raise ValueError("league must be non-empty")

    snapshot_time = _utc(snapshot_time_utc)
    if snapshot_time is None:
        raise ValueError("snapshot_time_utc must be a valid timestamp")

    rows = []
    for event in events:
        aggregated = aggregate_event_h2h(event)
        if aggregated is None:
            continue

        event_id = str(aggregated.get("event_id") or "").strip()
        kickoff = _utc(aggregated.get("commence_time"))
        if not event_id or kickoff is None or snapshot_time >= kickoff:
            continue

        bookmakers = _normalized_bookmakers(aggregated)
        if not bookmakers:
            continue

        aggregate = {
            "bookmakers_count": int(aggregated["bookmakers_count"]),
            "home_odds": float(aggregated["home_odds"]),
            "draw_odds": float(aggregated["draw_odds"]),
            "away_odds": float(aggregated["away_odds"]),
            "home_probability": float(aggregated["home_probability"]),
            "draw_probability": float(aggregated["draw_probability"]),
            "away_probability": float(aggregated["away_probability"]),
        }
        payload = {
            "schema_version": SCHEMA_VERSION,
            "research_only": True,
            "provider_market_keys": ["h2h"],
            "bookmakers": bookmakers,
            "aggregate": aggregate,
        }
        payload_text = _canonical_json(payload)

        rows.append(
            {
                "snapshot_key": _snapshot_key(league, event_id, snapshot_time),
                "league": league,
                "event_id": event_id,
                "home_team": str(aggregated.get("home_team") or ""),
                "away_team": str(aggregated.get("away_team") or ""),
                "kickoff_utc": kickoff.isoformat(),
                "snapshot_time_utc": snapshot_time.isoformat(),
                "provider": PROVIDER,
                "raw_bookmakers_count": len(event.get("bookmakers") or []),
                "accepted_bookmakers_count": len(bookmakers),
                "payload": payload,
                "payload_sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
            }
        )

    return rows


def save_h2h_bookmaker_snapshots(
    events,
    *,
    league: str,
    snapshot_time_utc: str,
    supabase_client=None,
) -> int:
    """Insert bookmaker-level rows using the caller's already-fetched events."""

    rows = build_h2h_bookmaker_rows(
        events,
        league=league,
        snapshot_time_utc=snapshot_time_utc,
    )
    if not rows:
        return 0

    if supabase_client is None:
        from database import supabase as supabase_client

    response = supabase_client.table(TABLE).insert(rows).execute()
    return len(response.data or [])
