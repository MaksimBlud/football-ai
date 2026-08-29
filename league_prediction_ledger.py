"""Canonical append-only league prediction ledger.

Research infrastructure only.

Properties:
- deterministic prediction identity;
- immutable existing rows;
- idempotent replay;
- pre-kickoff predictions only;
- MARKET_ONLY and STRUCTURAL_V2 modes are explicit;
- no model training;
- no production artifact mutation;
- no Structural V2 activation;
- no finished-result mutation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd


TABLE = "league_prediction_ledger"

PROBABILITY_TOLERANCE = 1e-9


class PredictionLedgerError(RuntimeError):
    """Base prediction-ledger failure."""


class PredictionLedgerConflictError(
    PredictionLedgerError
):
    """Existing immutable prediction conflicts with incoming state."""


def _canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _timestamp(
    value: Any,
) -> str:
    parsed = pd.to_datetime(
        value,
        utc=True,
        errors="raise",
    )

    return parsed.isoformat()


def _float(
    value: Any,
) -> float:
    result = float(value)

    if not np.isfinite(result):
        raise ValueError(
            "Prediction contains non-finite numeric value"
        )

    return result


def _argmax(
    home: float,
    draw: float,
    away: float,
) -> str:
    values = np.asarray(
        [home, draw, away],
        dtype=float,
    )

    return ("H", "D", "A")[
        int(values.argmax())
    ]


def _probability_stats(
    home: float,
    draw: float,
    away: float,
) -> tuple[str, float, float, float]:
    values = sorted(
        [home, draw, away],
        reverse=True,
    )

    pick = _argmax(
        home,
        draw,
        away,
    )

    probability_by_pick = {
        "H": home,
        "D": draw,
        "A": away,
    }

    return (
        pick,
        probability_by_pick[pick],
        values[0],
        values[0] - values[1],
    )


def prediction_key(
    row: dict[str, Any],
) -> str:
    """Create deterministic identity for one immutable prediction state."""

    payload = {
        "league": str(row["league"]),
        "event_id": str(row["event_id"]),
        "snapshot_time_utc": _timestamp(
            row["snapshot_time_utc"]
        ),
        "prediction_mode": str(
            row["prediction_mode"]
        ),
        "market_home_prob": _float(
            row["market_home_prob"]
        ),
        "market_draw_prob": _float(
            row["market_draw_prob"]
        ),
        "market_away_prob": _float(
            row["market_away_prob"]
        ),
        "structural_home_prob": (
            None
            if row.get("structural_home_prob") is None
            else _float(row["structural_home_prob"])
        ),
        "structural_draw_prob": (
            None
            if row.get("structural_draw_prob") is None
            else _float(row["structural_draw_prob"])
        ),
        "structural_away_prob": (
            None
            if row.get("structural_away_prob") is None
            else _float(row["structural_away_prob"])
        ),
    }

    digest = hashlib.sha256(
        _canonical_json(payload).encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        f'{payload["league"]}:'
        f'{digest}'
    )


def build_market_only_predictions(
    shadow: pd.DataFrame,
    *,
    observation_keys: dict[
        tuple[str, str],
        str,
    ] | None = None,
) -> pd.DataFrame:
    """Build canonical MARKET_ONLY predictions from serialized shadow."""

    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "commence_time_utc",
        "snapshot_time_utc",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "market_argmax",
        "market_shadow_status",
        "market_only",
    }

    missing = required - set(
        shadow.columns
    )

    if missing:
        raise ValueError(
            "Market shadow missing columns: "
            + ", ".join(sorted(missing))
        )

    work = shadow.copy()

    work = work.loc[
        work["market_shadow_status"] == "OK"
    ].copy()

    if work.empty:
        raise ValueError(
            "No valid market-shadow predictions"
        )

    market_only = (
        work["market_only"]
        .astype(str)
        .str.lower()
        .map(
            {
                "true": True,
                "false": False,
            }
        )
    )

    if market_only.isna().any():
        raise ValueError(
            "Invalid market_only value"
        )

    if not market_only.all():
        raise ValueError(
            "Non-market-only shadow supplied"
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
            "snapshot_time_utc",
            "commence_time_utc",
        ]
    ].isna().any().any():
        raise ValueError(
            "Invalid prediction timestamps"
        )

    if not (
        work["snapshot_time_utc"]
        < work["commence_time_utc"]
    ).all():
        raise ValueError(
            "Prediction must be strictly pre-kickoff"
        )

    probability_columns = [
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
    ]

    probabilities = (
        work[probability_columns]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
    )

    matrix = probabilities.to_numpy(
        dtype=float
    )

    if not np.isfinite(matrix).all():
        raise ValueError(
            "Non-finite market probabilities"
        )

    if (
        (matrix < 0.0).any()
        or
        (matrix > 1.0).any()
    ):
        raise ValueError(
            "Market probability outside [0, 1]"
        )

    if not np.allclose(
        matrix.sum(axis=1),
        1.0,
        atol=PROBABILITY_TOLERANCE,
    ):
        raise ValueError(
            "Market probabilities are not normalized"
        )

    rows: list[dict[str, Any]] = []

    for index, source in work.iterrows():
        home = _float(
            source[
                "market_home_probability"
            ]
        )
        draw = _float(
            source[
                "market_draw_probability"
            ]
        )
        away = _float(
            source[
                "market_away_probability"
            ]
        )

        (
            pick,
            pick_probability,
            top_probability,
            margin,
        ) = _probability_stats(
            home,
            draw,
            away,
        )

        source_pick = str(
            source["market_argmax"]
        )

        if source_pick != pick:
            raise ValueError(
                "market_argmax does not match probabilities: "
                f"{source['event_id']}"
            )

        snapshot = pd.to_datetime(
            source["snapshot_time_utc"],
            utc=True,
        )

        kickoff = pd.to_datetime(
            source["commence_time_utc"],
            utc=True,
        )

        hours_to_kickoff = (
            kickoff - snapshot
        ).total_seconds() / 3600.0

        observation_key = None

        if observation_keys is not None:
            observation_key = (
                observation_keys.get(
                    (
                        str(source["event_id"]),
                        snapshot.isoformat(),
                    )
                )
            )

        row = {
            "league": str(
                source["league"]
            ),
            "event_id": str(
                source["event_id"]
            ),
            "home_team": str(
                source["home_team"]
            ),
            "away_team": str(
                source["away_team"]
            ),
            "kickoff_utc":
                kickoff.isoformat(),
            "prediction_time_utc":
                snapshot.isoformat(),
            "snapshot_time_utc":
                snapshot.isoformat(),
            "hours_to_kickoff":
                float(hours_to_kickoff),

            "market_home_prob": home,
            "market_draw_prob": draw,
            "market_away_prob": away,

            "market_pick": pick,
            "market_pick_probability":
                pick_probability,

            "market_top_probability":
                top_probability,
            "market_second_probability":
                top_probability - margin,
            "market_probability_margin":
                margin,

            "structural_status":
                "CALIBRATION_REQUIRED",

            "structural_home_prob": None,
            "structural_draw_prob": None,
            "structural_away_prob": None,

            "structural_pick": None,
            "structural_pick_probability":
                None,

            "structural_top_probability":
                None,
            "structural_second_probability":
                None,
            "structural_probability_margin":
                None,

            "structural_score": None,
            "structural_applied": False,

            "prediction_mode":
                "MARKET_ONLY",

            "observation_key":
                observation_key,
        }

        row["prediction_key"] = (
            prediction_key(row)
        )

        rows.append(row)

    result = pd.DataFrame(rows)

    if result[
        "prediction_key"
    ].duplicated().any():
        raise ValueError(
            "Duplicate canonical prediction keys"
        )

    return result


def _comparable(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Normalize DB/Python representations for immutable comparison."""

    timestamp_columns = {
        "kickoff_utc",
        "prediction_time_utc",
        "snapshot_time_utc",
    }

    float_columns = {
        "hours_to_kickoff",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "market_pick_probability",
        "market_top_probability",
        "market_second_probability",
        "market_probability_margin",
        "structural_home_prob",
        "structural_draw_prob",
        "structural_away_prob",
        "structural_pick_probability",
        "structural_top_probability",
        "structural_second_probability",
        "structural_probability_margin",
        "structural_score",
    }

    ignored = {
        "created_at_utc",
    }

    result = {}

    for key, value in row.items():
        if key in ignored:
            continue

        if key in timestamp_columns:
            result[key] = (
                None
                if value is None
                else _timestamp(value)
            )
            continue

        if key in float_columns:
            result[key] = (
                None
                if value is None
                else _float(value)
            )
            continue

        result[key] = value

    return result


def _rows_equal(
    existing: dict[str, Any],
    incoming: dict[str, Any],
) -> bool:
    left = _comparable(existing)
    right = _comparable(incoming)

    keys = set(left) | set(right)

    float_columns = {
        "hours_to_kickoff",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "market_pick_probability",
        "market_top_probability",
        "market_second_probability",
        "market_probability_margin",
        "structural_home_prob",
        "structural_draw_prob",
        "structural_away_prob",
        "structural_pick_probability",
        "structural_top_probability",
        "structural_second_probability",
        "structural_probability_margin",
        "structural_score",
    }

    for key in keys:
        a = left.get(key)
        b = right.get(key)

        if (
            key in float_columns
            and a is not None
            and b is not None
        ):
            if not np.isclose(
                float(a),
                float(b),
                atol=1e-12,
                rtol=0.0,
            ):
                return False
            continue

        if a != b:
            return False

    return True


def persist_predictions(
    client,
    frame: pd.DataFrame,
) -> dict[str, int]:
    """Append predictions with immutable/idempotent semantics."""

    if frame.empty:
        return {
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
        }

    inserted = 0
    unchanged = 0
    conflicts = 0

    for row in frame.to_dict(
        orient="records"
    ):
        key = str(
            row["prediction_key"]
        )

        existing_response = (
            client
            .table(TABLE)
            .select("*")
            .eq(
                "prediction_key",
                key,
            )
            .limit(1)
            .execute()
        )

        existing_rows = (
            existing_response.data
            or []
        )

        if existing_rows:
            if _rows_equal(
                existing_rows[0],
                row,
            ):
                unchanged += 1
                continue

            conflicts += 1

            raise PredictionLedgerConflictError(
                "Prediction conflict for "
                + key
            )

        (
            client
            .table(TABLE)
            .insert(row)
            .execute()
        )

        inserted += 1

    return {
        "inserted": inserted,
        "unchanged": unchanged,
        "conflicts": conflicts,
    }
