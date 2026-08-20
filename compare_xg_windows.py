from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, log_loss


ROOT = Path(__file__).resolve().parent

LAST5_FILE = ROOT / "data" / "features_with_xg.csv"
LAST10_FILE = ROOT / "data" / "features_with_xg_last10.csv"

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "xg_window_comparison.csv"
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


LAST5 = [
    "home_xg_last5",
    "home_xga_last5",
    "home_npxg_last5",
    "home_npxga_last5",
    "away_xg_last5",
    "away_xga_last5",
    "away_npxg_last5",
    "away_npxga_last5",
    "xg_attack_difference",
    "xg_defence_difference",
]

LAST10 = [
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

ELO = [
    "home_elo",
    "away_elo",
    "elo_difference",
]


def bookmaker_proba(frame):
    odds = frame[
        ["home_odds", "draw_odds", "away_odds"]
    ].to_numpy(dtype=np.float64)

    p = 1.0 / odds

    return p / p.sum(
        axis=1,
        keepdims=True,
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


def load_file(path):
    df = pd.read_csv(path)

    df["target"] = df["result"].map({
        "H": 0,
        "D": 1,
        "A": 2,
    })

    return df


last5_df = load_file(LAST5_FILE)
last10_df = load_file(LAST10_FILE)


TESTS = [
    (
        "xg_last5",
        last5_df,
        LAST5,
    ),
    (
        "xg_last10",
        last10_df,
        LAST10,
    ),
    (
        "elo_xg_last5",
        last5_df,
        ELO + LAST5,
    ),
    (
        "elo_xg_last10",
        last10_df,
        ELO + LAST10,
    ),
]


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

    all_true = []
    all_model_proba = []
    all_book_proba = []

    print()
    print("=" * 100)
    print(name)
    print("=" * 100)

    for i in range(1, len(seasons)):

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

        mp = mp / mp.sum(
            axis=1,
            keepdims=True,
        )

        bp = bookmaker_proba(test)

        y = test[
            "target"
        ].to_numpy(dtype=int)

        print(
            f"{test_season}: "
            f"MODEL LL={log_loss(y, mp, labels=[0,1,2]):.4f} | "
            f"BOOK LL={log_loss(y, bp, labels=[0,1,2]):.4f}"
        )

        all_true.extend(
            y.tolist()
        )

        all_model_proba.extend(
            mp.tolist()
        )

        all_book_proba.extend(
            bp.tolist()
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

    model_acc = accuracy_score(
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

    book_ll = log_loss(
        y,
        bp,
        labels=[0, 1, 2],
    )

    book_brier = brier(
        y,
        bp,
    )


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
                "alpha": float(alpha),
                "log_loss": float(ll),
                "brier": float(br),
            }


    return {
        "model": name,
        "features": len(features),
        "model_accuracy": model_acc,
        "model_logloss": model_ll,
        "model_brier": model_brier,
        "book_logloss": book_ll,
        "book_brier": book_brier,
        "best_model_weight": best["alpha"],
        "best_blend_logloss": best["log_loss"],
        "blend_logloss_edge":
            book_ll - best["log_loss"],
        "best_blend_brier": best["brier"],
        "blend_brier_edge":
            book_brier - best["brier"],
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


ranking = results_df.sort_values(
    [
        "best_blend_logloss",
        "model_logloss",
    ]
)


print()
print("=" * 110)
print("XG WINDOW FINAL COMPARISON")
print("=" * 110)

print(
    ranking[
        [
            "model",
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
    ].to_string(index=False)
)


print()
print("=" * 110)
print("VERDICT")
print("=" * 110)

positive = ranking[
    ranking["blend_logloss_edge"] > 0
]

if positive.empty:
    print(
        "❌ Ни LAST5, ни LAST10 не добавили "
        "устойчивого сигнала поверх bookmaker."
    )
else:
    print(
        "✅ Найден положительный blend edge:"
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
        ].to_string(index=False)
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
