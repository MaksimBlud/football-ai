"""Read-only worst-case sampling planner for prospective Multi-Market collection.

The planner never calls a paid odds endpoint and never writes Supabase. It turns
future canonical odds-snapshot fixtures plus the provider's zero-cost quota
status into a deterministic, reserve-preserving collection plan.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from multi_market_policy import (
    CORNER_SOURCE_READY_LEAGUES,
    EVENT_REQUEST_MAX_CREDITS,
    FIRST_EVENT_MAX_CREDITS,
    HARD_RESERVE_CREDITS,
)

OUTPUT = Path("artifacts/multi_market_sampling_plan.json")
SCHEMA_VERSION = "MULTI_MARKET_SAMPLING_PLAN_V1"


def _int_credit(value: Any) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("credit value must be an integer") from exc
    if result < 0:
        raise ValueError("credit value must be non-negative")
    return result


def _batch_ready_events(events: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Keep only outcome-ready leagues and batch by first appearance.

    The input order is expected to be chronological. League priority is therefore
    determined only by the first upcoming fixture, never by outcomes, model
    scores, or observed research performance.
    """
    source = [dict(event) for event in events]
    ready = set(CORNER_SOURCE_READY_LEAGUES)
    filtered = [event for event in source if str(event.get("league")) in ready]
    league_order = list(dict.fromkeys(str(event["league"]) for event in filtered))
    batched = [event for league in league_order for event in filtered if str(event["league"]) == league]
    return batched, len(source) - len(filtered)


def plan_collection(
    events: Iterable[dict[str, Any]],
    *,
    remaining_credits: int,
    max_paid_credits: int | None = None,
) -> dict[str, Any]:
    remaining = _int_credit(remaining_credits)
    requested_cap = None if max_paid_credits is None else _int_credit(max_paid_credits)
    headroom = max(0, remaining - HARD_RESERVE_CREDITS)
    effective_cap = headroom if requested_cap is None else min(headroom, requested_cap)

    batched, skipped_no_corner_source = _batch_ready_events(events)
    selected: list[dict[str, Any]] = []
    opened_leagues: set[str] = set()
    planned_credits = 0

    for event in batched:
        league = str(event["league"])
        marginal_cost = FIRST_EVENT_MAX_CREDITS if league not in opened_leagues else EVENT_REQUEST_MAX_CREDITS
        if planned_credits + marginal_cost > effective_cap:
            break
        opened_leagues.add(league)
        planned_credits += marginal_cost
        selected.append({
            "league": league,
            "event_id": str(event.get("event_id") or ""),
            "home_team": str(event.get("home_team") or ""),
            "away_team": str(event.get("away_team") or ""),
            "commence_time_utc": str(event.get("commence_time_utc") or ""),
            "worst_case_marginal_credits": marginal_cost,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "research_only": True,
        "read_only": True,
        "writes_performed": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
        "remaining_credits": remaining,
        "available_headroom_credits": headroom,
        "requested_max_paid_credits": requested_cap,
        "effective_max_paid_credits": effective_cap,
        "source_events": len(batched) + skipped_no_corner_source,
        "eligible_events": len(batched),
        "skipped_no_corner_source": skipped_no_corner_source,
        "planned_events": len(selected),
        "planned_leagues": list(dict.fromkeys(row["league"] for row in selected)),
        "planned_credits_worst_case": planned_credits,
        "worst_case_remaining_credits": remaining - planned_credits,
        "hard_reserve_preserved": remaining - planned_credits >= HARD_RESERVE_CREDITS,
        "plan_complete_for_eligible_window": len(selected) == len(batched),
        "events": selected,
    }


def build_live_plan(*, now_utc: datetime | None = None, max_paid_credits: int | None = None) -> dict[str, Any]:
    """Build a live plan using only Supabase reads and the provider's free /sports preflight."""
    from multi_market_collector import load_future_events
    from multi_market_odds import fetch_quota_status

    now_utc = now_utc or datetime.now(UTC)
    quota = fetch_quota_status()
    remaining = quota.get("remaining")
    if remaining is None:
        raise RuntimeError("provider quota preflight omitted remaining credits")
    plan = plan_collection(
        load_future_events(now_utc),
        remaining_credits=_int_credit(remaining),
        max_paid_credits=max_paid_credits,
    )
    plan["generated_at_utc"] = now_utc.isoformat()
    plan["quota"] = dict(quota)
    return plan


def main() -> None:
    plan = build_live_plan()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
