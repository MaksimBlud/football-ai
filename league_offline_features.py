"""Leakage-safe generic temporal, structural and Elo features."""

from __future__ import annotations

import pandas as pd

from league_runtime_config import (
    LeagueRuntimeConfig,
)


LAST_MATCHES = 5


def _expected(
    rating_a: float,
    rating_b: float,
) -> float:
    return 1.0 / (
        1.0
        + 10.0
        ** (
            (
                rating_b
                - rating_a
            )
            / 400.0
        )
    )


def _average(
    values,
) -> float:
    values = list(
        values
    )

    if not values:
        return 0.0

    return float(
        sum(values)
        / len(values)
    )


def _points(
    result: str,
    *,
    home: bool,
) -> int:
    if result == "D":
        return 1

    if (
        home
        and result == "H"
    ):
        return 3

    if (
        not home
        and result == "A"
    ):
        return 3

    return 0


def build_temporal_elo_features(
    frame: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> pd.DataFrame:
    """Create strictly pre-match temporal/Structural-V2 features.

    Every output value for match N is calculated from matches before N.
    The current result updates team state only after the row is emitted.
    """

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

    missing = (
        required
        - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Missing historical columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    work = (
        frame
        .copy()
        .sort_values(
            [
                "match_date",
                "home_team",
                "away_team",
            ],
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )

    expected_league = (
        config
        .identity
        .identifier
    )

    observed_leagues = set(
        work[
            "league"
        ].dropna().astype(str).unique()
    )

    if observed_leagues != {
        expected_league,
    }:
        raise ValueError(
            "League mismatch"
        )

    played = {}
    ratings = {}

    team_history = {}
    home_venue_history = {}
    away_venue_history = {}

    rows = []

    initial = float(
        config
        .elo
        .initial_rating
    )

    k_factor = float(
        config
        .elo
        .k_factor
    )

    home_advantage = float(
        config
        .elo
        .home_advantage
    )

    minimum = int(
        config
        .temporal
        .min_prior_matches
    )

    for row in work.itertuples(
        index=False
    ):
        home = row.home_team
        away = row.away_team

        home_prior = int(
            played.get(
                home,
                0,
            )
        )

        away_prior = int(
            played.get(
                away,
                0,
            )
        )

        home_elo = float(
            ratings.get(
                home,
                initial,
            )
        )

        away_elo = float(
            ratings.get(
                away,
                initial,
            )
        )

        # Strictly PRE-MATCH histories.
        home_history = (
            team_history
            .get(
                home,
                [],
            )[-LAST_MATCHES:]
        )

        away_history = (
            team_history
            .get(
                away,
                [],
            )[-LAST_MATCHES:]
        )

        # Established venue contract uses all previous
        # matches at the relevant venue, not only last five.
        home_venue_matches = (
            home_venue_history
            .get(
                home,
                [],
            )
        )

        away_venue_matches = (
            away_venue_history
            .get(
                away,
                [],
            )
        )

        home_last5_points = sum(
            match[
                "points"
            ]
            for match in home_history
        )

        away_last5_points = sum(
            match[
                "points"
            ]
            for match in away_history
        )

        home_goals_scored_last5 = _average(
            match[
                "goals_scored"
            ]
            for match in home_history
        )

        home_goals_conceded_last5 = _average(
            match[
                "goals_conceded"
            ]
            for match in home_history
        )

        away_goals_scored_last5 = _average(
            match[
                "goals_scored"
            ]
            for match in away_history
        )

        away_goals_conceded_last5 = _average(
            match[
                "goals_conceded"
            ]
            for match in away_history
        )

        home_venue_win_rate = _average(
            match[
                "win"
            ]
            for match in home_venue_matches
        )

        away_venue_win_rate = _average(
            match[
                "win"
            ]
            for match in away_venue_matches
        )

        record = (
            row._asdict()
        )

        record.update(
            {
                "home_prior_matches":
                    home_prior,

                "away_prior_matches":
                    away_prior,

                "home_last5_points":
                    home_last5_points,

                "away_last5_points":
                    away_last5_points,

                "form_difference":
                    (
                        home_last5_points
                        - away_last5_points
                    ),

                "home_goals_scored_last5":
                    home_goals_scored_last5,

                "home_goals_conceded_last5":
                    home_goals_conceded_last5,

                "away_goals_scored_last5":
                    away_goals_scored_last5,

                "away_goals_conceded_last5":
                    away_goals_conceded_last5,

                "home_venue_win_rate":
                    home_venue_win_rate,

                "away_venue_win_rate":
                    away_venue_win_rate,

                "venue_win_rate_difference":
                    (
                        home_venue_win_rate
                        - away_venue_win_rate
                    ),

                "home_elo":
                    home_elo,

                "away_elo":
                    away_elo,

                # Keep previous generic raw rating difference
                # for compatibility.
                "elo_diff":
                    (
                        home_elo
                        - away_elo
                    ),

                # Historical Structural-V2 contract.
                "elo_difference":
                    (
                        home_elo
                        + home_advantage
                        - away_elo
                    ),

                "trainable":
                    (
                        home_prior
                        >= minimum
                        and away_prior
                        >= minimum
                    ),
            }
        )

        rows.append(
            record
        )

        # --------------------------------------------------
        # State mutation starts ONLY after current row exists.
        # --------------------------------------------------

        result = str(
            row.result
        )

        home_points = _points(
            result,
            home=True,
        )

        away_points = _points(
            result,
            home=False,
        )

        home_match = {
            "points":
                home_points,

            "win":
                1
                if result == "H"
                else 0,

            "goals_scored":
                float(
                    row.home_goals
                ),

            "goals_conceded":
                float(
                    row.away_goals
                ),
        }

        away_match = {
            "points":
                away_points,

            "win":
                1
                if result == "A"
                else 0,

            "goals_scored":
                float(
                    row.away_goals
                ),

            "goals_conceded":
                float(
                    row.home_goals
                ),
        }

        team_history.setdefault(
            home,
            [],
        ).append(
            home_match
        )

        team_history.setdefault(
            away,
            [],
        ).append(
            away_match
        )

        home_venue_history.setdefault(
            home,
            [],
        ).append(
            home_match
        )

        away_venue_history.setdefault(
            away,
            [],
        ).append(
            away_match
        )

        expected_home = _expected(
            home_elo
            + home_advantage,
            away_elo,
        )

        if (
            row.home_goals
            > row.away_goals
        ):
            actual_home = 1.0

        elif (
            row.home_goals
            < row.away_goals
        ):
            actual_home = 0.0

        else:
            actual_home = 0.5

        change = (
            k_factor
            * (
                actual_home
                - expected_home
            )
        )

        ratings[
            home
        ] = (
            home_elo
            + change
        )

        ratings[
            away
        ] = (
            away_elo
            - change
        )

        played[
            home
        ] = (
            home_prior
            + 1
        )

        played[
            away
        ] = (
            away_prior
            + 1
        )

    return pd.DataFrame(
        rows
    )
