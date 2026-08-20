from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import log_loss


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "experiments"
    / "challenger_walk_forward_predictions.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "challenger_vs_bookmaker.csv"
)


df = pd.read_csv(INPUT_FILE)

actual = df["actual"].to_numpy(dtype=int)


# ============================================================
# MODEL PROBABILITIES
# ============================================================

model_proba = df[
    ["p_home", "p_draw", "p_away"]
].to_numpy(dtype=np.float64)

model_proba = (
    model_proba
    / model_proba.sum(
        axis=1,
        keepdims=True,
    )
)


# ============================================================
# BOOKMAKER IMPLIED PROBABILITIES
#
# 1 / odds gives probabilities including bookmaker margin.
# Normalize them to remove overround.
# ============================================================

odds = df[
    ["home_odds", "draw_odds", "away_odds"]
].to_numpy(dtype=np.float64)

if np.any(odds <= 1.0):
    raise ValueError(
        "Найдены некорректные коэффициенты <= 1.0"
    )

bookmaker_raw = 1.0 / odds

bookmaker_proba = (
    bookmaker_raw
    / bookmaker_raw.sum(
        axis=1,
        keepdims=True,
    )
)


# ============================================================
# METRICS
# ============================================================

def multiclass_brier(y, proba):
    onehot = np.eye(3)[y]

    return float(
        np.mean(
            np.sum(
                (proba - onehot) ** 2,
                axis=1,
            )
        )
    )


model_ll = log_loss(
    actual,
    model_proba,
    labels=[0, 1, 2],
)

bookmaker_ll = log_loss(
    actual,
    bookmaker_proba,
    labels=[0, 1, 2],
)

model_brier = multiclass_brier(
    actual,
    model_proba,
)

bookmaker_brier = multiclass_brier(
    actual,
    bookmaker_proba,
)


model_pred = np.argmax(
    model_proba,
    axis=1,
)

bookmaker_pred = np.argmax(
    bookmaker_proba,
    axis=1,
)

model_accuracy = float(
    np.mean(model_pred == actual)
)

bookmaker_accuracy = float(
    np.mean(bookmaker_pred == actual)
)


# ============================================================
# PER-SEASON
# ============================================================

season_rows = []

for season, part in df.groupby(
    "season",
    sort=True,
):
    y = part[
        "actual"
    ].to_numpy(dtype=int)

    mp = part[
        ["p_home", "p_draw", "p_away"]
    ].to_numpy(dtype=np.float64)

    mp = (
        mp
        / mp.sum(
            axis=1,
            keepdims=True,
        )
    )

    season_odds = part[
        ["home_odds", "draw_odds", "away_odds"]
    ].to_numpy(dtype=np.float64)

    bp = 1.0 / season_odds

    bp = (
        bp
        / bp.sum(
            axis=1,
            keepdims=True,
        )
    )

    season_rows.append({
        "season": season,

        "matches":
            len(part),

        "model_accuracy":
            float(
                np.mean(
                    np.argmax(mp, axis=1)
                    == y
                )
            ),

        "bookmaker_accuracy":
            float(
                np.mean(
                    np.argmax(bp, axis=1)
                    == y
                )
            ),

        "model_logloss":
            log_loss(
                y,
                mp,
                labels=[0, 1, 2],
            ),

        "bookmaker_logloss":
            log_loss(
                y,
                bp,
                labels=[0, 1, 2],
            ),

        "model_brier":
            multiclass_brier(
                y,
                mp,
            ),

        "bookmaker_brier":
            multiclass_brier(
                y,
                bp,
            ),
    })


season_df = pd.DataFrame(
    season_rows
)

season_df[
    "logloss_edge"
] = (
    season_df["bookmaker_logloss"]
    - season_df["model_logloss"]
)

season_df[
    "brier_edge"
] = (
    season_df["bookmaker_brier"]
    - season_df["model_brier"]
)

season_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 100)
print("CHALLENGER VS BOOKMAKER — OOS PROBABILITY QUALITY")
print("=" * 100)

print()
print(
    f"{'METRIC':<20}"
    f"{'CHALLENGER':>15}"
    f"{'BOOKMAKER':>15}"
    f"{'EDGE':>15}"
)

print("-" * 65)

print(
    f"{'Accuracy':<20}"
    f"{model_accuracy:>15.6f}"
    f"{bookmaker_accuracy:>15.6f}"
    f"{model_accuracy - bookmaker_accuracy:>+15.6f}"
)

print(
    f"{'Log Loss':<20}"
    f"{model_ll:>15.6f}"
    f"{bookmaker_ll:>15.6f}"
    f"{bookmaker_ll - model_ll:>+15.6f}"
)

print(
    f"{'Brier':<20}"
    f"{model_brier:>15.6f}"
    f"{bookmaker_brier:>15.6f}"
    f"{bookmaker_brier - model_brier:>+15.6f}"
)

print()
print(
    "Для Log Loss и Brier положительный EDGE "
    "означает преимущество модели."
)

print()
print("=" * 100)
print("PER-SEASON")
print("=" * 100)

print(
    season_df.to_string(
        index=False
    )
)

print()
print(
    "Сезонов, где challenger лучше bookmaker по Log Loss:",
    int(
        (
            season_df["logloss_edge"] > 0
        ).sum()
    ),
    "/",
    len(season_df),
)

print(
    "Сезонов, где challenger лучше bookmaker по Brier:",
    int(
        (
            season_df["brier_edge"] > 0
        ).sum()
    ),
    "/",
    len(season_df),
)

print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
