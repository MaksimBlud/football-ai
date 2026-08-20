from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
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
    / "market_movement_predictability.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


FEATURES = [
    "open_p_home",
    "open_p_draw",
    "open_p_away",

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


XGB_PARAMS = {
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

SEASONS = sorted(
    df["season"].unique()
)


def synthetic_close(open_probs, moves):
    p = open_probs + moves

    p = np.clip(
        p,
        1e-6,
        None,
    )

    return (
        p
        / p.sum(
            axis=1,
            keepdims=True,
        )
    )


rows = []


print("=" * 120)
print("MARKET MOVEMENT — PREDICTABILITY TEST")
print("=" * 120)


for i in range(
    1,
    len(SEASONS),
):

    test_season = SEASONS[i]

    train = df[
        df["season"].isin(
            SEASONS[:i]
        )
    ].copy()

    test = df[
        df["season"]
        == test_season
    ].copy()


    X_train = train[FEATURES]
    X_test = test[FEATURES]

    actual_moves = test[
        TARGETS
    ].to_numpy(dtype=float)

    open_probs = test[
        [
            "open_p_home",
            "open_p_draw",
            "open_p_away",
        ]
    ].to_numpy(dtype=float)

    real_close = test[
        [
            "close_p_home",
            "close_p_draw",
            "close_p_away",
        ]
    ].to_numpy(dtype=float)

    y = test[
        "target"
    ].to_numpy(dtype=int)


    # ========================================================
    # ZERO MOVEMENT
    # ========================================================

    zero_moves = np.zeros_like(
        actual_moves
    )


    # ========================================================
    # HISTORICAL MEAN MOVEMENT
    # ========================================================

    mean_move = train[
        TARGETS
    ].mean().to_numpy(dtype=float)

    mean_moves = np.tile(
        mean_move,
        (
            len(test),
            1,
        ),
    )


    # ========================================================
    # RIDGE
    # ========================================================

    ridge_preds = []

    for target in TARGETS:

        model = make_pipeline(
            StandardScaler(),
            Ridge(
                alpha=10.0
            ),
        )

        model.fit(
            X_train,
            train[target],
        )

        ridge_preds.append(
            model.predict(
                X_test
            )
        )

    ridge_moves = np.column_stack(
        ridge_preds
    )


    # ========================================================
    # XGBOOST
    # ========================================================

    xgb_preds = []

    for target in TARGETS:

        model = XGBRegressor(
            **XGB_PARAMS
        )

        model.fit(
            X_train,
            train[target],
        )

        xgb_preds.append(
            model.predict(
                X_test
            )
        )

    xgb_moves = np.column_stack(
        xgb_preds
    )


    models = {
        "zero":
            zero_moves,

        "historical_mean":
            mean_moves,

        "ridge":
            ridge_moves,

        "xgboost":
            xgb_moves,
    }


    open_ll = log_loss(
        y,
        open_probs,
        labels=[0, 1, 2],
    )

    real_close_ll = log_loss(
        y,
        real_close,
        labels=[0, 1, 2],
    )


    print()
    print("-" * 120)
    print(test_season)
    print("-" * 120)

    print(
        f"OPEN LL={open_ll:.6f} | "
        f"REAL CLOSE LL={real_close_ll:.6f}"
    )


    for name, pred_moves in models.items():

        pred_close = synthetic_close(
            open_probs,
            pred_moves,
        )

        pred_ll = log_loss(
            y,
            pred_close,
            labels=[0, 1, 2],
        )

        mae = mean_absolute_error(
            actual_moves,
            pred_moves,
        )

        rmse = (
            mean_squared_error(
                actual_moves,
                pred_moves,
            )
            ** 0.5
        )


        # Correlation per class
        correlations = []

        for j in range(3):

            a = actual_moves[:, j]
            p = pred_moves[:, j]

            if (
                np.std(a) > 0
                and np.std(p) > 0
            ):
                corr = np.corrcoef(
                    a,
                    p,
                )[0, 1]
            else:
                corr = np.nan

            correlations.append(
                corr
            )


        direction_acc = np.mean(
            np.sign(actual_moves)
            ==
            np.sign(pred_moves)
        )


        rows.append({
            "season":
                test_season,

            "model":
                name,

            "matches":
                len(test),

            "movement_mae":
                mae,

            "movement_rmse":
                rmse,

            "corr_home":
                correlations[0],

            "corr_draw":
                correlations[1],

            "corr_away":
                correlations[2],

            "direction_accuracy":
                direction_acc,

            "open_logloss":
                open_ll,

            "predicted_logloss":
                pred_ll,

            "edge_vs_open":
                open_ll - pred_ll,

            "real_close_logloss":
                real_close_ll,
        })


        print(
            f"{name:<16} | "
            f"MAE={mae:.6f} | "
            f"RMSE={rmse:.6f} | "
            f"DIR={direction_acc:.4f} | "
            f"LL={pred_ll:.6f} | "
            f"EDGE={open_ll - pred_ll:+.6f}"
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
print("OVERALL WEIGHTED COMPARISON")
print("=" * 120)


summary = []

for model, g in result.groupby(
    "model"
):

    weights = g[
        "matches"
    ].to_numpy()

    def weighted(col):
        values = g[
            col
        ].to_numpy(dtype=float)

        mask = np.isfinite(
            values
        )

        if not mask.any():
            return np.nan

        valid_weights = weights[mask]

        if valid_weights.sum() <= 0:
            return np.nan

        return np.average(
            values[mask],
            weights=valid_weights,
        )

    summary.append({
        "model":
            model,

        "movement_mae":
            weighted(
                "movement_mae"
            ),

        "movement_rmse":
            weighted(
                "movement_rmse"
            ),

        "corr_home":
            weighted(
                "corr_home"
            ),

        "corr_draw":
            weighted(
                "corr_draw"
            ),

        "corr_away":
            weighted(
                "corr_away"
            ),

        "direction_accuracy":
            weighted(
                "direction_accuracy"
            ),

        "predicted_logloss":
            weighted(
                "predicted_logloss"
            ),

        "edge_vs_open":
            weighted(
                "edge_vs_open"
            ),
    })


summary = pd.DataFrame(
    summary
).sort_values(
    "predicted_logloss"
)


print(
    summary.to_string(
        index=False
    )
)


print()
print("=" * 120)
print("VERDICT")
print("=" * 120)

best = summary.iloc[0]

print(
    "Лучший predictor:",
    best["model"],
)

print(
    "Edge vs opening:",
    f"{best['edge_vs_open']:+.6f}",
)


if (
    best["model"] != "zero"
    and best["edge_vs_open"] > 0
):
    print(
        "✅ В opening-time features "
        "есть предсказуемая часть будущего движения."
    )
else:
    print(
        "❌ Текущие opening-time features "
        "не предсказывают будущий market movement "
        "лучше нулевого движения."
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
