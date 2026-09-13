"""Run Product Operational Automation v1 from durable Supabase sources.

Default mode is dry-run. ``--publish`` performs only two append-only operations:
1. newer outcome-free EPL pair-ledger AI generations -> product snapshots;
2. missing product lifecycle facts from stored odds + canonical finished results.

No provider call, inference, training, model promotion, research target read, bet,
or stake occurs here.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from advance_product_lifecycle import build_lifecycle_pass, load_live_inputs
from product_lifecycle import LIFECYCLE_TABLE, REGISTRATION_MODE_LIVE
from product_operational_automation import (
    OPERATIONAL_AUTOMATION_VERSION,
    PAIR_COLUMNS,
    PAIR_TABLE,
    PRODUCT_TABLE,
    build_incremental_product_rows,
    build_operational_report,
    source_coverage,
    validate_private_supabase_credentials,
)
from product_reliability import build_reliability_matrix
from product_snapshot_store import build_product_view_from_snapshot_rows


DEFAULT_PAGE_SIZE = 1000
DEFAULT_REPORT_PATH = Path("artifacts/product_operational_automation/report.json")


def _dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _fetch_pair_rows(client: Any, *, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (
            client.table(PAIR_TABLE)
            .select(PAIR_COLUMNS)
            .order("model_generated_at_utc")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        page = response.data or []
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return rows


def _future_rows(rows: list[dict[str, Any]], *, field: str, now: datetime, horizon: datetime) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        moment = _dt(value)
        if now < moment < horizon:
            result.append(row)
    return result


def _plan(
    *,
    pair_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    odds: list[dict[str, Any]],
    results: list[dict[str, Any]],
    lifecycle: list[dict[str, Any]],
    now: datetime,
    horizon_days: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    pending_predictions = build_incremental_product_rows(
        pair_rows,
        predictions,
        now_utc=now,
        horizon_days=horizon_days,
    )
    coverage = source_coverage(
        odds,
        predictions,
        pair_rows,
        now_utc=now,
        horizon_days=horizon_days,
    )
    existing_keys = {str(row.get("event_key") or "").strip() for row in lifecycle}
    lifecycle_plan = build_lifecycle_pass(
        predictions,
        odds,
        results,
        existing_event_keys=existing_keys,
        now_utc=now,
        registration_mode=REGISTRATION_MODE_LIVE,
    )
    return pending_predictions, coverage, lifecycle_plan


def _append_predictions(client: Any, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    response = client.table(PRODUCT_TABLE).insert(rows).execute()
    inserted = len(response.data or [])
    if inserted != len(rows):
        raise RuntimeError(f"expected {len(rows)} product snapshots, inserted {inserted}")


def _append_lifecycle(client: Any, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    response = client.table(LIFECYCLE_TABLE).insert(rows).execute()
    inserted = len(response.data or [])
    if inserted != len(rows):
        raise RuntimeError(f"expected {len(rows)} lifecycle events, inserted {inserted}")


def _final_report(
    *,
    pair_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    odds: list[dict[str, Any]],
    results: list[dict[str, Any]],
    lifecycle: list[dict[str, Any]],
    now: datetime,
    horizon_days: int,
) -> dict[str, Any]:
    pending_predictions, coverage, lifecycle_plan = _plan(
        pair_rows=pair_rows,
        predictions=predictions,
        odds=odds,
        results=results,
        lifecycle=lifecycle,
        now=now,
        horizon_days=horizon_days,
    )
    horizon = now + timedelta(days=horizon_days)
    future_predictions = _future_rows(
        predictions, field="commence_time_utc", now=now, horizon=horizon
    )
    future_odds = _future_rows(odds, field="commence_time_utc", now=now, horizon=horizon)
    product_view = build_product_view_from_snapshot_rows(future_predictions, future_odds)
    reliability = build_reliability_matrix(lifecycle)
    report = build_operational_report(
        coverage=coverage,
        pending_prediction_count=len(pending_predictions),
        lifecycle_counts=lifecycle_plan["counts"],
        lifecycle_pending_count=len(lifecycle_plan["events"]),
        reliability={
            "schema_version": reliability.get("schema_version"),
            "settled_predictions": (
                reliability.get("overall_history") or {}
            ).get("settled_predictions"),
            "evidence_state": (
                (reliability.get("overall_history") or {}).get("evidence_gate") or {}
            ).get("state"),
        },
        production_readiness=product_view.get("production_readiness"),
    )
    report["as_of_utc"] = now.isoformat()
    report["horizon_days"] = horizon_days
    report["source_counts"] = {
        "pair_ledger_rows": len(pair_rows),
        "product_prediction_rows": len(predictions),
        "odds_snapshot_rows": len(odds),
        "canonical_result_rows": len(results),
        "lifecycle_rows": len(lifecycle),
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--as-of-utc", default=None)
    parser.add_argument("--horizon-days", type=int, default=14)
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()
    if args.horizon_days < 1 or args.horizon_days > 30:
        parser.error("--horizon-days must be between 1 and 30")
    return args


def main() -> None:
    args = parse_args()
    validate_private_supabase_credentials(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
    )

    # Import only after private-credential preflight so public config can never
    # become an accidental write-capable fallback.
    from database import supabase

    now = _dt(args.as_of_utc or datetime.now(timezone.utc))
    pair_rows = _fetch_pair_rows(supabase)
    predictions, odds, results, lifecycle = load_live_inputs(supabase)

    pending_predictions, _coverage, lifecycle_plan = _plan(
        pair_rows=pair_rows,
        predictions=predictions,
        odds=odds,
        results=results,
        lifecycle=lifecycle,
        now=now,
        horizon_days=args.horizon_days,
    )

    if args.publish:
        _append_predictions(supabase, pending_predictions)
        if pending_predictions:
            predictions, odds, results, lifecycle = load_live_inputs(supabase)
            lifecycle_plan = build_lifecycle_pass(
                predictions,
                odds,
                results,
                existing_event_keys={
                    str(row.get("event_key") or "").strip() for row in lifecycle
                },
                now_utc=now,
                registration_mode=REGISTRATION_MODE_LIVE,
            )
        _append_lifecycle(supabase, lifecycle_plan["events"])
        predictions, odds, results, lifecycle = load_live_inputs(supabase)
    else:
        print("DRY RUN: no Supabase rows written.")

    report = _final_report(
        pair_rows=pair_rows,
        predictions=predictions,
        odds=odds,
        results=results,
        lifecycle=lifecycle,
        now=now,
        horizon_days=args.horizon_days,
    )
    report["publish_mode"] = bool(args.publish)

    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"PASS: {OPERATIONAL_AUTOMATION_VERSION} status={report['status']}")


if __name__ == "__main__":
    main()
