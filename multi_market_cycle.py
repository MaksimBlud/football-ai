"""Fail-closed lifecycle entry point for Multi-Market V2 research.

Schema readiness and zero-cost quota preflight are necessary but not sufficient
to enter a paid collection path. An explicit activation latch is also required,
so infrastructure recovery cannot silently activate provider spending.

This module does not activate settlement or prospective OOS evaluation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from multi_market_activation_status import build_status

OUTPUT = Path("artifacts/multi_market_cycle_status.json")
CYCLE_SCHEMA = "MULTI_MARKET_V2_CYCLE_STATUS_V1"


def _env_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def run_cycle(
    client: Any,
    fetch_quota: Callable[[], dict[str, Any]],
    collect_fn: Callable[[], dict[str, Any]],
    *,
    collection_enabled: bool = False,
) -> dict[str, Any]:
    readiness = build_status(client, fetch_quota)
    if readiness.get("collection_ready") is not True:
        return {
            "schema_version": CYCLE_SCHEMA,
            "research_only": True,
            "action": "NOOP_BLOCKED",
            "collection_activation_enabled": bool(collection_enabled),
            "collection_called": False,
            "paid_provider_requests": 0,
            "prospective_oos_evaluation_active": False,
            "readiness": readiness,
            "collection": None,
        }

    if not collection_enabled:
        return {
            "schema_version": CYCLE_SCHEMA,
            "research_only": True,
            "action": "NOOP_ACTIVATION_REQUIRED",
            "collection_activation_enabled": False,
            "collection_called": False,
            "paid_provider_requests": 0,
            "prospective_oos_evaluation_active": False,
            "readiness": readiness,
            "collection": None,
        }

    collection = dict(collect_fn())
    paid = int(collection.get("fetched") or collection.get("provider_paid_requests") or 0)
    return {
        "schema_version": CYCLE_SCHEMA,
        "research_only": True,
        "action": "COLLECTION_ATTEMPTED",
        "collection_activation_enabled": True,
        "collection_called": True,
        "paid_provider_requests": paid,
        "prospective_oos_evaluation_active": False,
        "readiness": readiness,
        "collection": collection,
    }


def main() -> None:
    from database import supabase
    from multi_market_collector import collect
    from multi_market_odds import fetch_quota_status

    result = run_cycle(
        supabase,
        fetch_quota_status,
        collect,
        collection_enabled=_env_enabled(os.getenv("MULTI_MARKET_COLLECTION_ENABLED")),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(result, indent=2, sort_keys=True, default=str)
    OUTPUT.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
