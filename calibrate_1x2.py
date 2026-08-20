import numpy as np
import pandas as pd

from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)
from artifact_lifecycle import save_candidate


INPUT = "data/1x2_oos_predictions.csv"
OUTPUT = "data/1x2_calibration_results.csv"
CALIBRATION_SEASONS = [
    "2017/2018",
    "2018/2019",
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
]

TEST_SEASONS = [
    "2023/2024",
    "2024/2025",
    "2025/2026",
]


PROBABILITY_COLUMNS = [
    "home_probability",
    "draw_probability",
    "away_probability",
]


def clip_probabilities(probabilities):
    probabilities = np.clip(
        probabilities,
        1e-7,
        1 - 1e-7,
    )

    probabilities = (
        probabilities
        / probabilities.sum(
            axis=1,
            keepdims=True,
        )
    )

    return probabilities


def multiclass_brier(
    actual,
    probabilities,
):
    targets = np.eye(3)[actual]

    return np.mean(
        np.sum(
            (
                probabilities
                - targets
            ) ** 2,
            axis=1,
        )
    )


def metrics(
    actual,
    probabilities,
):
    probabilities = clip_probabilities(
        probabilities
    )

    predictions = np.argmax(
        probabilities,
        axis=1,
    )

    return {
        "accuracy": accuracy_score(
            actual,
            predictions,
        ),
        "log_loss": log_loss(
            actual,
            probabilities,
            labels=[0, 1, 2],
        ),
        "brier": multiclass_brier(
            actual,
            probabilities,
        ),
    }


def apply_temperature(
    probabilities,
    temperature,
):
    probabilities = clip_probabilities(
        probabilities
    )

    logits = np.log(
        probabilities
    )

    scaled = (
        logits
        / temperature
    )

    scaled = (
        scaled
        - scaled.max(
            axis=1,
            keepdims=True,
        )
    )

    exp_values = np.exp(
        scaled
    )

    return (
        exp_values
        / exp_values.sum(
            axis=1,
            keepdims=True,
        )
    )


def fit_temperature(
    probabilities,
    actual,
):
    def objective(temperature):
        calibrated = apply_temperature(
            probabilities,
            temperature,
        )

        return log_loss(
            actual,
            calibrated,
            labels=[0, 1, 2],
        )

    result = minimize_scalar(
        objective,
        bounds=(0.2, 5.0),
        method="bounded",
    )

    return float(result.x)


print("Загружаю OOS 1X2 прогнозы...")

df = pd.read_csv(INPUT)

train_df = df[
    df["season"].isin(
        CALIBRATION_SEASONS
    )
].copy()

test_df = df[
    df["season"].isin(
        TEST_SEASONS
    )
].copy()


print(
    "Для калибровки:",
    len(train_df),
)

print(
    "Для честной проверки:",
    len(test_df),
)

print(
    "Тестовые сезоны:",
    TEST_SEASONS,
)


train_probabilities = (
    train_df[
        PROBABILITY_COLUMNS
    ].to_numpy()
)

test_probabilities = (
    test_df[
        PROBABILITY_COLUMNS
    ].to_numpy()
)

y_train = (
    train_df["actual_result"]
    .astype(int)
    .to_numpy()
)

y_test = (
    test_df["actual_result"]
    .astype(int)
    .to_numpy()
)


# ============================================================
# RAW
# ============================================================

raw_metrics = metrics(
    y_test,
    test_probabilities,
)


# ============================================================
# TEMPERATURE SCALING
# ============================================================

temperature = fit_temperature(
    train_probabilities,
    y_train,
)

temperature_probabilities = (
    apply_temperature(
        test_probabilities,
        temperature,
    )
)

temperature_metrics = metrics(
    y_test,
    temperature_probabilities,
)


# ============================================================
# MULTINOMIAL LOGISTIC CALIBRATION
# ============================================================

train_log_probabilities = np.log(
    clip_probabilities(
        train_probabilities
    )
)

test_log_probabilities = np.log(
    clip_probabilities(
        test_probabilities
    )
)

multinomial = LogisticRegression(
    max_iter=5000,
    random_state=42,
)

multinomial.fit(
    train_log_probabilities,
    y_train,
)

multinomial_probabilities = (
    multinomial.predict_proba(
        test_log_probabilities
    )
)

multinomial_metrics = metrics(
    y_test,
    multinomial_probabilities,
)


candidates = [
    (
        "RAW",
        raw_metrics,
    ),
    (
        "TEMPERATURE",
        temperature_metrics,
    ),
    (
        "MULTINOMIAL",
        multinomial_metrics,
    ),
]


print()
print("=" * 76)
print("КАЛИБРОВКА 1X2")
print("=" * 76)

for name, result in candidates:
    print(
        f"{name:12s} | "
        f"accuracy={result['accuracy']:.4f} | "
        f"log_loss={result['log_loss']:.4f} | "
        f"Brier={result['brier']:.4f}"
    )


best_name, best_metrics = min(
    candidates,
    key=lambda item: item[1]["log_loss"],
)

print()
print(
    "Лучший по log_loss:",
    best_name,
)

print(
    "Temperature:",
    f"{temperature:.4f}",
)


results = []

for name, result in candidates:
    results.append({
        "method": name,
        "accuracy": (
            result["accuracy"]
        ),
        "log_loss": (
            result["log_loss"]
        ),
        "brier": (
            result["brier"]
        ),
        "selected": (
            name == best_name
        ),
    })


pd.DataFrame(
    results
).to_csv(
    OUTPUT,
    index=False,
)


# ============================================================
# ОБУЧАЕМ ФИНАЛЬНЫЙ КАЛИБРАТОР НА ВСЕХ OOS ДАННЫХ
# ============================================================

all_probabilities = (
    df[
        PROBABILITY_COLUMNS
    ].to_numpy()
)

all_targets = (
    df["actual_result"]
    .astype(int)
    .to_numpy()
)


if best_name == "TEMPERATURE":
    final_temperature = (
        fit_temperature(
            all_probabilities,
            all_targets,
        )
    )

    calibrator = {
        "method": "TEMPERATURE",
        "temperature": (
            final_temperature
        ),
    }

elif best_name == "MULTINOMIAL":
    final_model = LogisticRegression(
        max_iter=5000,
        random_state=42,
    )

    final_model.fit(
        np.log(
            clip_probabilities(
                all_probabilities
            )
        ),
        all_targets,
    )

    calibrator = {
        "method": "MULTINOMIAL",
        "model": final_model,
    }

else:
    calibrator = {
        "method": "RAW",
    }


calibrator_path, manifest_path = save_candidate(
    calibrator,
    "1x2_calibrator.pkl",
    __file__,
    [INPUT],
    "1x2_probability_calibrator",
    PROBABILITY_COLUMNS,
    {"method": best_name, "calibration_seasons": CALIBRATION_SEASONS},
)


# ============================================================
# ПРОВЕРЯЕМ УВЕРЕННОСТЬ RAW И ЛУЧШЕГО МЕТОДА
# ============================================================

if best_name == "TEMPERATURE":
    best_test_probabilities = (
        temperature_probabilities
    )

elif best_name == "MULTINOMIAL":
    best_test_probabilities = (
        multinomial_probabilities
    )

else:
    best_test_probabilities = (
        test_probabilities
    )


raw_confidence = (
    test_probabilities.max(
        axis=1
    )
)

calibrated_confidence = (
    best_test_probabilities.max(
        axis=1
    )
)

raw_predictions = (
    test_probabilities.argmax(
        axis=1
    )
)

calibrated_predictions = (
    best_test_probabilities.argmax(
        axis=1
    )
)


print()
print("=" * 76)
print("ПРОВЕРКА УРОВНЕЙ УВЕРЕННОСТИ")
print("=" * 76)

for threshold in [
    0.50,
    0.60,
    0.70,
    0.80,
]:
    raw_mask = (
        raw_confidence >= threshold
    )

    calibrated_mask = (
        calibrated_confidence
        >= threshold
    )

    if raw_mask.sum() > 0:
        raw_hit = (
            raw_predictions[raw_mask]
            == y_test[raw_mask]
        ).mean()

        print(
            f"RAW >= {threshold:.0%}: "
            f"матчей={raw_mask.sum():4d} | "
            f"hit={raw_hit:.1%} | "
            f"avg_conf="
            f"{raw_confidence[raw_mask].mean():.1%}"
        )

    if calibrated_mask.sum() > 0:
        calibrated_hit = (
            calibrated_predictions[
                calibrated_mask
            ]
            == y_test[
                calibrated_mask
            ]
        ).mean()

        print(
            f"CAL >= {threshold:.0%}: "
            f"матчей={calibrated_mask.sum():4d} | "
            f"hit={calibrated_hit:.1%} | "
            f"avg_conf="
            f"{calibrated_confidence[calibrated_mask].mean():.1%}"
        )

    print()


print("=" * 76)
print("ИТОГ")
print("=" * 76)

print(
    "Выбран метод:",
    best_name,
)

print(
    "Калибратор сохранён:",
    calibrator_path,
)

print("Manifest saved:", manifest_path)

print(
    "Метрики сохранены:",
    OUTPUT,
)
