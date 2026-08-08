import joblib
import numpy as np
import pandas as pd

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    log_loss,
)


INPUT = "data/goal_markets_oos_predictions.csv"

OVER_CALIBRATOR_PATH = "over_2_5_calibrator.pkl"
BTTS_CALIBRATOR_PATH = "btts_calibrator.pkl"

META_PATH = "data/goal_market_calibration_results.csv"


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


def clip_probabilities(values):
    return np.clip(
        values,
        1e-6,
        1 - 1e-6,
    )


def calculate_metrics(
    actual,
    probabilities,
):
    probabilities = clip_probabilities(
        probabilities
    )

    return {
        "brier": brier_score_loss(
            actual,
            probabilities,
        ),
        "log_loss": log_loss(
            actual,
            np.column_stack([
                1 - probabilities,
                probabilities,
            ]),
            labels=[0, 1],
        ),
    }


def fit_and_test_market(
    market_name,
    probability_column,
    actual_column,
    train_df,
    test_df,
):
    x_train = (
        train_df[probability_column]
        .to_numpy()
    )

    y_train = (
        train_df[actual_column]
        .to_numpy()
    )

    x_test = (
        test_df[probability_column]
        .to_numpy()
    )

    y_test = (
        test_df[actual_column]
        .to_numpy()
    )


    # RAW
    raw_metrics = calculate_metrics(
        y_test,
        x_test,
    )


    # SIGMOID / PLATT
    sigmoid = LogisticRegression(
        random_state=42,
    )

    sigmoid.fit(
        x_train.reshape(-1, 1),
        y_train,
    )

    sigmoid_probabilities = (
        sigmoid.predict_proba(
            x_test.reshape(-1, 1)
        )[:, 1]
    )

    sigmoid_metrics = calculate_metrics(
        y_test,
        sigmoid_probabilities,
    )


    # ISOTONIC
    isotonic = IsotonicRegression(
        out_of_bounds="clip",
    )

    isotonic.fit(
        x_train,
        y_train,
    )

    isotonic_probabilities = isotonic.predict(
        x_test
    )

    isotonic_metrics = calculate_metrics(
        y_test,
        isotonic_probabilities,
    )


    candidates = [
        (
            "RAW",
            raw_metrics,
            None,
        ),
        (
            "SIGMOID",
            sigmoid_metrics,
            sigmoid,
        ),
        (
            "ISOTONIC",
            isotonic_metrics,
            isotonic,
        ),
    ]

    best = min(
        candidates,
        key=lambda item: item[1]["brier"],
    )

    print()
    print(market_name)
    print("-" * 70)

    for name, metrics, _ in candidates:
        print(
            f"{name:8s} | "
            f"Brier={metrics['brier']:.5f} | "
            f"log_loss={metrics['log_loss']:.5f}"
        )

    print(
        "Лучший по Brier:",
        best[0],
    )


    rows = []

    for name, metrics, _ in candidates:
        rows.append({
            "market": market_name,
            "method": name,
            "brier": metrics["brier"],
            "log_loss": metrics["log_loss"],
            "selected": (
                name == best[0]
            ),
        })


    # После честного выбора метода на последних
    # сезонах обучаем выбранный калибратор уже
    # на всех имеющихся OOS прогнозах.
    return (
        best[0],
        rows,
    )


def fit_final_calibrator(
    method,
    probability_column,
    actual_column,
    df,
):
    x = df[
        probability_column
    ].to_numpy()

    y = df[
        actual_column
    ].to_numpy()

    if method == "SIGMOID":
        calibrator = LogisticRegression(
            random_state=42,
        )

        calibrator.fit(
            x.reshape(-1, 1),
            y,
        )

        return {
            "method": "SIGMOID",
            "model": calibrator,
        }

    if method == "ISOTONIC":
        calibrator = IsotonicRegression(
            out_of_bounds="clip",
        )

        calibrator.fit(
            x,
            y,
        )

        return {
            "method": "ISOTONIC",
            "model": calibrator,
        }

    return {
        "method": "RAW",
        "model": None,
    }


print("Загружаю OOS-прогнозы...")

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


over_method, over_rows = (
    fit_and_test_market(
        market_name="OVER_2_5",
        probability_column=(
            "over_probability"
        ),
        actual_column="actual_over",
        train_df=train_df,
        test_df=test_df,
    )
)


btts_method, btts_rows = (
    fit_and_test_market(
        market_name="BTTS_YES",
        probability_column=(
            "btts_probability"
        ),
        actual_column="actual_btts",
        train_df=train_df,
        test_df=test_df,
    )
)


all_rows = (
    over_rows
    + btts_rows
)

results_df = pd.DataFrame(
    all_rows
)

results_df.to_csv(
    META_PATH,
    index=False,
)


over_final = fit_final_calibrator(
    method=over_method,
    probability_column=(
        "over_probability"
    ),
    actual_column="actual_over",
    df=df,
)

btts_final = fit_final_calibrator(
    method=btts_method,
    probability_column=(
        "btts_probability"
    ),
    actual_column="actual_btts",
    df=df,
)


joblib.dump(
    over_final,
    OVER_CALIBRATOR_PATH,
)

joblib.dump(
    btts_final,
    BTTS_CALIBRATOR_PATH,
)


print()
print("=" * 70)
print("ИТОГ")
print("=" * 70)

print(
    "ТБ 2.5:",
    over_method,
)

print(
    "BTTS:",
    btts_method,
)

print()
print(
    "Сохранено:",
    OVER_CALIBRATOR_PATH,
)

print(
    "Сохранено:",
    BTTS_CALIBRATOR_PATH,
)

print(
    "Метрики:",
    META_PATH,
)
