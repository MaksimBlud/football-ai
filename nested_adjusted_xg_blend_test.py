from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import log_loss


ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "features_with_opponent_adjusted_xg.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "nested_adjusted_xg_blend_results.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


FEATURES = [
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


PARAMS = {
    "n_estimators": 300,
    "max_depth": 2,
    "learning_rate": 0.01,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
}


ALPHAS = np.round(
    np.arange(
        0.00,
        0.201,
        0.01,
    ),
    2,
)


# ============================================================
# DATA
# ============================================================

df = pd.read_csv(DATA_FILE)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})


required = (
    FEATURES
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


# ============================================================
# СНАЧАЛА СОЗДАЁМ ЧЕСТНЫЕ OOS PREDICTIONS
# ДЛЯ КАЖДОГО СЕЗОНА
# ============================================================

season_predictions = {}


print()
print("=" * 100)
print("BUILDING OOS XG LAST10 PREDICTIONS")
print("=" * 100)


for i in range(
    1,
    len(seasons),
):

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


    model_p = model.predict_proba(
        test[FEATURES]
    ).astype(
        np.float64
    )


    model_p = (
        model_p
        / model_p.sum(
            axis=1,
            keepdims=True,
        )
    )


    book_p = bookmaker_proba(
        test
    )


    y = test[
        "target"
    ].to_numpy(
        dtype=int
    )


    season_predictions[
        test_season
    ] = {
        "y": y,
        "model": model_p,
        "book": book_p,
    }


    print(
        f"{test_season}: "
        f"MODEL LL="
        f"{log_loss(y, model_p, labels=[0,1,2]):.6f} | "
        f"BOOK LL="
        f"{log_loss(y, book_p, labels=[0,1,2]):.6f}"
    )


# ============================================================
# NESTED BLEND
#
# 2020/21 = история для выбора alpha
# 2021/22 = первый честный outer test
# ============================================================

oos_seasons = seasons[1:]

rows = []

all_y = []
all_book = []
all_nested = []


print()
print("=" * 100)
print("NESTED BLEND WALK-FORWARD")
print("=" * 100)


for outer_index in range(
    1,
    len(oos_seasons),
):

    test_season = oos_seasons[
        outer_index
    ]

    tuning_seasons = oos_seasons[
        :outer_index
    ]


    tuning_y = np.concatenate([
        season_predictions[s]["y"]
        for s in tuning_seasons
    ])

    tuning_model = np.vstack([
        season_predictions[s]["model"]
        for s in tuning_seasons
    ])

    tuning_book = np.vstack([
        season_predictions[s]["book"]
        for s in tuning_seasons
    ])


    best_alpha = None
    best_ll = None


    for alpha in ALPHAS:

        blend = (
            alpha * tuning_model
            +
            (1.0 - alpha) * tuning_book
        )


        ll = log_loss(
            tuning_y,
            blend,
            labels=[0, 1, 2],
        )


        if (
            best_ll is None
            or ll < best_ll
        ):
            best_ll = ll
            best_alpha = float(
                alpha
            )


    test_data = season_predictions[
        test_season
    ]

    y = test_data["y"]
    mp = test_data["model"]
    bp = test_data["book"]


    nested_blend = (
        best_alpha * mp
        +
        (1.0 - best_alpha) * bp
    )


    book_ll = log_loss(
        y,
        bp,
        labels=[0, 1, 2],
    )

    blend_ll = log_loss(
        y,
        nested_blend,
        labels=[0, 1, 2],
    )


    edge = (
        book_ll
        - blend_ll
    )


    rows.append({
        "season":
            test_season,

        "tuning_seasons":
            ",".join(
                tuning_seasons
            ),

        "selected_alpha":
            best_alpha,

        "tuning_logloss":
            best_ll,

        "book_logloss":
            book_ll,

        "blend_logloss":
            blend_ll,

        "edge":
            edge,
    })


    all_y.extend(
        y.tolist()
    )

    all_book.extend(
        bp.tolist()
    )

    all_nested.extend(
        nested_blend.tolist()
    )


    print()
    print(
        f"{test_season} | "
        f"alpha={best_alpha:.2f}"
    )

    print(
        f"BOOK  LL={book_ll:.6f}"
    )

    print(
        f"BLEND LL={blend_ll:.6f}"
    )

    print(
        f"EDGE={edge:+.6f}"
    )


# ============================================================
# OVERALL
# ============================================================

all_y = np.asarray(
    all_y,
    dtype=int,
)

all_book = np.asarray(
    all_book,
    dtype=np.float64,
)

all_nested = np.asarray(
    all_nested,
    dtype=np.float64,
)


overall_book_ll = log_loss(
    all_y,
    all_book,
    labels=[0, 1, 2],
)

overall_blend_ll = log_loss(
    all_y,
    all_nested,
    labels=[0, 1, 2],
)


overall_edge = (
    overall_book_ll
    - overall_blend_ll
)


results = pd.DataFrame(
    rows
)

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 100)
print("NESTED ADJUSTED XG BLEND — FINAL OUT-OF-SAMPLE RESULT")
print("=" * 100)

print(
    f"BOOKMAKER Log Loss: "
    f"{overall_book_ll:.6f}"
)

print(
    f"NESTED BLEND Log Loss: "
    f"{overall_blend_ll:.6f}"
)

print(
    f"EDGE: "
    f"{overall_edge:+.6f}"
)


print()
print(
    "Сезонов с положительным edge:",
    int(
        (
            results["edge"] > 0
        ).sum()
    ),
    "/",
    len(results),
)


print()
print("Выбранные alpha:")

print(
    results[
        [
            "season",
            "selected_alpha",
            "book_logloss",
            "blend_logloss",
            "edge",
        ]
    ].to_string(
        index=False
    )
)


print()
print("=" * 100)
print("VERDICT")
print("=" * 100)


if overall_edge > 0:

    print(
        "✅ Opponent-adjusted xG подтвердил положительный "
        "edge в nested out-of-sample тесте."
    )

else:

    print(
        "❌ Положительный edge opponent-adjusted xG "
        "не подтвердился в nested тесте."
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
