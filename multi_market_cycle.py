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


def main() -> None:
    if not schema_ready():
        print("MULTI_MARKET_V1=BLOCKED; schema not applied; provider quota not used")
        return
    result = collect()
    print("MULTI_MARKET_V1=COLLECTED")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
