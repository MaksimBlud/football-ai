"""Append-only Product Prediction Lifecycle & Performance Ledger v1.

The lifecycle records facts around already-persisted product predictions. It does
not train models, call paid providers, rewrite prior snapshots, or interpret a
value signal as a placed bet.

Lifecycle facts:
- PREDICTION_REGISTERED: immutable source prediction provenance;
- MARKET_OBSERVED: latest stored pre-kickoff 1X2 market observation;
- SETTLED: canonical finished result plus proper scoring-rule metrics.

The current lifecycle intentionally does not call a stored market observation a
"closing line" unless a future source contract explicitly qualifies it as one.
Therefore v1 never fabricates CLV or betting P&L.
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from team_names import normalize_team_name


LIFECYCLE_SCHEMA_VERSION = "product-lifecycle.v1"
LIFECYCLE_TABLE = "product_prediction_lifecycle_events"

EVENT_PREDICTION_REGISTERED = "PREDICTION_REGISTERED"
EVENT_MARKET_OBSERVED = "MARKET_OBSERVED"
EVENT_SETTLED = "SETTLED"
EVENT_TYPES = (
    EVENT_PREDICTION_REGISTERED,
    EVENT_MARKET_OBSERVED,
    EVENT_SETTLED,
)

OUTCOMES = ("HOME", "DRAW", "AWAY")
RESULT_TO_OUTCOME = {"H": "HOME", "D": "DRAW", "A": "AWAY"}
OUTCOME_TO_INDEX = {"HOME": 0, "DRAW": 1, "AWAY": 2}

REGISTRATION_MODE_LIVE = "live_publish"
REGISTRATION_MODE_LEGACY_BOOTSTRAP = "legacy_source_snapshot_bootstrap"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _float(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
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


def _iso_utc(value: Any, *, label: str) -> str:
    return _utc_datetime(value, label=label).isoformat()


def _probability_vector(row: Mapping[str, Any]) -> tuple[float, float, float]:
    values = tuple(
        _float(row.get(column))
        for column in ("home_probability", "draw_probability", "away_probability")
    )
    if any(value is None for value in values):
        raise ValueError("1X2 probability vector is required")
    vector = tuple(float(value) for value in values)
    if any(value < 0.0 or value > 1.0 for value in vector):
        raise ValueError("1X2 probability must be within [0, 1]")
    if not math.isclose(sum(vector), 1.0, abs_tol=1e-9):
        raise ValueError("1X2 probabilities must sum to 1")
    return vector


def _derived_pick(vector: tuple[float, float, float]) -> str:
    return OUTCOMES[max(range(3), key=lambda index: vector[index])]


def stable_product_match_id(row: Mapping[str, Any]) -> str:
    """Return the same stable identity used by the product contract."""
    event_id = _text(row.get("event_id"))
    if event_id:
        return f"event_{event_id}"

    parts = (
        _text(row.get("league")),
        _text(row.get("home_team_model") or row.get("home_team")),
        _text(row.get("away_team_model") or row.get("away_team")),
        _text(row.get("commence_time_utc")),
    )
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"fixture_{digest}"


def _registration_event_key(snapshot_id: Any) -> str:
    text = _text(snapshot_id)
    if not text:
        raise ValueError("source prediction snapshot id is required")
    return f"prediction_registered:{text}"


def _market_event_key(snapshot_id: Any, odds_snapshot_id: Any) -> str:
    prediction_id = _text(snapshot_id)
    odds_id = _text(odds_snapshot_id)
    if not prediction_id or not odds_id:
        raise ValueError("prediction and odds snapshot ids are required")
    return f"market_observed:{prediction_id}:{odds_id}"


def _settlement_event_key(snapshot_id: Any, result: Mapping[str, Any]) -> str:
    prediction_id = _text(snapshot_id)
    if not prediction_id:
        raise ValueError("source prediction snapshot id is required")
    result_identity = "|".join(
        (
            _text(result.get("league")),
            _text(result.get("match_date")),
            normalize_team_name(_text(result.get("home_team"))),
            normalize_team_name(_text(result.get("away_team"))),
            _text(result.get("result")).upper(),
            _text(result.get("home_goals")),
            _text(result.get("away_goals")),
        )
    )
    digest = hashlib.sha256(result_identity.encode("utf-8")).hexdigest()[:20]
    return f"settled:{prediction_id}:{digest}"


def _base_event(
    prediction: Mapping[str, Any],
    *,
    event_key: str,
    event_type: str,
    recorded_at_utc: Any,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported lifecycle event type: {event_type}")
    return {
        "lifecycle_schema_version": LIFECYCLE_SCHEMA_VERSION,
        "event_key": event_key,
        "event_type": event_type,
        "product_match_id": stable_product_match_id(prediction),
        "event_id": _text(prediction.get("event_id")) or None,
        "league": _text(prediction.get("league")),
        "commence_time_utc": _iso_utc(
            prediction.get("commence_time_utc"), label="commence_time_utc"
        ),
        "home_team": _text(prediction.get("home_team")),
        "away_team": _text(prediction.get("away_team")),
        "source_prediction_snapshot_id": int(prediction["id"]),
        "source_prediction_run_id": _text(prediction.get("run_id")) or None,
        "source_prediction_generated_at_utc": _iso_utc(
            prediction.get("generated_at_utc"), label="generated_at_utc"
        ),
        "source_prediction_created_at_utc": _iso_utc(
            prediction.get("created_at"), label="prediction created_at"
        ),
        "source_odds_snapshot_id": None,
        "source_odds_snapshot_time_utc": None,
        "source_result_match_date": None,
        "source_result_persisted_at_utc": None,
        "recorded_at_utc": _iso_utc(recorded_at_utc, label="recorded_at_utc"),
        "payload": dict(payload),
    }


def build_prediction_registered_event(
    prediction: Mapping[str, Any],
    *,
    recorded_at_utc: Any,
    registration_mode: str,
    market_reference: Mapping[str, Any] | None = None,
    decision_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze one pre-kickoff source prediction in the lifecycle.

    ``source_prediction_created_at_utc`` is copied from the durable source row;
    ``recorded_at_utc`` is the actual lifecycle insertion/pass time. They are
    deliberately distinct so a bootstrap cannot fabricate a historical
    lifecycle write.
    """
    if registration_mode not in {
        REGISTRATION_MODE_LIVE,
        REGISTRATION_MODE_LEGACY_BOOTSTRAP,
    }:
        raise ValueError("unsupported registration mode")

    kickoff = _utc_datetime(prediction.get("commence_time_utc"), label="kickoff")
    source_created = _utc_datetime(prediction.get("created_at"), label="prediction created_at")
    if source_created >= kickoff:
        raise ValueError("prediction snapshot is not pre-kickoff")

    vector = _probability_vector(prediction)
    payload: dict[str, Any] = {
        "registration_mode": registration_mode,
        "source_snapshot_was_pre_kickoff": True,
        "prediction": {
            "prediction_schema_version": _text(
                prediction.get("snapshot_schema_version")
            )
            or None,
            "run_id": _text(prediction.get("run_id")) or None,
            "home_probability": vector[0],
            "draw_probability": vector[1],
            "away_probability": vector[2],
            "derived_1x2_pick": _derived_pick(vector),
            "model_1x2_version": _text(prediction.get("model_1x2_version")) or None,
            "model_1x2_sha256": _text(prediction.get("model_1x2_sha256")) or None,
            "publisher_version": _text(prediction.get("publisher_version")) or None,
        },
        "market_reference_at_registration": None,
        "decision_at_registration": None,
    }

    if market_reference is not None:
        market_time = _utc_datetime(
            market_reference.get("snapshot_time_utc"),
            label="market snapshot_time_utc",
        )
        if market_time > source_created:
            raise ValueError("registration market reference is after source snapshot creation")
        payload["market_reference_at_registration"] = {
            "role": "latest_stored_observation_at_or_before_source_snapshot",
            "snapshot_id": int(market_reference["id"]),
            "snapshot_time_utc": market_time.isoformat(),
            "age_seconds_at_prediction_record": (
                source_created - market_time
            ).total_seconds(),
            "home_odds": _float(market_reference.get("home_odds")),
            "draw_odds": _float(market_reference.get("draw_odds")),
            "away_odds": _float(market_reference.get("away_odds")),
            "is_closing_qualified": False,
        }

    if decision_payload is not None:
        if registration_mode != REGISTRATION_MODE_LIVE:
            raise ValueError(
                "legacy bootstrap must not retroactively attach a decision framework"
            )
        payload["decision_at_registration"] = dict(decision_payload)

    return _base_event(
        prediction,
        event_key=_registration_event_key(prediction.get("id")),
        event_type=EVENT_PREDICTION_REGISTERED,
        recorded_at_utc=recorded_at_utc,
        payload=payload,
    )


def build_market_observed_event(
    prediction: Mapping[str, Any],
    odds_snapshot: Mapping[str, Any],
    *,
    recorded_at_utc: Any,
) -> dict[str, Any]:
    """Record the latest stored pre-kickoff market observation after kickoff.

    It is *not* called a closing line because existing odds snapshots do not
    carry a closing-qualified source contract.
    """
    kickoff = _utc_datetime(prediction.get("commence_time_utc"), label="kickoff")
    recorded = _utc_datetime(recorded_at_utc, label="recorded_at_utc")
    market_time = _utc_datetime(
        odds_snapshot.get("snapshot_time_utc"), label="market snapshot_time_utc"
    )
    if recorded < kickoff:
        raise ValueError("latest pre-kickoff market observation can be finalized only after kickoff")
    if market_time > kickoff:
        raise ValueError("market observation is after kickoff")
    if _text(prediction.get("event_id")) != _text(odds_snapshot.get("event_id")):
        raise ValueError("market observation event_id mismatch")

    payload = {
        "observation_role": "latest_stored_pre_kickoff",
        "minutes_before_kickoff": (kickoff - market_time).total_seconds() / 60.0,
        "home_odds": _float(odds_snapshot.get("home_odds")),
        "draw_odds": _float(odds_snapshot.get("draw_odds")),
        "away_odds": _float(odds_snapshot.get("away_odds")),
        "is_closing_qualified": False,
        "clv": None,
        "reason": (
            "Stored snapshot has no explicit closing-line qualification; "
            "v1 records market movement evidence but does not fabricate CLV."
        ),
    }
    event = _base_event(
        prediction,
        event_key=_market_event_key(prediction.get("id"), odds_snapshot.get("id")),
        event_type=EVENT_MARKET_OBSERVED,
        recorded_at_utc=recorded,
        payload=payload,
    )
    event["source_odds_snapshot_id"] = int(odds_snapshot["id"])
    event["source_odds_snapshot_time_utc"] = market_time.isoformat()
    return event


def _result_matches_prediction(
    prediction: Mapping[str, Any],
    result: Mapping[str, Any],
) -> bool:
    return (
        _text(prediction.get("league")) == _text(result.get("league"))
        and _text(prediction.get("match_date")) == _text(result.get("match_date"))
        and normalize_team_name(_text(prediction.get("home_team")))
        == normalize_team_name(_text(result.get("home_team")))
        and normalize_team_name(_text(prediction.get("away_team")))
        == normalize_team_name(_text(result.get("away_team")))
    )


def build_settled_event(
    prediction: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    recorded_at_utc: Any,
) -> dict[str, Any]:
    """Settle one immutable 1X2 prediction against canonical finished results."""
    if not _result_matches_prediction(prediction, result):
        raise ValueError("finished result does not match prediction fixture identity")

    result_code = _text(result.get("result")).upper()
    if result_code not in RESULT_TO_OUTCOME:
        raise ValueError("canonical result must be H, D or A")
    home_goals = int(result.get("home_goals"))
    away_goals = int(result.get("away_goals"))
    if home_goals < 0 or away_goals < 0:
        raise ValueError("finished result goals must be non-negative")
    derived_result = "H" if home_goals > away_goals else "A" if home_goals < away_goals else "D"
    if derived_result != result_code:
        raise ValueError("canonical result code disagrees with goals")

    vector = _probability_vector(prediction)
    actual_outcome = RESULT_TO_OUTCOME[result_code]
    actual_index = OUTCOME_TO_INDEX[actual_outcome]
    top_pick = _derived_pick(vector)
    actual_probability = vector[actual_index]
    one_hot = [0.0, 0.0, 0.0]
    one_hot[actual_index] = 1.0
    brier = sum((vector[i] - one_hot[i]) ** 2 for i in range(3))
    log_loss = -math.log(max(actual_probability, 1e-15))

    payload = {
        "settlement_scope": "1x2_model_probability",
        "actual_outcome": actual_outcome,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "model_pick": top_pick,
        "model_pick_probability": max(vector),
        "actual_outcome_probability": actual_probability,
        "prediction_correct": top_pick == actual_outcome,
        "multiclass_brier": brier,
        "log_loss": log_loss,
        "bet_result": None,
        "pnl": None,
        "roi": None,
        "clv": None,
        "reason": (
            "Framework v1 has no placed-bet contract and stored market observations "
            "are not closing-qualified; settlement reports forecast quality only."
        ),
    }
    event = _base_event(
        prediction,
        event_key=_settlement_event_key(prediction.get("id"), result),
        event_type=EVENT_SETTLED,
        recorded_at_utc=recorded_at_utc,
        payload=payload,
    )
    event["source_result_match_date"] = _text(result.get("match_date"))
    persisted_at = result.get("persisted_at_utc")
    if persisted_at:
        event["source_result_persisted_at_utc"] = _iso_utc(
            persisted_at, label="result persisted_at_utc"
        )
    return event


def performance_summary(
    settled_events: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate settled forecast-quality metrics without betting P&L."""
    events = [
        event
        for event in settled_events
        if _text(event.get("event_type")) == EVENT_SETTLED
    ]
    if not events:
        return {
            "schema_version": LIFECYCLE_SCHEMA_VERSION,
            "settled_predictions": 0,
            "accuracy": None,
            "mean_multiclass_brier": None,
            "mean_log_loss": None,
            "calibration": [],
            "betting_pnl_available": False,
            "clv_available": False,
        }

    payloads = [dict(event.get("payload") or {}) for event in events]
    correct = sum(1 for payload in payloads if payload.get("prediction_correct") is True)
    briers = [float(payload["multiclass_brier"]) for payload in payloads]
    losses = [float(payload["log_loss"]) for payload in payloads]

    buckets: dict[str, list[tuple[float, bool]]] = {}
    for payload in payloads:
        probability = float(payload["model_pick_probability"])
        lower = min(int(probability * 10) * 10, 90)
        upper = 100 if lower == 90 else lower + 10
        label = f"{lower}-{upper}%"
        buckets.setdefault(label, []).append(
            (probability, bool(payload.get("prediction_correct")))
        )

    calibration = []
    for label in sorted(buckets, key=lambda value: int(value.split("-")[0])):
        values = buckets[label]
        calibration.append(
            {
                "bucket": label,
                "n": len(values),
                "mean_predicted_probability": sum(v[0] for v in values) / len(values),
                "empirical_hit_rate": sum(1 for v in values if v[1]) / len(values),
            }
        )

    return {
        "schema_version": LIFECYCLE_SCHEMA_VERSION,
        "settled_predictions": len(events),
        "accuracy": correct / len(events),
        "mean_multiclass_brier": sum(briers) / len(briers),
        "mean_log_loss": sum(losses) / len(losses),
        "calibration": calibration,
        "betting_pnl_available": False,
        "clv_available": False,
    }
