"""Read-only advisory planner for preregistering a future capability-probe target.

This module never changes the active paid probe target, never calls a paid provider
endpoint, and never writes Supabase. It only proposes a deterministic future
fixture that can be reviewed and committed in a separate PR if the current target
expires before any probe request is attempted.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from multi_market_corner_capability_probe import PROHIBITED_LEAGUES, TARGET
from multi_market_policy import CORNER_SOURCE_READY_LEAGUES

OUTPUT = Path("artifacts/multi_market_probe_rollover_plan.json")
SCHEMA_VERSION = "MULTI_MARKET_PROBE_ROLLOVER_PLAN_V1"
MIN_ROLLOVER_LEAD = timedelta(hours=24)


def _ts(value: Any) -> pd.Timestamp:
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"invalid UTC timestamp: {value!r}")
    return parsed


def plan_rollover(events: Iterable[dict[str, Any]], *, now_utc: datetime) -> dict[str, Any]:
    now = pd.Timestamp(now_utc)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")
    target_kickoff = _ts(TARGET["commence_time_utc"])
    minimum_candidate_kickoff = now + MIN_ROLLOVER_LEAD

    identities: dict[str, set[tuple[str, str, str, str]]] = defaultdict(set)
    normalized: list[dict[str, str]] = []
    for raw in events:
        row = {
            "league": str(raw.get("league") or ""),
            "event_id": str(raw.get("event_id") or ""),
            "home_team": str(raw.get("home_team") or ""),
            "away_team": str(raw.get("away_team") or ""),
            "commence_time_utc": _ts(raw.get("commence_time_utc")).isoformat(),
        }
        if not row["event_id"]:
            continue
        normalized.append(row)
        identities[row["event_id"]].add((row["league"], row["home_team"], row["away_team"], row["commence_time_utc"]))

    ambiguous_event_ids = sorted(event_id for event_id, values in identities.items() if len(values) != 1)
    ready = set(CORNER_SOURCE_READY_LEAGUES)
    candidates = []
    for row in normalized:
        if row["event_id"] in ambiguous_event_ids:
            continue
        if row["league"] not in ready or row["league"] in PROHIBITED_LEAGUES:
            continue
        kickoff = _ts(row["commence_time_utc"])
        if kickoff < minimum_candidate_kickoff:
            continue
        candidates.append(row)

    candidates.sort(key=lambda row: (_ts(row["commence_time_utc"]), row["league"], row["event_id"]))
    candidate = candidates[0] if candidates else None
    seconds_remaining = max(0, int((target_kickoff - now).total_seconds()))

    return {
        "schema_version": SCHEMA_VERSION,
        "research_only": True,
        "read_only": True,
        "advisory_only": True,
        "writes_performed": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
        "active_target": dict(TARGET),
        "active_target_expired": now >= target_kickoff,
        "active_target_seconds_remaining": seconds_remaining,
        "minimum_rollover_lead_hours": int(MIN_ROLLOVER_LEAD.total_seconds() // 3600),
        "requires_separate_preregistration_pr": True,
        "automatic_target_switching_enabled": False,
        "ambiguous_event_ids_excluded": ambiguous_event_ids,
        "eligible_candidate_count": len(candidates),
        "proposed_candidate": candidate,
    }


def build_live_plan(*, now_utc: datetime | None = None) -> dict[str, Any]:
    from multi_market_collector import load_future_events

    now_utc = now_utc or datetime.now(UTC)
    plan = plan_rollover(load_future_events(now_utc), now_utc=now_utc)
    plan["generated_at_utc"] = now_utc.isoformat()
    return plan


def main() -> None:
    plan = build_live_plan()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
