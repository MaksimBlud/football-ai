from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)


ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "features_with_injuries.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "injury_signal_results.csv"
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


INJURY = [
    "home_injured_players",
    "away_injured_players",
    "injured_players_difference",

    "home_new_injuries_last7",
    "away_new_injuries_last7",
    "new_injuries_last7_difference",

    "home_new_injuries_last14",
    "away_new_injuries_last14",
    "new_injuries_last14_difference",
]


ELO = [
    "home_elo",
    "away_elo",
    "elo_difference",
]


FORM = [
    "home_last5_points",
    "away_last5_points",
    "form_difference",
]


FEATURE_SETS = {
    "injury_only":
        INJURY,

    "elo_injury":
        ELO + INJURY,

    "form_injury":
        FORM + INJURY,

    "elo_form_injury":
        ELO + FORM + INJURY,
}


print("Загружаю данные...")

df = pd.read_csv(DATA_FILE)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})


# ============================================================
# ВАЖНО:
# 2025/26 исключаем — injury dataset там неполный.
# Используем только полностью покрываемый диапазон.
# ============================================================

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


def bookmaker_proba(frame):

    odds = frame[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].to_numpy(dtype=np.float64)

    p = 1.0 / odds

    return (
        p
        / p.sum(
            axis=1,
            keepdims=True,
        )
    )


def brier(y, proba):

    onehot = np.eye(3)[y]

    return float(
        np.mean(
            np.sum(
                (proba - onehot) ** 2,
                axis=1,
            )
        )
    )


def evaluate(name, features):

    required = (
        features
        + [
            "season",
            "target",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    )

    data = df.dropna(
        subset=required
    ).copy()

    seasons = sorted(
        data["season"].unique()
    )

    all_y = []
    all_model = []
    all_book = []


    print()
    print("=" * 100)
    print(
        f"{name} "
        f"({len(features)} features)"
    )
    print("=" * 100)


    # 2019/20 train
    # 2020/21 -> 2024/25 OOS
    for i in range(
        1,
        len(seasons),
    ):

        test_season = seasons[i]

        train = data[
            data["season"].isin(
                seasons[:i]
            )
        ].copy()

        test = data[
            data["season"]
            == test_season
        ].copy()


        model = XGBClassifier(
            **PARAMS,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
        )


        model.fit(
            train[features],
            train["target"],
        )


        mp = model.predict_proba(
            test[features]
        ).astype(np.float64)

        mp = (
            mp
            / mp.sum(
                axis=1,
                keepdims=True,
            )
        )


        bp = bookmaker_proba(test)

        y = test[
            "target"
        ].to_numpy(dtype=int)


        model_ll = log_loss(
            y,
            mp,
            labels=[0, 1, 2],
        )

        book_ll = log_loss(
            y,
            bp,
            labels=[0, 1, 2],
        )


        print(
            f"{test_season}: "
            f"MODEL ACC="
            f"{accuracy_score(y, np.argmax(mp, axis=1)):.4f} | "
            f"LL={model_ll:.4f} || "
            f"BOOK ACC="
            f"{accuracy_score(y, np.argmax(bp, axis=1)):.4f} | "
            f"LL={book_ll:.4f}"
        )


        all_y.extend(
            y.tolist()
        )

        all_model.extend(
            mp.tolist()
        )

        all_book.extend(
            bp.tolist()
        )


    y = np.asarray(
        all_y,
        dtype=int,
    )

    mp = np.asarray(
        all_model,
        dtype=np.float64,
    )

    bp = np.asarray(
        all_book,
        dtype=np.float64,
    )


    model_accuracy = accuracy_score(
        y,
        np.argmax(mp, axis=1),
    )

    model_ll = log_loss(
        y,
        mp,
        labels=[0, 1, 2],
    )

    model_brier = brier(
        y,
        mp,
    )


    book_accuracy = accuracy_score(
        y,
        np.argmax(bp, axis=1),
    )

    book_ll = log_loss(
        y,
        bp,
        labels=[0, 1, 2],
    )

    book_brier = brier(
        y,
        bp,
    )


    # ========================================================
    # BLEND SEARCH
    # ========================================================

    best = None

    for alpha in np.arange(
        0.00,
        0.501,
        0.01,
    ):

        blend = (
            alpha * mp
            +
            (1.0 - alpha) * bp
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

        br = brier(
            y,
            blend,
        )


        if (
            best is None
            or ll < best["log_loss"]
        ):
            best = {
                "alpha":
                    float(alpha),

                "log_loss":
                    float(ll),

                "brier":
                    float(br),
            }


    return {
        "feature_set":
            name,

        "features":
            len(features),

        "matches":
            len(y),

        "model_accuracy":
            model_accuracy,

        "model_logloss":
            model_ll,

        "model_brier":
            model_brier,

        "book_accuracy":
            book_accuracy,

        "book_logloss":
            book_ll,

        "book_brier":
            book_brier,

        "best_model_weight":
            best["alpha"],

        "best_blend_logloss":
            best["log_loss"],

        "blend_logloss_edge":
            book_ll
            - best["log_loss"],

        "best_blend_brier":
            best["brier"],

        "blend_brier_edge":
            book_brier
            - best["brier"],
    }


results = []


for name, features in FEATURE_SETS.items():

    results.append(
        evaluate(
            name,
            features,
        )
    )


results_df = pd.DataFrame(
    results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


ranking = (
    results_df
    .sort_values(
        [
            "best_blend_logloss",
            "model_logloss",
        ]
    )
)


print()
print("=" * 120)
print("INJURY SIGNAL — FINAL RANKING")
print("=" * 120)

print(
    ranking[
        [
            "feature_set",
            "features",
            "matches",
            "model_accuracy",
            "model_logloss",
            "model_brier",
            "book_accuracy",
            "book_logloss",
            "best_model_weight",
            "best_blend_logloss",
            "blend_logloss_edge",
            "best_blend_brier",
            "blend_brier_edge",
        ]
    ]
    .to_string(index=False)
)


positive = ranking[
    ranking[
        "blend_logloss_edge"
    ] > 0
]


print()
print("=" * 120)
print("INJURY SIGNAL VERDICT")
print("=" * 120)


if positive.empty:

    print(
        "❌ Injury-признаки не улучшили "
        "bookmaker Log Loss."
    )

else:

    print(
        "✅ Найдены положительные injury signals:"
    )

    print()

    print(
        positive[
            [
                "feature_set",
                "best_model_weight",
                "best_blend_logloss",
                "blend_logloss_edge",
                "blend_brier_edge",
            ]
        ]
        .to_string(index=False)
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
