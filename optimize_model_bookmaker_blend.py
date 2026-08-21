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
    / "model_bookmaker_blend_results.csv"
)


df = pd.read_csv(INPUT_FILE)

actual = df[
    "actual"
].to_numpy(dtype=int)


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
# BOOKMAKER PROBABILITIES
# ============================================================

odds = df[
    ["home_odds", "draw_odds", "away_odds"]
].to_numpy(dtype=np.float64)

bookmaker_proba = 1.0 / odds

bookmaker_proba = (
    bookmaker_proba
    / bookmaker_proba.sum(
        axis=1,
        keepdims=True,
    )
)


def brier_score(y, proba):
    onehot = np.eye(3)[y]

    return float(
        np.mean(
            np.sum(
                (proba - onehot) ** 2,
                axis=1,
            )
        )
    )


def evaluate(proba):
    pred = np.argmax(
        proba,
        axis=1,
    )

    return {
        "accuracy": float(
            np.mean(pred == actual)
        ),
        "log_loss": float(
            log_loss(
                actual,
                proba,
                labels=[0, 1, 2],
            )
        ),
        "brier": brier_score(
            actual,
            proba,
        ),
    }


model_metrics = evaluate(
    model_proba
)

bookmaker_metrics = evaluate(
    bookmaker_proba
)


# ============================================================
# BLEND SEARCH
#
# alpha = вес модели
# 0.00 = чистый букмекер
# 1.00 = чистая модель
# ============================================================

alphas = np.round(
    np.arange(
        0.00,
        1.001,
        0.01,
    ),
    2,
)

rows = []


for alpha in alphas:

    blended = (
        alpha * model_proba
        +
        (1.0 - alpha) * bookmaker_proba
    )

    blended = (
        blended
        / blended.sum(
            axis=1,
            keepdims=True,
        )
    )

    m = evaluate(
        blended
    )

    rows.append({
        "alpha_model": float(alpha),
        "alpha_bookmaker": float(
            1.0 - alpha
        ),

        "accuracy":
            m["accuracy"],

        "log_loss":
            m["log_loss"],

        "brier":
            m["brier"],

        "logloss_vs_bookmaker":
            bookmaker_metrics["log_loss"]
            - m["log_loss"],

        "brier_vs_bookmaker":
            bookmaker_metrics["brier"]
            - m["brier"],
    })


results = pd.DataFrame(
    rows
)

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


best_logloss = (
    results
    .sort_values(
        [
            "log_loss",
            "brier",
        ]
    )
    .iloc[0]
)

best_brier = (
    results
    .sort_values(
        [
            "brier",
            "log_loss",
        ]
    )
    .iloc[0]
)

best_accuracy = (
    results
    .sort_values(
        [
            "accuracy",
            "log_loss",
        ],
        ascending=[
            False,
            True,
        ],
    )
    .iloc[0]
)


print()
print("=" * 100)
print("BASE MODELS")
print("=" * 100)

print(
    f"MODEL       | "
    f"ACC={model_metrics['accuracy']:.4f} | "
    f"LL={model_metrics['log_loss']:.6f} | "
    f"BRIER={model_metrics['brier']:.6f}"
)

print(
    f"BOOKMAKER   | "
    f"ACC={bookmaker_metrics['accuracy']:.4f} | "
    f"LL={bookmaker_metrics['log_loss']:.6f} | "
    f"BRIER={bookmaker_metrics['brier']:.6f}"
)


print()
print("=" * 100)
print("BEST LOG LOSS BLEND")
print("=" * 100)

print(
    f"Model weight:      "
    f"{best_logloss['alpha_model']:.2f}"
)

print(
    f"Bookmaker weight:  "
    f"{best_logloss['alpha_bookmaker']:.2f}"
)

print(
    f"Accuracy:          "
    f"{best_logloss['accuracy']:.4f}"
)

print(
    f"Log Loss:          "
    f"{best_logloss['log_loss']:.6f}"
)

print(
    f"vs bookmaker:      "
    f"{best_logloss['logloss_vs_bookmaker']:+.6f}"
)

print(
    f"Brier:             "
    f"{best_logloss['brier']:.6f}"
)

print(
    f"Brier edge:        "
    f"{best_logloss['brier_vs_bookmaker']:+.6f}"
)


print()
print("=" * 100)
print("BEST BRIER BLEND")
print("=" * 100)

print(
    f"Model weight:      "
    f"{best_brier['alpha_model']:.2f}"
)

print(
    f"Bookmaker weight:  "
    f"{best_brier['alpha_bookmaker']:.2f}"
)

print(
    f"Accuracy:          "
    f"{best_brier['accuracy']:.4f}"
)

print(
    f"Log Loss:          "
    f"{best_brier['log_loss']:.6f}"
)

print(
    f"Brier:             "
    f"{best_brier['brier']:.6f}"
)

print(
    f"vs bookmaker:      "
    f"{best_brier['brier_vs_bookmaker']:+.6f}"
)


print()
print("=" * 100)
print("BEST ACCURACY BLEND")
print("=" * 100)

print(
    f"Model weight:      "
    f"{best_accuracy['alpha_model']:.2f}"
)

print(
    f"Bookmaker weight:  "
    f"{best_accuracy['alpha_bookmaker']:.2f}"
)

print(
    f"Accuracy:          "
    f"{best_accuracy['accuracy']:.4f}"
)

print(
    f"Log Loss:          "
    f"{best_accuracy['log_loss']:.6f}"
)

print(
    f"Brier:             "
    f"{best_accuracy['brier']:.6f}"
)


print()
print("=" * 100)
print("TOP 15 BY LOG LOSS")
print("=" * 100)

print(
    results
    .sort_values("log_loss")
    .head(15)
    .to_string(
        index=False
    )
)

print()
print(
    "Если лучший alpha_model > 0 "
    "и Log Loss ниже чистого bookmaker, "
    "значит модель добавляет полезный сигнал."
)

print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
