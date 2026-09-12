"""Advance the append-only product lifecycle from already-stored data.

No model inference, training, paid provider call, or external result fetch occurs.
Default mode is dry-run. Live insertion requires --publish.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from product_lifecycle import (
    EVENT_SETTLED,
    LIFECYCLE_TABLE,
    REGISTRATION_MODE_LEGACY_BOOTSTRAP,
    REGISTRATION_MODE_LIVE,
    build_market_observed_event,
    build_prediction_registered_event,
    build_settled_event,
    performance_summary,
)
from product_markets import build_product_match
from team_names import normalize_team_name


PREDICTION_TABLE = "product_prediction_snapshots"
ODDS_TABLE = "odds_snapshots"
RESULT_TABLE = "league_finished_results"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dt(value: Any) -> datetime:
    text = _text(value)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _fixture_result_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _text(row.get("league")),
        _text(row.get("match_date")),
        normalize_team_name(_text(row.get("home_team"))),
        normalize_team_name(_text(row.get("away_team"))),
    )


def index_results(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    indexed: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        key = _fixture_result_key(row)
        previous = indexed.get(key)
        if previous is not None:
            identity = (
                _text(previous.get("result")),
                _text(previous.get("home_goals")),
                _text(previous.get("away_goals")),
            )
            candidate = (
                _text(row.get("result")),
                _text(row.get("home_goals")),
                _text(row.get("away_goals")),
            )
            if identity != candidate:
                raise ValueError(f"conflicting canonical results for {key}")
            if _text(row.get("persisted_at_utc")) > _text(previous.get("persisted_at_utc")):
                indexed[key] = row
        else:
            indexed[key] = row
    return indexed


def odds_for_event(
    odds_rows: Iterable[Mapping[str, Any]],
    *,
    event_id: str,
    at_or_before: datetime,
) -> dict[str, Any] | None:
    candidates = []
    for raw in odds_rows:
        row = dict(raw)
        if _text(row.get("event_id")) != event_id:
            continue
        snapshot_time = _dt(row.get("snapshot_time_utc"))
        if snapshot_time <= at_or_before:
            candidates.append((snapshot_time, row))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _decision_payload(prediction: Mapping[str, Any], odds: Mapping[str, Any] | None) -> dict[str, Any]:
    market = build_product_match(prediction, odds)
    return {
        "framework_version": market.get("decision_framework_version"),
        "main_forecast": market.get("main_forecast"),
        "alternatives": market.get("alternatives"),
        "value_signal": market.get("value_signal"),
        "confidence": market.get("confidence"),
        "bet_decision": market.get("bet_decision"),
    }


def build_lifecycle_pass(
    prediction_rows: Iterable[Mapping[str, Any]],
    odds_rows: Iterable[Mapping[str, Any]],
    result_rows: Iterable[Mapping[str, Any]],
    *,
    existing_event_keys: set[str] | None = None,
    now_utc: Any | None = None,
    registration_mode: str = REGISTRATION_MODE_LIVE,
) -> dict[str, Any]:
    """Build missing append-only lifecycle facts without mutating inputs."""
    if registration_mode not in {
        REGISTRATION_MODE_LIVE,
        REGISTRATION_MODE_LEGACY_BOOTSTRAP,
    }:
        raise ValueError("unsupported registration mode")

    now = _dt(now_utc or datetime.now(timezone.utc).isoformat())
    predictions = [dict(row) for row in prediction_rows]
    odds = [dict(row) for row in odds_rows]
    results = index_results(result_rows)
    known = set(existing_event_keys or set())

    pending: list[dict[str, Any]] = []
    counters = {
        "registered": 0,
        "market_observed": 0,
        "settled": 0,
        "skipped_non_pre_kickoff": 0,
    }

    for prediction in predictions:
        kickoff = _dt(prediction.get("commence_time_utc"))
        source_created = _dt(prediction.get("created_at"))
        if source_created >= kickoff:
            counters["skipped_non_pre_kickoff"] += 1
            continue

        snapshot_id = prediction.get("id")
        reg_key = f"prediction_registered:{snapshot_id}"
        event_id = _text(prediction.get("event_id"))
        registration_odds = (
            odds_for_event(odds, event_id=event_id, at_or_before=source_created)
            if event_id
            else None
        )

        if reg_key not in known:
            decision = None
            if registration_mode == REGISTRATION_MODE_LIVE:
                decision = _decision_payload(prediction, registration_odds)
            event = build_prediction_registered_event(
                prediction,
                recorded_at_utc=now,
                registration_mode=registration_mode,
                market_reference=registration_odds,
                decision_payload=decision,
            )
            pending.append(event)
            known.add(event["event_key"])
            counters["registered"] += 1

        if now >= kickoff and event_id:
            market_odds = odds_for_event(odds, event_id=event_id, at_or_before=kickoff)
            if market_odds is not None:
                market_key = f"market_observed:{snapshot_id}:{market_odds.get('id')}"
                if market_key not in known:
                    event = build_market_observed_event(
                        prediction,
                        market_odds,
                        recorded_at_utc=now,
                    )
                    pending.append(event)
                    known.add(event["event_key"])
                    counters["market_observed"] += 1

        result = results.get(_fixture_result_key(prediction))
        if result is not None:
            event = build_settled_event(
                prediction,
                result,
                recorded_at_utc=now,
            )
            if event["event_key"] not in known:
                pending.append(event)
                known.add(event["event_key"])
                counters["settled"] += 1

    return {"events": pending, "counts": counters}


def _fetch_all(client: Any, table: str, *, order: str | None = None, limit: int = 5000) -> list[dict[str, Any]]:
    query = client.table(table).select("*")
    if order:
        query = query.order(order)
    response = query.limit(limit).execute()
    return response.data or []


def load_live_inputs(client: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    predictions = _fetch_all(client, PREDICTION_TABLE, order="created_at")
    odds = _fetch_all(client, ODDS_TABLE, order="snapshot_time_utc")
    results = _fetch_all(client, RESULT_TABLE, order="match_date")
    lifecycle = _fetch_all(client, LIFECYCLE_TABLE, order="recorded_at_utc")
    return predictions, odds, results, lifecycle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registration-mode",
        choices=(REGISTRATION_MODE_LIVE, REGISTRATION_MODE_LEGACY_BOOTSTRAP),
        default=REGISTRATION_MODE_LIVE,
        help=(
            "Use legacy_source_snapshot_bootstrap only for durable snapshots that "
            "predate lifecycle rollout; it never retroactively attaches a decision framework."
        ),
    )
    parser.add_argument("--as-of-utc", default=None)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Append missing lifecycle events. Without this flag: dry-run only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from database import supabase

    predictions, odds, results, lifecycle = load_live_inputs(supabase)
    existing_keys = {_text(row.get("event_key")) for row in lifecycle}
    built = build_lifecycle_pass(
        predictions,
        odds,
        results,
        existing_event_keys=existing_keys,
        now_utc=args.as_of_utc,
        registration_mode=args.registration_mode,
    )
    pending = built["events"]

    if args.publish and pending:
        response = supabase.table(LIFECYCLE_TABLE).insert(pending).execute()
        inserted = len(response.data or [])
        if inserted != len(pending):
            raise RuntimeError(f"expected {len(pending)} inserted events, received {inserted}")
        lifecycle.extend(response.data or [])
    elif args.publish:
        print("No missing lifecycle events.")
    else:
        print("DRY RUN: no lifecycle rows written.")

    print("Lifecycle pass:", built["counts"])
    print("Pending events:", len(pending))
    settled = [row for row in lifecycle if _text(row.get("event_type")) == EVENT_SETTLED]
    if not args.publish:
        settled.extend(
            event for event in pending if _text(event.get("event_type")) == EVENT_SETTLED
        )
    print("Performance summary:", performance_summary(settled))


if __name__ == "__main__":
    main()
