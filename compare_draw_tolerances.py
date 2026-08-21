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
    / "draw_tolerance_comparison.csv"
)


df = pd.read_csv(INPUT_FILE)
seasons = sorted(df["season"].unique())


TOLERANCES = [
    0.0000,
    0.0025,
    0.0050,
    0.0075,
    0.0100,
]


MARGINS = np.round(
    np.arange(
        0.00,
        0.151,
        0.005,
    ),
    3,
)

MIN_DRAW_PROBS = np.round(
    np.arange(
        0.20,
        0.401,
        0.01,
    ),
    2,
)


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
        "draw_precision": float(
            precision[1]
        ),
        "draw_recall": float(
            recall[1]
        ),
        "draw_f1": float(
            f1[1]
        ),
        "draw_predictions": int(
            np.sum(pred == 1)
        ),
    }


def apply_rule(
    frame,
    margin,
    min_draw_prob,
):
    p_home = frame[
        "p_home"
    ].to_numpy(dtype=float)

    p_draw = frame[
        "p_draw"
    ].to_numpy(dtype=float)

    p_away = frame[
        "p_away"
    ].to_numpy(dtype=float)

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


def evaluate_tolerance(tolerance):
    all_actual = []
    all_baseline = []
    all_optimized = []

    selected_rules = []

    for i in range(1, len(seasons)):
        test_season = seasons[i]

        tuning = df[
            df["season"].isin(
                seasons[:i]
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

        tuning_baseline_pred = tuning[
            "argmax_pred"
        ].to_numpy(dtype=int)

        tuning_baseline = metrics(
            tuning_actual,
            tuning_baseline_pred,
        )

        best = None

        for margin in MARGINS:
            for min_draw_prob in MIN_DRAW_PROBS:

                tuning_pred = apply_rule(
                    tuning,
                    margin,
                    min_draw_prob,
                )

                m = metrics(
                    tuning_actual,
                    tuning_pred,
                )

                if (
                    m["accuracy"]
                    <
                    tuning_baseline["accuracy"]
                    - tolerance
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
                f"Нет допустимого правила "
                f"для tolerance={tolerance}"
            )

        actual = test[
            "actual"
        ].to_numpy(dtype=int)

        baseline_pred = test[
            "argmax_pred"
        ].to_numpy(dtype=int)

        optimized_pred = apply_rule(
            test,
            best["margin"],
            best["min_draw_prob"],
        )

        all_actual.extend(
            actual.tolist()
        )

        all_baseline.extend(
            baseline_pred.tolist()
        )

        all_optimized.extend(
            optimized_pred.tolist()
        )

        selected_rules.append(
            (
                test_season,
                best["margin"],
                best["min_draw_prob"],
            )
        )

    all_actual = np.array(
        all_actual,
        dtype=int,
    )

    all_baseline = np.array(
        all_baseline,
        dtype=int,
    )

    all_optimized = np.array(
        all_optimized,
        dtype=int,
    )

    base = metrics(
        all_actual,
        all_baseline,
    )

    opt = metrics(
        all_actual,
        all_optimized,
    )

    return {
        "tolerance": tolerance,

        "baseline_accuracy":
            base["accuracy"],

        "optimized_accuracy":
            opt["accuracy"],

        "accuracy_change":
            opt["accuracy"]
            - base["accuracy"],

        "baseline_draw_precision":
            base["draw_precision"],

        "optimized_draw_precision":
            opt["draw_precision"],

        "baseline_draw_recall":
            base["draw_recall"],

        "optimized_draw_recall":
            opt["draw_recall"],

        "draw_recall_change":
            opt["draw_recall"]
            - base["draw_recall"],

        "baseline_draw_f1":
            base["draw_f1"],

        "optimized_draw_f1":
            opt["draw_f1"],

        "draw_f1_change":
            opt["draw_f1"]
            - base["draw_f1"],

        "optimized_draw_predictions":
            opt["draw_predictions"],

        "rules": str(
            selected_rules
        ),
    }


results = []

print()
print("=" * 110)
print("DRAW TOLERANCE WALK-FORWARD COMPARISON")
print("=" * 110)


for tolerance in TOLERANCES:
    print()
    print(
        f"Проверяю tolerance="
        f"{tolerance:.4f} ..."
    )

    result = evaluate_tolerance(
        tolerance
    )

    results.append(result)


results_df = pd.DataFrame(
    results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 110)
print("FINAL COMPARISON")
print("=" * 110)

print(
    f"{'TOL':>8}"
    f"{'ACC':>10}"
    f"{'ΔACC':>10}"
    f"{'DRAW P':>10}"
    f"{'DRAW R':>10}"
    f"{'Δ R':>10}"
    f"{'DRAW F1':>10}"
    f"{'Δ F1':>10}"
    f"{'DRAWS':>8}"
)

print("-" * 96)

for row in results:
    print(
        f"{row['tolerance']:>8.4f}"
        f"{row['optimized_accuracy']:>10.4f}"
        f"{row['accuracy_change']:>+10.4f}"
        f"{row['optimized_draw_precision']:>10.4f}"
        f"{row['optimized_draw_recall']:>10.4f}"
        f"{row['draw_recall_change']:>+10.4f}"
        f"{row['optimized_draw_f1']:>10.4f}"
        f"{row['draw_f1_change']:>+10.4f}"
        f"{row['optimized_draw_predictions']:>8}"
    )


# ---------------------------------------------------------
# Выбираем консервативного кандидата:
# максимальный DRAW F1 среди тех, где OOS Accuracy
# упала не более чем на 0.5 процентного пункта.
# ---------------------------------------------------------

safe = results_df[
    results_df["accuracy_change"]
    >= -0.005
].copy()

if not safe.empty:
    best_safe = (
        safe
        .sort_values(
            [
                "optimized_draw_f1",
                "optimized_accuracy",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .iloc[0]
    )

    print()
    print("=" * 110)
    print("BEST SAFE OUT-OF-SAMPLE CANDIDATE")
    print("=" * 110)

    print(
        f"Tolerance: "
        f"{best_safe['tolerance']:.4f}"
    )

    print(
        f"Accuracy: "
        f"{best_safe['optimized_accuracy']:.4f} "
        f"({best_safe['accuracy_change']:+.4f})"
    )

    print(
        f"DRAW Recall: "
        f"{best_safe['optimized_draw_recall']:.4f} "
        f"({best_safe['draw_recall_change']:+.4f})"
    )

    print(
        f"DRAW F1: "
        f"{best_safe['optimized_draw_f1']:.4f} "
        f"({best_safe['draw_f1_change']:+.4f})"
    )

    print(
        f"DRAW Predictions: "
        f"{int(best_safe['optimized_draw_predictions'])}"
    )

else:
    print()
    print(
        "⚠️ Нет варианта с OOS "
        "Accuracy loss <= 0.005."
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
