"""Fail-closed scheduled entry point for Multi-Market V1."""
from __future__ import annotations

import json

from database import supabase
from multi_market_collector import TABLE, collect


def schema_ready() -> bool:
    try:
        supabase.table(TABLE).select("snapshot_key").limit(1).execute()
        return True
    except Exception:
        return False


def run_cycle() -> dict:
    if not schema_ready():
        return {
            "status": "BLOCKED_SCHEMA",
            "reason": "schema_not_applied",
            "provider_paid_requests": 0,
        }

    result = collect()
    if result.get("quota_blocked"):
        return {
            "status": "BLOCKED_LOW_QUOTA",
            "collector": result,
            "provider_paid_requests": int(result.get("provider_paid_requests", 0)),
        }

    inserted = int(result.get("inserted", 0))
    return {
        "status": "COLLECTED" if inserted > 0 else "NO_ELIGIBLE_COLLECTION",
        "collector": result,
        "provider_paid_requests": int(result.get("fetched", 0)),
    }


def main() -> None:
    result = run_cycle()
    print(f"MULTI_MARKET_V1={result['status']}")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
