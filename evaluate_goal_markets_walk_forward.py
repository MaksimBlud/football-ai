import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
    mean_absolute_error,
)
from xgboost import XGBRegressor

from poisson_utils import calculate_markets


INPUT = "data/features_with_elo.csv"
OUTPUT = "data/goal_markets_walk_forward_results.csv"


FEATURES = [
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


MODEL_PARAMS = {
    "n_estimators": 300,
    "max_depth": 3,
    "learning_rate": 0.02,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "random_state": 42,
}


print("Загружаю данные...")

df = pd.read_csv(INPUT)

required_columns = (
    FEATURES
    + [
        "season",
        "match_date",
        "home_goals",
        "away_goals",
    ]
)

df = df.dropna(
    subset=required_columns
).copy()

df["match_date"] = pd.to_datetime(
    df["match_date"],
    errors="coerce",
)

df = df.dropna(
    subset=["match_date"]
)

df = df.sort_values(
    [
        "match_date",
        "match_time",
    ]
).reset_index(drop=True)


df["actual_over_2_5"] = (
    (
        df["home_goals"]
        + df["away_goals"]
    ) > 2.5
).astype(int)

df["actual_btts"] = (
    (df["home_goals"] > 0)
    & (df["away_goals"] > 0)
).astype(int)


seasons = list(
    df["season"].dropna().unique()
)

print("Сезоны:", seasons)
print()


results = []


for test_index in range(1, len(seasons)):
    test_season = seasons[test_index]

    train_seasons = seasons[:test_index]

    train_df = df[
        df["season"].isin(train_seasons)
    ].copy()

    test_df = df[
        df["season"] == test_season
    ].copy()

    if train_df.empty or test_df.empty:
        continue

    X_train = train_df[FEATURES]
    X_test = test_df[FEATURES]

    y_home_train = train_df["home_goals"]
    y_away_train = train_df["away_goals"]

    y_home_test = test_df["home_goals"]
    y_away_test = test_df["away_goals"]


    home_model = XGBRegressor(
        **MODEL_PARAMS
    )

    away_model = XGBRegressor(
        **MODEL_PARAMS
    )

    home_model.fit(
        X_train,
        y_home_train,
    )

    away_model.fit(
        X_train,
        y_away_train,
    )


    home_pred = home_model.predict(
        X_test
    )

    away_pred = away_model.predict(
        X_test
    )

    home_pred = np.clip(
        home_pred,
        0,
        None,
    )

    away_pred = np.clip(
        away_pred,
        0,
        None,
    )


    over_probabilities = []
    btts_probabilities = []

    for expected_home, expected_away in zip(
        home_pred,
        away_pred,
    ):
        markets = calculate_markets(
            expected_home_goals=float(
                expected_home
            ),
            expected_away_goals=float(
                expected_away
            ),
        )

        over_probabilities.append(
            markets[
                "over_2_5_probability"
            ]
        )

        btts_probabilities.append(
            markets[
                "btts_yes_probability"
            ]
        )


    over_probabilities = np.array(
        over_probabilities
    )

    btts_probabilities = np.array(
        btts_probabilities
    )

    actual_over = (
        test_df["actual_over_2_5"]
        .to_numpy()
    )

    actual_btts = (
        test_df["actual_btts"]
        .to_numpy()
    )


    over_predictions = (
        over_probabilities >= 0.50
    ).astype(int)

    btts_predictions = (
        btts_probabilities >= 0.50
    ).astype(int)


    home_mae = mean_absolute_error(
        y_home_test,
        home_pred,
    )

    away_mae = mean_absolute_error(
        y_away_test,
        away_pred,
    )


    over_accuracy = accuracy_score(
        actual_over,
        over_predictions,
    )

    btts_accuracy = accuracy_score(
        actual_btts,
        btts_predictions,
    )


    over_brier = brier_score_loss(
        actual_over,
        over_probabilities,
    )

    btts_brier = brier_score_loss(
        actual_btts,
        btts_probabilities,
    )


    epsilon = 1e-7

    over_clipped = np.clip(
        over_probabilities,
        epsilon,
        1 - epsilon,
    )

    btts_clipped = np.clip(
        btts_probabilities,
        epsilon,
        1 - epsilon,
    )

    over_log_loss = log_loss(
        actual_over,
        np.column_stack(
            [
                1 - over_clipped,
                over_clipped,
            ]
        ),
        labels=[0, 1],
    )

    btts_log_loss = log_loss(
        actual_btts,
        np.column_stack(
            [
                1 - btts_clipped,
                btts_clipped,
            ]
        ),
        labels=[0, 1],
    )


    train_over_rate = (
        train_df["actual_over_2_5"]
        .mean()
    )

    train_btts_rate = (
        train_df["actual_btts"]
        .mean()
    )


    baseline_over_class = int(
        train_over_rate >= 0.50
    )

    baseline_btts_class = int(
        train_btts_rate >= 0.50
    )


    baseline_over_accuracy = (
        actual_over
        == baseline_over_class
    ).mean()

    baseline_btts_accuracy = (
        actual_btts
        == baseline_btts_class
    ).mean()


    baseline_over_brier = (
        (
            actual_over
            - train_over_rate
        ) ** 2
    ).mean()

    baseline_btts_brier = (
        (
            actual_btts
            - train_btts_rate
        ) ** 2
    ).mean()


    results.append({
        "season": test_season,
        "matches": len(test_df),

        "home_goals_mae": home_mae,
        "away_goals_mae": away_mae,

        "over_2_5_accuracy": (
            over_accuracy
        ),
        "over_2_5_baseline_accuracy": (
            baseline_over_accuracy
        ),
        "over_2_5_brier": (
            over_brier
        ),
        "over_2_5_baseline_brier": (
            baseline_over_brier
        ),
        "over_2_5_log_loss": (
            over_log_loss
        ),

        "btts_accuracy": (
            btts_accuracy
        ),
        "btts_baseline_accuracy": (
            baseline_btts_accuracy
        ),
        "btts_brier": (
            btts_brier
        ),
        "btts_baseline_brier": (
            baseline_btts_brier
        ),
        "btts_log_loss": (
            btts_log_loss
        ),
    })


    print(
        f"{test_season}: "
        f"home_MAE={home_mae:.3f}, "
        f"away_MAE={away_mae:.3f}, "
        f"ТБ2.5={over_accuracy:.3f}, "
        f"BTTS={btts_accuracy:.3f}, "
        f"ТБ_Brier={over_brier:.3f}, "
        f"BTTS_Brier={btts_brier:.3f}"
    )


results_df = pd.DataFrame(results)

if results_df.empty:
    raise RuntimeError(
        "Walk-forward результаты не созданы."
    )


results_df.to_csv(
    OUTPUT,
    index=False,
)


numeric_columns = [
    column
    for column in results_df.columns
    if column not in (
        "season",
        "matches",
    )
]


print()
print("Средние результаты:")
print(
    results_df[
        numeric_columns
    ].mean()
)

print()
print("Сравнение с baseline:")

print(
    "ТБ 2.5 accuracy:",
    f"{results_df['over_2_5_accuracy'].mean():.3f}",
    "| baseline:",
    f"{results_df['over_2_5_baseline_accuracy'].mean():.3f}",
)

print(
    "ТБ 2.5 Brier:",
    f"{results_df['over_2_5_brier'].mean():.3f}",
    "| baseline:",
    f"{results_df['over_2_5_baseline_brier'].mean():.3f}",
)

print(
    "BTTS accuracy:",
    f"{results_df['btts_accuracy'].mean():.3f}",
    "| baseline:",
    f"{results_df['btts_baseline_accuracy'].mean():.3f}",
)

print(
    "BTTS Brier:",
    f"{results_df['btts_brier'].mean():.3f}",
    "| baseline:",
    f"{results_df['btts_baseline_brier'].mean():.3f}",
)

print()
print(
    "Результаты сохранены:",
    OUTPUT,
)
