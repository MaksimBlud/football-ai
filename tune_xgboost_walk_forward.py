import itertools

import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
from xgboost import XGBClassifier


INPUT = "data/features_with_elo.csv"

FEATURES = [
    "home_odds",
    "draw_odds",
    "away_odds",
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

PARAM_GRID = {
    "n_estimators": [300, 500],
    "max_depth": [2, 3, 4],
    "learning_rate": [0.02, 0.05],
    "min_child_weight": [1, 5],
}


print("Загружаю данные...")

df = pd.read_csv(INPUT)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})

df["match_date"] = pd.to_datetime(
    df["match_date"],
    errors="coerce",
)

df = df.dropna(
    subset=FEATURES + [
        "target",
        "season",
        "match_date",
    ]
)

df = df.sort_values(
    ["match_date", "match_time"]
).reset_index(drop=True)

seasons = sorted(df["season"].unique())

# Первый доступный сезон используется только для обучения.
test_seasons = seasons[1:]

parameter_names = list(PARAM_GRID)
parameter_combinations = list(
    itertools.product(
        *[
            PARAM_GRID[name]
            for name in parameter_names
        ]
    )
)

print("Сезоны проверки:", test_seasons)
print("Комбинаций параметров:", len(parameter_combinations))
print()

all_results = []

for number, combination in enumerate(
    parameter_combinations,
    start=1,
):
    params = dict(
        zip(parameter_names, combination)
    )

    season_accuracies = []
    season_log_losses = []

    print(
        f"[{number}/{len(parameter_combinations)}] "
        f"{params}"
    )

    for test_season in test_seasons:
        train = df[df["season"] < test_season]
        test = df[df["season"] == test_season]

        if train.empty or test.empty:
            continue

        X_train = train[FEATURES]
        y_train = train["target"]

        X_test = test[FEATURES]
        y_test = test["target"]

        model = XGBClassifier(
            **params,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=2,
        )

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)

        season_accuracies.append(
            accuracy_score(y_test, predictions)
        )

        season_log_losses.append(
            log_loss(
                y_test,
                probabilities,
                labels=[0, 1, 2],
            )
        )

    mean_accuracy = sum(season_accuracies) / len(
        season_accuracies
    )

    mean_log_loss = sum(season_log_losses) / len(
        season_log_losses
    )

    result = {
        **params,
        "mean_accuracy": mean_accuracy,
        "mean_log_loss": mean_log_loss,
    }

    all_results.append(result)

    print(
        f"Средняя accuracy: {mean_accuracy:.4f}; "
        f"log_loss: {mean_log_loss:.4f}\n"
    )

results_df = pd.DataFrame(all_results)

results_df = results_df.sort_values(
    ["mean_accuracy", "mean_log_loss"],
    ascending=[False, True],
).reset_index(drop=True)

results_df.to_csv(
    "data/xgboost_tuning_results.csv",
    index=False,
)

print("Лучшие 10 комбинаций:")
print(results_df.head(10).to_string(index=False))

print(
    "\nРезультаты сохранены: "
    "data/xgboost_tuning_results.csv"
)
