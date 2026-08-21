from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "experiments"
    / "walk_forward_predictions.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "draw_threshold_results.csv"
)


df = pd.read_csv(INPUT_FILE)

actual = df["actual"].to_numpy(dtype=int)

p_home = df["p_home"].to_numpy(dtype=float)
p_draw = df["p_draw"].to_numpy(dtype=float)
p_away = df["p_away"].to_numpy(dtype=float)

proba = np.column_stack([
    p_home,
    p_draw,
    p_away,
])

base_pred = np.argmax(
    proba,
    axis=1,
)


def calculate_metrics(pred):
    accuracy = accuracy_score(
        actual,
        pred,
    )

    precision, recall, f1, support = (
        precision_recall_fscore_support(
            actual,
            pred,
            labels=[0, 1, 2],
            zero_division=0,
        )
    )

    return {
        "accuracy": float(accuracy),
        "draw_precision": float(precision[1]),
        "draw_recall": float(recall[1]),
        "draw_f1": float(f1[1]),
        "draw_predictions": int(
            np.sum(pred == 1)
        ),
    }


baseline = calculate_metrics(
    base_pred
)

print()
print("=" * 100)
print("BASELINE ARGMAX")
print("=" * 100)

print(
    f"Accuracy={baseline['accuracy']:.4f} | "
    f"DRAW Precision={baseline['draw_precision']:.4f} | "
    f"DRAW Recall={baseline['draw_recall']:.4f} | "
    f"DRAW F1={baseline['draw_f1']:.4f} | "
    f"DRAW Pred={baseline['draw_predictions']}"
)


results = []


# ------------------------------------------------------------
# RULE:
#
# Если DRAW не победитель argmax, разрешаем переключение
# на DRAW, когда:
#
# p_draw >= max(p_home, p_away) - margin
#
# Дополнительно требуем минимальный абсолютный p_draw.
# ------------------------------------------------------------

margins = np.round(
    np.arange(
        0.00,
        0.151,
        0.005,
    ),
    3,
)

min_draw_probs = np.round(
    np.arange(
        0.20,
        0.401,
        0.01,
    ),
    2,
)


for margin in margins:
    for min_draw_prob in min_draw_probs:

        pred = base_pred.copy()

        strongest_non_draw = np.maximum(
            p_home,
            p_away,
        )

        switch_to_draw = (
            (p_draw >= min_draw_prob)
            &
            (
                p_draw
                >= strongest_non_draw - margin
            )
        )

        pred[
            switch_to_draw
        ] = 1

        metrics = calculate_metrics(
            pred
        )

        results.append({
            "margin": float(margin),
            "min_draw_prob": float(
                min_draw_prob
            ),
            **metrics,
            "accuracy_change": (
                metrics["accuracy"]
                - baseline["accuracy"]
            ),
            "draw_f1_change": (
                metrics["draw_f1"]
                - baseline["draw_f1"]
            ),
            "draw_recall_change": (
                metrics["draw_recall"]
                - baseline["draw_recall"]
            ),
        })


results_df = pd.DataFrame(
    results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ------------------------------------------------------------
# Лучший DRAW F1 без сильного падения Accuracy
# ------------------------------------------------------------

acceptable = results_df[
    results_df["accuracy"]
    >= baseline["accuracy"] - 0.01
].copy()

if not acceptable.empty:
    best_balanced = (
        acceptable
        .sort_values(
            [
                "draw_f1",
                "accuracy",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .iloc[0]
    )
else:
    best_balanced = None


best_accuracy = (
    results_df
    .sort_values(
        [
            "accuracy",
            "draw_f1",
        ],
        ascending=[
            False,
            False,
        ],
    )
    .iloc[0]
)


best_draw_f1 = (
    results_df
    .sort_values(
        [
            "draw_f1",
            "accuracy",
        ],
        ascending=[
            False,
            False,
        ],
    )
    .iloc[0]
)


print()
print("=" * 100)
print("BEST ACCURACY")
print("=" * 100)

print(
    f"margin={best_accuracy['margin']:.3f} | "
    f"min_draw={best_accuracy['min_draw_prob']:.2f} | "
    f"ACC={best_accuracy['accuracy']:.4f} | "
    f"DRAW P={best_accuracy['draw_precision']:.4f} | "
    f"DRAW R={best_accuracy['draw_recall']:.4f} | "
    f"DRAW F1={best_accuracy['draw_f1']:.4f} | "
    f"DRAW Pred={int(best_accuracy['draw_predictions'])}"
)


print()
print("=" * 100)
print("BEST DRAW F1")
print("=" * 100)

print(
    f"margin={best_draw_f1['margin']:.3f} | "
    f"min_draw={best_draw_f1['min_draw_prob']:.2f} | "
    f"ACC={best_draw_f1['accuracy']:.4f} | "
    f"DRAW P={best_draw_f1['draw_precision']:.4f} | "
    f"DRAW R={best_draw_f1['draw_recall']:.4f} | "
    f"DRAW F1={best_draw_f1['draw_f1']:.4f} | "
    f"DRAW Pred={int(best_draw_f1['draw_predictions'])}"
)


if best_balanced is not None:
    print()
    print("=" * 100)
    print("BEST BALANCED")
    print("Accuracy loss <= 0.0100")
    print("=" * 100)

    print(
        f"margin={best_balanced['margin']:.3f} | "
        f"min_draw={best_balanced['min_draw_prob']:.2f} | "
        f"ACC={best_balanced['accuracy']:.4f} | "
        f"ΔACC={best_balanced['accuracy_change']:+.4f} | "
        f"DRAW P={best_balanced['draw_precision']:.4f} | "
        f"DRAW R={best_balanced['draw_recall']:.4f} | "
        f"DRAW F1={best_balanced['draw_f1']:.4f} | "
        f"ΔF1={best_balanced['draw_f1_change']:+.4f} | "
        f"DRAW Pred={int(best_balanced['draw_predictions'])}"
    )


print()
print("=" * 100)
print("TOP 15 BALANCED RULES")
print("=" * 100)

top = (
    acceptable
    .sort_values(
        [
            "draw_f1",
            "accuracy",
        ],
        ascending=[
            False,
            False,
        ],
    )
    .head(15)
)

print(
    top[
        [
            "margin",
            "min_draw_prob",
            "accuracy",
            "accuracy_change",
            "draw_precision",
            "draw_recall",
            "draw_f1",
            "draw_f1_change",
            "draw_predictions",
        ]
    ]
    .to_string(
        index=False
    )
)


print()
print("Проверено правил:", len(results_df))
print("Сохранено:")
print(OUTPUT_FILE)
print()
print("Модель НЕ переобучалась.")
print("Production-файлы НЕ изменены.")
