"""Fail-closed The Odds API quota budget guard.

Uses only the provider's zero-cost /sports endpoint. This module never fetches
odds/scores, never touches Supabase, and never changes model artifacts.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

import requests

from config import THE_ODDS_API_KEY
from multi_market_policy import HARD_RESERVE_CREDITS
from the_odds_service import BASE_URL


def _int_header(value: Any, *, name: str) -> int:
    if value is None or str(value).strip() == "":
        raise RuntimeError(f"The Odds API quota header missing: {name}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid The Odds API quota header {name}: {value!r}") from exc


def fetch_quota_status(*, session=requests) -> dict[str, int]:
    if not THE_ODDS_API_KEY:
        raise RuntimeError("THE_ODDS_API_KEY not configured")
    response = session.get(
        f"{BASE_URL}/sports/",
        params={"apiKey": THE_ODDS_API_KEY},
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"The Odds API quota preflight HTTP {response.status_code}: {response.text[:300]}"
        )
    return {
        "remaining": _int_header(response.headers.get("x-requests-remaining"), name="x-requests-remaining"),
        "used": _int_header(response.headers.get("x-requests-used"), name="x-requests-used"),
        "last_cost": _int_header(response.headers.get("x-requests-last"), name="x-requests-last"),
    }


def evaluate_budget(*, remaining: int, max_cost: int, reserve: int = HARD_RESERVE_CREDITS) -> dict[str, Any]:
    if max_cost < 1:
        raise ValueError("max_cost must be >= 1")
    if reserve < 0:
        raise ValueError("reserve must be >= 0")
    minimum_required = reserve + max_cost
    allowed = remaining >= minimum_required
    return {
        "schema_version": "ODDS_API_BUDGET_GUARD_V1",
        "allowed": allowed,
        "remaining": int(remaining),
        "hard_reserve_credits": int(reserve),
        "max_operation_cost_credits": int(max_cost),
        "minimum_required_credits": int(minimum_required),
        "reason": "BUDGET_AVAILABLE" if allowed else "HARD_RESERVE_PROTECTED",
        "paid_provider_requests": 0,
        "preflight_cost_credits": 0,
    }


def check_budget(*, max_cost: int, session=requests) -> dict[str, Any]:
    quota = fetch_quota_status(session=session)
    result = evaluate_budget(remaining=quota["remaining"], max_cost=max_cost)
    result["quota"] = quota
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cost", type=int, required=True)
    args = parser.parse_args()
    result = check_budget(max_cost=args.max_cost)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["allowed"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
