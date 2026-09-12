"""Read-only live sample-health monitor for ALL_LEAGUES_MARKET_ONLY_V1_1.

Only frozen prediction metadata is read. Result, score, winner and settlement
sources are deliberately outside this module.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable, Mapping

from all_leagues_market_only_v1_1_gate import (
    LEAGUES,
    V1_1_FREEZE_UTC,
    evaluate_gate,
    load_seed_keys,
    select_event_rows,
)


EXPERIMENT = "ALL_LEAGUES_MARKET_ONLY_V1_1"
LEDGER_TABLE = "league_prediction_ledger"
PAGE_SIZE = 1000
SEED_QUERY_CHUNK_SIZE = 50
METADATA_COLUMNS = (
    "prediction_key",
    "league",
    "event_id",
    "kickoff_utc",
    "prediction_time_utc",
    "snapshot_time_utc",
    "market_home_prob",
    "market_draw_prob",
    "market_away_prob",
    "structural_applied",
    "prediction_mode",
    "created_at_utc",
)
FUTURE_ORDER_FIELDS = (
    "created_at_utc",
    "prediction_time_utc",
    "snapshot_time_utc",
    "prediction_key",
)


class SampleHealthInputError(ValueError):
    pass


def _response_rows(response: object) -> list[dict[str, object]]:
    return [dict(row) for row in (getattr(response, "data", None) or [])]


def _created_at_utc(row: Mapping[str, object]) -> datetime:
    value = row.get("created_at_utc")
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise SampleHealthInputError("Live metadata row has invalid created_at_utc")
    if parsed.tzinfo is None:
        raise SampleHealthInputError("Live metadata created_at_utc must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _add_unique_row(
    rows_by_key: dict[str, dict[str, object]], row: Mapping[str, object]
) -> None:
    key = str(row.get("prediction_key", ""))
    if not key:
        raise SampleHealthInputError("Live metadata row is missing prediction_key")
    normalized = dict(row)
    existing = rows_by_key.get(key)
    if existing is not None and existing != normalized:
        raise SampleHealthInputError(f"Conflicting duplicate prediction_key: {key}")
    rows_by_key[key] = normalized


def fetch_metadata_rows(
    client,
    *,
    seed_keys: frozenset[str] | None = None,
    page_size: int = PAGE_SIZE,
) -> list[dict[str, object]]:
    """Fetch exact frozen seeds plus post-freeze MARKET_ONLY candidates."""
    if page_size <= 0:
        raise ValueError("page_size must be positive")

    frozen_seed_keys = load_seed_keys() if seed_keys is None else seed_keys
    rows_by_key: dict[str, dict[str, object]] = {}
    columns = ",".join(METADATA_COLUMNS)

    for chunk in _chunks(sorted(frozen_seed_keys), SEED_QUERY_CHUNK_SIZE):
        response = (
            client.table(LEDGER_TABLE)
            .select(columns)
            .in_("prediction_key", chunk)
            .execute()
        )
        for row in _response_rows(response):
            _add_unique_row(rows_by_key, row)

    freeze = V1_1_FREEZE_UTC.isoformat()
    for league in LEAGUES:
        start = 0
        while True:
            query = (
                client.table(LEDGER_TABLE)
                .select(columns)
                .eq("league", league)
                .eq("prediction_mode", "MARKET_ONLY")
                .eq("structural_applied", False)
                .gt("created_at_utc", freeze)
            )
            for field in FUTURE_ORDER_FIELDS:
                query = query.order(field, desc=False)
            batch = _response_rows(
                query.range(start, start + page_size - 1).execute()
            )
            for row in batch:
                _add_unique_row(rows_by_key, row)
            if len(batch) < page_size:
                break
            start += page_size

    return [rows_by_key[key] for key in sorted(rows_by_key)]


def build_sample_health(
    rows: Iterable[Mapping[str, object]],
    *,
    now_utc: datetime,
    seed_keys: frozenset[str] | None = None,
) -> dict[str, object]:
    frozen_seed_keys = load_seed_keys() if seed_keys is None else seed_keys
    materialized = [dict(row) for row in rows]
    fetched_keys = {str(row.get("prediction_key", "")) for row in materialized}
    missing_seed_keys = sorted(frozen_seed_keys - fetched_keys)
    if missing_seed_keys:
        raise SampleHealthInputError(
            f"Frozen seed integrity failure: {len(missing_seed_keys)} key(s) missing"
        )

    selected = select_event_rows(materialized, seed_keys=frozen_seed_keys)
    selected_seed_keys = {
        str(row["prediction_key"])
        for row in selected
        if str(row["prediction_key"]) in frozen_seed_keys
    }
    future_rows = [
        row
        for row in materialized
        if str(row.get("prediction_key", "")) not in frozen_seed_keys
        and _created_at_utc(row) > V1_1_FREEZE_UTC
    ]
    future_selected = [
        row
        for row in selected
        if str(row["prediction_key"]) not in frozen_seed_keys
    ]
    gate = evaluate_gate(
        materialized,
        now_utc=now_utc,
        seed_keys=frozen_seed_keys,
        stricter_gate_clear=False,
    )

    checked_at = now_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": "all_leagues_market_only_v1_1_sample_health_v1",
        "experiment": EXPERIMENT,
        "checked_at_utc": checked_at,
        "source": {
            "table": LEDGER_TABLE,
            "columns": list(METADATA_COLUMNS),
            "rows_fetched": len(materialized),
            "seed_keys_expected": len(frozen_seed_keys),
            "seed_keys_matched": len(selected_seed_keys),
            "post_freeze_candidate_rows": len(future_rows),
            "post_freeze_selected_events": len(future_selected),
        },
        "gate": gate,
        "safety": {
            "outcome_sources_read": False,
            "provider_requests": 0,
            "supabase_writes": 0,
            "production_artifact_changes": 0,
            "stricter_gates_assumed_clear": False,
        },
    }


def run_live(client, *, now_utc: datetime | None = None) -> dict[str, object]:
    checked_at = now_utc or datetime.now(timezone.utc)
    return build_sample_health(fetch_metadata_rows(client), now_utc=checked_at)


def main() -> int:
    from database import supabase

    print(json.dumps(run_live(supabase), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
