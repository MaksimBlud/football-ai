"""Public aggregate from immutable Product Lifecycle facts, never raw outcome rows.

Private lifecycle rows are read server-side only with an explicitly private
Supabase credential. The public response contains aggregate EPL 1X2 statistics
and exact model scopes; it cannot expose event IDs, teams, scores, user data,
per-event outcome records, research ledgers, or service credentials.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
from typing import Any, Mapping

from product_lifecycle import (
    EVENT_PREDICTION_REGISTERED,
    EVENT_SETTLED,
    LIFECYCLE_TABLE,
)
from product_reliability import (
    MIN_CALENDAR_MONTHS_FOR_REVIEW,
    MIN_SETTLED_FIXTURES_FOR_REVIEW,
    build_reliability_matrix,
    settled_reliability_records,
    wilson_interval,
)

PUBLIC_SCHEMA = "public-product-history.v1"
PAGE_SIZE = 500
MAX_EVENTS = 10000
EVENT_MARKET_OBSERVED = "MARKET_OBSERVED"
PUBLIC_LEAGUE = "EPL"
# SELECT only necessary lifecycle columns. No service-role source rows appear
# in the serialized public response.
LIFECYCLE_COLUMNS = ",".join((
    "id", "event_type", "source_prediction_snapshot_id",
    "product_match_id", "event_id", "league", "commence_time_utc",
    "source_prediction_created_at_utc", "recorded_at_utc", "payload",
))


def _parse_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("lifecycle timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _read_lifecycle(client: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    while True:
        # Explicitly never read frozen prospective research outcomes.
        response = (
            client.table(LIFECYCLE_TABLE)
            .select(LIFECYCLE_COLUMNS)
            .order("id")
            .range(len(rows), len(rows) + PAGE_SIZE - 1)
            .execute()
        )
        page = list(response.data or [])
        if len(page) > PAGE_SIZE:
            raise ValueError("lifecycle returned oversized page")
        rows.extend(page)
        if len(rows) >= MAX_EVENTS:
            raise ValueError("lifecycle exceeded safe bounded public aggregation")
        if len(page) < PAGE_SIZE:
            return rows


def _sanitized_scope(report: Mapping[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    scope = report["scope"]
    gate = report["evidence_gate"]
    metrics = report["metrics"]
    league = scope["league"]
    sha = scope["model_1x2_sha256"]
    scoped = [
        row for row in records
        if row["league"] == league and row["model_1x2_sha256"] == sha
    ]
    if not league or not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
        raise ValueError("incomplete exact-model provenance")
    n = len(scoped)
    if report["settled_predictions"] != n:
        raise ValueError("inconsistent reliability counts")
    correct = sum(row["prediction_correct"] is True for row in scoped)
    interval = wilson_interval(correct, n)
    return {
        "league": league,
        "model_1x2_sha256": sha,
        "settled_unique_fixtures": n,
        "correct_picks": correct,
        "accuracy": metrics["accuracy"],
        "multiclass_brier": metrics["mean_multiclass_brier"],
        "log_loss": metrics["mean_log_loss"],
        "accuracy_wilson_95": {"lower": interval[0], "upper": interval[1]} if interval else None,
        "first_kickoff_utc": gate.get("first_kickoff_utc"),
        "last_kickoff_utc": gate.get("last_kickoff_utc"),
        "evidence_state": gate["state"],
        "reviewable": gate["reviewable"],
        "reliability_status": "INCONCLUSIVE",
    }


def build_public_product_history(
    events: list[Mapping[str, Any]], *, now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = _parse_utc(now_utc or datetime.now(timezone.utc))
    # Product history can contain other operational leagues in the future.
    # Explicitly scope to EPL rather than either mixing or rejecting them.
    rows = [dict(row) for row in events if row.get("league") == PUBLIC_LEAGUE]
    if len(rows) >= MAX_EVENTS:
        raise ValueError("bounded lifecycle aggregation exceeded")
    ids: set[int] = set()
    for row in rows:
        row_id = int(row["id"])
        if row_id in ids:
            raise ValueError("duplicate lifecycle row ID")
        ids.add(row_id)
        if row.get("event_type") not in (
            EVENT_PREDICTION_REGISTERED, EVENT_MARKET_OBSERVED, EVENT_SETTLED
        ):
            raise ValueError("unrecognized product lifecycle event")
        if _parse_utc(row["recorded_at_utc"]) > now:
            raise ValueError("future lifecycle event in as-of historical report")
        if _parse_utc(row["source_prediction_created_at_utc"]) >= _parse_utc(row["commence_time_utc"]):
            raise ValueError("non-prekickoff prediction is not eligible")

    matrix = build_reliability_matrix(rows)
    records = settled_reliability_records(rows)
    seen_fixtures: set[tuple[str, str]] = set()
    for record in records:
        # No duplicate fixture can inflate public accuracy or sample gate even
        # when it came from another snapshot/version for that same EPL event.
        identity = (record["league"], record["product_match_id"])
        if not identity[1] or identity in seen_fixtures:
            raise ValueError("duplicate or missing settled product fixture identity")
        seen_fixtures.add(identity)

    counts = Counter(row["event_type"] for row in rows)
    scopes = [
        _sanitized_scope(report, records)
        for report in matrix["model_league_slices"]
        if report["scope"]["league"] == PUBLIC_LEAGUE
    ]
    if sum(item["settled_unique_fixtures"] for item in scopes) != len(records):
        raise ValueError("unknown or incomplete settled model provenance")
    latest = max((_parse_utc(row["recorded_at_utc"]) for row in rows), default=None)
    return {
        "schema_version": PUBLIC_SCHEMA,
        "as_of_utc": now.isoformat(),
        "last_lifecycle_fact_utc": latest.isoformat() if latest else None,
        "league": PUBLIC_LEAGUE,
        "market": "1x2",
        "events": {
            "prediction_registered": counts[EVENT_PREDICTION_REGISTERED],
            "market_observed": counts[EVENT_MARKET_OBSERVED],
            "settled": counts[EVENT_SETTLED],
        },
        "settled_unique_fixtures": len(records),
        "model_scopes": scopes,
        "policy": {
            "minimum_settled_fixtures_for_review": MIN_SETTLED_FIXTURES_FOR_REVIEW,
            "minimum_calendar_months_for_review": MIN_CALENDAR_MONTHS_FOR_REVIEW,
            "reliability_verdict": "INCONCLUSIVE",
            "evaluated_market": "1x2_model_probability",
            "betting_action": "NO_BET",
            "roi": None,
            "clv": None,
            "staking": None,
            "prediction_sources": "immutable_product_lifecycle_only",
            "contains_raw_outcomes": False,
            "includes_market_only_research": False,
            "automatic_model_promotion": False,
        },
    }


def load_public_product_history(client: Any, *, now_utc: datetime | None = None) -> dict[str, Any]:
    """Never downgrade missing private lifecycle access into empty public data."""
    return build_public_product_history(_read_lifecycle(client), now_utc=now_utc)
