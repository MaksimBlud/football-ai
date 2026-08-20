import pandas as pd
import numpy as np

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    confusion_matrix,
    classification_report,
)

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
    subset=FEATURES + ["target", "season", "match_date"]
).copy()

df = df.sort_values(
    ["match_date", "match_time"]
).reset_index(drop=True)

seasons = sorted(df["season"].unique())

print("Сезоны:", seasons)
print("Матчей после фильтрации:", len(df))
print()

results = []

all_true = []
all_pred = []
all_proba = []

for test_season in seasons[1:]:
    train = df[df["season"] < test_season].copy()
    test = df[df["season"] == test_season].copy()

    if train.empty or test.empty:
        continue

    X_train = train[FEATURES]
    y_train = train["target"]

    X_test = test[FEATURES]
    y_test = test["target"]

    model = XGBClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.02,
        min_child_weight=1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)

    # Нормализуем вероятности HOME/DRAW/AWAY до точной суммы 1.0
    row_sums = proba.sum(axis=1, keepdims=True)

    if np.any(row_sums <= 0):
        raise ValueError("Обнаружена строка вероятностей с суммой <= 0.")

    proba = proba / row_sums

    model_accuracy = accuracy_score(y_test, pred)

    model_log_loss = log_loss(
        y_test,
        proba,
        labels=[0, 1, 2],
    )

    y_onehot = np.eye(3)[y_test.to_numpy(dtype=int)]

    multiclass_brier = np.mean(
        np.sum((proba - y_onehot) ** 2, axis=1)
    )

    home_baseline = (y_test == 0).mean()

    bookmaker_pred = (
        test[
            ["home_odds", "draw_odds", "away_odds"]
        ]
        .to_numpy()
        .argmin(axis=1)
    )

    bookmaker_accuracy = accuracy_score(
        y_test,
        bookmaker_pred,
    )

    draw_predictions = int((pred == 1).sum())
    draw_correct = int(((pred == 1) & (y_test.to_numpy() == 1)).sum())
    draw_actual = int((y_test == 1).sum())

    results.append({
        "season": test_season,
        "train_matches": len(train),
        "test_matches": len(test),
        "model_accuracy": model_accuracy,
        "bookmaker_accuracy": bookmaker_accuracy,
        "home_baseline": home_baseline,
        "log_loss": model_log_loss,
        "brier": multiclass_brier,
        "draw_actual": draw_actual,
        "draw_predictions": draw_predictions,
        "draw_correct": draw_correct,
    })

    all_true.extend(y_test.tolist())
    all_pred.extend(pred.tolist())
    all_proba.extend(proba.tolist())

    print(
        f"{test_season}: "
        f"model={model_accuracy:.4f} | "
        f"bookmaker={bookmaker_accuracy:.4f} | "
        f"HOME={home_baseline:.4f} | "
        f"logloss={model_log_loss:.4f} | "
        f"brier={multiclass_brier:.4f} | "
        f"DRAW pred={draw_predictions}/{len(test)} "
        f"(correct={draw_correct}/{draw_actual})"
    )

results_df = pd.DataFrame(results)

print("\n===== СРЕДНИЕ ПО СЕЗОНАМ =====")
print(
    results_df[
        [
            "model_accuracy",
            "bookmaker_accuracy",
            "home_baseline",
            "log_loss",
            "brier",
        ]
    ].mean().to_string()
)

print("\n===== ВЗВЕШЕННЫЕ ПО ВСЕМ TEST-МАТЧАМ =====")

all_true = np.array(all_true)
all_pred = np.array(all_pred)
all_proba = np.array(all_proba)

# Дополнительная страховка после объединения всех сезонов
overall_row_sums = all_proba.sum(axis=1, keepdims=True)

if np.any(overall_row_sums <= 0):
    raise ValueError("Обнаружена итоговая строка вероятностей с суммой <= 0.")

all_proba = all_proba / overall_row_sums

overall_accuracy = accuracy_score(
    all_true,
    all_pred,
)

overall_log_loss = log_loss(
    all_true,
    all_proba,
    labels=[0, 1, 2],
)

overall_onehot = np.eye(3)[all_true]

overall_brier = np.mean(
    np.sum((all_proba - overall_onehot) ** 2, axis=1)
)

print("Всего test матчей:", len(all_true))
print("Accuracy:", round(overall_accuracy, 4))
print("Log Loss:", round(overall_log_loss, 4))
print("Brier:", round(overall_brier, 4))

print("\nConfusion matrix:")
print(
    confusion_matrix(
        all_true,
        all_pred,
        labels=[0, 1, 2],
    )
)

print("\nClassification report:")
print(
    classification_report(
        all_true,
        all_pred,
        labels=[0, 1, 2],
        target_names=["HOME", "DRAW", "AWAY"],
        zero_division=0,
    )
)

print("Предсказаний классов:")
print(
    pd.Series(all_pred)
    .map({0: "HOME", 1: "DRAW", 2: "AWAY"})
    .value_counts()
    .to_string()
)

results_df.to_csv(
    "data/walk_forward_production_results.csv",
    index=False,
)

print(
    "\nСохранено: data/walk_forward_production_results.csv"
)
