import joblib
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report


INPUT = "data/features_with_elo.csv"
MODEL_PATH = "football_model_xgboost_elo.pkl"


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
]


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
    n_estimators=500,
    max_depth=4,
    learning_rate=0.03,
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

joblib.dump(model, MODEL_PATH)

print("Модель сохранена:", MODEL_PATH)
