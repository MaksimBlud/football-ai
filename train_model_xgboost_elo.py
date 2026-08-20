import argparse
from datetime import datetime, UTC
from pathlib import Path

import joblib
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report


INPUT = "data/features_with_elo.csv"

PRODUCTION_MODEL_PATH = Path(
    "football_model_xgboost_elo.pkl"
)

CANDIDATE_DIR = Path(
    "artifacts/candidates"
)


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


parser = argparse.ArgumentParser()

parser.add_argument(
    "--production",
    action="store_true",
    help=(
        "Явно разрешить запись поверх production model. "
        "Без этого флага training сохраняет candidate artifact."
    ),
)

args = parser.parse_args()

if args.production:
    model_path = PRODUCTION_MODEL_PATH
    print(
        "⚠️ PRODUCTION MODE: модель будет записана в",
        model_path,
    )
else:
    CANDIDATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%d_%H%M%S"
    )

    model_path = (
        CANDIDATE_DIR
        / f"football_model_xgboost_elo_{timestamp}.pkl"
    )

    print(
        "Candidate mode. Production model не изменяется."
    )
    print(
        "Candidate artifact:",
        model_path,
    )


print("Загружаю данные...")

df = pd.read_csv(INPUT)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2
})

df = df.dropna(subset=FEATURES + ["target"])

X = df[FEATURES]
y = df["target"]

test_size = int(len(df) * 0.2)

X_train = X.iloc[:-test_size]
X_test = X.iloc[-test_size:]

y_train = y.iloc[:-test_size]
y_test = y.iloc[-test_size:]

print("Матчей:", len(df))
print("Для обучения:", len(X_train))
print("Для проверки:", len(X_test))

print("Обучаю модель...")

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
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
baseline_accuracy = (y_test == 0).mean()

print("Точность модели:", accuracy)
print("Базовый прогноз HOME:", baseline_accuracy)

print("\nОтчёт:")
print(
    classification_report(
        y_test,
        predictions,
        labels=[0, 1, 2],
        target_names=["HOME", "DRAW", "AWAY"],
        zero_division=0
    )
)

joblib.dump(model, model_path)

print("Модель сохранена:", model_path)

if not args.production:
    print(
        "Production model НЕ изменена:",
        PRODUCTION_MODEL_PATH,
    )
