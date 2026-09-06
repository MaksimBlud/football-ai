"""Preregistered one-request Multi-Market corner capability probe.

Research-only diagnostic. The target fixture is fixed in code from a prior
zero-cost sampling plan, before any provider response is observed. Runtime
checks exact live fixture identity and a fresh zero-cost quota preflight before
one event-only corner request. The probe never writes Supabase or model files;
a positive result is durable only through its workflow artifact until reviewed.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from multi_market_policy import CORNER_SOURCE_READY_LEAGUES, HARD_RESERVE_CREDITS

OUTPUT = Path("artifacts/multi_market_corner_capability_probe.json")
SOURCE_TABLE = "odds_snapshots"
MAX_PAID_REQUESTS = 1
MAX_PAID_CREDITS = 2
TARGET = {
    "league": "LIGUE_1",
    "event_id": "b292d9e6b90eb73e0547ace2a44728e8",
    "home_team": "Troyes",
    "away_team": "Strasbourg",
    "commence_time_utc": "2026-09-06T13:00:00+00:00",
}
PROHIBITED_LEAGUES = frozenset({"EREDIVISIE", "RPL", "TURKEY_SUPER_LIG", "PRIMEIRA_LIGA"})
CORNER_MARKETS = ("alternate_totals_corners", "alternate_team_totals_corners")


def _int_header(value: Any, *, name: str) -> int:
    if value in (None, ""):
        raise RuntimeError(f"provider quota header missing: {name}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid provider quota header {name}: {value!r}") from exc


def _load_target(client: Any) -> dict[str, Any] | None:
    response = (
        client.table(SOURCE_TABLE)
        .select("league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc")
        .eq("league", TARGET["league"])
        .eq("event_id", TARGET["event_id"])
        .order("snapshot_time_utc", desc=True)
        .limit(1)
        .execute()
    )
    rows = list(getattr(response, "data", None) or [])
    return dict(rows[0]) if rows else None


def _verify_target(row: dict[str, Any], now_utc: datetime) -> None:
    for key in ("league", "event_id", "home_team", "away_team"):
        if str(row.get(key) or "") != TARGET[key]:
            raise RuntimeError(f"preregistered target mismatch for {key}")
    observed = pd.to_datetime(row.get("commence_time_utc"), utc=True, errors="coerce")
    expected = pd.to_datetime(TARGET["commence_time_utc"], utc=True)
    if pd.isna(observed) or observed != expected:
        raise RuntimeError("preregistered target kickoff mismatch")
    if pd.Timestamp(now_utc) >= expected:
        raise RuntimeError("preregistered target is no longer prospective")
    if TARGET["league"] not in set(CORNER_SOURCE_READY_LEAGUES):
        raise RuntimeError("preregistered target league is not outcome-source-ready")
    if TARGET["league"] in PROHIBITED_LEAGUES:
        raise RuntimeError("preregistered target league is prohibited for this probe")


def _market_evidence(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    requested = set(CORNER_MARKETS)
    markets: set[str] = set()
    books: set[str] = set()
    for bookmaker in payload.get("bookmakers", []) or []:
        if not isinstance(bookmaker, dict):
            continue
        book = str(bookmaker.get("key") or bookmaker.get("title") or "")
        for market in bookmaker.get("markets", []) or []:
            key = str(market.get("key") or "")
            if key in requested:
                markets.add(key)
                if book:
                    books.add(book)
    return sorted(markets), sorted(books)


def run_probe(
    client: Any,
    fetch_quota_fn: Callable[[], dict[str, Any]],
    fetch_event_fn: Callable[..., tuple[dict[str, Any], dict[str, Any]]],
    *,
    sport_key: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = now_utc or datetime.now(UTC)
    result: dict[str, Any] = {
        "schema_version": "MULTI_MARKET_CORNER_CAPABILITY_PROBE_V1",
        "research_only": True,
        "preregistered": True,
        "target": dict(TARGET),
        "max_paid_requests": MAX_PAID_REQUESTS,
        "max_paid_credits": MAX_PAID_CREDITS,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
        "writes_performed": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
        "status": "BLOCKED",
    }

    row = _load_target(client)
    if row is None:
        result["blocker"] = "PREREGISTERED_TARGET_NOT_FOUND"
        return result
    _verify_target(row, now_utc)
    result["target_verified"] = True

    quota_before = dict(fetch_quota_fn())
    remaining_before = _int_header(quota_before.get("remaining"), name="remaining")
    if remaining_before - MAX_PAID_CREDITS < HARD_RESERVE_CREDITS:
        result["blocker"] = "HARD_RESERVE_PROTECTED"
        result["quota_before"] = quota_before
        return result
    result["quota_before"] = quota_before

    payload, quota_after = fetch_event_fn(
        sport_key,
        TARGET["event_id"],
        regions="eu",
        markets=CORNER_MARKETS,
    )
    result["paid_provider_requests"] = 1
    actual_cost = _int_header(quota_after.get("last_cost"), name="last_cost")
    remaining_after = _int_header(quota_after.get("remaining"), name="remaining")
    if actual_cost < 0 or actual_cost > MAX_PAID_CREDITS:
        raise RuntimeError(f"probe provider cost outside cap: {actual_cost}")
    if remaining_after < HARD_RESERVE_CREDITS:
        raise RuntimeError("probe crossed hard reserve")
    result["paid_provider_credits"] = actual_cost
    result["quota_after"] = dict(quota_after)

    market_keys, bookmaker_keys = _market_evidence(dict(payload or {}))
    result["corner_market_keys"] = market_keys
    result["corner_bookmaker_keys"] = bookmaker_keys
    result["corner_bookmaker_count"] = len(bookmaker_keys)
    result["status"] = "CAPABILITY_CONFIRMED" if market_keys else "CAPABILITY_MISS"
    return result


def _write_result(result: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


def main() -> None:
    from database import supabase
    from league_config import get_league_config
    from multi_market_odds import fetch_event_markets, fetch_quota_status

    result: dict[str, Any] = {
        "schema_version": "MULTI_MARKET_CORNER_CAPABILITY_PROBE_V1",
        "research_only": True,
        "preregistered": True,
        "target": dict(TARGET),
        "max_paid_requests": MAX_PAID_REQUESTS,
        "max_paid_credits": MAX_PAID_CREDITS,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
        "writes_performed": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
        "status": "FAILED",
    }
    try:
        config = get_league_config(TARGET["league"])
        if not config.odds_api_sport_key:
            raise RuntimeError("preregistered target league has no Odds API sport key")
        result = run_probe(
            supabase,
            fetch_quota_status,
            fetch_event_markets,
            sport_key=config.odds_api_sport_key,
        )
    except Exception as exc:
        result["status"] = "FAILED"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:1000]
        _write_result(result)
        raise

    _write_result(result)
    if result["status"] == "BLOCKED":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
