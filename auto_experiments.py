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

RESULTS_FILE.parent.mkdir(exist_ok=True)


EXPERIMENTS = [
    {
        "name": "baseline_recheck",
        "params": {
            "n_estimators": 300,
            "max_depth": 3,
            "learning_rate": 0.02,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    },
    {
        "name": "depth_2",
        "params": {
            "n_estimators": 300,
            "max_depth": 2,
            "learning_rate": 0.02,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    },
    {
        "name": "depth_4",
        "params": {
            "n_estimators": 300,
            "max_depth": 4,
            "learning_rate": 0.02,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    },
    {
        "name": "lr_001",
        "params": {
            "n_estimators": 500,
            "max_depth": 3,
            "learning_rate": 0.01,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    },
    {
        "name": "lr_003",
        "params": {
            "n_estimators": 250,
            "max_depth": 3,
            "learning_rate": 0.03,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    },
]


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


def evaluate_experiment(df, seasons, config):
    all_true = []
    all_pred = []
    all_proba = []

    print()
    print("=" * 88)
    print("EXPERIMENT:", config["name"])
    print("=" * 88)

    for i in range(1, len(seasons)):
        test_season = seasons[i]
        train_seasons = seasons[:i]

        train = df[
            df["season"].isin(train_seasons)
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

        model = XGBClassifier(
            **config["params"],
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
        )

        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)

        row_sums = proba.sum(
            axis=1,
            keepdims=True,
        )

        if np.any(row_sums <= 0):
            raise ValueError(
                "Вероятности содержат строку с суммой <= 0."
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

    all_true = np.array(all_true)
    all_pred = np.array(all_pred)
    all_proba = np.array(all_proba)

    all_proba = (
        all_proba
        / all_proba.sum(
            axis=1,
            keepdims=True,
        )
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

    result = {
        "accuracy": float(accuracy),
        "log_loss": float(loss),
        "brier": float(brier),
        "draw_precision": float(precision[1]),
        "draw_recall": float(recall[1]),
        "draw_f1": float(f1[1]),
        "draw_predictions": draw_predictions,
    }

    print(
        f"Accuracy={result['accuracy']:.4f} | "
        f"LogLoss={result['log_loss']:.4f} | "
        f"Brier={result['brier']:.4f} | "
        f"DRAW Recall={result['draw_recall']:.4f} | "
        f"DRAW F1={result['draw_f1']:.4f} | "
        f"DRAW Pred={result['draw_predictions']}"
    )

    return result


def save_result(name, params, metrics):
    file_exists = RESULTS_FILE.exists()

    with open(
        RESULTS_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "experiment",
                "accuracy",
                "log_loss",
                "brier",
                "draw_precision",
                "draw_recall",
                "draw_f1",
                "draw_predictions",
                "bookmaker_accuracy",
                "notes",
            ])

        writer.writerow([
            datetime.now().isoformat(
                timespec="seconds"
            ),
            name,
            metrics["accuracy"],
            metrics["log_loss"],
            metrics["brier"],
            metrics["draw_precision"],
            metrics["draw_recall"],
            metrics["draw_f1"],
            metrics["draw_predictions"],
            "",
            str(params),
        ])


def print_ranking(results):
    ranked = sorted(
        results,
        key=lambda x: (
            x["metrics"]["log_loss"],
            -x["metrics"]["accuracy"],
        ),
    )

    print()
    print("=" * 88)
    print("RANKING — сначала меньший Log Loss")
    print("=" * 88)

    print(
        f"{'EXPERIMENT':<20}"
        f"{'ACC':>10}"
        f"{'LOGLOSS':>12}"
        f"{'BRIER':>10}"
        f"{'DRAW R':>10}"
        f"{'DRAW F1':>10}"
    )

    print("-" * 72)

    for item in ranked:
        m = item["metrics"]

        print(
            f"{item['name']:<20}"
            f"{m['accuracy']:>10.4f}"
            f"{m['log_loss']:>12.4f}"
            f"{m['brier']:>10.4f}"
            f"{m['draw_recall']:>10.4f}"
            f"{m['draw_f1']:>10.4f}"
        )

    print()
    print(
        "Лучший по Log Loss:",
        ranked[0]["name"],
    )


def main():
    df, seasons = load_data()

    results = []

    for config in EXPERIMENTS:
        metrics = evaluate_experiment(
            df,
            seasons,
            config,
        )

        save_result(
            config["name"],
            config["params"],
            metrics,
        )

        results.append({
            "name": config["name"],
            "metrics": metrics,
        })

    print_ranking(results)

    print()
    print("Результаты сохранены:")
    print(RESULTS_FILE)
    print()
    print("Production-файлы НЕ изменены.")


if __name__ == "__main__":
    main()
