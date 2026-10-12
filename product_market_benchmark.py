"""Strict read-only EPL model-vs-bookmaker benchmark from immutable PRODUCT facts.

Comparison uses *only* the bookmaker prices frozen at model registration, not
post-hoc/closing odds. Each registered, already-settled product fixture is one
paired observation. Legacy bootstrap and live-publish are always separated.

No prospective research outcomes, raw match identities in output, retraining,
recalibration, model promotion, paid provider calls, database writes or bets.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from product_lifecycle import EVENT_PREDICTION_REGISTERED
from product_reliability import (
    MIN_CALENDAR_MONTHS_FOR_REVIEW,
    MIN_SETTLED_FIXTURES_FOR_REVIEW,
    settled_reliability_records,
    wilson_interval,
)

SCHEMA = "product-epl-market-benchmark.v1"
OUTCOMES = ("HOME", "DRAW", "AWAY")
MODES = ("legacy_source_snapshot_bootstrap", "live_publish")
MARKET_ROLE = "latest_stored_observation_at_or_before_source_snapshot"


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("missing market/provenance time")
    if dt.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _number(value: Any, name: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError("missing or invalid " + name)
    try:
        f = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid " + name) from exc
    if not math.isfinite(f):
        raise ValueError("non-finite " + name)
    return f


def _market_vector(registration: Mapping[str, Any]) -> tuple[float, float, float]:
    payload = registration.get("payload") or {}
    reference = payload.get("market_reference_at_registration")
    if not isinstance(reference, Mapping):
        raise ValueError("no frozen market-at-registration reference")
    if reference.get("role") != MARKET_ROLE or reference.get("is_closing_qualified") is not False:
        raise ValueError("market reference is not qualified as a stored non-closing quote")

    kickoff = _utc(registration.get("commence_time_utc"))
    created = _utc(registration.get("source_prediction_created_at_utc"))
    snap = _utc(reference.get("snapshot_time_utc"))
    if not snap <= created < kickoff:
        raise ValueError("market/forecast timestamp is not pre-kickoff")
    age = _number(reference.get("age_seconds_at_prediction_record"), "market age")
    if age < 0 or not math.isclose(age, (created - snap).total_seconds(), abs_tol=1.0):
        raise ValueError("market age differs from source chronology")

    odds = tuple(_number(reference.get(k), k) for k in ("home_odds", "draw_odds", "away_odds"))
    if any(x <= 1 for x in odds):
        raise ValueError("invalid decimal bookmaker odds")
    inverses = tuple(1.0 / x for x in odds)
    total = sum(inverses)
    if not 0.0 < total < math.inf:
        raise ValueError("invalid market implied probability total")
    return tuple(value / total for value in inverses)


def _pick(vector: tuple[float, float, float]) -> str:
    return OUTCOMES[max(range(3), key=lambda i: vector[i])]


def _scores(vector: tuple[float, float, float], actual: str) -> tuple[float, float]:
    index = OUTCOMES.index(actual)
    return (
        sum((p - float(i == index)) ** 2 for i, p in enumerate(vector)),
        -math.log(max(vector[index], 1e-15)),
    )


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    model_hits = sum(x["model_pick"] == x["actual"] for x in rows)
    market_hits = sum(x["market_pick"] == x["actual"] for x in rows)

    def average(key: str) -> float | None:
        return sum(x[key] for x in rows) / n if n else None

    def counts(key: str) -> dict[str, int]:
        return {outcome: sum(x[key] == outcome for x in rows) for outcome in OUTCOMES}

    return {
        "settled_fixtures": n,
        "model_correct": model_hits,
        "market_correct": market_hits,
        "model_accuracy": model_hits / n if n else None,
        "market_accuracy": market_hits / n if n else None,
        "model_accuracy_wilson_95": wilson_interval(model_hits, n),
        "market_accuracy_wilson_95": wilson_interval(market_hits, n),
        "model_brier": average("model_brier"),
        "market_brier": average("market_brier"),
        "model_log_loss": average("model_log_loss"),
        "market_log_loss": average("market_log_loss"),
        "paired_brier_delta_model_minus_market": (
            average("model_brier") - average("market_brier") if n else None
        ),
        "paired_log_loss_delta_model_minus_market": (
            average("model_log_loss") - average("market_log_loss") if n else None
        ),
        "model_pick_counts": counts("model_pick"),
        "market_pick_counts": counts("market_pick"),
        "actual_outcome_counts": counts("actual"),
        "mean_model_probabilities": {
            outcome: average("model_" + outcome.lower()) for outcome in OUTCOMES
        },
        "mean_market_probabilities": {
            outcome: average("market_" + outcome.lower()) for outcome in OUTCOMES
        },
        "model_market_pick_agreements": sum(x["model_pick"] == x["market_pick"] for x in rows),
    }


def build_product_market_benchmark(
    events: Iterable[Mapping[str, Any]], *, league: str = "EPL",
    model_sha256: str | None = None,
) -> dict[str, Any]:
    """Produce aggregate-only paired comparison. No inferred predictions/results."""
    if league != "EPL":
        raise ValueError("this report is EPL-only")
    values = [dict(x) for x in events]
    settled = settled_reliability_records(values)  # validates frozen score/provenance
    selected = [r for r in settled if r["league"] == league]
    shas = {r["model_1x2_sha256"] for r in selected}
    if model_sha256 is not None:
        if len(model_sha256) != 64 or any(c not in "0123456789abcdef" for c in model_sha256):
            raise ValueError("model artifact SHA must be 64 lowercase hex")
        selected = [r for r in selected if r["model_1x2_sha256"] == model_sha256]
        shas = {r["model_1x2_sha256"] for r in selected}
    if len(shas) > 1:
        raise ValueError("cannot pool different 1X2 model artifacts")
    if selected and (len(shas) != 1 or len(next(iter(shas))) != 64 or
                     any(c not in "0123456789abcdef" for c in next(iter(shas)))):
        raise ValueError("settled predictions missing model artifact SHA")

    source = {}
    for event in values:
        if event.get("event_type") != EVENT_PREDICTION_REGISTERED:
            continue
        snapshot_id = int(event["source_prediction_snapshot_id"])
        if snapshot_id in source:
            raise ValueError("duplicate source registration")
        source[snapshot_id] = event

    seen_fixtures: set[str] = set()
    rows: list[dict[str, Any]] = []
    for record in selected:
        fixture = record["product_match_id"]
        if not fixture or fixture in seen_fixtures:
            raise ValueError("duplicate settled fixture across snapshots")
        seen_fixtures.add(fixture)
        reg = source[record["source_prediction_snapshot_id"]]
        raw_prediction = (reg.get("payload") or {}).get("prediction") or {}
        model = tuple(
            _number(raw_prediction.get(key), key)
            for key in ("home_probability", "draw_probability", "away_probability")
        )
        if any(v < 0 or v > 1 for v in model) or not math.isclose(sum(model), 1, abs_tol=1e-9):
            raise ValueError("invalid frozen model probabilities")
        market = _market_vector(reg)
        mode = record["registration_mode"]
        if mode not in MODES:
            raise ValueError("registration provenance mode unknown")
        outcome = record["actual_outcome"]
        if outcome not in OUTCOMES:
            raise ValueError("settled outcome outside 1X2 scope")
        model_brier, model_log = _scores(model, outcome)
        market_brier, market_log = _scores(market, outcome)
        rows.append({
            "mode": mode,
            "actual": outcome,
            "model_pick": _pick(model),
            "market_pick": _pick(market),
            "model_brier": model_brier, "market_brier": market_brier,
            "model_log_loss": model_log, "market_log_loss": market_log,
            **{"model_" + key.lower(): value for key, value in zip(OUTCOMES, model)},
            **{"market_" + key.lower(): value for key, value in zip(OUTCOMES, market)},
        })

    n = len(rows)
    return {
        "schema_version": SCHEMA,
        "league": league,
        "market": "1x2",
        "model_sha256": next(iter(shas)) if shas else model_sha256,
        "source": "immutable PRODUCT PREDICTION_REGISTERED + SETTLED events",
        "comparator": "no-vig probabilities from frozen bookmaker odds at registration",
        "is_closing_line": False,
        "is_prospective_research": False,
        "population": "settled_product_predictions_with_frozen_market_reference",
        "overall": _summary(rows),
        "by_registration_mode": {mode: _summary([x for x in rows if x["mode"] == mode]) for mode in MODES},
        "sample_gate_minimum": MIN_SETTLED_FIXTURES_FOR_REVIEW,
        "calendar_gate_months": MIN_CALENDAR_MONTHS_FOR_REVIEW,
        "reviewable": False,  # Benchmark is descriptive; frozen reliability gate remains separate.
        "verdict": "DESCRIPTIVE_ONLY_INCONCLUSIVE",
        "no_bet": True,
        "roi": None, "clv": None, "promotion": False,
        "training_performed": False, "provider_calls": 0,
    }
