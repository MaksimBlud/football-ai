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
    / "features_with_elo.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "feature_group_signal_results.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


# ============================================================
# FEATURE GROUPS
# ============================================================

GROUPS = {
    "elo_only": [
        "home_elo",
        "away_elo",
        "elo_difference",
    ],

    "form_only": [
        "home_last5_points",
        "away_last5_points",
        "form_difference",
    ],

    "goals_only": [
        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",
    ],

    "shots_only": [
        "home_shots_last5",
        "away_shots_last5",
        "home_shots_target_last5",
        "away_shots_target_last5",
    ],

    "venue_only": [
        "home_venue_win_rate",
        "away_venue_win_rate",
        "home_venue_goals_scored",
        "away_venue_goals_scored",
    ],

    "elo_form": [
        "home_elo",
        "away_elo",
        "elo_difference",

        "home_last5_points",
        "away_last5_points",
        "form_difference",
    ],

    "elo_goals_shots": [
        "home_elo",
        "away_elo",
        "elo_difference",

        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",

        "home_shots_last5",
        "away_shots_last5",
        "home_shots_target_last5",
        "away_shots_target_last5",
    ],

    "all_no_odds": [
        "home_last5_points",
        "away_last5_points",
        "form_difference",

        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",

        "home_shots_last5",
        "away_shots_last5",
        "home_shots_target_last5",
        "away_shots_target_last5",

        "home_elo",
        "away_elo",
        "elo_difference",

        "home_venue_win_rate",
        "away_venue_win_rate",
        "home_venue_goals_scored",
        "away_venue_goals_scored",
    ],
}


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

df = pd.read_csv(DATA_FILE)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})


all_features = sorted(
    set(
        feature
        for features in GROUPS.values()
        for feature in features
    )
)


required = all_features + [
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


# ============================================================
# BOOKMAKER
# ============================================================

def bookmaker_probabilities(frame):

    odds = frame[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].to_numpy(dtype=np.float64)

    proba = 1.0 / odds

    return (
        proba
        / proba.sum(
            axis=1,
            keepdims=True,
        )
    )


# ============================================================
# BRIER
# ============================================================

def brier(y, proba):

    onehot = np.eye(3)[y]

    return float(
        np.mean(
            np.sum(
                (
                    proba
                    - onehot
                ) ** 2,
                axis=1,
            )
        )
    )


# ============================================================
# TEST ONE GROUP
# ============================================================

def test_group(
    group_name,
    features,
):

    all_true = []
    all_model_proba = []
    all_book_proba = []


    for test_index in range(
        2,
        len(seasons),
    ):

        test_season = seasons[
            test_index
        ]

        train = df[
            df["season"].isin(
                seasons[:test_index]
            )
        ].copy()

        test = df[
            df["season"]
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


        proba = model.predict_proba(
            test[features]
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


        book_proba = (
            bookmaker_probabilities(
                test
            )
        )


        all_true.extend(
            test[
                "target"
            ]
            .to_numpy(dtype=int)
            .tolist()
        )

        all_model_proba.extend(
            proba.tolist()
        )

        all_book_proba.extend(
            book_proba.tolist()
        )


    y = np.asarray(
        all_true,
        dtype=int,
    )

    mp = np.asarray(
        all_model_proba,
        dtype=np.float64,
    )

    bp = np.asarray(
        all_book_proba,
        dtype=np.float64,
    )


    model_pred = np.argmax(
        mp,
        axis=1,
    )


    model_acc = accuracy_score(
        y,
        model_pred,
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
    #
    # До 50% модели.
    # ========================================================

    best = None


    for alpha in np.arange(
        0.00,
        0.501,
        0.01,
    ):

        blended = (
            alpha * mp
            +
            (1.0 - alpha) * bp
        )


        blended = (
            blended
            / blended.sum(
                axis=1,
                keepdims=True,
            )
        )


        ll = log_loss(
            y,
            blended,
            labels=[0, 1, 2],
        )

        br = brier(
            y,
            blended,
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
        "group":
            group_name,

        "features":
            len(features),

        "model_accuracy":
            model_acc,

        "model_logloss":
            model_ll,

        "model_brier":
            model_brier,

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


# ============================================================
# RUN
# ============================================================

results = []


print()
print("=" * 110)
print("FEATURE GROUP SIGNAL TEST")
print("=" * 110)


for name, features in GROUPS.items():

    print()
    print(
        f"Проверяю {name} "
        f"({len(features)} features)..."
    )

    result = test_group(
        name,
        features,
    )

    results.append(
        result
    )

    print(
        f"MODEL LL={result['model_logloss']:.6f} | "
        f"best alpha={result['best_model_weight']:.2f} | "
        f"BLEND LL={result['best_blend_logloss']:.6f} | "
        f"edge={result['blend_logloss_edge']:+.6f}"
    )


results_df = pd.DataFrame(
    results
)


results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# RANKING
# ============================================================

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
print("=" * 110)
print("FINAL RANKING")
print("=" * 110)

print(
    ranking[
        [
            "group",
            "features",
            "model_accuracy",
            "model_logloss",
            "model_brier",
            "best_model_weight",
            "best_blend_logloss",
            "blend_logloss_edge",
            "best_blend_brier",
            "blend_brier_edge",
        ]
    ]
    .to_string(
        index=False
    )
)


positive = ranking[
    ranking[
        "blend_logloss_edge"
    ] > 0
]


print()
print("=" * 110)
print("INDEPENDENT SIGNAL VERDICT")
print("=" * 110)


if positive.empty:

    print(
        "❌ Ни одна группа признаков "
        "не улучшила bookmaker Log Loss."
    )

else:

    print(
        "✅ Найдены группы, которые "
        "улучшают bookmaker Log Loss:"
    )

    print()

    print(
        positive[
            [
                "group",
                "best_model_weight",
                "best_blend_logloss",
                "blend_logloss_edge",
            ]
        ]
        .to_string(
            index=False
        )
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
