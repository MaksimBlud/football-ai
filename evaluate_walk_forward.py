import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, log_loss


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
    "home_venue_matches",
    "away_venue_matches",
    "home_venue_win_rate",
    "away_venue_win_rate",
    "home_venue_goals_scored",
    "home_venue_goals_conceded",
    "away_venue_goals_scored",
    "away_venue_goals_conceded",
    "venue_win_rate_difference",
]


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

print("Сезоны:", seasons)
print()

results = []

for test_season in seasons[1:]:
    train = df[df["season"] < test_season]
    test = df[df["season"] == test_season]

    if train.empty or test.empty:
        continue

    X_train = train[FEATURES]
    y_train = train["target"]

    X_test = test[FEATURES]
    y_test = test["target"]

    model = XGBClassifier(
        n_estimators=500,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)

    model_accuracy = accuracy_score(
        y_test,
        predictions,
    )

    model_log_loss = log_loss(
        y_test,
        probabilities,
        labels=[0, 1, 2],
    )

    home_baseline = (y_test == 0).mean()

    odds_predictions = (
        test[
            [
                "home_odds",
                "draw_odds",
                "away_odds",
            ]
        ]
        .to_numpy()
        .argmin(axis=1)
    )

    odds_accuracy = accuracy_score(
        y_test,
        odds_predictions,
    )

    results.append({
        "season": test_season,
        "train_matches": len(train),
        "test_matches": len(test),
        "model_accuracy": model_accuracy,
        "odds_accuracy": odds_accuracy,
        "home_baseline": home_baseline,
        "log_loss": model_log_loss,
    })

    print(
        f"{test_season}: "
        f"модель={model_accuracy:.3f}, "
        f"букмекер={odds_accuracy:.3f}, "
        f"HOME={home_baseline:.3f}, "
        f"log_loss={model_log_loss:.3f}"
    )

results_df = pd.DataFrame(results)

print("\nСредние результаты:")

print(
    results_df[
        [
            "model_accuracy",
            "odds_accuracy",
            "home_baseline",
            "log_loss",
        ]
    ].mean()
)

results_df.to_csv(
    "data/walk_forward_results.csv",
    index=False,
)

print(
    "\nРезультаты сохранены: "
    "data/walk_forward_results.csv"
)
