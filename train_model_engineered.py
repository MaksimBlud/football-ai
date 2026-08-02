import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


INPUT = "data/features_engineered.csv"
MODEL_PATH = "football_model_engineered.pkl"


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
    "home_corners_last5",
    "away_corners_last5",
    "home_yellow_last5",
    "away_yellow_last5"
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

print("Матчей:", len(df))
print("Признаков:", len(FEATURES))
print("Разделяю данные...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    shuffle=False
)

print("Обучаю модель...")

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced",
    min_samples_leaf=3
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
