"""Read-only, bounded source-health report for the public EPL forecast site.

This is diagnostic metadata, not a forecast generator, an automated collector,
or evidence that a new round will be ingested without manual/provider action.
No service-role lifecycle tables, model hashes, or research outcomes are read.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from product_snapshot_store import (
    ODDS_COLUMNS,
    ODDS_TABLE,
    PREDICTION_COLUMNS,
    PREDICTION_TABLE,
    _parse_datetime,
    build_product_view_from_snapshot_rows,
)


SCHEMA_VERSION = "website-source-health.v1"
MAX_PREDICTION_ROWS = 1000
MAX_ODDS_ROWS = 5000


def _future_rows(client: Any, table: str, columns: str, timestamp: str, *,
                 now: datetime, horizon: datetime, limit: int) -> list[dict[str, Any]]:
    response = (
        client.table(table)
        .select(columns)
        .gt("commence_time_utc", now.isoformat())
        .lt("commence_time_utc", horizon.isoformat())
        .lte(timestamp, now.isoformat())
        .order(timestamp, desc=True)
        .limit(limit)
        .execute()
    )
    rows = list(response.data or [])
    if len(rows) >= limit:
        raise ValueError(f"{table} source-health query reached {limit}-row limit")
    for row in rows:
        kickoff = _parse_datetime(row.get("commence_time_utc"))
        captured = _parse_datetime(row.get(timestamp))
        if not (now < kickoff < horizon and captured <= now and captured < kickoff):
            raise ValueError(f"{table} returned invalid as-of or kickoff timestamp")
    return rows


def load_website_source_health(client: Any, *, now_utc: datetime | None = None,
                               horizon_days: int = 14) -> dict[str, Any]:
    """Report independent future market coverage without inventing predictions.

    An odds-only future event counts as WAITING_FOR_PREDICTION_SOURCE, not as
    proof of an available AI forecast. A valid model-only event counts as
    NO_PROVIDER_SNAPSHOTS, not as a verified bookmaker comparison.
    """
    if not 1 <= horizon_days <= 30:
        raise ValueError("horizon_days must be between 1 and 30")
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    now = now.astimezone(timezone.utc)
    horizon = now + timedelta(days=horizon_days)

    # Query both independently. Filtering odds to existing prediction IDs would
    # hide the very missing-source failure this diagnostic is meant to detect.
    predictions = _future_rows(
        client, PREDICTION_TABLE, PREDICTION_COLUMNS, "generated_at_utc",
        now=now, horizon=horizon, limit=MAX_PREDICTION_ROWS,
    )
    odds = _future_rows(
        client, ODDS_TABLE, ODDS_COLUMNS, "snapshot_time_utc",
        now=now, horizon=horizon, limit=MAX_ODDS_ROWS,
    )

    # Exactly the same backend eligibility and strict quote identity as the
    # public forecast feed. No private model SHA or probability is returned.
    view = build_product_view_from_snapshot_rows(predictions, odds)
    forecast_events = {
        str(item["match"].get("event_id") or "").strip()
        for item in view["matches"]
        if str(item["match"].get("event_id") or "").strip()
    }
    odds_events = {
        str(row.get("event_id") or "").strip()
        for row in odds
        if str(row.get("event_id") or "").strip()
    }
    priced = int(view["data_source"]["priced_event_count"])
    missing_forecasts = odds_events - forecast_events

    if not odds_events and not forecast_events:
        state = "NO_FUTURE_EVENTS"
    elif not odds_events:
        state = "NO_PROVIDER_SNAPSHOTS"
    elif not forecast_events or missing_forecasts:
        state = "WAITING_FOR_PREDICTION_SOURCE"
    elif priced < len(forecast_events):
        state = "PARTIAL_VERIFIED_COVERAGE"
    else:
        state = "COVERED"

    # Count-only public summary. Event IDs, individual private source rows,
    # lifecycle payloads, model artifact hashes, and odds are never returned.
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of_utc": now.isoformat(),
        "horizon_days": horizon_days,
        "state": state,
        "future_ai_events": len(forecast_events),
        "future_provider_odds_events": len(odds_events),
        "verified_prediction_market_pairs": priced,
        "provider_events_waiting_for_ai": len(missing_forecasts),
        "ai_events_without_verified_price": max(0, len(forecast_events) - priced),
        "earliest_model_kickoff_utc": min(
            (item["match"]["commence_time_utc"] for item in view["matches"]),
            default=None,
        ),
        "latest_model_generated_at_utc": max(
            (_parse_datetime(row["generated_at_utc"]).isoformat() for row in predictions),
            default=None,
        ),
        "latest_odds_snapshot_time_utc": max(
            (_parse_datetime(row["snapshot_time_utc"]).isoformat() for row in odds),
            default=None,
        ),
        "source_tables": {
            "ai": PREDICTION_TABLE,
            "market": ODDS_TABLE,
        },
        "safety": {
            "read_only": True,
            "provider_calls": False,
            "model_inference": False,
            "market_prices_are_live": False,
            "model_hashes_exposed": False,
        },
    }
