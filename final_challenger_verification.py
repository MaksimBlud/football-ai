from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    confusion_matrix,
    classification_report,
)

from model_utils import FEATURES


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "features_with_elo.csv"


MODELS = {
    "baseline": {
        "n_estimators": 300,
        "max_depth": 3,
        "learning_rate": 0.02,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },

    "challenger": {
        "n_estimators": 300,
        "max_depth": 2,
        "learning_rate": 0.01,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },
}


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

df = df.dropna(
    subset=required
).copy()

seasons = sorted(
    df["season"].unique()
)


def train_predict(train, test, params):
    model = XGBClassifier(
        **params,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    model.fit(
        train[FEATURES],
        train["target"],
    )

    proba = model.predict_proba(
        test[FEATURES]
    )

    proba = proba.astype(
        np.float64
    )

    proba = (
        proba
        / proba.sum(
            axis=1,
            keepdims=True,
        )
    )

    pred = np.argmax(
        proba,
        axis=1,
    )

    return pred, proba


results = {}


for model_name, params in MODELS.items():

    all_true = []
    all_pred = []
    all_proba = []

    print()
    print("=" * 100)
    print(model_name.upper())
    print("=" * 100)

    # Те же outer seasons, что и nested test:
    # 2021/22 -> 2025/26
    for i in range(2, len(seasons)):

        test_season = seasons[i]

        train = df[
            df["season"].isin(
                seasons[:i]
            )
        ].copy()

        test = df[
            df["season"]
            == test_season
        ].copy()

        pred, proba = train_predict(
            train,
            test,
            params,
        )

        y = test[
            "target"
        ].to_numpy(dtype=int)

        all_true.extend(
            y.tolist()
        )

        all_pred.extend(
            pred.tolist()
        )

        all_proba.extend(
            proba.tolist()
        )

    all_true = np.asarray(
        all_true,
        dtype=int,
    )

    all_pred = np.asarray(
        all_pred,
        dtype=int,
    )

    all_proba = np.asarray(
        all_proba,
        dtype=np.float64,
    )

    accuracy = accuracy_score(
        all_true,
        all_pred,
    )

    ll = log_loss(
        all_true,
        all_proba,
        labels=[0, 1, 2],
    )

    onehot = np.eye(3)[
        all_true
    ]

    brier = np.mean(
        np.sum(
            (all_proba - onehot) ** 2,
            axis=1,
        )
    )

    cm = confusion_matrix(
        all_true,
        all_pred,
        labels=[0, 1, 2],
    )

    report = classification_report(
        all_true,
        all_pred,
        labels=[0, 1, 2],
        target_names=[
            "HOME",
            "DRAW",
            "AWAY",
        ],
        zero_division=0,
    )

    counts = pd.Series(
        all_pred
    ).map({
        0: "HOME",
        1: "DRAW",
        2: "AWAY",
    }).value_counts()

    results[model_name] = {
        "accuracy": accuracy,
        "log_loss": ll,
        "brier": brier,
    }

    print(
        f"Accuracy: {accuracy:.6f}"
    )

    print(
        f"Log Loss: {ll:.6f}"
    )

    print(
        f"Brier: {brier:.6f}"
    )

    print()
    print("Confusion matrix:")
    print(cm)

    print()
    print("Classification report:")
    print(report)

    print("Predictions:")
    print(counts.to_string())


print()
print("=" * 100)
print("FINAL BASELINE VS CHALLENGER")
print("=" * 100)

baseline = results["baseline"]
challenger = results["challenger"]

print(
    f"{'METRIC':<20}"
    f"{'BASELINE':>15}"
    f"{'CHALLENGER':>15}"
    f"{'CHANGE':>15}"
)

print("-" * 65)

print(
    f"{'Accuracy':<20}"
    f"{baseline['accuracy']:>15.6f}"
    f"{challenger['accuracy']:>15.6f}"
    f"{challenger['accuracy'] - baseline['accuracy']:>+15.6f}"
)

print(
    f"{'Log Loss':<20}"
    f"{baseline['log_loss']:>15.6f}"
    f"{challenger['log_loss']:>15.6f}"
    f"{challenger['log_loss'] - baseline['log_loss']:>+15.6f}"
)

print(
    f"{'Brier':<20}"
    f"{baseline['brier']:>15.6f}"
    f"{challenger['brier']:>15.6f}"
    f"{challenger['brier'] - baseline['brier']:>+15.6f}"
)

print()
print("Production-файлы НЕ изменены.")
