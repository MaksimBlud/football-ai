"""One-shot guarded live canary for the first prospective Multi-Market sample.

This entry point is intentionally stricter than the recurring collector:
- the snapshot table must still be empty, so a rerun fails before provider spend;
- a fresh zero-cost planner must fit two fixtures from one outcome-ready league
  inside the 3-request / 6-credit canary envelope;
- the collector is called with explicit caps and the hard reserve remains intact;
- exactly two unique prospective snapshots must be written and contain real
  corner-market/bookmaker payloads.

It never enables scheduled collection, settlement, evaluation, or promotion.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from multi_market_collector import TABLE, collect
from multi_market_policy import CORNER_SOURCE_READY_LEAGUES, HARD_RESERVE_CREDITS
from multi_market_sampling_plan import build_live_plan

OUTPUT = Path("artifacts/multi_market_first_paid_canary.json")
MAX_PAID_REQUESTS = 3
MAX_PAID_CREDITS = 6
EXPECTED_EVENTS = 2
PROHIBITED_LEAGUES = frozenset({"RPL", "TURKEY_SUPER_LIG"})
CORNER_MARKETS = frozenset({"alternate_totals_corners", "alternate_team_totals_corners"})


def _count_snapshots(client: Any) -> int:
    response = client.table(TABLE).select("snapshot_key", count="exact").limit(0).execute()
    count = getattr(response, "count", None)
    if count is None:
        raise RuntimeError("snapshot baseline count unavailable")
    return int(count)


def _load_canary_rows(client: Any) -> list[dict[str, Any]]:
    response = (
        client.table(TABLE)
        .select("snapshot_key,league,event_id,home_team,away_team,kickoff_utc,snapshot_time_utc,payload,provider")
        .order("snapshot_time_utc")
        .limit(EXPECTED_EVENTS + 1)
        .execute()
    )
    return [dict(row) for row in (getattr(response, "data", None) or [])]


def _validate_plan(plan: dict[str, Any]) -> tuple[str, list[str]]:
    if plan.get("read_only") is not True or plan.get("writes_performed") is not False:
        raise RuntimeError("planner lost read-only contract")
    if int(plan.get("paid_provider_requests") or 0) != 0 or int(plan.get("paid_provider_credits") or 0) != 0:
        raise RuntimeError("planner unexpectedly consumed paid provider quota")
    if plan.get("hard_reserve_preserved") is not True:
        raise RuntimeError("planner does not preserve hard reserve")
    if int(plan.get("worst_case_remaining_credits") or -1) < HARD_RESERVE_CREDITS:
        raise RuntimeError("planner worst-case remaining crosses hard reserve")
    events = list(plan.get("events") or [])
    if len(events) < EXPECTED_EVENTS:
        raise RuntimeError("fewer than two canary fixtures fit the safe envelope")
    first_two = events[:EXPECTED_EVENTS]
    leagues = [str(row.get("league") or "") for row in first_two]
    if len(set(leagues)) != 1:
        raise RuntimeError("first two canary fixtures are not in the same league")
    league = leagues[0]
    if league not in set(CORNER_SOURCE_READY_LEAGUES) or league in PROHIBITED_LEAGUES:
        raise RuntimeError(f"canary league is not outcome-ready: {league}")
    marginal = [int(row.get("worst_case_marginal_credits") or 0) for row in first_two]
    if marginal != [4, 2]:
        raise RuntimeError(f"unexpected same-league marginal credit plan: {marginal}")
    if sum(marginal) > MAX_PAID_CREDITS:
        raise RuntimeError("two-event canary exceeds credit cap")
    event_ids = [str(row.get("event_id") or "") for row in first_two]
    if not all(event_ids) or len(set(event_ids)) != EXPECTED_EVENTS:
        raise RuntimeError("canary planner produced invalid/duplicate event ids")
    return league, event_ids


def _validate_collection(collection: dict[str, Any], expected_league: str) -> None:
    if collection.get("quota_blocked") is True:
        raise RuntimeError("collector became quota-blocked after preflight")
    checks = {
        "featured_requests": 1,
        "event_requests": 2,
        "provider_paid_requests": MAX_PAID_REQUESTS,
        "fetched": EXPECTED_EVENTS,
        "inserted": EXPECTED_EVENTS,
    }
    for key, expected in checks.items():
        if int(collection.get(key) or 0) != expected:
            raise RuntimeError(f"unexpected {key}: {collection.get(key)!r}, expected {expected}")
    credits = int(collection.get("provider_paid_credits") or 0)
    if credits < 1 or credits > MAX_PAID_CREDITS:
        raise RuntimeError(f"paid credits outside canary envelope: {credits}")
    if int(collection.get("max_paid_requests") or 0) != MAX_PAID_REQUESTS:
        raise RuntimeError("collector request cap mismatch")
    if int(collection.get("max_paid_credits") or 0) != MAX_PAID_CREDITS:
        raise RuntimeError("collector credit cap mismatch")
    leagues = list(collection.get("collection_leagues") or [])
    if not leagues or leagues[0] != expected_league:
        raise RuntimeError(f"unexpected collection league order: {leagues}")
    if any(str(league) in PROHIBITED_LEAGUES for league in leagues):
        raise RuntimeError(f"prohibited league reached collection: {leagues}")
    quota_before = collection.get("quota_before") or {}
    before = int(quota_before.get("remaining") or 0)
    if before - credits < HARD_RESERVE_CREDITS:
        raise RuntimeError("actual canary spend crosses hard reserve")


def _audit_rows(rows: list[dict[str, Any]], expected_league: str, expected_event_ids: list[str]) -> dict[str, Any]:
    if len(rows) != EXPECTED_EVENTS:
        raise RuntimeError(f"expected exactly two stored snapshots, found {len(rows)}")
    keys = [str(row.get("snapshot_key") or "") for row in rows]
    event_ids = [str(row.get("event_id") or "") for row in rows]
    if not all(keys) or len(set(keys)) != EXPECTED_EVENTS:
        raise RuntimeError("duplicate/empty snapshot keys detected")
    if set(event_ids) != set(expected_event_ids):
        raise RuntimeError(f"stored event ids differ from preregistered canary plan: {event_ids}")
    if any(str(row.get("league") or "") != expected_league for row in rows):
        raise RuntimeError("stored snapshot league differs from preregistered canary league")

    market_keys: set[str] = set()
    bookmaker_keys: set[str] = set()
    per_event: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row.get("payload") or {})
        row_markets = {str(key) for key in (payload.get("provider_market_keys") or []) if key}
        books = list(payload.get("bookmakers") or [])
        row_books = {str(book.get("key") or book.get("title") or "") for book in books if isinstance(book, dict)}
        if not row_markets.intersection(CORNER_MARKETS):
            raise RuntimeError(f"stored event {row.get('event_id')} has no corner market")
        if not row_books:
            raise RuntimeError(f"stored event {row.get('event_id')} has no bookmaker payload")
        market_keys.update(row_markets)
        bookmaker_keys.update(key for key in row_books if key)
        per_event.append({
            "event_id": str(row.get("event_id") or ""),
            "home_team": str(row.get("home_team") or ""),
            "away_team": str(row.get("away_team") or ""),
            "kickoff_utc": str(row.get("kickoff_utc") or ""),
            "snapshot_time_utc": str(row.get("snapshot_time_utc") or ""),
            "provider_market_keys": sorted(row_markets),
            "bookmaker_count": len(row_books),
        })
    return {
        "unique_snapshot_keys": len(set(keys)),
        "unique_events": len(set(event_ids)),
        "provider_market_keys": sorted(market_keys),
        "bookmaker_keys": sorted(bookmaker_keys),
        "events": per_event,
    }


def run_canary(
    client: Any,
    *,
    build_plan_fn: Callable[..., dict[str, Any]] = build_live_plan,
    collect_fn: Callable[..., dict[str, Any]] = collect,
) -> dict[str, Any]:
    baseline = _count_snapshots(client)
    result: dict[str, Any] = {
        "schema_version": "MULTI_MARKET_FIRST_PAID_CANARY_V1",
        "research_only": True,
        "prospective_oos_evaluation_active": False,
        "production_promotion": False,
        "max_paid_requests": MAX_PAID_REQUESTS,
        "max_paid_credits": MAX_PAID_CREDITS,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
        "snapshot_count_before": baseline,
        "preflight": None,
        "collection": None,
        "post_collection": None,
        "status": "BLOCKED",
    }
    if baseline != 0:
        result["blocker"] = "FIRST_CANARY_REQUIRES_EMPTY_SNAPSHOT_TABLE"
        return result

    plan = dict(build_plan_fn(max_paid_credits=MAX_PAID_CREDITS))
    expected_league, expected_event_ids = _validate_plan(plan)
    result["preflight"] = {
        "remaining_credits": int(plan["remaining_credits"]),
        "planned_events": int(plan["planned_events"]),
        "planned_credits_worst_case": int(plan["planned_credits_worst_case"]),
        "worst_case_remaining_credits": int(plan["worst_case_remaining_credits"]),
        "hard_reserve_preserved": bool(plan["hard_reserve_preserved"]),
        "paid_provider_requests": int(plan["paid_provider_requests"]),
        "paid_provider_credits": int(plan["paid_provider_credits"]),
        "expected_league": expected_league,
        "expected_event_ids": expected_event_ids,
    }

    collection = dict(collect_fn(max_paid_requests=MAX_PAID_REQUESTS, max_paid_credits=MAX_PAID_CREDITS))
    result["collection"] = collection
    _validate_collection(collection, expected_league)

    count_after = _count_snapshots(client)
    rows = _load_canary_rows(client)
    audit = _audit_rows(rows, expected_league, expected_event_ids)
    if count_after != EXPECTED_EVENTS:
        raise RuntimeError(f"snapshot table count after canary is {count_after}, expected {EXPECTED_EVENTS}")
    result["snapshot_count_after"] = count_after
    result["post_collection"] = audit
    result["status"] = "PASSED"
    return result


def main() -> None:
    from database import supabase

    result: dict[str, Any]
    try:
        result = run_canary(supabase)
        if result.get("status") != "PASSED":
            raise RuntimeError(str(result.get("blocker") or "canary blocked"))
    except Exception as exc:
        result = locals().get("result", {
            "schema_version": "MULTI_MARKET_FIRST_PAID_CANARY_V1",
            "research_only": True,
            "status": "FAILED",
        })
        result["status"] = "FAILED"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:1000]
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        raise

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
