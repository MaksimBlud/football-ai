"""Durable Supabase persistence for La Liga Structural V2 live research.

Properties:
- research-only;
- append-only immutable observations;
- immutable completed results;
- duplicate-key race safe;
- explicit schema WAIT vs database FAIL;
- Supabase is authoritative in durable mode;
- local CSV files are working mirrors only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


OBSERVATIONS_TABLE = (
    "la_liga_structural_v2_observations"
)

RESULTS_TABLE = (
    "la_liga_finished_results"
)

OBSERVATION_KEY = "observation_key"

RESULT_KEY = (
    "season",
    "match_date",
    "home_team",
    "away_team",
)

OBSERVATION_MIRROR_COLUMNS = (
    "league",
    "event_id",
    "commence_time_utc",
    "home_team",
    "away_team",
    "home_prior_matches",
    "away_prior_matches",
    "structural_ready",
    "structural_score",
    "correction_enabled",
    "realized_correction_weight",
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
    "shadow_home_probability",
    "shadow_draw_probability",
    "shadow_away_probability",
    "market_argmax",
    "shadow_argmax",
    "prediction_source",
    "research_only",
    "snapshot_time_utc",
    "market_generated_at_utc",
    "recorded_at_utc",
    "pre_kickoff_valid",
    "observation_key",
)

RESULT_MIRROR_COLUMNS = (
    "season",
    "league",
    "match_date",
    "match_time",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "source",
    "source_competition",
    "source_updated_at_utc",
)


class PersistenceConflictError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class DatabaseState:
    status: str
    detail: str


def _error_text(
    exc: Exception,
) -> str:
    values = [
        str(exc),
    ]

    for name in (
        "code",
        "message",
        "details",
        "hint",
        "status_code",
    ):
        value = getattr(
            exc,
            name,
            None,
        )

        if value is not None:
            values.append(
                str(value)
            )

    return " ".join(
        values
    ).lower()


def classify_database_error(
    exc: Exception,
) -> DatabaseState:
    text = _error_text(
        exc
    )

    unavailable = (
        "42501" in text
        or "28p01" in text
        or "pgrst301" in text
        or "permission denied" in text
        or "not authorized" in text
        or "authentication" in text
        or "timeout" in text
        or "timed out" in text
        or "network" in text
        or "connection" in text
    )

    if unavailable:
        return DatabaseState(
            "FAIL",
            "DATABASE_UNAVAILABLE",
        )

    missing = (
        "42p01" in text
        or "pgrst205" in text
        or "undefined relation" in text
        or "undefined table" in text
        or (
            "relation" in text
            and "does not exist" in text
        )
    )

    if missing:
        return DatabaseState(
            "WAIT",
            "DATABASE_SCHEMA_NOT_APPLIED",
        )

    return DatabaseState(
        "FAIL",
        "DATABASE_UNAVAILABLE",
    )


def is_unique_conflict(
    exc: Exception,
) -> bool:
    text = _error_text(
        exc
    )

    return (
        "23505" in text
        or "duplicate key" in text
        or "unique constraint" in text
        or "unique violation" in text
    )


def check_schema(
    client,
) -> DatabaseState:
    try:
        (
            client
            .table(
                OBSERVATIONS_TABLE
            )
            .select(
                OBSERVATION_KEY
            )
            .limit(1)
            .execute()
        )

        (
            client
            .table(
                RESULTS_TABLE
            )
            .select(
                "season"
            )
            .limit(1)
            .execute()
        )

    except Exception as exc:
        return (
            classify_database_error(
                exc
            )
        )

    return DatabaseState(
        "PASS",
        "DATABASE_SCHEMA_READY",
    )


def _json_value(
    value: Any,
) -> Any:
    if value is None:
        return None

    if (
        not isinstance(
            value,
            (
                list,
                dict,
            ),
        )
        and pd.isna(value)
    ):
        return None

    if isinstance(
        value,
        (
            datetime,
            date,
            pd.Timestamp,
        ),
    ):
        return (
            pd.Timestamp(
                value
            ).isoformat()
        )

    if isinstance(
        value,
        np.generic,
    ):
        return value.item()

    return value


def _payload(
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: _json_value(
            value
        )
        for key, value
        in row.items()
    }


def _canonical(
    value: Any,
) -> str:
    if isinstance(
        value,
        str,
    ):
        try:
            value = json.loads(
                value
            )
        except json.JSONDecodeError:
            pass

    return json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        default=str,
    )


def observation_record(
    row: dict[str, Any],
) -> dict[str, Any]:
    payload = _payload(
        row
    )

    identity = str(
        payload.get(
            OBSERVATION_KEY,
            "",
        )
    )

    if not identity:
        raise ValueError(
            "Observation lacks observation_key"
        )

    if (
        payload.get(
            "league"
        )
        != "LA_LIGA"
    ):
        raise ValueError(
            "Observation league must be LA_LIGA"
        )

    if (
        payload.get(
            "market_argmax"
        )
        != payload.get(
            "shadow_argmax"
        )
    ):
        raise ValueError(
            "Structural V2 changed market argmax"
        )

    if (
        payload.get(
            "pre_kickoff_valid"
        )
        is not True
    ):
        raise ValueError(
            "Observation is not valid pre-kickoff"
        )

    if (
        payload.get(
            "research_only"
        )
        is not True
    ):
        raise ValueError(
            "Observation is not research-only"
        )

    return {
        "observation_key":
            identity,
        "league":
            "LA_LIGA",
        "event_id":
            str(
                payload.get(
                    "event_id",
                    "",
                )
            ),
        "snapshot_time_utc":
            payload.get(
                "snapshot_time_utc"
            ),
        "commence_time_utc":
            payload.get(
                "commence_time_utc"
            ),
        "payload":
            payload,
    }


def result_record(
    row: dict[str, Any],
) -> dict[str, Any]:
    payload = _payload(
        row
    )

    if (
        payload.get(
            "league"
        )
        != "LA_LIGA"
    ):
        raise ValueError(
            "Result league must be LA_LIGA"
        )

    result = payload.get(
        "result"
    )

    if result not in (
        "H",
        "D",
        "A",
    ):
        raise ValueError(
            "Invalid match result"
        )

    return payload


def _read_observation(
    client,
    identity: str,
):
    response = (
        client
        .table(
            OBSERVATIONS_TABLE
        )
        .select(
            "observation_key,payload"
        )
        .eq(
            OBSERVATION_KEY,
            identity,
        )
        .limit(1)
        .execute()
    )

    rows = (
        response.data
        or []
    )

    return (
        rows[0]
        if rows
        else None
    )


def _read_result(
    client,
    record: dict[str, Any],
):
    query = (
        client
        .table(
            RESULTS_TABLE
        )
        .select("*")
    )

    for key in RESULT_KEY:
        query = query.eq(
            key,
            record[key],
        )

    response = (
        query
        .limit(1)
        .execute()
    )

    rows = (
        response.data
        or []
    )

    return (
        rows[0]
        if rows
        else None
    )


def insert_observation(
    client,
    row: dict[str, Any],
) -> str:
    candidate = (
        observation_record(
            row
        )
    )

    identity = candidate[
        OBSERVATION_KEY
    ]

    existing = (
        _read_observation(
            client,
            identity,
        )
    )

    if existing is not None:
        if (
            _canonical(
                existing.get(
                    "payload"
                )
            )
            == _canonical(
                candidate[
                    "payload"
                ]
            )
        ):
            return "unchanged"

        raise PersistenceConflictError(
            "Conflicting observation: "
            f"{identity}"
        )

    try:
        (
            client
            .table(
                OBSERVATIONS_TABLE
            )
            .insert(
                candidate
            )
            .execute()
        )

        return "inserted"

    except Exception as exc:
        if not is_unique_conflict(
            exc
        ):
            raise

    existing = (
        _read_observation(
            client,
            identity,
        )
    )

    if (
        existing is not None
        and _canonical(
            existing.get(
                "payload"
            )
        )
        == _canonical(
            candidate[
                "payload"
            ]
        )
    ):
        return "unchanged"

    raise PersistenceConflictError(
        "Conflicting observation "
        "after concurrent insert: "
        f"{identity}"
    )


def _same_result(
    existing: dict,
    candidate: dict,
) -> bool:
    return (
        int(
            existing[
                "home_goals"
            ]
        )
        == int(
            candidate[
                "home_goals"
            ]
        )
        and int(
            existing[
                "away_goals"
            ]
        )
        == int(
            candidate[
                "away_goals"
            ]
        )
        and str(
            existing[
                "result"
            ]
        )
        == str(
            candidate[
                "result"
            ]
        )
    )


def insert_result(
    client,
    row: dict[str, Any],
) -> str:
    candidate = (
        result_record(
            row
        )
    )

    existing = (
        _read_result(
            client,
            candidate,
        )
    )

    if existing is not None:
        if _same_result(
            existing,
            candidate,
        ):
            return "unchanged"

        raise PersistenceConflictError(
            "Conflicting finished result"
        )

    try:
        (
            client
            .table(
                RESULTS_TABLE
            )
            .insert(
                candidate
            )
            .execute()
        )

        return "inserted"

    except Exception as exc:
        if not is_unique_conflict(
            exc
        ):
            raise

    existing = (
        _read_result(
            client,
            candidate,
        )
    )

    if (
        existing is not None
        and _same_result(
            existing,
            candidate,
        )
    ):
        return "unchanged"

    raise PersistenceConflictError(
        "Conflicting finished result "
        "after concurrent insert"
    )


def persist_observations(
    client,
    frame: pd.DataFrame,
) -> dict[str, int]:
    metrics = {
        "input": len(frame),
        "inserted": 0,
        "unchanged": 0,
    }

    for row in (
        frame.to_dict(
            orient="records"
        )
    ):
        state = insert_observation(
            client,
            row,
        )

        metrics[state] += 1

    return metrics


def persist_results(
    client,
    frame: pd.DataFrame,
) -> dict[str, int]:
    metrics = {
        "input": len(frame),
        "inserted": 0,
        "unchanged": 0,
    }

    for row in (
        frame.to_dict(
            orient="records"
        )
    ):
        state = insert_result(
            client,
            row,
        )

        metrics[state] += 1

    return metrics


def fetch_observations(
    client,
) -> pd.DataFrame:
    response = (
        client
        .table(
            OBSERVATIONS_TABLE
        )
        .select(
            "payload"
        )
        .execute()
    )

    rows = []

    for item in (
        response.data
        or []
    ):
        value = item.get(
            "payload"
        )

        if isinstance(
            value,
            str,
        ):
            value = json.loads(
                value
            )

        rows.append(
            value
        )

    if not rows:
        return pd.DataFrame(
            columns=OBSERVATION_MIRROR_COLUMNS
        )

    frame = pd.DataFrame(
        rows
    )

    missing = [
        column
        for column in OBSERVATION_MIRROR_COLUMNS
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Durable observation payload missing columns: "
            + ", ".join(missing)
        )

    return frame[
        list(OBSERVATION_MIRROR_COLUMNS)
    ].copy()


def fetch_results(
    client,
) -> pd.DataFrame:
    response = (
        client
        .table(
            RESULTS_TABLE
        )
        .select(
            ",".join(
                RESULT_MIRROR_COLUMNS
            )
        )
        .execute()
    )

    rows = (
        response.data
        or []
    )

    if not rows:
        return pd.DataFrame(
            columns=RESULT_MIRROR_COLUMNS
        )

    frame = pd.DataFrame(
        rows
    )

    return frame[
        list(RESULT_MIRROR_COLUMNS)
    ].copy()


def write_mirror(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        path,
        index=False,
    )


def hydrate_local_mirrors(
    client,
    history_path: Path,
    results_path: Path,
) -> dict[str, int]:
    observations = (
        fetch_observations(
            client
        )
    )

    results = (
        fetch_results(
            client
        )
    )

    # Supabase is authoritative in durable mode.
    # Always rewrite mirrors, including the legitimate empty state,
    # so stale files from a previous runner cannot become authority.
    write_mirror(
        observations,
        history_path,
    )

    write_mirror(
        results,
        results_path,
    )

    return {
        "observations":
            len(observations),
        "results":
            len(results),
    }
