"""Zero-cost, outcome-free collection status for EPL_AI_MARKET_PAIR_V1."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
LEAGUE = "EPL"
PAIR_TABLE = "epl_ai_market_pair_ledger"
SNAPSHOT_TABLE = "odds_snapshots"
CONTRACT_PATH = Path("research/epl_ai_market_pair_v1.json")
PAGE_SIZE = 1000
MAX_PAGES = 20
RECENT_SCHEDULER_ROWS = 100
NO_FUTURE_MATCH_COOLDOWN_HOURS = 24
MANUAL_REVIEW_EXIT_CODE = 4


def _read_paginated(client, table: str, columns: str, *, filters: dict[str, str] | None = None) -> pd.DataFrame:
    rows: list[dict] = []
    for page in range(MAX_PAGES):
        start = page * PAGE_SIZE
        query = client.table(table).select(columns)
        for column, value in (filters or {}).items():
            query = query.eq(column, value)
        response = query.range(start, start + PAGE_SIZE - 1).execute()
        batch = list(getattr(response, "data", None) or [])
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            return pd.DataFrame(rows)
    raise RuntimeError(f"bounded pagination exhausted for {table}")


def _required_interval_hours(hours_to_match: float | None) -> int:
    if hours_to_match is None:
        return NO_FUTURE_MATCH_COOLDOWN_HOURS
    if hours_to_match > 72:
        return 12
    if hours_to_match > 24:
        return 6
    if hours_to_match > 6:
        return 4
    return 2


def build_status(*, pairs: pd.DataFrame, snapshots: pd.DataFrame, now_utc: pd.Timestamp, primary_cohort_size: int) -> dict:
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")

    pair_events = 0 if pairs.empty else int(pairs["event_id"].astype(str).nunique())
    latest_snapshot = None
    snapshot_age_hours = None
    future_snapshot_events = 0
    nearest_kickoff = None
    hours_to_nearest_match = None
    required_interval_hours = NO_FUTURE_MATCH_COOLDOWN_HOURS
    snapshot_due = True
    status_reason = "NO_VALID_SNAPSHOT"

    if not snapshots.empty:
        work = snapshots.copy()
        work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
        work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
        valid = work[work["snapshot_time_utc"].notna() & work["commence_time_utc"].notna()].copy()
        if not valid.empty:
            latest_snapshot_ts = valid["snapshot_time_utc"].max()
            latest_snapshot = latest_snapshot_ts.isoformat()
            snapshot_age_hours = float((now_utc - latest_snapshot_ts).total_seconds() / 3600)

            recent = valid.sort_values("snapshot_time_utc", ascending=False).head(RECENT_SCHEDULER_ROWS)
            future = recent[recent["commence_time_utc"] > now_utc].copy()
            future_snapshot_events = int(future["event_id"].astype(str).nunique())

            if future.empty:
                required_interval_hours = NO_FUTURE_MATCH_COOLDOWN_HOURS
                status_reason = "NO_FUTURE_MATCH_COOLDOWN"
            else:
                nearest_kickoff_ts = future["commence_time_utc"].min()
                nearest_kickoff = nearest_kickoff_ts.isoformat()
                hours_to_nearest_match = float((nearest_kickoff_ts - now_utc).total_seconds() / 3600)
                required_interval_hours = _required_interval_hours(hours_to_nearest_match)
                status_reason = "SNAPSHOT_DUE" if snapshot_age_hours >= required_interval_hours else "CADENCE_NOT_DUE"

            snapshot_due = snapshot_age_hours >= required_interval_hours
            if future.empty:
                status_reason = "SNAPSHOT_DUE" if snapshot_due else "NO_FUTURE_MATCH_COOLDOWN"

    return {
        "experiment_id": EXPERIMENT_ID,
        "league": LEAGUE,
        "primary_cohort_size": int(primary_cohort_size),
        "collected_events": pair_events,
        "remaining_events": max(int(primary_cohort_size) - pair_events, 0),
        "latest_snapshot_utc": latest_snapshot,
        "latest_snapshot_age_hours": snapshot_age_hours,
        "future_snapshot_events": future_snapshot_events,
        "nearest_future_kickoff_utc": nearest_kickoff,
        "hours_to_nearest_match": hours_to_nearest_match,
        "scheduler_required_interval_hours": int(required_interval_hours),
        "scheduler_would_request_snapshot": bool(snapshot_due),
        "collection_status": "MANUAL_REVIEW" if snapshot_due else "FRESH",
        "collection_status_reason": status_reason,
        "paid_collection_policy": "MANUAL_ONLY",
        "automatic_paid_calls": False,
        "outcome_reads": 0,
        "research_only": True,
    }


def status_exit_code(payload: dict, *, require_fresh: bool) -> int:
    if require_fresh and payload.get("collection_status") != "FRESH":
        return MANUAL_REVIEW_EXIT_CODE
    return 0


def load_live_status(client, *, now_utc: pd.Timestamp | None = None) -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    primary_cohort_size = int(contract["evaluation"]["primary_cohort_size"])
    pairs = _read_paginated(client, PAIR_TABLE, "event_id", filters={"experiment_id": EXPERIMENT_ID})
    snapshots = _read_paginated(
        client,
        SNAPSHOT_TABLE,
        "league,event_id,snapshot_time_utc,commence_time_utc",
        filters={"league": LEAGUE},
    )
    now = now_utc if now_utc is not None else pd.Timestamp(datetime.now(timezone.utc))
    return build_status(pairs=pairs, snapshots=snapshots, now_utc=now, primary_cohort_size=primary_cohort_size)


def main() -> None:
    from database import supabase

    parser = argparse.ArgumentParser(description="Zero-cost EPL pair collection status")
    parser.add_argument(
        "--require-fresh",
        action="store_true",
        help="exit non-zero when manual review is required; never triggers provider calls",
    )
    args = parser.parse_args()
    payload = load_live_status(supabase)
    print(json.dumps(payload, indent=2, sort_keys=True))
    code = status_exit_code(payload, require_fresh=args.require_fresh)
    if code:
        print("MANUAL_REVIEW: guarded paid snapshot may be due; no provider call was made")
        raise SystemExit(code)
    print("PASS: zero-cost outcome-free EPL pair collection status complete")


if __name__ == "__main__":
    main()
