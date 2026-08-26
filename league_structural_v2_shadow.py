"""Generic Structural Edge V2 live-shadow primitives.

Research-only.

No persistence.
No production promotion.
No source-network access.

The algorithm is shared, while every league must provide its own
validated runtime configuration and reference/training data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import league_structural_edge_v2 as structural_v2

from league_runtime_config import (
    LeagueRuntimeConfig,
)


STRUCTURAL_FEATURES = (
    "elo_difference",
    "form_difference",
    "venue_win_rate_difference",
    "home_goals_scored_last5",
    "away_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_conceded_last5",
    "home_venue_goals_scored",
    "away_venue_goals_scored",
    "home_venue_goals_conceded",
    "away_venue_goals_conceded",
)


@dataclass(frozen=True)
class TeamState:
    matches: int
    elo: float


def validate_single_league(
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
    *,
    label: str,
) -> None:
    if frame.empty:
        return

    if "league" not in frame.columns:
        raise ValueError(
            f"{label} missing league column"
        )

    league_id = (
        config.identity.identifier
    )

    observed = set(
        frame["league"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if observed != {league_id}:
        raise ValueError(
            f"{label} league mismatch: "
            f"expected={league_id}, observed={sorted(observed)}"
        )


def fit_reference_stats(
    training: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> dict:
    validate_single_league(
        training,
        config,
        label="training",
    )

    return structural_v2.fit_stats(
        training
    )


def structural_scores(
    rows: pd.DataFrame,
    stats: dict,
) -> pd.Series:
    return structural_v2.structural_score(
        rows,
        stats,
    )


def apply_structural_v2(
    market_probability: np.ndarray,
    scores: np.ndarray,
    config: LeagueRuntimeConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply target-league Structural V2 calibration.

    Returns:
        corrected probabilities
        enabled mask
        realized correction weights
    """

    config.validate()

    corrected = []
    enabled = []
    realized_weights = []

    alpha = (
        config.structural_v2
        .structural_alpha
    )

    threshold = (
        config.structural_v2
        .edge_threshold
    )

    for market_row, score in zip(
        market_probability,
        scores,
    ):
        score_value = float(
            score
        )

        use_correction = (
            np.isfinite(
                score_value
            )
            and abs(
                score_value
            )
            >= threshold
        )

        if not use_correction:
            corrected.append(
                np.asarray(
                    market_row,
                    dtype=float,
                )
            )
            enabled.append(
                False
            )
            realized_weights.append(
                0.0
            )
            continue

        output = (
            structural_v2
            .argmax_preserving_correction(
                np.asarray(
                    market_row,
                    dtype=float,
                ),
                score_value,
                structural_alpha=alpha,
            )
        )

        if isinstance(
            output,
            tuple,
        ):
            probability = (
                np.asarray(
                    output[0],
                    dtype=float,
                )
            )

            weight = (
                float(output[1])
                if len(output) > 1
                else 1.0
            )
        else:
            probability = (
                np.asarray(
                    output,
                    dtype=float,
                )
            )
            weight = 1.0

        if (
            np.argmax(
                probability
            )
            != np.argmax(
                market_row
            )
        ):
            raise RuntimeError(
                "Structural V2 changed market argmax"
            )

        if (
            not np.isfinite(
                probability
            ).all()
            or (
                probability
                <= 0
            ).any()
        ):
            raise RuntimeError(
                "Invalid Structural V2 probabilities"
            )

        probability = (
            probability
            / probability.sum()
        )

        corrected.append(
            probability
        )

        enabled.append(
            True
        )

        realized_weights.append(
            weight
        )

    return (
        np.asarray(
            corrected,
            dtype=float,
        ),
        np.asarray(
            enabled,
            dtype=bool,
        ),
        np.asarray(
            realized_weights,
            dtype=float,
        ),
    )


def structural_ready(
    *,
    home_prior_matches: int,
    away_prior_matches: int,
    config: LeagueRuntimeConfig,
) -> bool:
    minimum = (
        config.structural_v2
        .min_prior_matches
    )

    return (
        int(
            home_prior_matches
        )
        >= minimum
        and int(
            away_prior_matches
        )
        >= minimum
    )
