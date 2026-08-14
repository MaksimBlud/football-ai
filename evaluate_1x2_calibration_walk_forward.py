import numpy as np
import pandas as pd

from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)

INPUT = "data/1x2_oos_predictions.csv"

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

    return (
        probabilities
        / probabilities.sum(
            axis=1,
            keepdims=True,
        )
    )


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
        "confidence": float(
            probabilities.max(
                axis=1
            ).mean()
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

df = pd.read_csv(
    INPUT
)

seasons = sorted(
    df["season"].unique()
)

print(
    "OOS матчей:",
    len(df),
)

print(
    "Сезоны:",
    seasons,
)

rows = []

print()
print("=" * 95)
print("WALK-FORWARD CALIBRATION 1X2")
print("=" * 95)

# Первый OOS-сезон используется
# как начальная calibration history.
for test_season in seasons[1:]:
    train = df[
        df["season"] < test_season
    ].copy()

    test = df[
        df["season"] == test_season
    ].copy()

    if train.empty or test.empty:
        continue

    train_probabilities = (
        train[
            PROBABILITY_COLUMNS
        ]
        .to_numpy()
    )

    test_probabilities = (
        test[
            PROBABILITY_COLUMNS
        ]
        .to_numpy()
    )

    y_train = (
        train["actual_result"]
        .astype(int)
        .to_numpy()
    )

    y_test = (
        test["actual_result"]
        .astype(int)
        .to_numpy()
    )

    # RAW
    raw_probabilities = (
        test_probabilities
    )

    # TEMPERATURE
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

    # MULTINOMIAL
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

    methods = {
        "RAW": raw_probabilities,
        "TEMPERATURE": (
            temperature_probabilities
        ),
        "MULTINOMIAL": (
            multinomial_probabilities
        ),
    }

    output = []

    for method, probabilities in methods.items():
        result = metrics(
            y_test,
            probabilities,
        )

        rows.append({
            "season": test_season,
            "method": method,
            "matches": len(test),
            "temperature": (
                temperature
                if method == "TEMPERATURE"
                else np.nan
            ),
            **result,
        })

        output.append(
            f"{method}: "
            f"acc={result['accuracy']:.3f}, "
            f"LL={result['log_loss']:.4f}, "
            f"Brier={result['brier']:.4f}"
        )

    print(
        f"{test_season}: "
        + " | ".join(output)
    )


results = pd.DataFrame(
    rows
)

print()
print("=" * 95)
print("СРЕДНИЕ WALK-FORWARD РЕЗУЛЬТАТЫ")
print("=" * 95)

summary = (
    results
    .groupby("method")
    .agg(
        seasons=("season", "nunique"),
        matches=("matches", "sum"),
        accuracy=("accuracy", "mean"),
        log_loss=("log_loss", "mean"),
        brier=("brier", "mean"),
        confidence=("confidence", "mean"),
    )
    .sort_values("log_loss")
)

print(
    summary.to_string(
        float_format=lambda x: f"{x:.5f}"
    )
)

print()
print(
    "Лучший по log_loss:",
    summary.index[0],
)

print(
    "Лучший по Brier:",
    summary.sort_values(
        "brier"
    ).index[0],
)


OUTPUT = (
    "data/1x2_calibration_walk_forward_results.csv"
)

results.to_csv(
    OUTPUT,
    index=False,
)

print()
print(
    "Сохранено:",
    OUTPUT,
)

print(
    "Production 1x2_calibrator.pkl "
    "НЕ изменялся."
)
