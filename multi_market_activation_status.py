"""Read-only Multi-Market V2 lifecycle readiness status.

This module combines the exact live schema probe with the provider's zero-cost
quota preflight. It reports infrastructure readiness only: paid collection still
requires an explicit manual activation latch in ``multi_market_cycle``.

It never creates schema, writes Supabase, performs a paid odds request, settles
a match, evaluates OOS outcomes, or changes production models.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from multi_market_policy import (
    CORNER_SOURCE_READY_LEAGUES,
    EVENT_REQUEST_MAX_CREDITS,
    HARD_RESERVE_CREDITS,
    MIN_COLLECTION_REMAINING_CREDITS,
)
from multi_market_schema_probe import probe_schema

OUTPUT = Path("artifacts/multi_market_activation_status.json")
STATUS_SCHEMA = "MULTI_MARKET_V2_READINESS_STATUS_V1"
OOS_PROTOCOL_VERSION = "MULTI_MARKET_V2_OOS_PROTOCOL_V1"

TABLE_SNAPSHOTS = "league_multi_market_snapshots"
TABLE_SETTLEMENTS = "league_multi_market_settlements"
TABLE_CORNERS = "league_corner_results"


def _safe_quota(fetch_quota: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return dict(fetch_quota()), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {str(exc)[:400]}"


def _quota_ready(quota: dict[str, Any] | None) -> bool:
    if not quota:
        return False
    remaining = quota.get("remaining")
    try:
        return remaining is not None and int(remaining) >= MIN_COLLECTION_REMAINING_CREDITS
    except (TypeError, ValueError):
        return False


def build_status(client: Any, fetch_quota: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Build read-only infrastructure readiness from live schema + zero-cost quota."""
    schema = probe_schema(client)
    ready_tables = set(schema.get("ready_tables") or [])
    quota, quota_error = _safe_quota(fetch_quota)
    quota_ready = _quota_ready(quota)

    snapshots_ready = TABLE_SNAPSHOTS in ready_tables
    settlements_ready = TABLE_SETTLEMENTS in ready_tables
    corners_ready = TABLE_CORNERS in ready_tables

    collection_ready = snapshots_ready and quota_ready
    goals_settlement_ready = snapshots_ready and settlements_ready
    corner_storage_ready = snapshots_ready and settlements_ready and corners_ready
    oos_structural_ready = corner_storage_ready

    per_league_corner = {
        league: {"source_ready": True, "schema_ready": corner_storage_ready, "corner_settlement_ready": corner_storage_ready}
        for league in CORNER_SOURCE_READY_LEAGUES
    }

    blockers: list[str] = []
    for table in (TABLE_SNAPSHOTS, TABLE_SETTLEMENTS, TABLE_CORNERS):
        if table not in ready_tables:
            blockers.append(f"SCHEMA_MISSING_OR_INCOMPATIBLE:{table}")
    if not quota_ready:
        blockers.append("QUOTA_BELOW_CREDIT_RESERVE_OR_UNAVAILABLE")

    lifecycle_status = "INFRASTRUCTURE_READY_AWAITING_MANUAL_ACTIVATION" if collection_ready else "BLOCKED"

    return {
        "schema_version": STATUS_SCHEMA,
        "research_only": True,
        "read_only": True,
        "schema": schema,
        "quota": quota,
        "quota_error": quota_error,
        "quota_threshold": MIN_COLLECTION_REMAINING_CREDITS,
        "quota_threshold_semantics": "hard_reserve_plus_one_worst_case_event_request",
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
        "event_request_max_credits": EVENT_REQUEST_MAX_CREDITS,
        "quota_ready": quota_ready,
        "collection_ready": collection_ready,
        "infrastructure_collection_ready": collection_ready,
        "manual_collection_activation_required": True,
        "scheduled_collection_enabled": False,
        "goals_settlement_ready": goals_settlement_ready,
        "corner_storage_ready": corner_storage_ready,
        "corner_source_ready_leagues": list(CORNER_SOURCE_READY_LEAGUES),
        "per_league_corner_readiness": per_league_corner,
        "oos_protocol_version": OOS_PROTOCOL_VERSION,
        "oos_protocol_frozen": True,
        "oos_structural_ready": oos_structural_ready,
        "prospective_oos_evaluation_active": False,
        "activation_ready": collection_ready,
        "status": lifecycle_status,
        "blockers": blockers,
        "writes_performed": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
    }


def main() -> None:
    from database import supabase
    from multi_market_odds import fetch_quota_status
    status = build_status(supabase, fetch_quota_status)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
