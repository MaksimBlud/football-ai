from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    log_loss,
)


ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "historical_market_movement_dataset.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "future_market_movement_results.csv"
)

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)


# ============================================================
# FEATURES AVAILABLE AT OPENING
#
# Closing probabilities / moves are NEVER inputs.
# ============================================================

FEATURES = [
    # Opening market
    "open_p_home",
    "open_p_draw",
    "open_p_away",

    # Existing football signal
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
]


TARGETS = [
    "move_home",
    "move_draw",
    "move_away",
]


PARAMS = {
    "n_estimators": 300,
    "max_depth": 2,
    "learning_rate": 0.01,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "random_state": 42,
}


df = pd.read_csv(DATA_FILE)

df["target"] = pd.to_numeric(
    df["target"],
    errors="coerce",
)


SEASONS = sorted(
    df["season"]
    .dropna()
    .unique()
)


required = (
    FEATURES
    + TARGETS
    + [
        "target",
        "season",
        "open_p_home",
        "open_p_draw",
        "open_p_away",
        "close_p_home",
        "close_p_draw",
        "close_p_away",
    ]
)

df = df.dropna(
    subset=required
).copy()


print("=" * 120)
print(
    "FUTURE MARKET MOVEMENT — "
    "WALK-FORWARD REGRESSION"
)
print("=" * 120)

print(
    "Матчей:",
    len(df),
)

print(
    "Сезоны:",
    SEASONS,
)


all_y = []

all_open = []
all_real_close = []
all_pred_close = []

all_actual_moves = []
all_pred_moves = []

rows = []


# ============================================================
# WALK FORWARD
# ============================================================

for i in range(
    1,
    len(SEASONS),
):

    test_season = (
        SEASONS[i]
    )

    train_seasons = (
        SEASONS[:i]
    )

    train = df[
        df["season"].isin(
            train_seasons
        )
    ].copy()

    test = df[
        df["season"]
        == test_season
    ].copy()


    X_train = train[
        FEATURES
    ]

    X_test = test[
        FEATURES
    ]


    predictions = []


    for target_col in TARGETS:

        model = XGBRegressor(
            **PARAMS
        )

        model.fit(
            X_train,
            train[
                target_col
            ],
        )

        pred = model.predict(
            X_test
        )

        predictions.append(
            pred
        )


    pred_moves = np.column_stack(
        predictions
    )


    actual_moves = test[
        TARGETS
    ].to_numpy(
        dtype=float
    )


    open_probs = test[
        [
            "open_p_home",
            "open_p_draw",
            "open_p_away",
        ]
    ].to_numpy(
        dtype=float
    )


    real_close = test[
        [
            "close_p_home",
            "close_p_draw",
            "close_p_away",
        ]
    ].to_numpy(
        dtype=float
    )


    # ========================================================
    # SYNTHETIC CLOSE
    # ========================================================

    pred_close = (
        open_probs
        + pred_moves
    )


    # Защита от отрицательных/нулевых вероятностей
    pred_close = np.clip(
        pred_close,
        1e-6,
        None,
    )


    pred_close = (
        pred_close
        / pred_close.sum(
            axis=1,
            keepdims=True,
        )
    )


    y = test[
        "target"
    ].to_numpy(
        dtype=int
    )


    # ========================================================
    # METRICS
    # ========================================================

    open_ll = log_loss(
        y,
        open_probs,
        labels=[0, 1, 2],
    )

    pred_ll = log_loss(
        y,
        pred_close,
        labels=[0, 1, 2],
    )

    real_close_ll = log_loss(
        y,
        real_close,
        labels=[0, 1, 2],
    )


    move_mae = mean_absolute_error(
        actual_moves,
        pred_moves,
    )


    move_rmse = mean_squared_error(
        actual_moves,
        pred_moves,
    ) ** 0.5


    # Направление движения по каждой вероятности
    direction_accuracy = np.mean(
        np.sign(
            actual_moves
        )
        ==
        np.sign(
            pred_moves
        )
    )


    # Правильно ли предсказали сторону
    # самого сильного движения
    actual_side = np.argmax(
        np.abs(
            actual_moves
        ),
        axis=1,
    )

    pred_side = np.argmax(
        np.abs(
            pred_moves
        ),
        axis=1,
    )

    strongest_side_accuracy = np.mean(
        actual_side
        == pred_side
    )


    print()
    print("-" * 120)
    print(test_season)
    print("-" * 120)

    print(
        f"OPEN LL:           "
        f"{open_ll:.6f}"
    )

    print(
        f"PREDICTED CLOSE LL:"
        f" {pred_ll:.6f}"
    )

    print(
        f"REAL CLOSE LL:     "
        f"{real_close_ll:.6f}"
    )

    print(
        f"EDGE vs OPEN:      "
        f"{open_ll - pred_ll:+.6f}"
    )

    print(
        f"GAP TO REAL CLOSE: "
        f"{pred_ll - real_close_ll:+.6f}"
    )

    print(
        f"Movement MAE:      "
        f"{move_mae:.6f}"
    )

    print(
        f"Movement RMSE:     "
        f"{move_rmse:.6f}"
    )

    print(
        f"Direction accuracy:"
        f" {direction_accuracy:.4f}"
    )

    print(
        f"Strongest-side acc:"
        f" {strongest_side_accuracy:.4f}"
    )


    rows.append({
        "season":
            test_season,

        "matches":
            len(test),

        "open_logloss":
            open_ll,

        "predicted_close_logloss":
            pred_ll,

        "real_close_logloss":
            real_close_ll,

        "edge_vs_open":
            open_ll - pred_ll,

        "gap_to_real_close":
            pred_ll - real_close_ll,

        "movement_mae":
            move_mae,

        "movement_rmse":
            move_rmse,

        "direction_accuracy":
            direction_accuracy,

        "strongest_side_accuracy":
            strongest_side_accuracy,
    })


    all_y.extend(
        y.tolist()
    )

    all_open.extend(
        open_probs.tolist()
    )

    all_real_close.extend(
        real_close.tolist()
    )

    all_pred_close.extend(
        pred_close.tolist()
    )

    all_actual_moves.extend(
        actual_moves.tolist()
    )

    all_pred_moves.extend(
        pred_moves.tolist()
    )


# ============================================================
# OVERALL
# ============================================================

all_y = np.asarray(
    all_y,
    dtype=int,
)

all_open = np.asarray(
    all_open,
    dtype=float,
)

all_real_close = np.asarray(
    all_real_close,
    dtype=float,
)

all_pred_close = np.asarray(
    all_pred_close,
    dtype=float,
)

all_actual_moves = np.asarray(
    all_actual_moves,
    dtype=float,
)

all_pred_moves = np.asarray(
    all_pred_moves,
    dtype=float,
)


open_ll = log_loss(
    all_y,
    all_open,
    labels=[0, 1, 2],
)

pred_ll = log_loss(
    all_y,
    all_pred_close,
    labels=[0, 1, 2],
)

real_close_ll = log_loss(
    all_y,
    all_real_close,
    labels=[0, 1, 2],
)


direction_accuracy = np.mean(
    np.sign(
        all_actual_moves
    )
    ==
    np.sign(
        all_pred_moves
    )
)


actual_side = np.argmax(
    np.abs(
        all_actual_moves
    ),
    axis=1,
)

pred_side = np.argmax(
    np.abs(
        all_pred_moves
    ),
    axis=1,
)

strongest_side_accuracy = np.mean(
    actual_side
    == pred_side
)


print()
print("=" * 120)
print(
    "OVERALL OUT-OF-SAMPLE RESULT"
)
print("=" * 120)

print(
    "OOS матчей:",
    len(all_y),
)

print(
    "OPEN Log Loss:",
    round(
        open_ll,
        6,
    ),
)

print(
    "PREDICTED CLOSE Log Loss:",
    round(
        pred_ll,
        6,
    ),
)

print(
    "REAL CLOSE Log Loss:",
    round(
        real_close_ll,
        6,
    ),
)

print()

print(
    "EDGE vs OPEN:",
    f"{open_ll - pred_ll:+.6f}",
)

print(
    "GAP TO REAL CLOSE:",
    f"{pred_ll - real_close_ll:+.6f}",
)

print()

print(
    "Movement MAE:",
    round(
        mean_absolute_error(
            all_actual_moves,
            all_pred_moves,
        ),
        6,
    ),
)

print(
    "Movement RMSE:",
    round(
        mean_squared_error(
            all_actual_moves,
            all_pred_moves,
        ) ** 0.5,
        6,
    ),
)

print(
    "Direction accuracy:",
    round(
        direction_accuracy,
        4,
    ),
)

print(
    "Strongest-side accuracy:",
    round(
        strongest_side_accuracy,
        4,
    ),
)


result = pd.DataFrame(
    rows
)

result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 120)
print("VERDICT")
print("=" * 120)


positive_seasons = int(
    (
        result[
            "edge_vs_open"
        ] > 0
    ).sum()
)


print(
    "Сезонов synthetic close "
    "лучше opening:",
    positive_seasons,
    "/",
    len(result),
)


if (
    pred_ll < open_ll
):

    print(
        "✅ Модель предсказывает часть "
        "будущего market movement."
    )

    print(
        "Synthetic closing line "
        "улучшает opening Log Loss."
    )

else:

    print(
        "❌ Synthetic closing line "
        "не улучшила opening market."
    )


print()
print(
    "Сохранено:"
)

print(
    OUTPUT_FILE
)

print()
print(
    "Production-файлы НЕ изменены."
)
