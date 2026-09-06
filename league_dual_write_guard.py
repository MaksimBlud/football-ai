"""Fail-closed dual-write guard for generic MARKET_ONLY league live cycles.

Research-only infrastructure. The guard never writes finished results, reads
outcomes, loads a model, activates Structural V2, or repairs historical evidence.
It validates and preflights the complete observation + canonical-ledger plan
before the first append, retries one non-deterministic append failure, then
read-after-write verifies both durable sides.
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


@dataclass(frozen=True)
class DualWriteResult:
    observation_metrics: dict[str, int]
    ledger_metrics: dict[str, int]
    plan: DualWritePlan


def _league(config) -> str:
    return str(config.identity.identifier)


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
    league = _league(config)
    validated = validate_observations(observations, config)
    keys = _observation_key_map(validated)
    predictions = build_market_only_predictions(shadow, observation_keys=keys)

    if len(predictions) != len(validated):
        raise RuntimeError(f"{league} observation/ledger plan row counts disagree")
    if predictions["observation_key"].isna().any():
        raise RuntimeError(f"{league} ledger plan contains unlinked observations")
    if not (predictions["prediction_mode"] == "MARKET_ONLY").all():
        raise RuntimeError(f"{league} ledger plan contains non-MARKET_ONLY state")
    if predictions["structural_applied"].astype(bool).any():
        raise RuntimeError(f"{league} ledger plan unexpectedly applies Structural V2")

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
    try:
        return action()
    except conflict_type:
        raise
    except Exception:
        return action()


def execute_dual_write(
    client,
    shadow: pd.DataFrame,
    observations: pd.DataFrame,
    config,
    *,
    observation_writer: Callable | None = None,
    prediction_writer: Callable | None = None,
) -> DualWriteResult:
    """Preflight, append, and verify one generic MARKET_ONLY durable batch."""
    league = _league(config)
    plan = prepare_dual_write(client, shadow, observations, config)
    observation_write = observation_writer or observation_store.persist_observations
    prediction_write = prediction_writer or persist_predictions

    _retry_append(
        lambda: observation_write(client, observations, config),
        PersistenceConflictError,
    )
    observation_verified = preflight_observations(client, observations, config)
    expected_observations = plan.observation_present + plan.observation_missing
    if (
        observation_verified["missing"] != 0
        or observation_verified["present"] != expected_observations
    ):
        raise RuntimeError(f"{league} observation read-after-write verification failed")

    _retry_append(
        lambda: prediction_write(client, plan.predictions),
        PredictionLedgerConflictError,
    )
    prediction_verified = preflight_predictions(client, plan.predictions)
    expected_predictions = plan.prediction_present + plan.prediction_missing
    if (
        prediction_verified["missing"] != 0
        or prediction_verified["present"] != expected_predictions
    ):
        raise RuntimeError(f"{league} ledger read-after-write verification failed")

    return DualWriteResult(
        observation_metrics={
            "inserted": plan.observation_missing,
            "unchanged": plan.observation_present,
            "conflicts": 0,
        },
        ledger_metrics={
            "inserted": plan.prediction_missing,
            "unchanged": plan.prediction_present,
            "conflicts": 0,
        },
        plan=plan,
    )
