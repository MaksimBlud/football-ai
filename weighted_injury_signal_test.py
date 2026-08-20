from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, log_loss


ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "features_with_weighted_injuries.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "weighted_injury_signal_results.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


PARAMS = {
    "n_estimators": 300,
    "max_depth": 2,
    "learning_rate": 0.01,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "eval_metric": "mlogloss",
}


WEIGHTED_INJURY = [
    "home_missing_minutes365",
    "away_missing_minutes365",
    "missing_minutes365_difference",

    "home_missing_minutes_share",
    "away_missing_minutes_share",
    "missing_minutes_share_difference",

    "home_key_players_injured",
    "away_key_players_injured",
    "key_players_injured_difference",

    "home_weighted_injury_count",
    "away_weighted_injury_count",
    "weighted_injury_count_difference",
]


ELO = [
    "home_elo",
    "away_elo",
    "elo_difference",
]


FEATURE_SETS = {
    "weighted_injury_only":
        WEIGHTED_INJURY,

    "elo_weighted_injury":
        ELO + WEIGHTED_INJURY,
}


TARGET_MAP = {
    "H": 0,
    "D": 1,
    "A": 2,
}


ALPHAS = np.round(
    np.arange(
        0.00,
        0.31,
        0.01,
    ),
    2,
)


# ============================================================
# LOAD
# ============================================================

print("Загружаю данные...")

df = pd.read_csv(DATA_FILE)

df["match_date"] = pd.to_datetime(
    df["match_date"],
    errors="coerce",
)

df["target"] = df["result"].map(
    TARGET_MAP
)


# Используем только период,
# где weighted injuries валидны.
SEASONS = [
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
]

df = df[
    df["season"].isin(SEASONS)
].copy()


# ============================================================
# BOOKMAKER PROBABILITIES
# ============================================================

odds = df[
    [
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
].astype(float)

raw_book = 1.0 / odds.to_numpy()

book_proba = (
    raw_book
    / raw_book.sum(
        axis=1,
        keepdims=True,
    )
)

df["_book_h"] = book_proba[:, 0]
df["_book_d"] = book_proba[:, 1]
df["_book_a"] = book_proba[:, 2]


# ============================================================
# WALK FORWARD
# ============================================================

results = []


for name, features in FEATURE_SETS.items():

    print()
    print("=" * 100)
    print(
        f"{name} "
        f"({len(features)} features)"
    )
    print("=" * 100)

    all_y = []
    all_model = []
    all_book = []


    for test_idx in range(
        1,
        len(SEASONS),
    ):

        test_season = SEASONS[
            test_idx
        ]

        train_seasons = SEASONS[
            :test_idx
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


        required = (
            features
            + [
                "target",
                "_book_h",
                "_book_d",
                "_book_a",
            ]
        )


        train = train.dropna(
            subset=required
        )

        test = test.dropna(
            subset=required
        )


        if (
            len(train) == 0
            or len(test) == 0
        ):
            continue


        X_train = train[features]
        y_train = train["target"].astype(int)

        X_test = test[features]
        y_test = test["target"].astype(int)


        model = XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            **PARAMS,
        )

        model.fit(
            X_train,
            y_train,
        )


        model_proba = model.predict_proba(
            X_test
        )

        model_proba = (
            model_proba
            / model_proba.sum(
                axis=1,
                keepdims=True,
            )
        )


        book = test[
            [
                "_book_h",
                "_book_d",
                "_book_a",
            ]
        ].to_numpy()


        model_ll = log_loss(
            y_test,
            model_proba,
            labels=[0, 1, 2],
        )

        book_ll = log_loss(
            y_test,
            book,
            labels=[0, 1, 2],
        )


        model_acc = accuracy_score(
            y_test,
            np.argmax(
                model_proba,
                axis=1,
            ),
        )

        book_acc = accuracy_score(
            y_test,
            np.argmax(
                book,
                axis=1,
            ),
        )


        print(
            f"{test_season}: "
            f"MODEL ACC={model_acc:.4f} | "
            f"LL={model_ll:.4f} || "
            f"BOOK ACC={book_acc:.4f} | "
            f"LL={book_ll:.4f}"
        )


        all_y.append(
            y_test.to_numpy()
        )

        all_model.append(
            model_proba
        )

        all_book.append(
            book
        )


    if not all_y:
        continue


    y = np.concatenate(
        all_y
    )

    model_p = np.vstack(
        all_model
    )

    book_p = np.vstack(
        all_book
    )


    model_ll = log_loss(
        y,
        model_p,
        labels=[0, 1, 2],
    )

    book_ll = log_loss(
        y,
        book_p,
        labels=[0, 1, 2],
    )


    model_acc = accuracy_score(
        y,
        np.argmax(
            model_p,
            axis=1,
        ),
    )


    # ========================================================
    # BLEND SEARCH
    # ========================================================

    best_alpha = 0.0
    best_ll = book_ll


    for alpha in ALPHAS:

        blend = (
            alpha * model_p
            + (1.0 - alpha) * book_p
        )

        blend = (
            blend
            / blend.sum(
                axis=1,
                keepdims=True,
            )
        )


        ll = log_loss(
            y,
            blend,
            labels=[0, 1, 2],
        )


        if ll < best_ll:
            best_ll = ll
            best_alpha = float(
                alpha
            )


    edge = (
        book_ll
        - best_ll
    )


    results.append({
        "feature_set": name,
        "features": len(features),
        "matches": len(y),
        "model_accuracy": model_acc,
        "model_logloss": model_ll,
        "book_logloss": book_ll,
        "best_model_weight":
            best_alpha,
        "best_blend_logloss":
            best_ll,
        "blend_logloss_edge":
            edge,
    })


# ============================================================
# FINAL
# ============================================================

result = pd.DataFrame(
    results
)

result = result.sort_values(
    [
        "blend_logloss_edge",
        "model_logloss",
    ],
    ascending=[
        False,
        True,
    ],
).reset_index(drop=True)


result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 120)
print(
    "WEIGHTED INJURY SIGNAL — FINAL RANKING"
)
print("=" * 120)

print(
    result.to_string(
        index=False
    )
)


print()
print("=" * 120)
print("VERDICT")
print("=" * 120)


positive = result[
    (
        result[
            "blend_logloss_edge"
        ] > 0
    )
    &
    (
        result[
            "best_model_weight"
        ] > 0
    )
]


if len(positive):

    print(
        "⚠️ Найден потенциальный "
        "weighted injury signal."
    )

    print()
    print(
        positive[
            [
                "feature_set",
                "best_model_weight",
                "best_blend_logloss",
                "blend_logloss_edge",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Это ещё НЕ promotion: "
        "потребуется nested test."
    )

else:

    print(
        "❌ Weighted injury signal "
        "не улучшил bookmaker Log Loss."
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
