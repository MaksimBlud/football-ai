import joblib
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)
from xgboost import XGBRegressor


INPUT = "data/features_with_elo.csv"

HOME_MODEL_PATH = "home_goals_model_no_odds.pkl"
AWAY_MODEL_PATH = "away_goals_model_no_odds.pkl"

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


print("Загружаю данные...")

df = pd.read_csv(INPUT)

df = df.dropna(
    subset=FEATURES + [
        "home_goals",
        "away_goals",
    ]
)

X = df[FEATURES]

y_home = df["home_goals"]
y_away = df["away_goals"]

test_size = int(len(df) * 0.2)

X_train = X.iloc[:-test_size]
X_test = X.iloc[-test_size:]

y_home_train = y_home.iloc[:-test_size]
y_home_test = y_home.iloc[-test_size:]

y_away_train = y_away.iloc[:-test_size]
y_away_test = y_away.iloc[-test_size:]

print("Матчей:", len(df))
print("Для обучения:", len(X_train))
print("Для проверки:", len(X_test))

common_params = {
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

print("\nОбучаю модель голов хозяев...")

home_model = XGBRegressor(**common_params)
home_model.fit(X_train, y_home_train)

print("Обучаю модель голов гостей...")

away_model = XGBRegressor(**common_params)
away_model.fit(X_train, y_away_train)

home_predictions = home_model.predict(X_test)
away_predictions = away_model.predict(X_test)

# Число ожидаемых голов не должно быть отрицательным.
home_predictions = home_predictions.clip(min=0)
away_predictions = away_predictions.clip(min=0)

home_mae = mean_absolute_error(
    y_home_test,
    home_predictions,
)

away_mae = mean_absolute_error(
    y_away_test,
    away_predictions,
)

home_rmse = mean_squared_error(
    y_home_test,
    home_predictions,
) ** 0.5

away_rmse = mean_squared_error(
    y_away_test,
    away_predictions,
) ** 0.5

print("\nРезультаты:")

print(
    "Голы хозяев — "
    f"MAE: {home_mae:.4f}, "
    f"RMSE: {home_rmse:.4f}"
)

print(
    "Голы гостей — "
    f"MAE: {away_mae:.4f}, "
    f"RMSE: {away_rmse:.4f}"
)

baseline_home = y_home_train.mean()
baseline_away = y_away_train.mean()

baseline_home_mae = mean_absolute_error(
    y_home_test,
    [baseline_home] * len(y_home_test),
)

baseline_away_mae = mean_absolute_error(
    y_away_test,
    [baseline_away] * len(y_away_test),
)

print("\nБазовый прогноз средним количеством голов:")

print(
    "Хозяева — "
    f"{baseline_home:.3f} гола, "
    f"MAE: {baseline_home_mae:.4f}"
)

print(
    "Гости — "
    f"{baseline_away:.3f} гола, "
    f"MAE: {baseline_away_mae:.4f}"
)

joblib.dump(
    home_model,
    HOME_MODEL_PATH,
)

joblib.dump(
    away_model,
    AWAY_MODEL_PATH,
)

print("\nМодели сохранены:")
print(HOME_MODEL_PATH)
print(AWAY_MODEL_PATH)
