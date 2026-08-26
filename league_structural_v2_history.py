"""Generic append-only Structural V2 live observation history."""

from __future__ import annotations

import hashlib
import json

import pandas as pd

from league_runtime_config import (
    LeagueRuntimeConfig,
)


def canonical_value(
    value,
):
    if pd.isna(value):
        return None

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if hasattr(
        value,
        "item",
    ):
        try:
            return value.item()
        except Exception:
            pass

    return value


def observation_key(
    row: pd.Series | dict,
    config: LeagueRuntimeConfig,
) -> str:
    data = dict(
        row
    )

    league = data.get(
        "league"
    )

    if (
        league
        != config.identity.identifier
    ):
        raise ValueError(
            "Observation league mismatch"
        )

    key_fields = (
        "league",
        "event_id",
        "commence_time_utc",
        "snapshot_time_utc",
        "home_team",
        "away_team",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "shadow_home_probability",
        "shadow_draw_probability",
        "shadow_away_probability",
        "market_argmax",
        "shadow_argmax",
        "prediction_source",
    )

    payload = {
        field: canonical_value(
            data.get(
                field
            )
        )
        for field in key_fields
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def validate_pre_kickoff(
    row: pd.Series | dict,
    config: LeagueRuntimeConfig,
) -> None:
    data = dict(
        row
    )

    if (
        data.get(
            "league"
        )
        != config.identity.identifier
    ):
        raise ValueError(
            "Observation league mismatch"
        )

    snapshot = pd.to_datetime(
        data.get(
            "snapshot_time_utc"
        ),
        utc=True,
        errors="coerce",
    )

    kickoff = pd.to_datetime(
        data.get(
            "commence_time_utc"
        ),
        utc=True,
        errors="coerce",
    )

    if (
        pd.isna(
            snapshot
        )
        or pd.isna(
            kickoff
        )
        or snapshot
        >= kickoff
    ):
        raise ValueError(
            "Observation must be recorded before kickoff"
        )

    market_argmax = (
        data.get(
            "market_argmax"
        )
    )

    shadow_argmax = (
        data.get(
            "shadow_argmax"
        )
    )

    if market_argmax != shadow_argmax:
        raise ValueError(
            "Structural observation changed market argmax"
        )


def prepare_observations(
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> pd.DataFrame:
    result = frame.copy()

    if result.empty:
        return result

    for _, row in result.iterrows():
        validate_pre_kickoff(
            row,
            config,
        )

    result[
        "observation_key"
    ] = [
        observation_key(
            row,
            config,
        )
        for _, row in result.iterrows()
    ]

    if result[
        "observation_key"
    ].duplicated().any():
        raise ValueError(
            "Duplicate observations in input"
        )

    return result


def append_only(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> tuple[pd.DataFrame, int]:
    incoming = (
        prepare_observations(
            incoming,
            config,
        )
    )

    if existing.empty:
        return (
            incoming.reset_index(
                drop=True
            ),
            len(incoming),
        )

    result = (
        existing.copy()
    )

    if (
        "observation_key"
        not in result.columns
    ):
        raise ValueError(
            "Existing history missing observation_key"
        )

    existing_by_key = {
        str(row[
            "observation_key"
        ]): row
        for _, row
        in result.iterrows()
    }

    new_rows = []

    for _, row in incoming.iterrows():
        key = str(
            row[
                "observation_key"
            ]
        )

        prior = (
            existing_by_key
            .get(
                key
            )
        )

        if prior is None:
            new_rows.append(
                row
            )
            continue

        common_columns = [
            column
            for column in incoming.columns
            if column in result.columns
        ]

        left = {
            column: canonical_value(
                prior[
                    column
                ]
            )
            for column in common_columns
        }

        right = {
            column: canonical_value(
                row[
                    column
                ]
            )
            for column in common_columns
        }

        if left != right:
            raise ValueError(
                "Observation conflict for existing key "
                + key
            )

    if new_rows:
        result = pd.concat(
            [
                result,
                pd.DataFrame(
                    new_rows
                ),
            ],
            ignore_index=True,
        )

    return (
        result.reset_index(
            drop=True
        ),
        len(new_rows),
    )
