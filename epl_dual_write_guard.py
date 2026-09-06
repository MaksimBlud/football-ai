"""Fail-closed guard for the scheduled EPL observation/ledger dual write.

Research-only infrastructure.  The guard never writes finished results, loads a
model, activates Structural V2, or repairs historical evidence.  It only makes
the existing append-only observation -> canonical-ledger sequence safer:

1. validate the complete observation batch and derive deterministic keys;
2. build the complete canonical MARKET_ONLY ledger plan from the same serialized
   market-shadow boundary;
3. preflight immutable conflicts in both durable tables before the first write;
4. allow one idempotent replay for non-deterministic write failures;
5. verify every planned prediction is present and immutable after the write.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

import league_supabase_persistence as observation_store
from league_live_persistence import (
    PersistenceConflictError,
    immutable_payload_equal,
    validate_observations,
)
from league_prediction_ledger import (
    PredictionLedgerConflictError,
    TABLE as LEDGER_TABLE,
    _rows_equal,
    build_market_only_predictions,
    persist_predictions,
)


@dataclass(frozen=True)
class DualWritePlan:
    observations: pd.DataFrame
    predictions: pd.DataFrame
    observation_present: int
    observation_missing: int
    prediction_present: int
    prediction_missing: int


def _observation_key_map(frame: pd.DataFrame) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for row in frame.itertuples(index=False):
        snapshot = pd.to_datetime(row.snapshot_time_utc, utc=True, errors="raise")
        key = (str(row.event_id), snapshot.isoformat())
        if key in result:
            raise ValueError("Duplicate event/snapshot observation identity")
        result[key] = str(row.observation_key)
    return result


def preflight_observations(client, frame: pd.DataFrame, config) -> dict[str, int]:
    """Validate all incoming observations and detect immutable conflicts only."""
    incoming = validate_observations(frame, config)
    existing = observation_store.fetch_observations(client, config)
    existing_by_key = {
        str(row["observation_key"]): observation_store.observation_storage_record(
            row.to_dict()
        )
        for _, row in existing.iterrows()
    }

    present = 0
    missing = 0
    for _, row in incoming.iterrows():
        record = observation_store.observation_storage_record(row.to_dict())
        key = str(record["observation_key"])
        previous = existing_by_key.get(key)
        if previous is None:
            missing += 1
            continue
        comparable_previous = {
            column: previous.get(column) for column in record.keys()
        }
        if not immutable_payload_equal(comparable_previous, record):
            raise PersistenceConflictError("Observation conflict for " + key)
        present += 1

    if present + missing != len(incoming):
        raise RuntimeError("Observation preflight did not cover the full batch")
    return {"present": present, "missing": missing}


def preflight_predictions(client, frame: pd.DataFrame) -> dict[str, int]:
    """Read-only immutable conflict check for every planned prediction row."""
    present = 0
    missing = 0
    for row in frame.to_dict(orient="records"):
        key = str(row["prediction_key"])
        response = (
            client.table(LEDGER_TABLE)
            .select("*")
            .eq("prediction_key", key)
            .limit(1)
            .execute()
        )
        existing = response.data or []
        if not existing:
            missing += 1
            continue
        if not _rows_equal(existing[0], row):
            raise PredictionLedgerConflictError("Prediction conflict for " + key)
        present += 1

    if present + missing != len(frame):
        raise RuntimeError("Prediction preflight did not cover the full plan")
    return {"present": present, "missing": missing}


def prepare_dual_write(client, shadow: pd.DataFrame, observations: pd.DataFrame, config) -> DualWritePlan:
    """Build and preflight both append-only sides before the first write."""
    validated = validate_observations(observations, config)
    keys = _observation_key_map(validated)
    predictions = build_market_only_predictions(shadow, observation_keys=keys)

    if len(predictions) != len(validated):
        raise RuntimeError("EPL observation/ledger plan row counts disagree")
    if predictions["observation_key"].isna().any():
        raise RuntimeError("EPL ledger plan contains unlinked observations")
    if not (predictions["prediction_mode"] == "MARKET_ONLY").all():
        raise RuntimeError("EPL ledger plan contains non-MARKET_ONLY state")
    if predictions["structural_applied"].astype(bool).any():
        raise RuntimeError("EPL ledger plan unexpectedly applies Structural V2")

    observation_state = preflight_observations(client, observations, config)
    prediction_state = preflight_predictions(client, predictions)

    return DualWritePlan(
        observations=validated,
        predictions=predictions,
        observation_present=observation_state["present"],
        observation_missing=observation_state["missing"],
        prediction_present=prediction_state["present"],
        prediction_missing=prediction_state["missing"],
    )


def _retry_append(action: Callable[[], dict], conflict_type: type[BaseException]) -> dict:
    """Retry one non-deterministic append failure; immutable conflicts never retry."""
    try:
        return action()
    except conflict_type:
        raise
    except Exception:
        return action()


def persist_observations_with_retry(
    client,
    raw_observations: pd.DataFrame,
    config,
    *,
    persist_fn: Callable | None = None,
) -> dict:
    writer = persist_fn or observation_store.persist_observations
    return _retry_append(
        lambda: writer(client, raw_observations, config),
        PersistenceConflictError,
    )


def persist_predictions_with_retry(
    client,
    predictions: pd.DataFrame,
    *,
    persist_fn: Callable | None = None,
) -> dict[str, int]:
    writer = persist_fn or persist_predictions
    _retry_append(
        lambda: writer(client, predictions),
        PredictionLedgerConflictError,
    )
    verified = preflight_predictions(client, predictions)
    if verified["missing"] != 0 or verified["present"] != len(predictions):
        raise RuntimeError("EPL ledger read-after-write verification failed")
    return verified
