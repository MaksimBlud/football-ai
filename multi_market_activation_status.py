"""Read-only activation status for Multi-Market V1.

Checks only whether the dedicated Supabase table exists and whether the provider
quota is high enough to start paid event-market collection. The quota check uses
the provider's zero-cost /sports endpoint. No DDL, writes, or paid market calls.
"""
from __future__ import annotations

import json
from pathlib import Path

from database import supabase
from multi_market_collector import START_MIN_REQUESTS_REMAINING, TABLE
from multi_market_odds import fetch_quota_status

OUTPUT = Path("artifacts/multi_market_activation_status.json")


def check_schema() -> tuple[bool, str | None]:
    try:
        supabase.table(TABLE).select("snapshot_key").limit(1).execute()
        return True, None
    except Exception as exc:
        return False, str(exc)[:500]


def build_status() -> dict:
    schema_ready, schema_error = check_schema()
    quota = fetch_quota_status()
    remaining = quota.get("remaining")
    quota_ready = remaining is not None and int(remaining) >= START_MIN_REQUESTS_REMAINING
    ready = bool(schema_ready and quota_ready)
    return {
        "schema_version": "MULTI_MARKET_V1",
        "schema_ready": schema_ready,
        "schema_error": schema_error,
        "quota": quota,
        "quota_threshold": START_MIN_REQUESTS_REMAINING,
        "quota_ready": quota_ready,
        "activation_ready": ready,
        "status": "READY" if ready else "BLOCKED",
        "writes_performed": False,
        "paid_provider_requests": 0,
    }


def main() -> None:
    status = build_status()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
