"""Empirical Reliability / Calibration Layer v1 for Football AI.

The layer reads immutable Product Prediction Lifecycle events and produces
reproducible forecast-quality evidence. It does not train/calibrate models,
change probabilities, promote a model/market, change Product Decision tiers,
or create betting recommendations.

Primary reliability claims are scoped to an exact 1X2 model artifact SHA and
league. Cross-model history is descriptive only.
"""

from __future__ import annotations

import calendar
import math
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from product_lifecycle import (
    EVENT_PREDICTION_REGISTERED,
    EVENT_SETTLED,
)


RELIABILITY_SCHEMA_VERSION = "product-reliability.v1"
MARKET_SCOPE = "1x2_model_probability"
MIN_SETTLED_FIXTURES_FOR_REVIEW = 100
MIN_CALENDAR_MONTHS_FOR_REVIEW = 4
WILSON_95_Z = 1.959963984540054
UNIFORM_1X2_BRIER = 2.0 / 3.0
UNIFORM_1X2_LOG_LOSS = math.log(3.0)
OUTCOMES = ("HOME", "DRAW", "AWAY")
OUTCOME_TO_INDEX = {outcome: index for index, outcome in enumerate(OUTCOMES)}

EVIDENCE_NO_DATA = "NO_SETTLED_DATA"
EVIDENCE_ACCUMULATING_SAMPLE = "ACCUMULATING_SAMPLE"
EVIDENCE_ACCUMULATING_TIME = "ACCUMULATING_TIME"
EVIDENCE_REVIEWABLE = "REVIEWABLE"
EVIDENCE_DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _finite_float(value: Any, *, label: str) -> float:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{label} is required")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{label} must be finite")
    return parsed


def _utc_datetime(value: Any, *, label: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = _text(value)
        if not text:
            raise ValueError(f"{label} is required")
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _add_calendar_months(value: datetime, months: int) -> datetime:
    if months < 0:
        raise ValueError("months must be non-negative")
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def wilson_interval(successes: int, total: int) -> tuple[float, float] | None:
    """Return a 95% Wilson interval for a binomial hit rate."""
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("invalid successes/total")
    if total == 0:
        return None
    z2 = WILSON_95_Z**2
    p = successes / total
    denominator = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denominator
    margin = (
        WILSON_95_Z
        * math.sqrt(p * (1.0 - p) / total + z2 / (4.0 * total**2))
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def _registration_index(
    events: Iterable[Mapping[str, Any]],
) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for raw in events:
        if _text(raw.get("event_type")) != EVENT_PREDICTION_REGISTERED:
            continue
        row = dict(raw)
        snapshot_id = int(row["source_prediction_snapshot_id"])
        if snapshot_id in indexed:
            raise ValueError(
                f"duplicate PREDICTION_REGISTERED event for snapshot {snapshot_id}"
            )
        indexed[snapshot_id] = row
    return indexed


def _settlement_index(
    events: Iterable[Mapping[str, Any]],
) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for raw in events:
        if _text(raw.get("event_type")) != EVENT_SETTLED:
            continue
        row = dict(raw)
        snapshot_id = int(row["source_prediction_snapshot_id"])
        if snapshot_id in indexed:
            raise ValueError(
                "multiple SETTLED facts for one prediction require an explicit "
                f"result-correction contract; snapshot={snapshot_id}"
            )
        indexed[snapshot_id] = row
    return indexed


def _frozen_probability_vector(prediction: Mapping[str, Any]) -> tuple[float, float, float]:
    vector = tuple(
        _finite_float(prediction.get(key), label=key)
        for key in ("home_probability", "draw_probability", "away_probability")
    )
    if any(value < 0.0 or value > 1.0 for value in vector):
        raise ValueError("frozen registration probability outside [0,1]")
    if not math.isclose(sum(vector), 1.0, abs_tol=1e-9):
        raise ValueError("frozen registration probabilities do not sum to one")
    return vector


def _verify_settlement_metrics(
    prediction: Mapping[str, Any],
    settlement_payload: Mapping[str, Any],
) -> tuple[float, float, float, bool, str, str]:
    vector = _frozen_probability_vector(prediction)
    actual_outcome = _text(settlement_payload.get("actual_outcome"))
    if actual_outcome not in OUTCOME_TO_INDEX:
        raise ValueError("settlement actual_outcome must be HOME, DRAW or AWAY")
    actual_index = OUTCOME_TO_INDEX[actual_outcome]
    model_index = max(range(3), key=lambda index: vector[index])
    model_pick = OUTCOMES[model_index]
    model_pick_probability = vector[model_index]
    expected_correct = model_pick == actual_outcome

    one_hot = [0.0, 0.0, 0.0]
    one_hot[actual_index] = 1.0
    expected_brier = sum((vector[i] - one_hot[i]) ** 2 for i in range(3))
    expected_log_loss = -math.log(max(vector[actual_index], 1e-15))

    stored_pick = _text(settlement_payload.get("model_pick"))
    stored_probability = _finite_float(
        settlement_payload.get("model_pick_probability"),
        label="model_pick_probability",
    )
    stored_brier = _finite_float(
        settlement_payload.get("multiclass_brier"), label="multiclass_brier"
    )
    stored_log_loss = _finite_float(
        settlement_payload.get("log_loss"), label="log_loss"
    )
    stored_correct = settlement_payload.get("prediction_correct") is True

    if stored_pick != model_pick:
        raise ValueError("settlement model_pick disagrees with frozen probabilities")
    if stored_correct != expected_correct:
        raise ValueError("settlement prediction_correct disagrees with frozen probabilities")
    for label, stored, expected in (
        ("model_pick_probability", stored_probability, model_pick_probability),
        ("multiclass_brier", stored_brier, expected_brier),
        ("log_loss", stored_log_loss, expected_log_loss),
    ):
        if not math.isclose(stored, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"settlement {label} disagrees with frozen probabilities")

    return (
        model_pick_probability,
        expected_brier,
        expected_log_loss,
        expected_correct,
        model_pick,
        actual_outcome,
    )


def settled_reliability_records(
    events: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Join settled facts to their frozen registration provenance and verify scores."""
    rows = [dict(event) for event in events]
    registrations = _registration_index(rows)
    settlements = _settlement_index(rows)
    output: list[dict[str, Any]] = []

    for snapshot_id, settlement in sorted(settlements.items()):
        registration = registrations.get(snapshot_id)
        if registration is None:
            raise ValueError(
                f"SETTLED event has no PREDICTION_REGISTERED provenance: {snapshot_id}"
            )
        if _text(registration.get("product_match_id")) != _text(
            settlement.get("product_match_id")
        ):
            raise ValueError("registration/settlement product_match_id mismatch")
        if _text(registration.get("league")) != _text(settlement.get("league")):
            raise ValueError("registration/settlement league mismatch")

        registration_payload = dict(registration.get("payload") or {})
        prediction = dict(registration_payload.get("prediction") or {})
        settlement_payload = dict(settlement.get("payload") or {})
        if _text(settlement_payload.get("settlement_scope")) != MARKET_SCOPE:
            raise ValueError("unsupported settlement scope in reliability layer")

        (
            probability,
            brier,
            log_loss,
            prediction_correct,
            model_pick,
            actual_outcome,
        ) = _verify_settlement_metrics(prediction, settlement_payload)

        decision = registration_payload.get("decision_at_registration")
        framework_version = None
        if isinstance(decision, Mapping):
            framework_version = _text(decision.get("framework_version")) or None

        output.append(
            {
                "source_prediction_snapshot_id": snapshot_id,
                "product_match_id": _text(settlement.get("product_match_id")),
                "event_id": _text(settlement.get("event_id")) or None,
                "league": _text(settlement.get("league")),
                "commence_time_utc": _utc_datetime(
                    settlement.get("commence_time_utc"), label="commence_time_utc"
                ),
                "model_1x2_version": _text(prediction.get("model_1x2_version")) or None,
                "model_1x2_sha256": _text(prediction.get("model_1x2_sha256")) or None,
                "registration_mode": _text(registration_payload.get("registration_mode")),
                "decision_framework_version": framework_version,
                "model_pick": model_pick,
                "model_pick_probability": probability,
                "actual_outcome": actual_outcome,
                "prediction_correct": prediction_correct,
                "multiclass_brier": brier,
                "log_loss": log_loss,
            }
        )

    return output


def _probability_bucket(probability: float) -> str:
    lower = min(int(probability * 10.0) * 10, 90)
    upper = 100 if lower == 90 else lower + 10
    return f"{lower}-{upper}%"


def _calibration(records: list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], float | None]:
    if not records:
        return [], None
    buckets: dict[str, list[tuple[float, bool]]] = {}
    for record in records:
        probability = float(record["model_pick_probability"])
        buckets.setdefault(_probability_bucket(probability), []).append(
            (probability, bool(record["prediction_correct"]))
        )

    output: list[dict[str, Any]] = []
    weighted_abs_gap = 0.0
    for label in sorted(buckets, key=lambda item: int(item.split("-")[0])):
        values = buckets[label]
        n = len(values)
        successes = sum(1 for _, correct in values if correct)
        mean_probability = sum(probability for probability, _ in values) / n
        hit_rate = successes / n
        gap = hit_rate - mean_probability
        interval = wilson_interval(successes, n)
        assert interval is not None
        weighted_abs_gap += n * abs(gap)
        output.append(
            {
                "bucket": label,
                "n": n,
                "mean_predicted_probability": mean_probability,
                "empirical_hit_rate": hit_rate,
                "calibration_gap": gap,
                "absolute_calibration_gap": abs(gap),
                "hit_rate_wilson_95": {
                    "lower": interval[0],
                    "upper": interval[1],
                },
                "mean_prediction_inside_hit_rate_wilson_95": (
                    interval[0] <= mean_probability <= interval[1]
                ),
                "interpretation": (
                    "descriptive_only; no bucket-level reliability threshold is "
                    "defined in product-reliability.v1"
                ),
            }
        )
    return output, weighted_abs_gap / len(records)


def _evidence_gate(
    records: list[Mapping[str, Any]],
    *,
    exact_model_league_scope: bool,
) -> dict[str, Any]:
    n = len(records)
    if not exact_model_league_scope:
        return {
            "state": EVIDENCE_DESCRIPTIVE_ONLY,
            "sample_gate_passed": False,
            "calendar_span_gate_passed": False,
            "reviewable": False,
            "reason": (
                "Reliability claims require an exact model artifact SHA and league; "
                "cross-model/cross-league aggregates are descriptive only."
            ),
        }
    if n == 0:
        return {
            "state": EVIDENCE_NO_DATA,
            "sample_gate_passed": False,
            "calendar_span_gate_passed": False,
            "reviewable": False,
            "reason": "No settled predictions exist for this exact model/league scope.",
        }

    sample_passed = n >= MIN_SETTLED_FIXTURES_FOR_REVIEW
    first = min(record["commence_time_utc"] for record in records)
    last = max(record["commence_time_utc"] for record in records)
    required_end = _add_calendar_months(first, MIN_CALENDAR_MONTHS_FOR_REVIEW)
    time_passed = last >= required_end

    if not sample_passed:
        state = EVIDENCE_ACCUMULATING_SAMPLE
        reason = (
            f"Need at least {MIN_SETTLED_FIXTURES_FOR_REVIEW} settled fixtures "
            "before reliability review."
        )
    elif not time_passed:
        state = EVIDENCE_ACCUMULATING_TIME
        reason = (
            f"Sample count is sufficient, but evidence must span at least "
            f"{MIN_CALENDAR_MONTHS_FOR_REVIEW} calendar months."
        )
    else:
        state = EVIDENCE_REVIEWABLE
        reason = (
            "Pre-registered sample/time evidence gates are satisfied. This makes "
            "the slice eligible for reliability review, not automatically reliable."
        )

    return {
        "state": state,
        "sample_gate_passed": sample_passed,
        "calendar_span_gate_passed": time_passed,
        "reviewable": sample_passed and time_passed,
        "first_kickoff_utc": first.isoformat(),
        "last_kickoff_utc": last.isoformat(),
        "required_calendar_span_end_utc": required_end.isoformat(),
        "reason": reason,
    }


def reliability_summary(
    records: Iterable[Mapping[str, Any]],
    *,
    league: str | None = None,
    model_1x2_sha256: str | None = None,
) -> dict[str, Any]:
    """Build one reliability slice.

    A reliability claim is only review-eligible when both exact ``league`` and
    exact ``model_1x2_sha256`` are supplied and the pre-registered evidence gates
    are satisfied. v1 still emits no PASS/FAIL quality verdict.
    """
    league_filter = _text(league) or None
    sha_filter = _text(model_1x2_sha256) or None
    selected = []
    for raw in records:
        row = dict(raw)
        if league_filter is not None and _text(row.get("league")) != league_filter:
            continue
        if sha_filter is not None and _text(row.get("model_1x2_sha256")) != sha_filter:
            continue
        selected.append(row)

    exact_scope = league_filter is not None and sha_filter is not None
    gate = _evidence_gate(selected, exact_model_league_scope=exact_scope)
    calibration, ece = _calibration(selected)

    if selected:
        n = len(selected)
        correct = sum(1 for row in selected if row.get("prediction_correct") is True)
        mean_brier = sum(float(row["multiclass_brier"]) for row in selected) / n
        mean_log_loss = sum(float(row["log_loss"]) for row in selected) / n
        accuracy = correct / n
        brier_skill_vs_uniform = 1.0 - mean_brier / UNIFORM_1X2_BRIER
        log_loss_improvement_vs_uniform = UNIFORM_1X2_LOG_LOSS - mean_log_loss
    else:
        n = 0
        accuracy = None
        mean_brier = None
        mean_log_loss = None
        brier_skill_vs_uniform = None
        log_loss_improvement_vs_uniform = None

    return {
        "schema_version": RELIABILITY_SCHEMA_VERSION,
        "scope": {
            "market": "1x2",
            "league": league_filter,
            "model_1x2_sha256": sha_filter,
            "exact_model_league_scope": exact_scope,
        },
        "settled_predictions": n,
        "evidence_gate": gate,
        "metrics": {
            "accuracy": accuracy,
            "mean_multiclass_brier": mean_brier,
            "mean_log_loss": mean_log_loss,
            "top_pick_expected_calibration_error": ece,
            "brier_skill_vs_uniform_1x2": brier_skill_vs_uniform,
            "log_loss_improvement_vs_uniform_1x2": log_loss_improvement_vs_uniform,
            "calibration": calibration,
        },
        "reliability_verdict": {
            "status": "INCONCLUSIVE",
            "claim": None,
            "reason": (
                "product-reliability.v1 defines evidence-readiness gates and "
                "descriptive metrics, but no post-outcome quality threshold. A later "
                "preregistered review may define PASS/FAIL without tuning on this sample."
            ),
        },
        "automatic_effects": {
            "changes_decision_tier": False,
            "changes_forecast_ranking": False,
            "changes_model_probability": False,
            "promotes_model": False,
            "creates_bet_recommendation": False,
        },
    }


def build_reliability_matrix(
    events: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return descriptive overall history plus exact model/league slices."""
    records = settled_reliability_records(events)
    keys = sorted(
        {
            (_text(row.get("league")), _text(row.get("model_1x2_sha256")))
            for row in records
            if _text(row.get("league")) and _text(row.get("model_1x2_sha256"))
        }
    )
    slices = [
        reliability_summary(records, league=league, model_1x2_sha256=sha)
        for league, sha in keys
    ]
    return {
        "schema_version": RELIABILITY_SCHEMA_VERSION,
        "policy": {
            "source": "immutable product_prediction_lifecycle_events",
            "settlement_scope": MARKET_SCOPE,
            "primary_claim_scope": "exact model_1x2_sha256 + league + 1x2",
            "min_settled_fixtures_for_review": MIN_SETTLED_FIXTURES_FOR_REVIEW,
            "min_calendar_months_for_review": MIN_CALENDAR_MONTHS_FOR_REVIEW,
            "thresholds_preregistered_before_product_settlements": True,
            "quality_pass_fail_threshold_defined": False,
            "automatic_decision_tier_change": False,
            "automatic_model_promotion": False,
            "automatic_bet_recommendation": False,
        },
        "overall_history": reliability_summary(records),
        "model_league_slices": slices,
    }
