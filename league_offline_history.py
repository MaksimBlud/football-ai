"""Generic Football-Data historical normalization for offline research."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from league_runtime_config import (
    LeagueRuntimeConfig,
)


REQUIRED_COLUMNS = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
}


def normalize_team(
    value,
    config: LeagueRuntimeConfig,
) -> str:
    name = str(value).strip()

    if not name:
        raise ValueError(
            "Empty team name"
        )

    return config.aliases.get(
        name,
        name,
    )


def parse_football_data_date(
    series: pd.Series,
) -> pd.Series:
    raw = (
        series
        .astype(str)
        .str.strip()
    )

    parsed_four = pd.to_datetime(
        raw,
        format="%d/%m/%Y",
        errors="coerce",
    )

    remaining = parsed_four.isna()

    parsed_two = pd.to_datetime(
        raw.where(remaining),
        format="%d/%m/%y",
        errors="coerce",
    )

    result = parsed_four.fillna(
        parsed_two
    )

    if result.isna().any():
        bad = sorted(
            raw[
                result.isna()
            ].unique()
        )

        raise ValueError(
            "Unparseable Football-Data dates: "
            + repr(
                bad[:10]
            )
        )

    return result


def normalize_football_data_frame(
    frame: pd.DataFrame,
    *,
    config: LeagueRuntimeConfig,
    season: str,
    require_complete: bool = False,
) -> pd.DataFrame:
    missing = (
        REQUIRED_COLUMNS
        - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Missing Football-Data columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    if (
        require_complete
        and len(frame) != 380
    ):
        raise ValueError(
            f"Incomplete season {season}: "
            f"{len(frame)} rows"
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
                    frame["FTHG"],
                    errors="raise",
                ).astype(int),

            "away_goals":
                pd.to_numeric(
                    frame["FTAG"],
                    errors="raise",
                ).astype(int),

            "result":
                frame[
                    "FTR"
                ].astype(str),
        }
    )

    valid_results = {
        "H",
        "D",
        "A",
    }

    if not set(
        result["result"]
    ).issubset(
        valid_results
    ):
        raise ValueError(
            "Unexpected full-time result"
        )

    identity = [
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
    ]

    if result.duplicated(
        subset=identity
    ).any():
        raise ValueError(
            f"Duplicate fixture identity in {season}"
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


def load_configured_history(
    *,
    config: LeagueRuntimeConfig,
    raw_directory: Path,
    file_prefix: str,
    require_complete: bool = True,
) -> pd.DataFrame:
    frames = []

    for code, season in (
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

        if not path.exists():
            raise FileNotFoundError(
                path
            )

        source = pd.read_csv(
            path
        )

        normalized = (
            normalize_football_data_frame(
                source,
                config=config,
                season=season,
                require_complete=require_complete,
            )
        )

        frames.append(
            normalized
        )

    combined = pd.concat(
        frames,
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
            "Duplicate historical fixture identities"
        )

    combined = (
        combined
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

    return combined
