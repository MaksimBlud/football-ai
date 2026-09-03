"""Append-only Supabase persistence for prospective availability research."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

POLL_TABLE = "prospective_availability_polls"
OBSERVATION_TABLE = "prospective_availability_observations"


class AvailabilityPersistenceConflict(RuntimeError):
    pass


def _rows(response: Any) -> list[dict]:
    return list(getattr(response, "data", None) or [])


def check_schema(client) -> tuple[str, str]:
    try:
        client.table(POLL_TABLE).select("poll_key").limit(1).execute()
        client.table(OBSERVATION_TABLE).select("observation_key").limit(1).execute()
    except Exception as exc:
        text = str(exc).lower()
        if any(marker in text for marker in ("does not exist", "could not find", "relation", "schema cache")):
            return "WAIT", "PROSPECTIVE_AVAILABILITY_SCHEMA_NOT_APPLIED"
        return "FAIL", f"PROSPECTIVE_AVAILABILITY_DATABASE_ERROR: {type(exc).__name__}: {exc}"
    return "PASS", "PROSPECTIVE_AVAILABILITY_SCHEMA_READY"


def _normalize_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _record(values: dict) -> dict:
    return {key: _normalize_value(value) for key, value in values.items()}


def _comparable(record: dict, *, ignored=("persisted_at_utc",)) -> dict:
    return {key: value for key, value in record.items() if key not in ignored}


def _equal(left: dict, right: dict) -> bool:
    return _comparable(_record(left)) == _comparable(_record(right))


def fetch_polls(client, league: str | None = None) -> pd.DataFrame:
    query = client.table(POLL_TABLE).select("*")
    if league is not None:
        query = query.eq("league", league)
    response = query.order("observed_at_utc", desc=False).execute()
    frame = pd.DataFrame(_rows(response))
    for column in ("commence_time_utc", "observed_at_utc", "persisted_at_utc"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    return frame


def fetch_observations(client, league: str | None = None) -> pd.DataFrame:
    query = client.table(OBSERVATION_TABLE).select("*")
    if league is not None:
        query = query.eq("league", league)
    response = query.order("observed_at_utc", desc=False).execute()
    frame = pd.DataFrame(_rows(response))
    for column in (
        "commence_time_utc",
        "source_timestamp_utc",
        "observed_at_utc",
        "first_seen_timestamp_utc",
        "persisted_at_utc",
    ):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    return frame


def _existing_by(client, table: str, key: str, values: list[str]) -> dict[str, dict]:
    if not values:
        return {}
    response = client.table(table).select("*").in_(key, list(dict.fromkeys(values))).execute()
    return {str(row[key]): row for row in _rows(response)}


def _first_seen_by_state(client, state_keys: list[str]) -> dict[str, str]:
    if not state_keys:
        return {}
    response = (
        client.table(OBSERVATION_TABLE)
        .select("state_key,first_seen_timestamp_utc")
        .in_("state_key", list(dict.fromkeys(state_keys)))
        .order("first_seen_timestamp_utc", desc=False)
        .execute()
    )
    result = {}
    for row in _rows(response):
        result.setdefault(str(row["state_key"]), str(row["first_seen_timestamp_utc"]))
    return result


def persist_poll(client, poll: dict, observations: pd.DataFrame) -> dict:
    poll_record = _record(poll)
    key = str(poll_record["poll_key"])
    existing_poll = _existing_by(client, POLL_TABLE, "poll_key", [key]).get(key)
    poll_inserted = 0
    poll_unchanged = 0
    if existing_poll is not None:
        # observed_at is intentionally earliest collector sighting for an identical full state.
        comparable = dict(poll_record)
        comparable["observed_at_utc"] = existing_poll.get("observed_at_utc")
        if not _equal(existing_poll, comparable):
            raise AvailabilityPersistenceConflict(f"Poll conflict for {key}")
        poll_unchanged = 1
        poll_record["observed_at_utc"] = existing_poll.get("observed_at_utc")
    else:
        client.table(POLL_TABLE).insert(poll_record).execute()
        poll_inserted = 1

    if observations is None or observations.empty:
        return {
            "poll_inserted": poll_inserted,
            "poll_unchanged": poll_unchanged,
            "observations_inserted": 0,
            "observations_unchanged": 0,
            "conflicts": 0,
        }

    incoming = [_record(row.to_dict()) for _, row in observations.iterrows()]
    state_first_seen = _first_seen_by_state(client, [str(row["state_key"]) for row in incoming])
    for row in incoming:
        state = str(row["state_key"])
        if state in state_first_seen:
            row["first_seen_timestamp_utc"] = state_first_seen[state]
        elif poll_unchanged:
            row["first_seen_timestamp_utc"] = poll_record["observed_at_utc"]

    existing = _existing_by(
        client,
        OBSERVATION_TABLE,
        "observation_key",
        [str(row["observation_key"]) for row in incoming],
    )
    inserted = unchanged = 0
    for row in incoming:
        observation_key = str(row["observation_key"])
        previous = existing.get(observation_key)
        if previous is not None:
            if not _equal(previous, row):
                raise AvailabilityPersistenceConflict(f"Observation conflict for {observation_key}")
            unchanged += 1
            continue
        client.table(OBSERVATION_TABLE).insert(row).execute()
        inserted += 1
    return {
        "poll_inserted": poll_inserted,
        "poll_unchanged": poll_unchanged,
        "observations_inserted": inserted,
        "observations_unchanged": unchanged,
        "conflicts": 0,
    }
