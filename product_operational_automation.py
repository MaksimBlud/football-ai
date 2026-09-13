"""Safe orchestration primitives for Product Operational Automation v1.

The automation is deliberately narrow. It can bridge already-produced,
outcome-free EPL AI rows into immutable product prediction snapshots and can
advance the existing append-only product lifecycle from already-stored odds and
canonical results. It never runs model inference/training, calls a paid provider,
reads frozen research target outcomes, promotes models/markets, or creates bets.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from bootstrap_product_predictions_from_pair_ledger import (
    PAIR_TABLE,
    PRODUCT_TABLE,
    snapshot_from_pair_row,
)


OPERATIONAL_AUTOMATION_VERSION = "product-operational-automation.v1"
PAIR_EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
PAIR_LEAGUE = "EPL"
FROZEN_EPL_MODEL_SHA256 = (
    "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
)
OPERATIONAL_PUBLISHER_VERSION = "product-publisher.pair-ledger-operational.v1"

SOURCE_NO_FUTURE_EVENTS = "NO_FUTURE_EVENTS"
SOURCE_COVERED = "COVERED"
SOURCE_READY_TO_INGEST = "READY_TO_INGEST_PREDICTIONS"
SOURCE_WAITING = "WAITING_FOR_PREDICTION_SOURCE"

CYCLE_HEALTHY_NOOP = "HEALTHY_NOOP"
CYCLE_READY_TO_APPLY = "READY_TO_APPLY"
CYCLE_ACTION_REQUIRED = "ACTION_REQUIRED"

PAIR_COLUMNS = ",".join(
    [
        "experiment_id",
        "league",
        "event_id",
        "provider_home_team",
        "provider_away_team",
        "model_home_team",
        "model_away_team",
        "kickoff_utc",
        "model_generated_at_utc",
        "model_home_prob",
        "model_draw_prob",
        "model_away_prob",
        "model_artifact_sha256",
        "code_commit_sha",
    ]
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = _text(value)
        if not text:
            raise ValueError("timestamp is required")
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def validate_private_supabase_credentials(
    *,
    supabase_url: str | None,
    supabase_key: str | None,
) -> None:
    """Reject missing/public credentials before any write-capable client import."""
    if not _text(supabase_url):
        raise RuntimeError("SUPABASE_URL is required for operational automation")
    key = _text(supabase_key)
    if not key:
        raise RuntimeError("SUPABASE_KEY is required for operational automation")
    if key.startswith("sb_publishable_"):
        raise RuntimeError(
            "Operational automation requires the private SUPABASE_KEY; "
            "publishable credentials are read-only and must never be used as a write fallback"
        )


def _latest_by_event(
    rows: Iterable[Mapping[str, Any]],
    *,
    event_field: str,
    timestamp_field: str,
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        event_id = _text(row.get(event_field))
        if not event_id:
            continue
        timestamp = _dt(row.get(timestamp_field))
        previous = latest.get(event_id)
        if previous is None or timestamp > _dt(previous.get(timestamp_field)):
            latest[event_id] = row
    return latest


def _validate_pair_row(row: Mapping[str, Any]) -> None:
    if _text(row.get("experiment_id")) != PAIR_EXPERIMENT_ID:
        raise ValueError("unexpected pair-ledger experiment_id")
    if _text(row.get("league")) != PAIR_LEAGUE:
        raise ValueError("operational pair bridge only supports EPL")
    event_id = _text(row.get("event_id"))
    if not event_id:
        raise ValueError("pair-ledger event_id is required")
    generated = _dt(row.get("model_generated_at_utc"))
    kickoff = _dt(row.get("kickoff_utc"))
    if generated >= kickoff:
        raise ValueError(f"pair-ledger model generation is not pre-kickoff: {event_id}")
    if _text(row.get("model_artifact_sha256")) != FROZEN_EPL_MODEL_SHA256:
        raise ValueError(f"unexpected EPL model artifact SHA for event {event_id}")


def build_incremental_product_rows(
    pair_rows: Iterable[Mapping[str, Any]],
    product_rows: Iterable[Mapping[str, Any]],
    *,
    now_utc: Any,
    horizon_days: int = 14,
) -> list[dict[str, Any]]:
    """Bridge only genuinely newer durable AI generations into product snapshots."""
    if horizon_days < 1 or horizon_days > 30:
        raise ValueError("horizon_days must be between 1 and 30")
    now = _dt(now_utc)
    horizon = now + timedelta(days=horizon_days)

    eligible_pairs: list[dict[str, Any]] = []
    for raw in pair_rows:
        row = dict(raw)
        kickoff = _dt(row.get("kickoff_utc"))
        if not (now < kickoff < horizon):
            continue
        _validate_pair_row(row)
        eligible_pairs.append(row)

    latest_pairs = _latest_by_event(
        eligible_pairs,
        event_field="event_id",
        timestamp_field="model_generated_at_utc",
    )
    latest_products = _latest_by_event(
        product_rows,
        event_field="event_id",
        timestamp_field="generated_at_utc",
    )

    pending: list[dict[str, Any]] = []
    for event_id, pair in sorted(
        latest_pairs.items(), key=lambda item: _dt(item[1]["kickoff_utc"])
    ):
        previous = latest_products.get(event_id)
        pair_generated = _dt(pair["model_generated_at_utc"])
        if previous is not None:
            previous_generated = _dt(previous["generated_at_utc"])
            if pair_generated <= previous_generated:
                continue

        run_id = f"pair-ledger-operational:{pair_generated.strftime('%Y%m%dT%H%M%SZ')}"
        snapshot = snapshot_from_pair_row(pair, run_id=run_id)
        snapshot["publisher_version"] = OPERATIONAL_PUBLISHER_VERSION
        pending.append(snapshot)

    return pending


def source_coverage(
    odds_rows: Iterable[Mapping[str, Any]],
    product_rows: Iterable[Mapping[str, Any]],
    pair_rows: Iterable[Mapping[str, Any]],
    *,
    pending_product_rows: Iterable[Mapping[str, Any]] = (),
    now_utc: Any,
    horizon_days: int = 14,
) -> dict[str, Any]:
    """Explain whether every known future EPL odds event has a validated AI source."""
    now = _dt(now_utc)
    horizon = now + timedelta(days=horizon_days)

    def future_event_ids(rows: Iterable[Mapping[str, Any]], kickoff_field: str) -> set[str]:
        result: set[str] = set()
        for row in rows:
            event_id = _text(row.get("event_id"))
            if not event_id or _text(row.get("league")) != PAIR_LEAGUE:
                continue
            kickoff = _dt(row.get(kickoff_field))
            if now < kickoff < horizon:
                result.add(event_id)
        return result

    odds_ids = future_event_ids(odds_rows, "commence_time_utc")
    product_ids = future_event_ids(product_rows, "commence_time_utc")
    product_ids |= future_event_ids(pending_product_rows, "commence_time_utc")

    valid_pair_ids: set[str] = set()
    for raw in pair_rows:
        row = dict(raw)
        if _text(row.get("league")) != PAIR_LEAGUE:
            continue
        kickoff = _dt(row.get("kickoff_utc"))
        if not (now < kickoff < horizon):
            continue
        _validate_pair_row(row)
        valid_pair_ids.add(_text(row.get("event_id")))

    missing_product = odds_ids - product_ids
    ready_from_pair = missing_product & valid_pair_ids
    waiting = missing_product - valid_pair_ids

    if not odds_ids:
        state = SOURCE_NO_FUTURE_EVENTS
    elif waiting:
        state = SOURCE_WAITING
    elif ready_from_pair:
        state = SOURCE_READY_TO_INGEST
    else:
        state = SOURCE_COVERED

    return {
        "state": state,
        "known_future_odds_events": len(odds_ids),
        "covered_product_events": len(odds_ids & product_ids),
        "ready_from_pair_ledger": len(ready_from_pair),
        "waiting_for_prediction_source": len(waiting),
        "waiting_event_ids": sorted(waiting),
        "coverage_ratio": (len(odds_ids & product_ids) / len(odds_ids)) if odds_ids else None,
    }


def build_operational_report(
    *,
    coverage: Mapping[str, Any],
    pending_prediction_count: int,
    lifecycle_counts: Mapping[str, Any],
    lifecycle_pending_count: int,
    reliability: Mapping[str, Any] | None = None,
    production_readiness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic automation report without causing side effects."""
    source_state = _text(coverage.get("state"))
    if source_state == SOURCE_WAITING:
        status = CYCLE_ACTION_REQUIRED
    elif pending_prediction_count or lifecycle_pending_count:
        status = CYCLE_READY_TO_APPLY
    else:
        status = CYCLE_HEALTHY_NOOP

    return {
        "schema_version": OPERATIONAL_AUTOMATION_VERSION,
        "status": status,
        "prediction_source": dict(coverage),
        "pending": {
            "product_prediction_snapshots": int(pending_prediction_count),
            "lifecycle_events": int(lifecycle_pending_count),
            "lifecycle_counts": dict(lifecycle_counts),
        },
        "reliability": dict(reliability or {}),
        "production_readiness": dict(production_readiness or {}),
        "safety": {
            "paid_provider_calls": False,
            "the_odds_api_key_required": False,
            "model_inference": False,
            "model_training": False,
            "model_promotion": False,
            "research_target_outcomes_read": False,
            "betting_actions": False,
            "staking_actions": False,
            "prediction_bridge_source": PAIR_TABLE,
            "prediction_destination": PRODUCT_TABLE,
            "lifecycle_writes_append_only": True,
        },
    }
