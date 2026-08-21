from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from model_utils import FEATURES


ROOT = Path(__file__).resolve().parent

DATA_FILE = ROOT / "data" / "features_with_elo.csv"
OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "walk_forward_predictions.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


BASE_PARAMS = {
    "n_estimators": 300,
    "max_depth": 3,
    "learning_rate": 0.02,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
}


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

df = df.dropna(
    subset=required
).copy()

seasons = sorted(
    df["season"].unique()
)

print("Матчей после фильтрации:", len(df))
print("Сезоны:", seasons)

rows = []


for i in range(1, len(seasons)):
    test_season = seasons[i]

    train = df[
        df["season"].isin(
            seasons[:i]
        )
    ].copy()

    test = df[
        df["season"] == test_season
    ].copy()

    if train.empty or test.empty:
        continue

    print()
    print(
        f"{test_season}: "
        f"train={len(train)} | "
        f"test={len(test)}"
    )

    X_train = train[FEATURES]
    y_train = train["target"]

    X_test = test[FEATURES]

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
    )

    proba = model.predict_proba(
        X_test
    )

    row_sums = proba.sum(
        axis=1,
        keepdims=True,
    )

    if np.any(row_sums <= 0):
        raise ValueError(
            "Обнаружена строка вероятностей "
            "с суммой <= 0."
        )

    proba = proba / row_sums

    pred = np.argmax(
        proba,
        axis=1,
    )

    test_reset = test.reset_index(
        drop=True
    )

    for j in range(len(test_reset)):
        row = test_reset.iloc[j]

        rows.append({
            "season": test_season,
            "actual": int(row["target"]),
            "actual_label": row["result"],

            "p_home": float(proba[j, 0]),
            "p_draw": float(proba[j, 1]),
            "p_away": float(proba[j, 2]),

            "argmax_pred": int(pred[j]),

            "home_odds": float(
                row["home_odds"]
            ),
            "draw_odds": float(
                row["draw_odds"]
            ),
            "away_odds": float(
                row["away_odds"]
            ),
        })


out = pd.DataFrame(rows)

out.to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print("=" * 88)
print("WALK-FORWARD MATCH-LEVEL EXPORT")
print("=" * 88)

print("Строк сохранено:", len(out))

print()
print("Распределение actual:")
print(
    out["actual_label"]
    .value_counts()
    .to_string()
)

print()
print("Распределение argmax:")
print(
    out["argmax_pred"]
    .map({
        0: "HOME",
        1: "DRAW",
        2: "AWAY",
    })
    .value_counts()
    .to_string()
)

prob_sum = (
    out[
        ["p_home", "p_draw", "p_away"]
    ]
    .sum(axis=1)
)

print()
print(
    "Минимальная сумма вероятностей:",
    prob_sum.min(),
)

print(
    "Максимальная сумма вероятностей:",
    prob_sum.max(),
)

print()
print("Сохранено:")
print(OUTPUT_FILE)
print()
print("Production-файлы НЕ изменены.")
