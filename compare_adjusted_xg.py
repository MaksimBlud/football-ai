from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)


ROOT = Path(__file__).resolve().parent

RAW_FILE = (
    ROOT
    / "data"
    / "features_with_xg_last10.csv"
)

ADJ_FILE = (
    ROOT
    / "data"
    / "features_with_opponent_adjusted_xg.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "adjusted_xg_comparison.csv"
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


RAW_XG = [
    "home_xg_last10",
    "home_xga_last10",
    "home_npxg_last10",
    "home_npxga_last10",

    "away_xg_last10",
    "away_xga_last10",
    "away_npxg_last10",
    "away_npxga_last10",

    "xg_attack_difference_last10",
    "xg_defence_difference_last10",
]


ADJ_XG = [
    "home_adj_xg_last10",
    "home_adj_xga_last10",
    "away_adj_xg_last10",
    "away_adj_xga_last10",

    "home_opponent_elo_last10",
    "away_opponent_elo_last10",

    "adj_xg_attack_difference",
    "adj_xg_defence_difference",
    "opponent_strength_difference",
]


ELO = [
    "home_elo",
    "away_elo",
    "elo_difference",
]


def load_data(path):
    df = pd.read_csv(path)

    df["target"] = df["result"].map({
        "H": 0,
        "D": 1,
        "A": 2,
    })

    return df


raw_df = load_data(RAW_FILE)
adj_df = load_data(ADJ_FILE)


TESTS = [
    (
        "raw_xg_last10",
        raw_df,
        RAW_XG,
    ),
    (
        "adjusted_xg",
        adj_df,
        ADJ_XG,
    ),
    (
        "elo_raw_xg",
        raw_df,
        ELO + RAW_XG,
    ),
    (
        "elo_adjusted_xg",
        adj_df,
        ELO + ADJ_XG,
    ),
]


def bookmaker_proba(frame):
    odds = frame[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].to_numpy(
        dtype=np.float64
    )

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


def evaluate(name, df, features):

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
    print(name)
    print("=" * 100)

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

        if train.empty or test.empty:
            continue

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
        ).astype(
            np.float64
        )

        mp = (
            mp
            / mp.sum(
                axis=1,
                keepdims=True,
            )
        )

        bp = bookmaker_proba(
            test
        )

        y = test[
            "target"
        ].to_numpy(
            dtype=int
        )

        print(
            f"{test_season}: "
            f"MODEL LL="
            f"{log_loss(y, mp, labels=[0,1,2]):.4f} | "
            f"BOOK LL="
            f"{log_loss(y, bp, labels=[0,1,2]):.4f}"
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

    model_acc = accuracy_score(
        y,
        np.argmax(
            mp,
            axis=1,
        ),
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
        "model":
            name,

        "features":
            len(features),

        "matches":
            len(y),

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


results = []

for name, df, features in TESTS:

    results.append(
        evaluate(
            name,
            df,
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
print("=" * 115)
print("OPPONENT-ADJUSTED XG — FINAL COMPARISON")
print("=" * 115)

print(
    ranking[
        [
            "model",
            "features",
            "matches",
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


print()
print("=" * 115)
print("VERDICT")
print("=" * 115)

positive = ranking[
    ranking[
        "blend_logloss_edge"
    ] > 0
]

if positive.empty:

    print(
        "❌ Opponent-adjusted xG "
        "не улучшил bookmaker."
    )

else:

    print(
        "✅ Найден положительный "
        "opponent-adjusted xG signal:"
    )

    print()

    print(
        positive[
            [
                "model",
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
