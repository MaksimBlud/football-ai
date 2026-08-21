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
    / "walk_forward_draw_optimizer_results.csv"
)


df = pd.read_csv(INPUT_FILE)

seasons = sorted(df["season"].unique())


def metrics(actual, pred):
    accuracy = accuracy_score(actual, pred)

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

    pred = np.argmax(proba, axis=1)

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


all_actual = []
all_baseline_pred = []
all_optimized_pred = []

season_results = []


print()
print("=" * 110)
print("WALK-FORWARD DRAW DECISION OPTIMIZER")
print("=" * 110)


# Первый test-сезон нельзя оптимизировать:
# до него нет предыдущего walk-forward test сезона.
#
# Поэтому:
# 2020/21 = только история для подбора
# 2021/22 и далее = честная out-of-sample проверка

for i in range(1, len(seasons)):
    test_season = seasons[i]

    tuning_seasons = seasons[:i]

    tuning = df[
        df["season"].isin(tuning_seasons)
    ].copy()

    test = df[
        df["season"] == test_season
    ].copy()

    if tuning.empty or test.empty:
        continue

    best_rule = None

    for margin in margins:
        for min_draw_prob in min_draw_probs:

            tuning_actual = tuning[
                "actual"
            ].to_numpy(dtype=int)

            tuning_pred = apply_rule(
                tuning,
                margin,
                min_draw_prob,
            )

            m = metrics(
                tuning_actual,
                tuning_pred,
            )

            # Разрешаем максимум -0.5 процентного пункта
            # Accuracy относительно обычного argmax
            tuning_base = metrics(
                tuning_actual,
                tuning[
                    "argmax_pred"
                ].to_numpy(dtype=int),
            )

            if (
                m["accuracy"]
                < tuning_base["accuracy"] - 0.005
            ):
                continue

            candidate = {
                "margin": float(margin),
                "min_draw_prob": float(
                    min_draw_prob
                ),
                **m,
            }

            if best_rule is None:
                best_rule = candidate
                continue

            if (
                candidate["draw_f1"]
                > best_rule["draw_f1"]
            ):
                best_rule = candidate

            elif (
                candidate["draw_f1"]
                == best_rule["draw_f1"]
                and candidate["accuracy"]
                > best_rule["accuracy"]
            ):
                best_rule = candidate

    if best_rule is None:
        raise RuntimeError(
            f"Не найдено допустимое правило "
            f"для {test_season}"
        )

    actual = test[
        "actual"
    ].to_numpy(dtype=int)

    baseline_pred = test[
        "argmax_pred"
    ].to_numpy(dtype=int)

    optimized_pred = apply_rule(
        test,
        best_rule["margin"],
        best_rule["min_draw_prob"],
    )

    baseline_metrics = metrics(
        actual,
        baseline_pred,
    )

    optimized_metrics = metrics(
        actual,
        optimized_pred,
    )

    all_actual.extend(actual.tolist())
    all_baseline_pred.extend(
        baseline_pred.tolist()
    )
    all_optimized_pred.extend(
        optimized_pred.tolist()
    )

    season_results.append({
        "season": test_season,
        "margin": best_rule["margin"],
        "min_draw_prob": best_rule[
            "min_draw_prob"
        ],

        "baseline_accuracy":
            baseline_metrics["accuracy"],

        "optimized_accuracy":
            optimized_metrics["accuracy"],

        "accuracy_change":
            optimized_metrics["accuracy"]
            - baseline_metrics["accuracy"],

        "baseline_draw_recall":
            baseline_metrics["draw_recall"],

        "optimized_draw_recall":
            optimized_metrics["draw_recall"],

        "baseline_draw_f1":
            baseline_metrics["draw_f1"],

        "optimized_draw_f1":
            optimized_metrics["draw_f1"],

        "baseline_draw_predictions":
            baseline_metrics["draw_predictions"],

        "optimized_draw_predictions":
            optimized_metrics["draw_predictions"],
    })

    print()
    print(
        f"{test_season} | "
        f"margin={best_rule['margin']:.3f} | "
        f"min_draw={best_rule['min_draw_prob']:.2f}"
    )

    print(
        f"ARGMAX: "
        f"ACC={baseline_metrics['accuracy']:.4f} | "
        f"DRAW R={baseline_metrics['draw_recall']:.4f} | "
        f"DRAW F1={baseline_metrics['draw_f1']:.4f} | "
        f"DRAWS={baseline_metrics['draw_predictions']}"
    )

    print(
        f"OPT:    "
        f"ACC={optimized_metrics['accuracy']:.4f} | "
        f"DRAW R={optimized_metrics['draw_recall']:.4f} | "
        f"DRAW F1={optimized_metrics['draw_f1']:.4f} | "
        f"DRAWS={optimized_metrics['draw_predictions']}"
    )


all_actual = np.array(
    all_actual,
    dtype=int,
)

all_baseline_pred = np.array(
    all_baseline_pred,
    dtype=int,
)

all_optimized_pred = np.array(
    all_optimized_pred,
    dtype=int,
)


baseline_overall = metrics(
    all_actual,
    all_baseline_pred,
)

optimized_overall = metrics(
    all_actual,
    all_optimized_pred,
)


results_df = pd.DataFrame(
    season_results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 110)
print("OVERALL OUT-OF-SAMPLE RESULT")
print("=" * 110)

print(
    f"ARGMAX: "
    f"ACC={baseline_overall['accuracy']:.4f} | "
    f"DRAW P={baseline_overall['draw_precision']:.4f} | "
    f"DRAW R={baseline_overall['draw_recall']:.4f} | "
    f"DRAW F1={baseline_overall['draw_f1']:.4f} | "
    f"DRAWS={baseline_overall['draw_predictions']}"
)

print(
    f"OPT:    "
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
        - baseline_overall["accuracy"],
        4,
    ),
)

print(
    "Δ DRAW Recall:",
    round(
        optimized_overall["draw_recall"]
        - baseline_overall["draw_recall"],
        4,
    ),
)

print(
    "Δ DRAW F1:",
    round(
        optimized_overall["draw_f1"]
        - baseline_overall["draw_f1"],
        4,
    ),
)

print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
