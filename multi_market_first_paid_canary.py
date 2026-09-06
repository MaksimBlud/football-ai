"""One-shot guarded live canary for the first prospective Multi-Market sample.

This entry point is intentionally stricter than the recurring collector:
- an empty snapshot table permits the one-time paid canary path;
- a non-empty table is audited read-only and can never trigger provider spend;
- a fresh zero-cost planner must fit two fixtures from one outcome-ready league
  inside the 3-request / 6-credit canary envelope;
- the collector is called with explicit caps and the hard reserve remains intact;
- exactly two unique prospective snapshots must be written and contain real
  corner-market/bookmaker payloads to pass.

It never enables scheduled collection, settlement, evaluation, or promotion.
Provider-aware modules are imported only on the empty-table paid path.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from multi_market_policy import CORNER_SOURCE_READY_LEAGUES, HARD_RESERVE_CREDITS

OUTPUT = Path("artifacts/multi_market_first_paid_canary.json")
TABLE = "league_multi_market_snapshots"
MAX_PAID_REQUESTS = 3
MAX_PAID_CREDITS = 6
EXPECTED_EVENTS = 2
PROHIBITED_LEAGUES = frozenset({"RPL", "TURKEY_SUPER_LIG"})
CORNER_MARKETS = frozenset({"alternate_totals_corners", "alternate_team_totals_corners"})


def _default_build_plan(**kwargs: Any) -> dict[str, Any]:
    from multi_market_sampling_plan import build_live_plan

    return dict(build_live_plan(**kwargs))


def _default_collect(**kwargs: Any) -> dict[str, Any]:
    from multi_market_collector import collect

    return dict(collect(**kwargs))


def _default_fetch_quota() -> dict[str, Any]:
    from multi_market_odds import fetch_quota_status

    return dict(fetch_quota_status())


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
    if len(events) != EXPECTED_EVENTS:
        raise RuntimeError(f"canary plan must contain exactly two fixtures, found {len(events)}")
    leagues = [str(row.get("league") or "") for row in events]
    if len(set(leagues)) != 1:
        raise RuntimeError("first two canary fixtures are not in the same league")
    league = leagues[0]
    if league not in set(CORNER_SOURCE_READY_LEAGUES) or league in PROHIBITED_LEAGUES:
        raise RuntimeError(f"canary league is not outcome-ready: {league}")
    marginal = [int(row.get("worst_case_marginal_credits") or 0) for row in events]
    if marginal != [4, 2]:
        raise RuntimeError(f"unexpected same-league marginal credit plan: {marginal}")
    if sum(marginal) > MAX_PAID_CREDITS:
        raise RuntimeError("two-event canary exceeds credit cap")
    event_ids = [str(row.get("event_id") or "") for row in events]
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


def _audit_rows(
    rows: list[dict[str, Any]],
    expected_league: str,
    expected_event_ids: list[str],
    *,
    require_corners: bool = True,
) -> dict[str, Any]:
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
    missing_corner_event_ids: list[str] = []
    event_last_costs: list[int | None] = []
    featured_last_costs: list[int | None] = []
    observed_remaining: list[int] = []
    per_event: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row.get("payload") or {})
        row_markets = {str(key) for key in (payload.get("provider_market_keys") or []) if key}
        books = list(payload.get("bookmakers") or [])
        row_books = {str(book.get("key") or book.get("title") or "") for book in books if isinstance(book, dict)}
        event_id = str(row.get("event_id") or "")
        if not row_markets.intersection(CORNER_MARKETS):
            missing_corner_event_ids.append(event_id)
            if require_corners:
                raise RuntimeError(f"stored event {event_id} has no corner market")
        if not row_books:
            raise RuntimeError(f"stored event {event_id} has no bookmaker payload")
        market_keys.update(row_markets)
        bookmaker_keys.update(key for key in row_books if key)
        event_quota = dict(payload.get("quota") or {})
        featured_quota = dict(payload.get("featured_quota") or {})
        event_last = event_quota.get("last_cost")
        featured_last = featured_quota.get("last_cost")
        event_last_costs.append(int(event_last) if event_last not in (None, "") else None)
        featured_last_costs.append(int(featured_last) if featured_last not in (None, "") else None)
        remaining = event_quota.get("remaining")
        if remaining not in (None, ""):
            observed_remaining.append(int(remaining))
        per_event.append({
            "event_id": event_id,
            "home_team": str(row.get("home_team") or ""),
            "away_team": str(row.get("away_team") or ""),
            "kickoff_utc": str(row.get("kickoff_utc") or ""),
            "snapshot_time_utc": str(row.get("snapshot_time_utc") or ""),
            "provider_market_keys": sorted(row_markets),
            "bookmaker_count": len(row_books),
            "event_last_cost": event_last_costs[-1],
            "featured_last_cost": featured_last_costs[-1],
        })
    return {
        "unique_snapshot_keys": len(set(keys)),
        "unique_events": len(set(event_ids)),
        "provider_market_keys": sorted(market_keys),
        "bookmaker_keys": sorted(bookmaker_keys),
        "missing_corner_event_ids": missing_corner_event_ids,
        "event_last_costs": event_last_costs,
        "featured_last_costs": featured_last_costs,
        "observed_remaining_credits": min(observed_remaining) if observed_remaining else None,
        "events": per_event,
    }


def _audit_existing_failed_canary(client: Any, baseline: int, result: dict[str, Any]) -> dict[str, Any]:
    if baseline != EXPECTED_EVENTS:
        result["blocker"] = "FIRST_CANARY_REQUIRES_EMPTY_SNAPSHOT_TABLE"
        return result
    rows = _load_canary_rows(client)
    leagues = {str(row.get("league") or "") for row in rows}
    event_ids = [str(row.get("event_id") or "") for row in rows]
    if len(leagues) != 1 or not all(event_ids):
        result["blocker"] = "EXISTING_CANARY_ROWS_NOT_CANONICAL"
        return result
    league = next(iter(leagues))
    audit = _audit_rows(rows, league, event_ids, require_corners=False)
    result["snapshot_count_after"] = baseline
    result["post_collection"] = audit
    result["provider_recheck_performed"] = False
    if len(audit["missing_corner_event_ids"]) == EXPECTED_EVENTS:
        result["status"] = "BLOCKED_NO_CORNER_MARKET"
        result["blocker"] = "FIRST_PAID_CANARY_NO_CORNER_MARKET"
        return result
    result["blocker"] = "EXISTING_CANARY_ROWS_REQUIRE_MANUAL_REVIEW"
    return result


def run_canary(
    client: Any,
    *,
    build_plan_fn: Callable[..., dict[str, Any]] | None = None,
    collect_fn: Callable[..., dict[str, Any]] | None = None,
    fetch_quota_fn: Callable[[], dict[str, Any]] | None = None,
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
        "quota_after": None,
        "status": "BLOCKED",
    }
    if baseline != 0:
        return _audit_existing_failed_canary(client, baseline, result)

    # Only after the irreversible first-canary baseline guard may live planner
    # and provider-aware modules be loaded or invoked.
    build_plan_fn = build_plan_fn or _default_build_plan
    collect_fn = collect_fn or _default_collect
    fetch_quota_fn = fetch_quota_fn or _default_fetch_quota

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
    quota_after = dict(fetch_quota_fn())
    remaining_after = int(quota_after.get("remaining") or -1)
    if remaining_after < HARD_RESERVE_CREDITS:
        raise RuntimeError("post-canary quota is below hard reserve")
    result["snapshot_count_after"] = count_after
    result["post_collection"] = audit
    result["quota_after"] = quota_after
    result["status"] = "PASSED"
    return result


def main() -> None:
    from database import supabase

    result: dict[str, Any]
    try:
        result = run_canary(supabase)
        if result.get("status") not in {"PASSED", "BLOCKED_NO_CORNER_MARKET"}:
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
