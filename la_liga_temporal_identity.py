"""Fail-closed canonicalization for durable La Liga observation identities.

The durable Structural V2 table is append-only and historically used the full
observation payload to derive ``observation_key``. Reconstructing an old market
snapshot with newer football history can therefore produce a second structural
payload for the same real-world temporal identity. The first row that was
actually persisted is the only observation that can be treated as prospective
for that timestamp.

This module never mutates or deletes historical rows. It deterministically
selects the earliest durable observation for ``(league, event_id,
snapshot_time_utc)`` and fails closed if duplicate rows disagree on the market
state that existed at that snapshot.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd


MARKET_FIELDS = (
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
    "market_argmax",
)


class TemporalObservationConflictError(RuntimeError):
    """Raised when one temporal identity cannot be canonicalized safely."""


@dataclass(frozen=True)
class CanonicalObservationMetrics:
    input: int
    canonical: int
    duplicate_temporal_rows: int
    structural_drift_rows: int


def _payload(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise TemporalObservationConflictError(
            "La Liga duplicate durable observation payload is not an object"
        )
    return value


def _timestamp(value: Any, *, field: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        raise TemporalObservationConflictError(
            f"La Liga durable observation has invalid {field}: {value!r}"
        )
    return parsed


def _market_fingerprint(payload: dict[str, Any]) -> str:
    missing = [field for field in MARKET_FIELDS if field not in payload]
    if missing:
        raise TemporalObservationConflictError(
            "La Liga duplicate durable observation lacks market fields: "
            + ", ".join(missing)
        )
    return json.dumps(
        {field: payload.get(field) for field in MARKET_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_observation_key_map(
    rows: Iterable[dict[str, Any]],
    *,
    league: str = "LA_LIGA",
) -> tuple[dict[tuple[str, str], str], CanonicalObservationMetrics]:
    """Return first-durable observation keys keyed by event/snapshot identity.

    A singleton row needs no persistence ordering and remains compatible with
    the original minimal observation projection. Ordering metadata and market
    payload are required only when two rows claim the same temporal identity.
    Duplicate structural reconstructions remain in durable storage as audit
    history but can never replace the first prospective observation. Any market
    disagreement under that identity is a hard conflict.
    """

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    input_count = 0

    for source in rows:
        input_count += 1
        row = dict(source)
        if str(row.get("league")) != league:
            raise TemporalObservationConflictError(
                "Foreign league in La Liga durable observations"
            )

        event_id = str(row.get("event_id") or "")
        observation_key = str(row.get("observation_key") or "")
        if not event_id or not observation_key:
            raise TemporalObservationConflictError(
                "La Liga durable observation lacks immutable identity"
            )

        snapshot = _timestamp(
            row.get("snapshot_time_utc"),
            field="snapshot_time_utc",
        )
        identity = (event_id, snapshot.isoformat())
        grouped.setdefault(identity, []).append(
            {
                "observation_key": observation_key,
                "persisted_at_utc": row.get("persisted_at_utc"),
                "payload": row.get("payload"),
            }
        )

    result: dict[tuple[str, str], str] = {}
    duplicate_temporal_rows = 0
    structural_drift_rows = 0

    for identity, candidates in grouped.items():
        if len(candidates) == 1:
            result[identity] = candidates[0]["observation_key"]
            continue

        duplicate_temporal_rows += len(candidates) - 1
        ordered: list[dict[str, Any]] = []
        for candidate in candidates:
            payload = _payload(candidate.get("payload"))
            ordered.append(
                {
                    "observation_key": candidate["observation_key"],
                    "persisted": _timestamp(
                        candidate.get("persisted_at_utc"),
                        field="persisted_at_utc",
                    ),
                    "market_fingerprint": _market_fingerprint(payload),
                }
            )

        ordered.sort(
            key=lambda item: (
                item["persisted"],
                item["observation_key"],
            )
        )
        canonical = ordered[0]
        result[identity] = canonical["observation_key"]

        for candidate in ordered[1:]:
            if candidate["market_fingerprint"] != canonical["market_fingerprint"]:
                raise TemporalObservationConflictError(
                    "Conflicting market payload for La Liga temporal identity: "
                    f"{identity[0]} @ {identity[1]}"
                )
            if candidate["observation_key"] != canonical["observation_key"]:
                structural_drift_rows += 1

    metrics = CanonicalObservationMetrics(
        input=input_count,
        canonical=len(result),
        duplicate_temporal_rows=duplicate_temporal_rows,
        structural_drift_rows=structural_drift_rows,
    )
    return result, metrics
