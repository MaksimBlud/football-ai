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
    / "challenger_walk_forward_predictions.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


PARAMS = {
    "n_estimators": 300,
    "max_depth": 2,
    "learning_rate": 0.01,
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

print("Матчей:", len(df))
print("Сезоны:", seasons)

rows = []


# Те же 5 outer test сезонов,
# что в nested verification.
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

    print()
    print(
        f"{test_season}: "
        f"train={len(train)} | "
        f"test={len(test)}"
    )

    model = XGBClassifier(
        **PARAMS,
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

    test = test.reset_index(
        drop=True
    )

    for j in range(len(test)):

        row = test.iloc[j]

        rows.append({
            "season": test_season,

            "actual":
                int(row["target"]),

            "actual_label":
                row["result"],

            "p_home":
                float(proba[j, 0]),

            "p_draw":
                float(proba[j, 1]),

            "p_away":
                float(proba[j, 2]),

            "argmax_pred":
                int(pred[j]),

            "home_odds":
                float(row["home_odds"]),

            "draw_odds":
                float(row["draw_odds"]),

            "away_odds":
                float(row["away_odds"]),
        })


out = pd.DataFrame(rows)

out.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 90)
print("CHALLENGER MATCH-LEVEL EXPORT")
print("=" * 90)

print("Строк:", len(out))

print()
print("Actual:")
print(
    out["actual_label"]
    .value_counts()
    .to_string()
)

print()
print("Argmax:")
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

print()
print(
    "Средняя P(DRAW):",
    round(
        out["p_draw"].mean(),
        4,
    ),
)

print(
    "Максимальная P(DRAW):",
    round(
        out["p_draw"].max(),
        4,
    ),
)

print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
