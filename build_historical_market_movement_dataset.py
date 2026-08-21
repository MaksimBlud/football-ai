from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

ODDS_DIR = (
    ROOT
    / "data"
    / "external"
    / "football_data_odds"
)

FEATURES_FILE = (
    ROOT
    / "data"
    / "features_with_elo.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "historical_market_movement_dataset.csv"
)


SEASONS = {
    "2019/2020": "1920",
    "2020/2021": "2021",
    "2021/2022": "2122",
    "2022/2023": "2223",
    "2023/2024": "2324",
    "2024/2025": "2425",
}


TEAM_MAP = {
    "Man United": "Man United",
    "Man City": "Man City",
    "Nott'm Forest": "Nott'm Forest",
    "Newcastle": "Newcastle",
    "Tottenham": "Tottenham",
    "West Ham": "West Ham",
    "Wolves": "Wolves",
    "Leicester": "Leicester",
    "Brighton": "Brighton",
    "Sheffield United": "Sheffield United",
    "West Brom": "West Brom",
    "Norwich": "Norwich",
    "Watford": "Watford",
    "Leeds": "Leeds",
    "Burnley": "Burnley",
    "Bournemouth": "Bournemouth",
    "Southampton": "Southampton",
    "Fulham": "Fulham",
    "Brentford": "Brentford",
    "Luton": "Luton",
    "Ipswich": "Ipswich",
}


def normalize_team(name):
    if pd.isna(name):
        return name

    name = str(name).strip()

    return TEAM_MAP.get(
        name,
        name,
    )


def odds_to_probs(frame, cols, prefix):
    odds = (
        frame[cols]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .to_numpy(dtype=float)
    )

    implied = 1.0 / odds

    probs = (
        implied
        / implied.sum(
            axis=1,
            keepdims=True,
        )
    )

    frame[
        f"{prefix}_p_home"
    ] = probs[:, 0]

    frame[
        f"{prefix}_p_draw"
    ] = probs[:, 1]

    frame[
        f"{prefix}_p_away"
    ] = probs[:, 2]

    return frame


# ============================================================
# LOAD HISTORICAL OPEN/CLOSE ODDS
# ============================================================

parts = []

for season, code in SEASONS.items():

    path = (
        ODDS_DIR
        / f"EPL_{code}.csv"
    )

    df = pd.read_csv(path)

    required = [
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTR",
        "B365H",
        "B365D",
        "B365A",
        "B365CH",
        "B365CD",
        "B365CA",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise SystemExit(
            f"❌ {path}: missing {missing}"
        )

    x = df[required].copy()

    x["season"] = season

    x["match_date"] = pd.to_datetime(
        x["Date"],
        dayfirst=True,
        errors="coerce",
    ).dt.normalize()

    x["home_team"] = (
        x["HomeTeam"]
        .map(normalize_team)
    )

    x["away_team"] = (
        x["AwayTeam"]
        .map(normalize_team)
    )

    x = odds_to_probs(
        x,
        [
            "B365H",
            "B365D",
            "B365A",
        ],
        "open",
    )

    x = odds_to_probs(
        x,
        [
            "B365CH",
            "B365CD",
            "B365CA",
        ],
        "close",
    )

    x[
        "move_home"
    ] = (
        x["close_p_home"]
        - x["open_p_home"]
    )

    x[
        "move_draw"
    ] = (
        x["close_p_draw"]
        - x["open_p_draw"]
    )

    x[
        "move_away"
    ] = (
        x["close_p_away"]
        - x["open_p_away"]
    )

    x[
        "max_abs_move"
    ] = (
        x[
            [
                "move_home",
                "move_draw",
                "move_away",
            ]
        ]
        .abs()
        .max(axis=1)
    )

    x[
        "strongest_move_side"
    ] = (
        x[
            [
                "move_home",
                "move_draw",
                "move_away",
            ]
        ]
        .abs()
        .idxmax(axis=1)
        .str.replace(
            "move_",
            "",
            regex=False,
        )
        .str.upper()
    )

    parts.append(x)


market = pd.concat(
    parts,
    ignore_index=True,
)


# ============================================================
# LOAD OUR FEATURES
# ============================================================

features = pd.read_csv(
    FEATURES_FILE
)

features["match_date"] = pd.to_datetime(
    features["match_date"],
    errors="coerce",
).dt.normalize()

features["home_team"] = (
    features["home_team"]
    .map(normalize_team)
)

features["away_team"] = (
    features["away_team"]
    .map(normalize_team)
)


# ============================================================
# JOIN
# ============================================================

keys = [
    "season",
    "match_date",
    "home_team",
    "away_team",
]


merged = market.merge(
    features,
    on=keys,
    how="left",
    suffixes=(
        "_market",
        "",
    ),
    indicator=True,
)


print("=" * 120)
print("HISTORICAL MARKET MOVEMENT DATASET")
print("=" * 120)

print(
    "Market rows:",
    len(market),
)

print(
    "Feature rows:",
    len(features),
)

print(
    "Merged rows:",
    len(merged),
)


print()
print("=" * 120)
print("JOIN QUALITY")
print("=" * 120)

print(
    merged["_merge"]
    .value_counts()
    .to_string()
)


unmatched = merged[
    merged["_merge"]
    != "both"
].copy()

print()
print(
    "Unmatched:",
    len(unmatched),
)


if not unmatched.empty:

    print()
    print(
        unmatched[
            [
                "season",
                "match_date",
                "home_team",
                "away_team",
            ]
        ]
        .head(50)
        .to_string(index=False)
    )


# ============================================================
# TARGET CHECK
# ============================================================

target_from_market = (
    merged["FTR"]
    .map({
        "H": 0,
        "D": 1,
        "A": 2,
    })
)

if "result" in merged.columns:
    target_from_features = (
        merged["result"]
        .map({
            "H": 0,
            "D": 1,
            "A": 2,
        })
    )

    target_match = (
        target_from_market
        == target_from_features
    )

    print()
    print("=" * 120)
    print("TARGET CONSISTENCY")
    print("=" * 120)

    print(
        "Matched targets:",
        int(target_match.sum()),
        "/",
        len(merged),
    )

    print(
        "Mismatches:",
        int((~target_match).sum()),
    )


# ============================================================
# SAVE CLEAN DATASET
# ============================================================

merged["target"] = target_from_market

merged = merged.drop(
    columns=["_merge"]
)

merged.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 120)
print("MARKET MOVEMENT SUMMARY")
print("=" * 120)

summary = (
    merged.groupby("season")
    .agg(
        matches=(
            "target",
            "size",
        ),

        avg_abs_move=(
            "max_abs_move",
            "mean",
        ),

        median_abs_move=(
            "max_abs_move",
            "median",
        ),

        p90_abs_move=(
            "max_abs_move",
            lambda x:
                x.quantile(0.90),
        ),

        max_abs_move=(
            "max_abs_move",
            "max",
        ),
    )
)

print(
    summary.to_string()
)


print()
print("=" * 120)
print("STRONGEST MOVE DISTRIBUTION")
print("=" * 120)

print(
    merged[
        "strongest_move_side"
    ]
    .value_counts()
    .to_string()
)


print()
print("=" * 120)
print("TOP 25 MARKET MOVES")
print("=" * 120)

print(
    merged[
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "open_p_home",
            "open_p_draw",
            "open_p_away",
            "close_p_home",
            "close_p_draw",
            "close_p_away",
            "move_home",
            "move_draw",
            "move_away",
            "max_abs_move",
            "strongest_move_side",
            "FTR",
        ]
    ]
    .sort_values(
        "max_abs_move",
        ascending=False,
    )
    .head(25)
    .to_string(index=False)
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
