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
    / "challenger_draw_walk_forward_results.csv"
)


df = pd.read_csv(INPUT_FILE)
seasons = sorted(df["season"].unique())


MARGINS = np.round(
    np.arange(
        0.00,
        0.201,
        0.005,
    ),
    3,
)

MIN_DRAW_PROBS = np.round(
    np.arange(
        0.18,
        0.361,
        0.01,
    ),
    2,
)

TOLERANCE = 0.005


def metrics(actual, pred):
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


def apply_rule(frame, margin, min_draw_prob):
    p_home = frame["p_home"].to_numpy(dtype=float)
    p_draw = frame["p_draw"].to_numpy(dtype=float)
    p_away = frame["p_away"].to_numpy(dtype=float)

    proba = np.column_stack([
        p_home,
        p_draw,
        p_away,
    ])

    pred = np.argmax(
        proba,
        axis=1,
    )

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

    pred[switch_to_draw] = 1

    return pred


rows = []

all_actual = []
all_argmax = []
all_optimized = []


print()
print("=" * 110)
print("CHALLENGER + DRAW LAYER — OUT-OF-SAMPLE WALK-FORWARD")
print("=" * 110)


# Первый challenger test-сезон = 2021/22.
# Для подбора правила нужен хотя бы один прошлый
# challenger test-сезон, поэтому честная проверка
# начинается с 2022/23.

for i in range(1, len(seasons)):

    test_season = seasons[i]

    tuning_seasons = seasons[:i]

    tuning = df[
        df["season"].isin(
            tuning_seasons
        )
    ].copy()

    test = df[
        df["season"] == test_season
    ].copy()

    if tuning.empty or test.empty:
        continue

    tuning_actual = tuning[
        "actual"
    ].to_numpy(dtype=int)

    tuning_argmax = tuning[
        "argmax_pred"
    ].to_numpy(dtype=int)

    tuning_base_metrics = metrics(
        tuning_actual,
        tuning_argmax,
    )

    best = None

    for margin in MARGINS:
        for min_draw_prob in MIN_DRAW_PROBS:

            pred = apply_rule(
                tuning,
                margin,
                min_draw_prob,
            )

            m = metrics(
                tuning_actual,
                pred,
            )

            # Не разрешаем потерять больше 0.5 п.п.
            # Accuracy на прошлых данных.
            if (
                m["accuracy"]
                <
                tuning_base_metrics["accuracy"]
                - TOLERANCE
            ):
                continue

            candidate = {
                "margin": float(margin),
                "min_draw_prob": float(
                    min_draw_prob
                ),
                **m,
            }

            if best is None:
                best = candidate
                continue

            if (
                candidate["draw_f1"]
                > best["draw_f1"]
            ):
                best = candidate

            elif (
                candidate["draw_f1"]
                == best["draw_f1"]
                and
                candidate["accuracy"]
                > best["accuracy"]
            ):
                best = candidate

    if best is None:
        raise RuntimeError(
            f"Не найдено допустимое правило "
            f"для {test_season}"
        )

    actual = test[
        "actual"
    ].to_numpy(dtype=int)

    argmax_pred = test[
        "argmax_pred"
    ].to_numpy(dtype=int)

    optimized_pred = apply_rule(
        test,
        best["margin"],
        best["min_draw_prob"],
    )

    argmax_metrics = metrics(
        actual,
        argmax_pred,
    )

    optimized_metrics = metrics(
        actual,
        optimized_pred,
    )

    all_actual.extend(
        actual.tolist()
    )

    all_argmax.extend(
        argmax_pred.tolist()
    )

    all_optimized.extend(
        optimized_pred.tolist()
    )

    rows.append({
        "season": test_season,

        "margin":
            best["margin"],

        "min_draw_prob":
            best["min_draw_prob"],

        "argmax_accuracy":
            argmax_metrics["accuracy"],

        "optimized_accuracy":
            optimized_metrics["accuracy"],

        "accuracy_change":
            optimized_metrics["accuracy"]
            - argmax_metrics["accuracy"],

        "argmax_draw_recall":
            argmax_metrics["draw_recall"],

        "optimized_draw_recall":
            optimized_metrics["draw_recall"],

        "argmax_draw_f1":
            argmax_metrics["draw_f1"],

        "optimized_draw_f1":
            optimized_metrics["draw_f1"],

        "argmax_draw_predictions":
            argmax_metrics["draw_predictions"],

        "optimized_draw_predictions":
            optimized_metrics["draw_predictions"],
    })

    print()
    print(
        f"{test_season} | "
        f"margin={best['margin']:.3f} | "
        f"min_draw={best['min_draw_prob']:.2f}"
    )

    print(
        f"ARGMAX: "
        f"ACC={argmax_metrics['accuracy']:.4f} | "
        f"DRAW R={argmax_metrics['draw_recall']:.4f} | "
        f"DRAW F1={argmax_metrics['draw_f1']:.4f} | "
        f"DRAWS={argmax_metrics['draw_predictions']}"
    )

    print(
        f"LAYER:  "
        f"ACC={optimized_metrics['accuracy']:.4f} | "
        f"DRAW R={optimized_metrics['draw_recall']:.4f} | "
        f"DRAW F1={optimized_metrics['draw_f1']:.4f} | "
        f"DRAWS={optimized_metrics['draw_predictions']}"
    )


all_actual = np.asarray(
    all_actual,
    dtype=int,
)

all_argmax = np.asarray(
    all_argmax,
    dtype=int,
)

all_optimized = np.asarray(
    all_optimized,
    dtype=int,
)


argmax_overall = metrics(
    all_actual,
    all_argmax,
)

optimized_overall = metrics(
    all_actual,
    all_optimized,
)


results = pd.DataFrame(
    rows
)

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 110)
print("FINAL OUT-OF-SAMPLE RESULT")
print("=" * 110)

print(
    f"ARGMAX: "
    f"ACC={argmax_overall['accuracy']:.4f} | "
    f"DRAW P={argmax_overall['draw_precision']:.4f} | "
    f"DRAW R={argmax_overall['draw_recall']:.4f} | "
    f"DRAW F1={argmax_overall['draw_f1']:.4f} | "
    f"DRAWS={argmax_overall['draw_predictions']}"
)

print(
    f"LAYER:  "
    f"ACC={optimized_overall['accuracy']:.4f} | "
    f"DRAW P={optimized_overall['draw_precision']:.4f} | "
    f"DRAW R={optimized_overall['draw_recall']:.4f} | "
    f"DRAW F1={optimized_overall['draw_f1']:.4f} | "
    f"DRAWS={optimized_overall['draw_predictions']}"
)

print()
print(
    "Δ Accuracy:",
    round(
        optimized_overall["accuracy"]
        - argmax_overall["accuracy"],
        4,
    ),
)

print(
    "Δ DRAW Recall:",
    round(
        optimized_overall["draw_recall"]
        - argmax_overall["draw_recall"],
        4,
    ),
)

print(
    "Δ DRAW F1:",
    round(
        optimized_overall["draw_f1"]
        - argmax_overall["draw_f1"],
        4,
    ),
)

print()
print("=" * 110)
print("PER-SEASON RESULTS")
print("=" * 110)

print(
    results.to_string(
        index=False
    )
)

print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Модель НЕ переобучалась.")
print("Production-файлы НЕ изменены.")
