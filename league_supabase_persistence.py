"""Generic Supabase persistence adapter for league research runtimes.

This module does not apply migrations and does not activate any league.

It provides:
- schema readiness checks;
- complete league-scoped reads with deterministic PostgREST pagination;
- idempotent insert-only observations;
- immutable finished-result inserts;
- explicit conflict detection.

Existing La Liga persistence remains operationally authoritative until a
later activation/parity task.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from league_live_persistence import (
    PersistenceConflictError,
    PersistenceState,
    immutable_payload_equal,
    validate_observations,
    validate_results,
)
from league_runtime_config import LeagueRuntimeConfig


GENERIC_OBSERVATION_TABLE = "league_structural_v2_observations"
GENERIC_RESULTS_TABLE = "league_finished_results"
PAGE_SIZE = 1000


def _response_rows(response: Any) -> list[dict]:
    return list(getattr(response, "data", None) or [])


def _fetch_league_rows(
    client,
    table: str,
    league: str,
    *,
    order_fields: tuple[str, ...],
    page_size: int = PAGE_SIZE,
) -> list[dict]:
    """Read every league row without relying on the PostgREST default limit.

    A new query object is built for every page. Multiple deterministic order
    fields prevent page-boundary drift when the primary timestamp/date field
    contains ties. Lightweight non-PostgREST test doubles that do not expose
    ``range`` retain the historical one-shot read path.
    """
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    if not order_fields:
        raise ValueError("at least one deterministic order field is required")

    rows: list[dict] = []
    start = 0
    while True:
        query = client.table(table).select("*").eq("league", league)
        for field in order_fields:
            query = query.order(field, desc=False)

        range_method = getattr(query, "range", None)
        if not callable(range_method):
            if start != 0:
                raise RuntimeError("pagination-capable query lost range()")
            return _response_rows(query.execute())

        response = range_method(start, start + page_size - 1).execute()
        batch = _response_rows(response)
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size

    return rows


def check_schema(client) -> PersistenceState:
    """Check both generic durable tables without mutating state."""
    try:
        (
            client.table(GENERIC_OBSERVATION_TABLE)
            .select("observation_key")
            .limit(1)
            .execute()
        )
        (
            client.table(GENERIC_RESULTS_TABLE)
            .select("league")
            .limit(1)
            .execute()
        )
    except Exception as exc:
        message = str(exc).lower()
        missing_markers = (
            "does not exist",
            "could not find the table",
            "relation",
            "schema cache",
        )
        if any(marker in message for marker in missing_markers):
            return PersistenceState(
                status="WAIT",
                detail="GENERIC_DATABASE_SCHEMA_NOT_APPLIED",
            )
        return PersistenceState(
            status="FAIL",
            detail=(
                "GENERIC_DATABASE_ERROR: "
                + type(exc).__name__
                + ": "
                + str(exc)
            ),
        )
    return PersistenceState(
        status="PASS",
        detail="GENERIC_DATABASE_SCHEMA_READY",
    )


OBSERVATION_PAYLOAD_DATETIME_FIELDS = (
    "market_generated_at_utc",
    "recorded_at_utc",
)


def _canonical_payload_datetime(value):
    """Return one stable ISO-8601 representation for payload datetimes."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return stripped
        try:
            parsed = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
        except ValueError:
            return value
        return parsed.isoformat()
    return value


def _canonical_observation_payload(payload):
    """Normalize representation-only datetime differences."""
    normalized = dict(payload or {})
    for field in OBSERVATION_PAYLOAD_DATETIME_FIELDS:
        if field in normalized:
            normalized[field] = _canonical_payload_datetime(normalized[field])
    return normalized


OBSERVATION_STORAGE_COLUMNS = (
    "observation_key",
    "league",
    "event_id",
    "snapshot_time_utc",
    "commence_time_utc",
    "payload",
)


def _normalize_record(record: dict) -> dict:
    result = {}
    for key, value in record.items():
        try:
            missing = pd.isna(value)
        except (TypeError, ValueError):
            missing = False
        if isinstance(missing, bool) and missing:
            result[key] = None
            continue
        if isinstance(value, pd.Timestamp):
            result[key] = value.isoformat()
            continue
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
            continue
        if hasattr(value, "item"):
            try:
                value = value.item()
            except Exception:
                pass
        result[key] = value
    return result


def observation_storage_record(row: dict) -> dict:
    """Encode one validated observation to the SQL table contract."""
    normalized = _normalize_record(dict(row))
    payload = {
        key: value
        for key, value in normalized.items()
        if key
        not in {
            "observation_key",
            "league",
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
            "persisted_at_utc",
        }
    }
    return {
        "observation_key": normalized["observation_key"],
        "league": normalized["league"],
        "event_id": normalized["event_id"],
        "snapshot_time_utc": normalized["snapshot_time_utc"],
        "commence_time_utc": normalized["commence_time_utc"],
        "payload": _canonical_observation_payload(payload),
    }


def observation_runtime_record(row: dict) -> dict:
    """Decode one SQL observation row back to the runtime contract."""
    result = dict(row)
    payload = result.pop("payload", None)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Observation payload must be a JSON object")
    persisted = result.pop("persisted_at_utc", None)
    result.update(payload)
    if persisted is not None:
        result["persisted_at_utc"] = persisted
    return result


def fetch_observations(client, config: LeagueRuntimeConfig) -> pd.DataFrame:
    stored_rows = _fetch_league_rows(
        client,
        GENERIC_OBSERVATION_TABLE,
        config.identity.identifier,
        order_fields=("snapshot_time_utc", "event_id", "observation_key"),
    )
    frame = pd.DataFrame(
        [observation_runtime_record(row) for row in stored_rows]
    )
    for column in (
        "snapshot_time_utc",
        "commence_time_utc",
        "market_generated_at_utc",
        "recorded_at_utc",
        "persisted_at_utc",
    ):
        if column in frame.columns:
            frame[column] = pd.to_datetime(
                frame[column], utc=True, errors="coerce"
            )
    return frame


def fetch_results(client, config: LeagueRuntimeConfig) -> pd.DataFrame:
    rows = _fetch_league_rows(
        client,
        GENERIC_RESULTS_TABLE,
        config.identity.identifier,
        order_fields=("match_date", "season", "home_team", "away_team"),
    )
    frame = pd.DataFrame(rows)
    if "match_date" in frame.columns:
        frame["match_date"] = pd.to_datetime(
            frame["match_date"], errors="coerce"
        ).dt.date
    for column in ("source_updated_at_utc", "persisted_at_utc"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(
                frame[column], utc=True, errors="coerce"
            )
    return frame


def persist_observations(
    client,
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> dict:
    incoming = validate_observations(frame, config)
    if incoming.empty:
        return {"inserted": 0, "unchanged": 0, "conflicts": 0}

    existing = fetch_observations(client, config)
    existing_by_key = {
        str(row["observation_key"]): observation_storage_record(row.to_dict())
        for _, row in existing.iterrows()
    }

    inserted = 0
    unchanged = 0
    for _, row in incoming.iterrows():
        record = observation_storage_record(_normalize_record(row.to_dict()))
        key = str(record["observation_key"])
        previous = existing_by_key.get(key)
        if previous is not None:
            comparable_previous = {
                column: previous.get(column) for column in record.keys()
            }
            if not immutable_payload_equal(comparable_previous, record):
                raise PersistenceConflictError("Observation conflict for " + key)
            unchanged += 1
            continue
        client.table(GENERIC_OBSERVATION_TABLE).insert(record).execute()
        existing_by_key[key] = record
        inserted += 1

    return {"inserted": inserted, "unchanged": unchanged, "conflicts": 0}


def _result_key(record: dict) -> tuple:
    return (
        record.get("league"),
        str(record.get("season")),
        str(record.get("match_date")),
        record.get("home_team"),
        record.get("away_team"),
    )


def persist_results(
    client,
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> dict:
    incoming = validate_results(frame, config)
    if incoming.empty:
        return {"inserted": 0, "unchanged": 0, "conflicts": 0}

    existing = fetch_results(client, config)
    existing_by_key = {
        _result_key(_normalize_record(row.to_dict())): _normalize_record(
            row.to_dict()
        )
        for _, row in existing.iterrows()
    }

    inserted = 0
    unchanged = 0
    for _, row in incoming.iterrows():
        record = _normalize_record(row.to_dict())
        key = _result_key(record)
        previous = existing_by_key.get(key)
        if previous is not None:
            comparable_previous = {
                column: previous.get(column) for column in record.keys()
            }
            if not immutable_payload_equal(comparable_previous, record):
                raise PersistenceConflictError(
                    "Finished-result conflict for " + repr(key)
                )
            unchanged += 1
            continue
        client.table(GENERIC_RESULTS_TABLE).insert(record).execute()
        existing_by_key[key] = record
        inserted += 1

    return {"inserted": inserted, "unchanged": unchanged, "conflicts": 0}
