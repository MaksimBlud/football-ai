from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "experiments"
    / "challenger_walk_forward_predictions.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "value_bet_backtest_results.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


THRESHOLDS = [
    0.00,
    0.01,
    0.02,
    0.03,
    0.05,
    0.07,
    0.10,
]


df = pd.read_csv(INPUT_FILE)


# ============================================================
# BASIC CHECK
# ============================================================

required = [
    "season",
    "actual",
    "p_home",
    "p_draw",
    "p_away",
    "home_odds",
    "draw_odds",
    "away_odds",
]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:
    raise SystemExit(
        f"❌ Missing columns: {missing}"
    )


# ============================================================
# BOOKMAKER FAIR PROBABILITIES
# ============================================================

odds = df[
    [
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
].to_numpy(dtype=float)

raw_implied = 1.0 / odds

book_proba = (
    raw_implied
    / raw_implied.sum(
        axis=1,
        keepdims=True,
    )
)


model_proba = df[
    [
        "p_home",
        "p_draw",
        "p_away",
    ]
].to_numpy(dtype=float)

model_proba = (
    model_proba
    / model_proba.sum(
        axis=1,
        keepdims=True,
    )
)


df["book_p_home"] = book_proba[:, 0]
df["book_p_draw"] = book_proba[:, 1]
df["book_p_away"] = book_proba[:, 2]


df["edge_home"] = (
    df["p_home"]
    - df["book_p_home"]
)

df["edge_draw"] = (
    df["p_draw"]
    - df["book_p_draw"]
)

df["edge_away"] = (
    df["p_away"]
    - df["book_p_away"]
)


# ============================================================
# LONG FORMAT — ONE ROW PER POSSIBLE BET
# ============================================================

bets = []


for idx, row in df.iterrows():

    actual = int(row["actual"])

    sides = [
        (
            0,
            "HOME",
            float(row["p_home"]),
            float(row["book_p_home"]),
            float(row["home_odds"]),
            float(row["edge_home"]),
        ),
        (
            1,
            "DRAW",
            float(row["p_draw"]),
            float(row["book_p_draw"]),
            float(row["draw_odds"]),
            float(row["edge_draw"]),
        ),
        (
            2,
            "AWAY",
            float(row["p_away"]),
            float(row["book_p_away"]),
            float(row["away_odds"]),
            float(row["edge_away"]),
        ),
    ]

    for side_id, side, mp, bp, price, edge in sides:

        won = (
            actual == side_id
        )

        profit = (
            price - 1.0
            if won
            else -1.0
        )

        bets.append({
            "match_index":
                idx,

            "season":
                row["season"],

            "side":
                side,

            "side_id":
                side_id,

            "actual":
                actual,

            "model_probability":
                mp,

            "book_probability":
                bp,

            "edge":
                edge,

            "odds":
                price,

            "won":
                int(won),

            "profit":
                profit,
        })


bets = pd.DataFrame(
    bets
)


# ============================================================
# BACKTEST
# ============================================================

rows = []


print("=" * 125)
print("FOOTBALL AI — VALUE BET OOS BACKTEST")
print("=" * 125)

print(
    "Матчей:",
    len(df),
)

print(
    "Потенциальных исходов:",
    len(bets),
)


for threshold in THRESHOLDS:

    selected = bets[
        bets["edge"]
        >= threshold
    ].copy()


    print()
    print("-" * 125)
    print(
        f"EDGE >= {threshold:.0%}"
    )
    print("-" * 125)


    if selected.empty:
        print("Ставок: 0")
        continue


    total_bets = len(selected)

    wins = int(
        selected["won"].sum()
    )

    stake = float(
        total_bets
    )

    profit = float(
        selected["profit"].sum()
    )

    roi = (
        profit / stake
    )

    hit_rate = (
        wins / total_bets
    )

    avg_odds = float(
        selected["odds"].mean()
    )

    avg_edge = float(
        selected["edge"].mean()
    )


    print(
        f"Bets={total_bets} | "
        f"Wins={wins} | "
        f"Hit={hit_rate:.3f} | "
        f"AvgOdds={avg_odds:.3f} | "
        f"AvgEdge={avg_edge:.3%} | "
        f"Profit={profit:+.2f} | "
        f"ROI={roi:+.2%}"
    )


    # ========================================================
    # BY SEASON
    # ========================================================

    season_rows = []

    for season, g in selected.groupby(
        "season"
    ):

        n = len(g)

        p = float(
            g["profit"].sum()
        )

        season_roi = (
            p / n
        )

        season_rows.append({
            "season":
                season,

            "bets":
                n,

            "profit":
                p,

            "roi":
                season_roi,
        })


    season_df = pd.DataFrame(
        season_rows
    )


    print()
    print(
        season_df
        .to_string(
            index=False,
            formatters={
                "profit":
                    lambda x:
                        f"{x:+.2f}",

                "roi":
                    lambda x:
                        f"{x:+.2%}",
            },
        )
    )


    positive_seasons = int(
        (
            season_df["roi"]
            > 0
        ).sum()
    )


    rows.append({
        "threshold":
            threshold,

        "bets":
            total_bets,

        "wins":
            wins,

        "hit_rate":
            hit_rate,

        "avg_odds":
            avg_odds,

        "avg_edge":
            avg_edge,

        "profit":
            profit,

        "roi":
            roi,

        "positive_seasons":
            positive_seasons,

        "season_count":
            len(season_df),
    })


# ============================================================
# BEST SIDE PER MATCH ONLY
#
# Чтобы не ставить несколько исходов одного матча.
# ============================================================

best_per_match = (
    bets
    .sort_values(
        [
            "match_index",
            "edge",
        ],
        ascending=[
            True,
            False,
        ],
    )
    .groupby(
        "match_index",
        as_index=False,
    )
    .head(1)
)


print()
print("=" * 125)
print("BEST VALUE SIDE PER MATCH")
print("=" * 125)


for threshold in THRESHOLDS:

    selected = best_per_match[
        best_per_match["edge"]
        >= threshold
    ].copy()

    if selected.empty:
        continue


    n = len(selected)

    profit = float(
        selected["profit"].sum()
    )

    roi = (
        profit / n
    )

    wins = int(
        selected["won"].sum()
    )


    season_stats = (
        selected
        .groupby("season")
        .agg(
            bets=("won", "size"),
            wins=("won", "sum"),
            profit=("profit", "sum"),
        )
        .reset_index()
    )

    season_stats["roi"] = (
        season_stats["profit"]
        / season_stats["bets"]
    )


    positive_seasons = int(
        (
            season_stats["roi"]
            > 0
        ).sum()
    )


    print(
        f"EDGE >= {threshold:.0%} | "
        f"Bets={n} | "
        f"Wins={wins} | "
        f"Profit={profit:+.2f} | "
        f"ROI={roi:+.2%} | "
        f"Positive seasons="
        f"{positive_seasons}/{len(season_stats)}"
    )


# ============================================================
# SAVE
# ============================================================

result = pd.DataFrame(
    rows
)

result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 125)
print("FINAL RANKING")
print("=" * 125)

if not result.empty:

    ranking = (
        result[
            result["bets"] >= 50
        ]
        .sort_values(
            [
                "roi",
                "positive_seasons",
            ],
            ascending=[
                False,
                False,
            ],
        )
    )

    if ranking.empty:
        ranking = result.sort_values(
            "roi",
            ascending=False,
        )

    print(
        ranking.to_string(
            index=False,
            formatters={
                "threshold":
                    lambda x:
                        f"{x:.1%}",

                "hit_rate":
                    lambda x:
                        f"{x:.3f}",

                "avg_odds":
                    lambda x:
                        f"{x:.3f}",

                "avg_edge":
                    lambda x:
                        f"{x:.3%}",

                "profit":
                    lambda x:
                        f"{x:+.2f}",

                "roi":
                    lambda x:
                        f"{x:+.2%}",
            },
        )
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
