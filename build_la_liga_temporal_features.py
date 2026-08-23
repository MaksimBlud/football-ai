"""Build leakage-safe La Liga features using the established feature schema.

Research-only:
- reads normalized local La Liga history;
- reuses the established pre-match feature builder;
- adds explicit prior-match / warm-up metadata;
- writes only under data/;
- performs no Supabase write;
- performs no training or promotion.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from feature_engineering import build_features


INPUT = Path(
    "data/la_liga_official_history_2016_2026_normalized.csv"
)

OUTPUT = Path(
    "data/la_liga_features_temporal.csv"
)

TRAINABLE_OUTPUT = Path(
    "data/la_liga_features_trainable.csv"
)

MIN_PRIOR_MATCHES = 5


def add_prior_match_counts(
    history: pd.DataFrame,
) -> pd.DataFrame:
    frame = history.copy()

    frame["match_date"] = pd.to_datetime(
        frame["match_date"],
        errors="raise",
    )

    frame = (
        frame
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

    counts: dict[str, int] = {}

    home_prior = []
    away_prior = []

    for _, row in frame.iterrows():
        home = str(row["home_team"])
        away = str(row["away_team"])

        home_prior.append(
            counts.get(home, 0)
        )

        away_prior.append(
            counts.get(away, 0)
        )

        counts[home] = (
            counts.get(home, 0) + 1
        )

        counts[away] = (
            counts.get(away, 0) + 1
        )

    frame["home_prior_matches"] = (
        home_prior
    )

    frame["away_prior_matches"] = (
        away_prior
    )

    frame["warmup_ok"] = (
        (
            frame["home_prior_matches"]
            >= MIN_PRIOR_MATCHES
        )
        &
        (
            frame["away_prior_matches"]
            >= MIN_PRIOR_MATCHES
        )
    )

    return frame


def build() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    history = pd.read_csv(
        INPUT
    )

    if set(
        history["league"]
        .dropna()
        .unique()
    ) != {"LA_LIGA"}:
        raise RuntimeError(
            "Input is not pure LA_LIGA history"
        )

    ordered = add_prior_match_counts(
        history
    )

    # Established feature_engineering.build_features()
    # calculates features before inserting the
    # current match into its internal history.
    features = build_features(
        ordered.copy()
    )

    if len(features) != len(ordered):
        raise RuntimeError(
            "Feature row count differs from history"
        )

    metadata = ordered[
        [
            "season",
            "match_date",
            "match_time",
            "home_team",
            "away_team",
            "home_prior_matches",
            "away_prior_matches",
            "warmup_ok",
        ]
    ].copy()

    metadata["match_date"] = (
        pd.to_datetime(
            metadata["match_date"]
        )
        .dt.strftime("%Y-%m-%d")
    )

    features["match_date"] = (
        pd.to_datetime(
            features["match_date"]
        )
        .dt.strftime("%Y-%m-%d")
    )

    key = [
        "season",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
    ]

    result = features.merge(
        metadata,
        on=key,
        how="left",
        validate="one_to_one",
    )

    result.insert(
        0,
        "league",
        "LA_LIGA",
    )

    if result[
        [
            "home_prior_matches",
            "away_prior_matches",
            "warmup_ok",
        ]
    ].isna().any().any():
        raise RuntimeError(
            "Warm-up metadata merge failed"
        )

    trainable = (
        result[
            result["warmup_ok"]
            .astype(bool)
        ]
        .copy()
        .reset_index(drop=True)
    )

    return (
        result.reset_index(drop=True),
        trainable,
    )


def main() -> None:
    features, trainable = build()

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    features.to_csv(
        OUTPUT,
        index=False,
    )

    trainable.to_csv(
        TRAINABLE_OUTPUT,
        index=False,
    )

    print("=" * 72)
    print("LA LIGA TEMPORAL FEATURES")
    print("=" * 72)

    print(
        "all rows:",
        len(features),
    )

    print(
        "trainable rows:",
        len(trainable),
    )

    print(
        "warm-up removed:",
        len(features) - len(trainable),
    )

    print(
        "features:",
        len(features.columns),
    )

    print()
    print("TRAINABLE ROWS PER SEASON:")

    print(
        trainable["season"]
        .value_counts()
        .sort_index()
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
