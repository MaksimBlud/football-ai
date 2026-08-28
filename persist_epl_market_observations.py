"""Persist EPL MARKET_ONLY live observations to the generic durable store.

This module:
- reads the existing EPL market shadow;
- converts valid market-only rows to the generic observation contract;
- writes only league_structural_v2_observations;
- never writes finished results;
- never invokes Structural V2;
- never invokes the production model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from database import supabase

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)

from league_supabase_persistence import (
    persist_observations,
)


MARKET_COLUMNS = (
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
)


def load_market_shadow() -> pd.DataFrame:
    return pd.read_csv(
        EPL_RUNTIME_CONFIG
        .paths
        .market_shadow
    )


def build_market_only_observations(
    shadow: pd.DataFrame,
) -> pd.DataFrame:
    """Convert valid EPL market shadow rows to durable observations."""

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

    missing = (
        required
        - set(shadow.columns)
    )

    if missing:
        raise ValueError(
            "Market shadow missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    work = shadow.copy()

    league_id = (
        EPL_RUNTIME_CONFIG
        .identity
        .identifier
    )

    if not (
        work["league"]
        == league_id
    ).all():
        raise ValueError(
            "Market shadow contains non-EPL rows"
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
            "market_only contains invalid values"
        )

    work["market_only"] = (
        market_only
    )

    if not work[
        "market_only"
    ].all():
        raise ValueError(
            "Non-market-only EPL shadow supplied"
        )

    work = work.loc[
        work[
            "market_shadow_status"
        ]
        == "OK"
    ].copy()

    if work.empty:
        raise ValueError(
            "No valid EPL market observations"
        )

    work[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        work[
            "snapshot_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    work[
        "commence_time_utc"
    ] = pd.to_datetime(
        work[
            "commence_time_utc"
        ],
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
            "Invalid EPL observation timestamps"
        )

    if not (
        work[
            "snapshot_time_utc"
        ]
        <
        work[
            "commence_time_utc"
        ]
    ).all():
        raise ValueError(
            "EPL observation must be pre-kickoff"
        )

    probability = work[
        list(
            MARKET_COLUMNS
        )
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    matrix = probability.to_numpy(
        dtype=float
    )

    if not np.isfinite(
        matrix
    ).all():
        raise ValueError(
            "Non-finite EPL market probabilities"
        )

    if not np.allclose(
        matrix.sum(
            axis=1
        ),
        1.0,
        atol=1e-12,
    ):
        raise ValueError(
            "EPL market probabilities are not normalized"
        )

    result = pd.DataFrame(
        {
            "league":
                work[
                    "league"
                ].astype(str),

            "event_id":
                work[
                    "event_id"
                ].astype(str),

            "home_team":
                work[
                    "home_team"
                ].astype(str),

            "away_team":
                work[
                    "away_team"
                ].astype(str),

            "snapshot_time_utc":
                work[
                    "snapshot_time_utc"
                ],

            "commence_time_utc":
                work[
                    "commence_time_utc"
                ],

            "market_home_probability":
                probability[
                    "market_home_probability"
                ].astype(float),

            "market_draw_probability":
                probability[
                    "market_draw_probability"
                ].astype(float),

            "market_away_probability":
                probability[
                    "market_away_probability"
                ].astype(float),

            # MARKET_ONLY means shadow == market.
            "shadow_home_probability":
                probability[
                    "market_home_probability"
                ].astype(float),

            "shadow_draw_probability":
                probability[
                    "market_draw_probability"
                ].astype(float),

            "shadow_away_probability":
                probability[
                    "market_away_probability"
                ].astype(float),

            "market_argmax":
                work[
                    "market_argmax"
                ].astype(str),

            "shadow_argmax":
                work[
                    "market_argmax"
                ].astype(str),

            "structural_ready":
                False,

            "structural_score":
                None,

            "correction_enabled":
                False,

            "realized_correction_weight":
                0.0,

            "prediction_source":
                "MARKET_ONLY",

            "pre_kickoff_valid":
                True,

            "research_only":
                True,
        }
    )

    if result[
        "event_id"
    ].duplicated().any():
        raise ValueError(
            "Duplicate EPL event_id in current market shadow"
        )

    return result.reset_index(
        drop=True
    )


def persist_current_market_observations() -> dict:
    shadow = load_market_shadow()

    observations = (
        build_market_only_observations(
            shadow
        )
    )

    metrics = persist_observations(
        supabase,
        observations,
        EPL_RUNTIME_CONFIG,
    )

    print(
        "incoming observations:",
        len(observations),
    )

    print(
        "persistence metrics:",
        metrics,
    )

    return metrics


def main() -> None:
    persist_current_market_observations()


if __name__ == "__main__":
    main()
