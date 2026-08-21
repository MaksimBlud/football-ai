from pathlib import Path
from datetime import datetime
import csv

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    precision_recall_fscore_support,
)

from model_utils import FEATURES


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "features_with_elo.csv"
RESULTS_FILE = ROOT / "experiments" / "experiments.csv"


DRAW_WEIGHTS = [
    1.00,
    1.10,
    1.20,
    1.30,
    1.50,
    1.75,
    2.00,
]


BASE_PARAMS = {
    "n_estimators": 300,
    "max_depth": 3,
    "learning_rate": 0.02,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
}


def load_data():
    print("Загружаю данные...")

    df = pd.read_csv(DATA_FILE)

    df["target"] = df["result"].map({
        "H": 0,
        "D": 1,
        "A": 2,
    })

    required = FEATURES + [
        "season",
        "target",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]

    df = df.dropna(subset=required).copy()

    seasons = sorted(df["season"].unique())

    print("Матчей:", len(df))
    print("Сезоны:", seasons)

    return df, seasons


def evaluate(df, seasons, draw_weight):
    all_true = []
    all_pred = []
    all_proba = []

    print()
    print("=" * 88)
    print(f"DRAW WEIGHT: {draw_weight:.2f}")
    print("=" * 88)

    for i in range(1, len(seasons)):
        test_season = seasons[i]

        train = df[
            df["season"].isin(seasons[:i])
        ].copy()

        test = df[
            df["season"] == test_season
        ].copy()

        if train.empty or test.empty:
            continue

        X_train = train[FEATURES]
        y_train = train["target"]

        X_test = test[FEATURES]
        y_test = test["target"]

        sample_weight = np.ones(
            len(y_train),
            dtype=float,
        )

        sample_weight[
            y_train.to_numpy(dtype=int) == 1
        ] = draw_weight

        model = XGBClassifier(
            **BASE_PARAMS,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
        )

        model.fit(
            X_train,
            y_train,
            sample_weight=sample_weight,
        )

        proba = model.predict_proba(X_test)

        row_sums = proba.sum(
            axis=1,
            keepdims=True,
        )

        if np.any(row_sums <= 0):
            raise ValueError(
                "Строка вероятностей имеет сумму <= 0."
            )

        proba = proba / row_sums
        pred = np.argmax(proba, axis=1)

        all_true.extend(
            y_test.to_numpy(dtype=int).tolist()
        )
        all_pred.extend(
            pred.tolist()
        )
        all_proba.extend(
            proba.tolist()
        )

    all_true = np.asarray(all_true)
    all_pred = np.asarray(all_pred)
    all_proba = np.asarray(all_proba)

    all_proba = (
        all_proba
        / all_proba.sum(axis=1, keepdims=True)
    )

    accuracy = accuracy_score(
        all_true,
        all_pred,
    )

    loss = log_loss(
        all_true,
        all_proba,
        labels=[0, 1, 2],
    )

    onehot = np.eye(3)[all_true]

    brier = np.mean(
        np.sum(
            (all_proba - onehot) ** 2,
            axis=1,
        )
    )

    precision, recall, f1, support = (
        precision_recall_fscore_support(
            all_true,
            all_pred,
            labels=[0, 1, 2],
            zero_division=0,
        )
    )

    draw_predictions = int(
        np.sum(all_pred == 1)
    )

    metrics = {
        "accuracy": float(accuracy),
        "log_loss": float(loss),
        "brier": float(brier),
        "draw_precision": float(precision[1]),
        "draw_recall": float(recall[1]),
        "draw_f1": float(f1[1]),
        "draw_predictions": draw_predictions,
    }

    print(
        f"Accuracy={metrics['accuracy']:.4f} | "
        f"LogLoss={metrics['log_loss']:.4f} | "
        f"Brier={metrics['brier']:.4f} | "
        f"DRAW Precision={metrics['draw_precision']:.4f} | "
        f"DRAW Recall={metrics['draw_recall']:.4f} | "
        f"DRAW F1={metrics['draw_f1']:.4f} | "
        f"DRAW Pred={metrics['draw_predictions']}"
    )

    return metrics


def save_result(draw_weight, metrics):
    with open(
        RESULTS_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            datetime.now().isoformat(
                timespec="seconds"
            ),
            f"draw_weight_{draw_weight:.2f}",
            metrics["accuracy"],
            metrics["log_loss"],
            metrics["brier"],
            metrics["draw_precision"],
            metrics["draw_recall"],
            metrics["draw_f1"],
            metrics["draw_predictions"],
            "",
            f"sample_weight DRAW={draw_weight}",
        ])


def print_ranking(results):
    print()
    print("=" * 100)
    print("DRAW EXPERIMENT RANKING")
    print("=" * 100)

    print(
        f"{'WEIGHT':>8}"
        f"{'ACC':>10}"
        f"{'LOGLOSS':>12}"
        f"{'BRIER':>10}"
        f"{'DRAW P':>10}"
        f"{'DRAW R':>10}"
        f"{'DRAW F1':>10}"
        f"{'DRAWS':>8}"
    )

    print("-" * 88)

    for item in results:
        m = item["metrics"]

        print(
            f"{item['weight']:>8.2f}"
            f"{m['accuracy']:>10.4f}"
            f"{m['log_loss']:>12.4f}"
            f"{m['brier']:>10.4f}"
            f"{m['draw_precision']:>10.4f}"
            f"{m['draw_recall']:>10.4f}"
            f"{m['draw_f1']:>10.4f}"
            f"{m['draw_predictions']:>8}"
        )

    best_logloss = min(
        results,
        key=lambda x: x["metrics"]["log_loss"],
    )

    best_draw_f1 = max(
        results,
        key=lambda x: x["metrics"]["draw_f1"],
    )

    best_accuracy = max(
        results,
        key=lambda x: x["metrics"]["accuracy"],
    )

    print()
    print(
        "Лучший Log Loss:",
        f"weight={best_logloss['weight']:.2f}",
        f"({best_logloss['metrics']['log_loss']:.4f})",
    )

    print(
        "Лучший DRAW F1:",
        f"weight={best_draw_f1['weight']:.2f}",
        f"({best_draw_f1['metrics']['draw_f1']:.4f})",
    )

    print(
        "Лучшая Accuracy:",
        f"weight={best_accuracy['weight']:.2f}",
        f"({best_accuracy['metrics']['accuracy']:.4f})",
    )


def main():
    df, seasons = load_data()

    results = []

    for draw_weight in DRAW_WEIGHTS:
        metrics = evaluate(
            df,
            seasons,
            draw_weight,
        )

        save_result(
            draw_weight,
            metrics,
        )

        results.append({
            "weight": draw_weight,
            "metrics": metrics,
        })

    print_ranking(results)

    print()
    print(
        "Production-файлы НЕ изменены."
    )


if __name__ == "__main__":
    main()
