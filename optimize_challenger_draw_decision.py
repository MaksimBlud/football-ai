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
    / "challenger_walk_forward_predictions.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "challenger_draw_threshold_results.csv"
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


def metrics(pred):
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


baseline = metrics(
    base_pred
)


print()
print("=" * 100)
print("CHALLENGER ARGMAX BASELINE")
print("=" * 100)

print(
    f"Accuracy={baseline['accuracy']:.4f} | "
    f"DRAW P={baseline['draw_precision']:.4f} | "
    f"DRAW R={baseline['draw_recall']:.4f} | "
    f"DRAW F1={baseline['draw_f1']:.4f} | "
    f"DRAW Pred={baseline['draw_predictions']}"
)


margins = np.round(
    np.arange(
        0.00,
        0.201,
        0.005,
    ),
    3,
)

min_draw_probs = np.round(
    np.arange(
        0.18,
        0.361,
        0.01,
    ),
    2,
)


results = []


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

        m = metrics(
            pred
        )

        results.append({
            "margin": float(margin),
            "min_draw_prob": float(
                min_draw_prob
            ),
            **m,

            "accuracy_change":
                m["accuracy"]
                - baseline["accuracy"],

            "draw_recall_change":
                m["draw_recall"]
                - baseline["draw_recall"],

            "draw_f1_change":
                m["draw_f1"]
                - baseline["draw_f1"],
        })


results_df = pd.DataFrame(
    results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ----------------------------------------------------------
# Лучший Accuracy
# ----------------------------------------------------------

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


# ----------------------------------------------------------
# Лучший DRAW F1
# ----------------------------------------------------------

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


# ----------------------------------------------------------
# SAFE:
# не допускаем падение Accuracy более 0.5 п.п.
# ----------------------------------------------------------

safe = results_df[
    results_df["accuracy_change"]
    >= -0.005
].copy()


if not safe.empty:
    best_safe = (
        safe
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
    best_safe = None


print()
print("=" * 100)
print("BEST ACCURACY")
print("=" * 100)

print(
    f"margin={best_accuracy['margin']:.3f} | "
    f"min_draw={best_accuracy['min_draw_prob']:.2f} | "
    f"ACC={best_accuracy['accuracy']:.4f} | "
    f"ΔACC={best_accuracy['accuracy_change']:+.4f} | "
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
    f"ΔACC={best_draw_f1['accuracy_change']:+.4f} | "
    f"DRAW P={best_draw_f1['draw_precision']:.4f} | "
    f"DRAW R={best_draw_f1['draw_recall']:.4f} | "
    f"DRAW F1={best_draw_f1['draw_f1']:.4f} | "
    f"DRAW Pred={int(best_draw_f1['draw_predictions'])}"
)


if best_safe is not None:
    print()
    print("=" * 100)
    print("BEST SAFE")
    print("Accuracy loss <= 0.005")
    print("=" * 100)

    print(
        f"margin={best_safe['margin']:.3f} | "
        f"min_draw={best_safe['min_draw_prob']:.2f} | "
        f"ACC={best_safe['accuracy']:.4f} | "
        f"ΔACC={best_safe['accuracy_change']:+.4f} | "
        f"DRAW P={best_safe['draw_precision']:.4f} | "
        f"DRAW R={best_safe['draw_recall']:.4f} | "
        f"DRAW F1={best_safe['draw_f1']:.4f} | "
        f"ΔF1={best_safe['draw_f1_change']:+.4f} | "
        f"DRAW Pred={int(best_safe['draw_predictions'])}"
    )


print()
print("=" * 100)
print("TOP 15 SAFE")
print("=" * 100)

print(
    safe[
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
    .to_string(
        index=False
    )
)


print()
print(
    "Проверено правил:",
    len(results_df),
)

print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Модель НЕ переобучалась.")
print("Production-файлы НЕ изменены.")
