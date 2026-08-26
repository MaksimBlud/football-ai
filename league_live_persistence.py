"""Generic durable persistence primitives for league research runtimes.

This module is intentionally infrastructure-only.

Properties:
- league-aware;
- research-only;
- append-only observations;
- immutable finished results;
- deterministic identities;
- idempotent inserts;
- explicit schema WAIT versus database FAIL;
- no model training;
- no artifact promotion;
- no league activation;
- no migration application.

Existing La Liga operational persistence remains authoritative until a
separate activation task explicitly migrates it to this generic layer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from league_runtime_config import LeagueRuntimeConfig


@dataclass(frozen=True)
class PersistenceState:
    status: str
    detail: str


class PersistenceError(RuntimeError):
    """Base generic durable-persistence failure."""


class PersistenceConflictError(PersistenceError):
    """Existing immutable durable state conflicts with incoming state."""


class PersistenceSchemaError(PersistenceError):
    """Required durable schema is unavailable or incompatible."""


def canonical_json(value: Any) -> str:
    """Return deterministic JSON used for immutable identity checks."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def observation_key(
    *,
    config: LeagueRuntimeConfig,
    row: dict,
) -> str:
    """Create a league-scoped content-aware observation identity.

    Observation identity represents the immutable prediction state, not
    merely the underlying market snapshot. This preserves multiple valid
    Structural V2 states recorded against the same source market price,
    while exact replay remains idempotent.
    """

    from league_structural_v2_history import (
        observation_key as history_observation_key,
    )

    payload = dict(
        row
    )

    payload[
        "league"
    ] = config.identity.identifier

    content_key = (
        history_observation_key(
            payload,
            config,
        )
    )

    return (
        f"{config.identity.identifier}:"
        f"{content_key}"
    )


def result_identity_columns() -> tuple[str, ...]:
    """Immutable finished-fixture identity shared by all leagues."""

    return (
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
    )


def validate_observations(
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> pd.DataFrame:
    """Validate generic research observations without writing anything."""

    if frame.empty:
        return frame.copy()

    required = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "market_argmax",
        "shadow_argmax",
        "pre_kickoff_valid",
        "research_only",
    }

    missing = required - set(frame.columns)

    if missing:
        raise ValueError(
            "Missing observation columns: "
            + ", ".join(sorted(missing))
        )

    work = frame.copy()

    expected = config.identity.identifier

    observed = set(
        work["league"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if observed != {expected}:
        raise ValueError(
            "Observation league mismatch: "
            f"expected={expected!r}, "
            f"observed={sorted(observed)!r}"
        )

    work["snapshot_time_utc"] = pd.to_datetime(
        work["snapshot_time_utc"],
        utc=True,
        errors="coerce",
    )

    work["commence_time_utc"] = pd.to_datetime(
        work["commence_time_utc"],
        utc=True,
        errors="coerce",
    )

    if work[
        [
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
        ]
    ].isna().any().any():
        raise ValueError(
            "Observation identity/timestamps contain null values"
        )

    if not (
        work["snapshot_time_utc"]
        < work["commence_time_utc"]
    ).all():
        raise ValueError(
            "Observation must be strictly pre-kickoff"
        )

    if not (
        work["market_argmax"].astype(str)
        == work["shadow_argmax"].astype(str)
    ).all():
        raise ValueError(
            "Structural V2 observation changed market argmax"
        )

    if not (
        work["pre_kickoff_valid"]
        .astype(bool)
    ).all():
        raise ValueError(
            "Observation is not marked pre_kickoff_valid"
        )

    if not (
        work["research_only"]
        .astype(bool)
    ).all():
        raise ValueError(
            "Observation is not marked research_only"
        )

    work["observation_key"] = [
        observation_key(
            config=config,
            row=row.to_dict(),
        )
        for _, row in work.iterrows()
    ]

    if work["observation_key"].duplicated().any():
        raise ValueError(
            "Duplicate observation identities in incoming frame"
        )

    return work.reset_index(drop=True)


def validate_results(
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> pd.DataFrame:
    """Validate immutable generic finished results."""

    if frame.empty:
        return frame.copy()

    required = {
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    }

    missing = required - set(frame.columns)

    if missing:
        raise ValueError(
            "Missing result columns: "
            + ", ".join(sorted(missing))
        )

    work = frame.copy()

    expected = config.identity.identifier

    observed = set(
        work["league"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if observed != {expected}:
        raise ValueError(
            "Result league mismatch: "
            f"expected={expected!r}, "
            f"observed={sorted(observed)!r}"
        )

    work["match_date"] = pd.to_datetime(
        work["match_date"],
        errors="coerce",
    ).dt.date

    work["home_goals"] = pd.to_numeric(
        work["home_goals"],
        errors="coerce",
    )

    work["away_goals"] = pd.to_numeric(
        work["away_goals"],
        errors="coerce",
    )

    if work[
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "home_goals",
            "away_goals",
            "result",
        ]
    ].isna().any().any():
        raise ValueError(
            "Finished result contains null required values"
        )

    if (
        (work["home_goals"] < 0)
        | (work["away_goals"] < 0)
    ).any():
        raise ValueError(
            "Finished result contains negative goals"
        )

    derived = []

    for row in work.itertuples():
        if row.home_goals > row.away_goals:
            derived.append("H")
        elif row.home_goals < row.away_goals:
            derived.append("A")
        else:
            derived.append("D")

    if (
        work["result"]
        .astype(str)
        .to_numpy()
        != derived
    ).any():
        raise ValueError(
            "Finished result disagrees with goal score"
        )

    identity = list(
        result_identity_columns()
    )

    if work.duplicated(
        subset=identity
    ).any():
        raise ValueError(
            "Duplicate finished-result identity in incoming frame"
        )

    return work.reset_index(drop=True)


def immutable_payload_equal(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    """Compare immutable records deterministically."""

    return canonical_json(left) == canonical_json(right)
