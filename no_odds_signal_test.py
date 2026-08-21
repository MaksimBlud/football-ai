from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)

from model_utils import FEATURES


ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "features_with_elo.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "no_odds_walk_forward_predictions.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


# ============================================================
# УБИРАЕМ ТОЛЬКО БУКМЕКЕРСКИЕ КОЭФФИЦИЕНТЫ
# ============================================================

ODDS_FEATURES = [
    "home_odds",
    "draw_odds",
    "away_odds",
]

NO_ODDS_FEATURES = [
    feature
    for feature in FEATURES
    if feature not in ODDS_FEATURES
]


# Challenger-параметры, которые ранее выиграли
# nested walk-forward.
PARAMS = {
    "n_estimators": 300,
    "max_depth": 2,
    "learning_rate": 0.01,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
}


# ============================================================
# DATA
# ============================================================

print("Загружаю данные...")

df = pd.read_csv(DATA_FILE)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})


required = (
    NO_ODDS_FEATURES
    + [
        "season",
        "target",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
)

df = df.dropna(
    subset=required
).copy()


seasons = sorted(
    df["season"].unique()
)


print("Матчей:", len(df))
print("Сезоны:", seasons)

print()
print("NO-ODDS FEATURES:")

for i, feature in enumerate(
    NO_ODDS_FEATURES,
    1,
):
    print(
        f"{i:2}. {feature}"
    )

print()
print(
    "Всего независимых признаков:",
    len(NO_ODDS_FEATURES),
)


# ============================================================
# WALK-FORWARD
#
# Начинаем с 2021/2022, чтобы сравнение было идентично
# challenger verification: 5 OOS сезонов / 1900 матчей.
# ============================================================

rows = []


for test_index in range(
    2,
    len(seasons),
):

    test_season = seasons[
        test_index
    ]

    train_seasons = seasons[
        :test_index
    ]

    train = df[
        df["season"].isin(
            train_seasons
        )
    ].copy()

    test = df[
        df["season"]
        == test_season
    ].copy()


    if train.empty or test.empty:
        continue


    X_train = train[
        NO_ODDS_FEATURES
    ]

    y_train = train[
        "target"
    ]


    X_test = test[
        NO_ODDS_FEATURES
    ]

    y_test = test[
        "target"
    ]


    model = XGBClassifier(
        **PARAMS,
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
    ).astype(
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


    # ========================================================
    # BOOKMAKER
    # ========================================================

    odds = test[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].to_numpy(
        dtype=np.float64
    )


    bookmaker_proba = (
        1.0 / odds
    )


    bookmaker_proba = (
        bookmaker_proba
        / bookmaker_proba.sum(
            axis=1,
            keepdims=True,
        )
    )


    bookmaker_pred = np.argmax(
        bookmaker_proba,
        axis=1,
    )


    # ========================================================
    # SEASON METRICS
    # ========================================================

    model_acc = accuracy_score(
        y_test,
        pred,
    )

    model_ll = log_loss(
        y_test,
        proba,
        labels=[0, 1, 2],
    )


    book_acc = accuracy_score(
        y_test,
        bookmaker_pred,
    )

    book_ll = log_loss(
        y_test,
        bookmaker_proba,
        labels=[0, 1, 2],
    )


    print()
    print(
        f"{test_season}: "
        f"NO-ODDS ACC={model_acc:.4f} | "
        f"LL={model_ll:.4f} || "
        f"BOOK ACC={book_acc:.4f} | "
        f"LL={book_ll:.4f}"
    )


    # ========================================================
    # MATCH-LEVEL EXPORT
    # ========================================================

    for position, (
        idx,
        row,
    ) in enumerate(
        test.iterrows()
    ):

        rows.append({
            "season":
                test_season,

            "actual":
                int(
                    y_test.loc[idx]
                ),

            "p_home":
                float(
                    proba[
                        position,
                        0,
                    ]
                ),

            "p_draw":
                float(
                    proba[
                        position,
                        1,
                    ]
                ),

            "p_away":
                float(
                    proba[
                        position,
                        2,
                    ]
                ),

            "model_pred":
                int(
                    pred[position]
                ),

            "book_p_home":
                float(
                    bookmaker_proba[
                        position,
                        0,
                    ]
                ),

            "book_p_draw":
                float(
                    bookmaker_proba[
                        position,
                        1,
                    ]
                ),

            "book_p_away":
                float(
                    bookmaker_proba[
                        position,
                        2,
                    ]
                ),

            "book_pred":
                int(
                    bookmaker_pred[
                        position
                    ]
                ),

            "home_odds":
                float(
                    row["home_odds"]
                ),

            "draw_odds":
                float(
                    row["draw_odds"]
                ),

            "away_odds":
                float(
                    row["away_odds"]
                ),
        })


# ============================================================
# OVERALL
# ============================================================

out = pd.DataFrame(
    rows
)


actual = out[
    "actual"
].to_numpy(
    dtype=int
)


model_proba = out[
    [
        "p_home",
        "p_draw",
        "p_away",
    ]
].to_numpy(
    dtype=np.float64
)


book_proba = out[
    [
        "book_p_home",
        "book_p_draw",
        "book_p_away",
    ]
].to_numpy(
    dtype=np.float64
)


model_pred = out[
    "model_pred"
].to_numpy(
    dtype=int
)

book_pred = out[
    "book_pred"
].to_numpy(
    dtype=int
)


model_accuracy = accuracy_score(
    actual,
    model_pred,
)

book_accuracy = accuracy_score(
    actual,
    book_pred,
)


model_logloss = log_loss(
    actual,
    model_proba,
    labels=[0, 1, 2],
)

book_logloss = log_loss(
    actual,
    book_proba,
    labels=[0, 1, 2],
)


onehot = np.eye(3)[
    actual
]


model_brier = np.mean(
    np.sum(
        (
            model_proba
            - onehot
        ) ** 2,
        axis=1,
    )
)


book_brier = np.mean(
    np.sum(
        (
            book_proba
            - onehot
        ) ** 2,
        axis=1,
    )
)


# ============================================================
# DISAGREEMENT
# ============================================================

disagree = (
    model_pred
    != book_pred
)


model_correct = (
    model_pred
    == actual
)

book_correct = (
    book_pred
    == actual
)


disagree_count = int(
    disagree.sum()
)


model_disagree_accuracy = (
    model_correct[
        disagree
    ].mean()
)

book_disagree_accuracy = (
    book_correct[
        disagree
    ].mean()
)


# ============================================================
# SAVE
# ============================================================

out.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 100)
print("NO-ODDS INDEPENDENT SIGNAL — OOS RESULT")
print("=" * 100)

print(
    "OOS матчей:",
    len(out),
)

print()

print(
    f"NO-ODDS MODEL | "
    f"ACC={model_accuracy:.6f} | "
    f"LL={model_logloss:.6f} | "
    f"BRIER={model_brier:.6f}"
)

print(
    f"BOOKMAKER     | "
    f"ACC={book_accuracy:.6f} | "
    f"LL={book_logloss:.6f} | "
    f"BRIER={book_brier:.6f}"
)


print()
print("=" * 100)
print("DISAGREEMENT")
print("=" * 100)

print(
    "Разошлись прогнозы:",
    disagree_count,
)

print(
    "Доля:",
    round(
        disagree_count
        / len(out),
        4,
    ),
)

print()

print(
    "NO-ODDS MODEL accuracy:",
    round(
        model_disagree_accuracy,
        4,
    ),
)

print(
    "BOOKMAKER accuracy:",
    round(
        book_disagree_accuracy,
        4,
    ),
)

print(
    "Разница:",
    round(
        model_disagree_accuracy
        - book_disagree_accuracy,
        4,
    ),
)


print()
print("=" * 100)
print("MODEL PREDICTIONS")
print("=" * 100)

label_map = {
    0: "HOME",
    1: "DRAW",
    2: "AWAY",
}

print(
    pd.Series(
        model_pred
    )
    .map(
        label_map
    )
    .value_counts()
    .to_string()
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
