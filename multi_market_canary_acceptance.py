"""Strict read-only acceptance for the first controlled Multi-Market paid canary.

This verifier does not call the odds provider, does not read match outcomes, and
does not write Supabase. It validates the cycle audit plus the exact durable
snapshot row created by a 2-request / 4-credit first canary.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from multi_market_policy import CORNER_SOURCE_READY_LEAGUES, HARD_RESERVE_CREDITS

CYCLE_STATUS = Path("artifacts/multi_market_cycle_status.json")
OUTPUT = Path("artifacts/multi_market_first_canary_acceptance.json")
SCHEMA_VERSION = "MULTI_MARKET_FIRST_CANARY_ACCEPTANCE_V1"
SNAPSHOT_TABLE = "league_multi_market_snapshots"


def _int(value: Any, name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    return result


def _fetch_exact_snapshot(client: Any, snapshot_key: str) -> list[dict[str, Any]]:
    response = (
        client.table(SNAPSHOT_TABLE)
        .select("snapshot_key,league,event_id,home_team,away_team,kickoff_utc,snapshot_time_utc,payload,provider")
        .eq("snapshot_key", snapshot_key)
        .limit(2)
        .execute()
    )
    return [dict(row) for row in (response.data or [])]


def evaluate_first_canary(cycle_status: dict[str, Any], client: Any) -> dict[str, Any]:
    reasons: list[str] = []
    collection = cycle_status.get("collection") or {}

    if cycle_status.get("schema_version") != "MULTI_MARKET_V2_CYCLE_STATUS_V1":
        reasons.append("CYCLE_SCHEMA_MISMATCH")
    if cycle_status.get("action") != "COLLECTION_ATTEMPTED":
        reasons.append("COLLECTION_NOT_ATTEMPTED")
    if cycle_status.get("collection_activation_enabled") is not True:
        reasons.append("MANUAL_ACTIVATION_NOT_RECORDED")
    if cycle_status.get("prospective_oos_evaluation_active") is not False:
        reasons.append("OOS_EVALUATION_MUST_REMAIN_INACTIVE")

    if collection.get("max_paid_requests") is None or _int(collection.get("max_paid_requests"), "max_paid_requests") != 2:
        reasons.append("CANARY_REQUEST_CAP_MUST_EQUAL_2")
    if collection.get("max_paid_credits") is None or _int(collection.get("max_paid_credits"), "max_paid_credits") != 4:
        reasons.append("CANARY_CREDIT_CAP_MUST_EQUAL_4")

    for key, expected in (("featured_requests", 1), ("event_requests", 1), ("fetched", 1), ("inserted", 1)):
        if _int(collection.get(key, 0), key) != expected:
            reasons.append(f"{key.upper()}_MUST_EQUAL_{expected}")

    provider_requests = _int(collection.get("provider_paid_requests", 0), "provider_paid_requests")
    top_level_requests = _int(cycle_status.get("paid_provider_requests", 0), "paid_provider_requests")
    provider_credits = _int(collection.get("provider_paid_credits", 0), "provider_paid_credits")
    if provider_requests != 2 or top_level_requests != provider_requests:
        reasons.append("PAID_REQUEST_ACCOUNTING_MUST_EQUAL_2")
    if provider_credits < 1 or provider_credits > 4:
        reasons.append("PAID_CREDITS_OUTSIDE_FIRST_CANARY_RANGE")
    if _int(collection.get("hard_reserve_credits", HARD_RESERVE_CREDITS), "hard_reserve_credits") != HARD_RESERVE_CREDITS:
        reasons.append("HARD_RESERVE_POLICY_MISMATCH")

    keys = list(collection.get("inserted_snapshot_keys") or [])
    if len(keys) != 1 or not str(keys[0]).strip():
        reasons.append("EXACTLY_ONE_DURABLE_SNAPSHOT_KEY_REQUIRED")
        snapshot_key = None
    else:
        snapshot_key = str(keys[0])

    collection_leagues = list(collection.get("collection_leagues") or [])
    if len(collection_leagues) != 1 or collection_leagues[0] not in CORNER_SOURCE_READY_LEAGUES:
        reasons.append("EXACTLY_ONE_OUTCOME_READY_LEAGUE_REQUIRED")

    row = None
    if snapshot_key is not None:
        rows = _fetch_exact_snapshot(client, snapshot_key)
        if len(rows) != 1:
            reasons.append("DURABLE_SNAPSHOT_ROW_MUST_BE_UNIQUE")
        else:
            row = rows[0]
            league = str(row.get("league") or "")
            if league not in CORNER_SOURCE_READY_LEAGUES:
                reasons.append("DURABLE_SNAPSHOT_LEAGUE_NOT_OUTCOME_READY")
            if len(collection_leagues) == 1 and league != str(collection_leagues[0]):
                reasons.append("DURABLE_SNAPSHOT_LEAGUE_MISMATCH")
            if str(row.get("provider") or "") != "THE_ODDS_API":
                reasons.append("DURABLE_SNAPSHOT_PROVIDER_MISMATCH")

            snapshot_time = pd.to_datetime(row.get("snapshot_time_utc"), utc=True, errors="coerce")
            kickoff = pd.to_datetime(row.get("kickoff_utc"), utc=True, errors="coerce")
            if pd.isna(snapshot_time) or pd.isna(kickoff) or not snapshot_time < kickoff:
                reasons.append("DURABLE_SNAPSHOT_NOT_STRICTLY_PRE_KICKOFF")

            payload = row.get("payload")
            if not isinstance(payload, dict):
                reasons.append("DURABLE_SNAPSHOT_PAYLOAD_INVALID")
            else:
                if payload.get("schema_version") != "MULTI_MARKET_V1":
                    reasons.append("DURABLE_SNAPSHOT_SCHEMA_MISMATCH")
                if payload.get("research_only") is not True:
                    reasons.append("DURABLE_SNAPSHOT_NOT_RESEARCH_ONLY")

    accepted = not reasons
    return {
        "schema_version": SCHEMA_VERSION,
        "research_only": True,
        "read_only": True,
        "outcomes_read": False,
        "writes_performed": False,
        "paid_provider_requests_performed_by_verifier": 0,
        "accepted": accepted,
        "reasons": reasons,
        "snapshot_key": snapshot_key,
        "league": None if row is None else row.get("league"),
        "event_id": None if row is None else row.get("event_id"),
        "provider_paid_requests": provider_requests,
        "provider_paid_credits": provider_credits,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
    }


def main() -> None:
    from database import supabase

    cycle_status = json.loads(CYCLE_STATUS.read_text(encoding="utf-8"))
    report = evaluate_first_canary(cycle_status, supabase)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if not report["accepted"]:
        raise SystemExit("First Multi-Market canary acceptance failed: " + ", ".join(report["reasons"]))


if __name__ == "__main__":
    main()
