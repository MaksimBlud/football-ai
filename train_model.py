
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


INPUT = "data/features_strength.csv"


print("Загружаю данные...")

df = pd.read_csv(INPUT)


# Убираем текстовые поля
df = df.drop(
    columns=[
        "home_team",
        "away_team"
    ]
)


# Цель модели
# HOME = 0
# DRAW = 1
# AWAY = 2

df["target"] = df["result"].map({
    "HOME": 0,
    "DRAW": 1,
    "AWAY": 2
})


# Удаляем ненужные колонки

FEATURES = [
    "home_last5_points",
    "away_last5_points",
    "form_difference"
]

df = df.dropna(subset=FEATURES + ["target"])

X = df[FEATURES]
y = df["target"]


print("Разделяю данные...")


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    shuffle=False
)


print("Обучаю модель...")


model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)


model.fit(
    X_train,
    y_train
)


predictions = model.predict(X_test)


accuracy = accuracy_score(
    y_test,
    predictions
)


print("Точность модели:", accuracy)


# сохраняем модель

import joblib

joblib.dump(
    model,
    "football_model.pkl"
)


print("Модель сохранена: football_model.pkl")