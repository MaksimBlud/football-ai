"""Historical bookmaker 1X2 market utilities.

Offline research only.

No model training.
No live activation.
No Supabase writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from league_offline_history import (
    normalize_team,
    parse_football_data_date,
)

from league_runtime_config import (
    LeagueRuntimeConfig,
)


@dataclass(frozen=True)
class MarketTriplet:
    home: str
    draw: str
    away: str
    source: str


CANDIDATES = (
    MarketTriplet(
        "AvgH",
        "AvgD",
        "AvgA",
        "FOOTBALL_DATA_AVERAGE",
    ),
    MarketTriplet(
        "B365H",
        "B365D",
        "B365A",
        "BET365",
    ),
    MarketTriplet(
        "PSH",
        "PSD",
        "PSA",
        "PINNACLE",
    ),
    MarketTriplet(
        "WHH",
        "WHD",
        "WHA",
        "WILLIAM_HILL",
    ),
    MarketTriplet(
        "VCH",
        "VCD",
        "VCA",
        "VCBET",
    ),
    MarketTriplet(
        "BWH",
        "BWD",
        "BWA",
        "BETWAY",
    ),
)


def choose_market_triplet(
    frames: list[pd.DataFrame],
) -> MarketTriplet:
    best = None
    best_coverage = -1

    for candidate in CANDIDATES:
        total = 0
        supported = True

        for frame in frames:
            columns = (
                candidate.home,
                candidate.draw,
                candidate.away,
            )

            if not all(
                column in frame.columns
                for column in columns
            ):
                supported = False
                break

            valid = (
                frame[
                    list(columns)
                ]
                .apply(
                    pd.to_numeric,
                    errors="coerce",
                )
                .gt(1.0)
                .all(axis=1)
            )

            total += int(
                valid.sum()
            )

        if (
            supported
            and total > best_coverage
        ):
            best = candidate
            best_coverage = total

    if best is None:
        raise ValueError(
            "No common historical 1X2 market triplet"
        )

    return best


def no_vig_probabilities(
    home_odds: pd.Series,
    draw_odds: pd.Series,
    away_odds: pd.Series,
) -> pd.DataFrame:
    home = pd.to_numeric(
        home_odds,
        errors="coerce",
    )

    draw = pd.to_numeric(
        draw_odds,
        errors="coerce",
    )

    away = pd.to_numeric(
        away_odds,
        errors="coerce",
    )

    valid = (
        (home > 1.0)
        & (draw > 1.0)
        & (away > 1.0)
    )

    inverse_home = 1.0 / home
    inverse_draw = 1.0 / draw
    inverse_away = 1.0 / away

    total = (
        inverse_home
        + inverse_draw
        + inverse_away
    )

    result = pd.DataFrame(
        {
            "market_home_probability":
                inverse_home / total,

            "market_draw_probability":
                inverse_draw / total,

            "market_away_probability":
                inverse_away / total,

            "market_overround":
                total - 1.0,

            "market_valid":
                valid,
        }
    )

    result.loc[
        ~valid,
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
            "market_overround",
        ],
    ] = pd.NA

    return result


def normalize_market_frame(
    frame: pd.DataFrame,
    *,
    config: LeagueRuntimeConfig,
    season: str,
    triplet: MarketTriplet,
) -> pd.DataFrame:
    required = {
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
        triplet.home,
        triplet.draw,
        triplet.away,
    }

    missing = (
        required
        - set(
            frame.columns
        )
    )

    if missing:
        raise ValueError(
            "Missing market columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    result = pd.DataFrame(
        {
            "league":
                config.identity.identifier,

            "season":
                season,

            "match_date":
                parse_football_data_date(
                    frame["Date"]
                ),

            "home_team":
                frame[
                    "HomeTeam"
                ].map(
                    lambda value:
                        normalize_team(
                            value,
                            config,
                        )
                ),

            "away_team":
                frame[
                    "AwayTeam"
                ].map(
                    lambda value:
                        normalize_team(
                            value,
                            config,
                        )
                ),

            "home_goals":
                pd.to_numeric(
                    frame[
                        "FTHG"
                    ],
                    errors="raise",
                ).astype(int),

            "away_goals":
                pd.to_numeric(
                    frame[
                        "FTAG"
                    ],
                    errors="raise",
                ).astype(int),

            "result":
                frame[
                    "FTR"
                ].astype(str),

            "market_home_odds":
                pd.to_numeric(
                    frame[
                        triplet.home
                    ],
                    errors="coerce",
                ),

            "market_draw_odds":
                pd.to_numeric(
                    frame[
                        triplet.draw
                    ],
                    errors="coerce",
                ),

            "market_away_odds":
                pd.to_numeric(
                    frame[
                        triplet.away
                    ],
                    errors="coerce",
                ),

            "market_source":
                triplet.source,
        }
    )

    probabilities = (
        no_vig_probabilities(
            result[
                "market_home_odds"
            ],
            result[
                "market_draw_odds"
            ],
            result[
                "market_away_odds"
            ],
        )
    )

    result = pd.concat(
        [
            result,
            probabilities,
        ],
        axis=1,
    )

    result[
        "market_argmax"
    ] = (
        result[
            [
                "market_home_probability",
                "market_draw_probability",
                "market_away_probability",
            ]
        ]
        .idxmax(
            axis=1,
        )
        .map(
            {
                "market_home_probability": "H",
                "market_draw_probability": "D",
                "market_away_probability": "A",
            }
        )
    )

    result = (
        result
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

    return result


def load_historical_market(
    *,
    config: LeagueRuntimeConfig,
    raw_directory: Path,
    file_prefix: str,
) -> tuple[pd.DataFrame, MarketTriplet]:
    frames = []
    metadata = []

    for _, season in (
        config
        .historical_source
        .season_codes
        .items()
    ):
        start_year = int(
            season.split("-")[0]
        )

        path = (
            raw_directory
            / (
                f"{file_prefix}_"
                f"{start_year}_"
                f"{start_year + 1}.csv"
            )
        )

        frame = pd.read_csv(
            path
        )

        frames.append(
            frame
        )

        metadata.append(
            season
        )

    triplet = choose_market_triplet(
        frames
    )

    normalized = []

    for frame, season in zip(
        frames,
        metadata,
    ):
        normalized.append(
            normalize_market_frame(
                frame,
                config=config,
                season=season,
                triplet=triplet,
            )
        )

    combined = pd.concat(
        normalized,
        ignore_index=True,
    )

    identity = [
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
    ]

    if combined.duplicated(
        subset=identity
    ).any():
        raise ValueError(
            "Duplicate market fixture identities"
        )

    return (
        combined,
        triplet,
    )
