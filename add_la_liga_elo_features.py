"""Add leakage-safe Elo features to La Liga temporal dataset.

Research-only:
- Elo before each match uses only previous matches;
- current result updates Elo only after feature capture;
- writes only research CSV files;
- performs no model training or promotion.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


INPUT = Path(
    "data/la_liga_features_temporal.csv"
)

OUTPUT = Path(
    "data/la_liga_features_with_elo.csv"
)

TRAINABLE_OUTPUT = Path(
    "data/la_liga_features_with_elo_trainable.csv"
)

INITIAL_ELO = 1500.0
K_FACTOR = 20.0
HOME_ADVANTAGE = 65.0


def expected_score(
    rating_a: float,
    rating_b: float,
) -> float:
    return 1.0 / (
        1.0
        + 10.0 ** (
            (rating_b - rating_a)
            / 400.0
        )
    )


def actual_scores(
    result: str,
) -> tuple[float, float]:
    if result == "H":
        return 1.0, 0.0

    if result == "A":
        return 0.0, 1.0

    if result == "D":
        return 0.5, 0.5

    raise ValueError(
        f"Unknown result: {result}"
    )


def add_elo(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    df = frame.copy()

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="raise",
    )

    df = (
        df
        .sort_values(
            [
                "match_date",
                "match_time",
                "home_team",
                "away_team",
            ]
        )
        .reset_index(drop=True)
    )

    ratings: dict[str, float] = {}

    home_elo = []
    away_elo = []

    for _, row in df.iterrows():
        home = str(
            row["home_team"]
        )

        away = str(
            row["away_team"]
        )

        h_rating = ratings.get(
            home,
            INITIAL_ELO,
        )

        a_rating = ratings.get(
            away,
            INITIAL_ELO,
        )

        # Store PRE-MATCH ratings.
        home_elo.append(h_rating)
        away_elo.append(a_rating)

        adjusted_home = (
            h_rating
            + HOME_ADVANTAGE
        )

        expected_home = expected_score(
            adjusted_home,
            a_rating,
        )

        expected_away = (
            1.0 - expected_home
        )

        actual_home, actual_away = (
            actual_scores(
                str(row["result"])
            )
        )

        # Update only AFTER capturing
        # the current match features.
        ratings[home] = (
            h_rating
            + K_FACTOR
            * (
                actual_home
                - expected_home
            )
        )

        ratings[away] = (
            a_rating
            + K_FACTOR
            * (
                actual_away
                - expected_away
            )
        )

    df["home_elo"] = home_elo
    df["away_elo"] = away_elo

    df["elo_difference"] = (
        df["home_elo"]
        - df["away_elo"]
    )

    df["match_date"] = (
        df["match_date"]
        .dt.strftime("%Y-%m-%d")
    )

    return df


def main() -> None:
    frame = pd.read_csv(
        INPUT
    )

    if set(
        frame["league"]
        .dropna()
        .unique()
    ) != {"LA_LIGA"}:
        raise RuntimeError(
            "Input is not pure LA_LIGA"
        )

    result = add_elo(
        frame
    )

    trainable = (
        result[
            result["warmup_ok"]
            .astype(bool)
        ]
        .copy()
        .reset_index(drop=True)
    )

    result.to_csv(
        OUTPUT,
        index=False,
    )

    trainable.to_csv(
        TRAINABLE_OUTPUT,
        index=False,
    )

    print("=" * 72)
    print("LA LIGA ELO FEATURES")
    print("=" * 72)

    print(
        "rows:",
        len(result),
    )

    print(
        "trainable:",
        len(trainable),
    )

    print(
        "teams:",
        len(
            set(result["home_team"])
            | set(result["away_team"])
        ),
    )

    print()
    print("ELO SUMMARY:")

    print(
        result[
            [
                "home_elo",
                "away_elo",
                "elo_difference",
            ]
        ]
        .describe()
        .to_string()
    )

    print()
    print(
        "output:",
        OUTPUT,
    )

    print(
        "trainable:",
        TRAINABLE_OUTPUT,
    )


if __name__ == "__main__":
    main()
