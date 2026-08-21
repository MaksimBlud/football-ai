from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)

from model_utils import FEATURES


ROOT = Path(__file__).resolve().parent

DATA_FILE = ROOT / "data" / "features_with_elo.csv"

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "nested_walk_forward_xgb_results.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


# ============================================================
# КАНДИДАТЫ
# ============================================================

CANDIDATES = {
    "baseline": {
        "n_estimators": 300,
        "max_depth": 3,
        "learning_rate": 0.02,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },

    "depth_2": {
        "n_estimators": 300,
        "max_depth": 2,
        "learning_rate": 0.02,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },

    "lr_001": {
        "n_estimators": 300,
        "max_depth": 3,
        "learning_rate": 0.01,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },

    "depth2_lr001": {
        "n_estimators": 300,
        "max_depth": 2,
        "learning_rate": 0.01,
        "min_child_weight": 1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },
}


# ============================================================
# DATA
# ============================================================

print("Загружаю данные...")

df = pd.read_csv(DATA_FILE)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})

required = FEATURES + [
    "season",
    "target",
    "home_odds",
    "draw_odds",
    "away_odds",
]

df = df.dropna(
    subset=required
).copy()

seasons = sorted(
    df["season"].unique()
)

print("Матчей:", len(df))
print("Сезоны:", seasons)


def train_predict(train, test, params):
    X_train = train[FEATURES]
    y_train = train["target"]

    X_test = test[FEATURES]

    model = XGBClassifier(
        **params,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    proba = model.predict_proba(
        X_test
    )

    row_sums = proba.sum(
        axis=1,
        keepdims=True,
    )

    if np.any(row_sums <= 0):
        raise ValueError(
            "Некорректная сумма вероятностей."
        )

    # Переводим в float64 и нормализуем вероятности
    # для стабильного расчёта Log Loss.
    proba = proba.astype(np.float64)
    proba = proba / proba.sum(
        axis=1,
        keepdims=True,
    )

    pred = np.argmax(
        proba,
        axis=1,
    )

    return pred, proba


def evaluate_candidate(
    train_seasons,
    candidate_params,
):
    """
    Внутренний walk-forward только внутри прошлых сезонов.

    Возвращаем средний log loss по всем внутренним
    validation матчам.
    """

    inner_true = []
    inner_proba = []

    # Нужны минимум два сезона:
    # один train + один validation.
    if len(train_seasons) < 2:
        return None

    for j in range(
        1,
        len(train_seasons),
    ):
        inner_train_seasons = (
            train_seasons[:j]
        )

        validation_season = (
            train_seasons[j]
        )

        inner_train = df[
            df["season"].isin(
                inner_train_seasons
            )
        ].copy()

        validation = df[
            df["season"]
            == validation_season
        ].copy()

        if (
            inner_train.empty
            or validation.empty
        ):
            continue

        _, proba = train_predict(
            inner_train,
            validation,
            candidate_params,
        )

        inner_true.extend(
            validation[
                "target"
            ]
            .to_numpy(dtype=int)
            .tolist()
        )

        inner_proba.extend(
            proba.tolist()
        )

    if not inner_true:
        return None

    inner_true = np.array(
        inner_true,
        dtype=int,
    )

    inner_proba = np.array(
        inner_proba,
    )

    score = log_loss(
        inner_true,
        inner_proba,
        labels=[0, 1, 2],
    )

    return float(score)


# ============================================================
# OUTER WALK-FORWARD
# ============================================================

rows = []

all_true = []
all_selected_pred = []
all_selected_proba = []

all_baseline_pred = []
all_baseline_proba = []


print()
print("=" * 100)
print("NESTED WALK-FORWARD XGBOOST")
print("=" * 100)


# Для честного nested WF первый usable test —
# 2022/23:
#
# 2019/20 train
# 2020/21 inner validation
# 2021/22 уже может использоваться в дальнейшем,
# и т.д.
#
# Начинаем с index=2, чтобы до test было
# минимум два сезона.

for i in range(2, len(seasons)):

    test_season = seasons[i]

    past_seasons = seasons[:i]

    test = df[
        df["season"]
        == test_season
    ].copy()

    if test.empty:
        continue

    print()
    print("-" * 100)
    print(
        f"OUTER TEST: {test_season}"
    )
    print(
        "Доступные прошлые сезоны:",
        past_seasons,
    )

    candidate_scores = {}

    for name, params in CANDIDATES.items():

        score = evaluate_candidate(
            past_seasons,
            params,
        )

        if score is None:
            continue

        candidate_scores[name] = score

        print(
            f"{name:<20} "
            f"inner LogLoss={score:.6f}"
        )

    if not candidate_scores:
        raise RuntimeError(
            "Нет результатов внутренней проверки."
        )

    selected_name = min(
        candidate_scores,
        key=candidate_scores.get,
    )

    selected_params = CANDIDATES[
        selected_name
    ]

    print(
        "SELECTED:",
        selected_name,
    )

    # --------------------------------------------------------
    # Обучаем выбранную модель на ВСЕХ прошлых сезонах
    # --------------------------------------------------------

    outer_train = df[
        df["season"].isin(
            past_seasons
        )
    ].copy()

    selected_pred, selected_proba = (
        train_predict(
            outer_train,
            test,
            selected_params,
        )
    )

    # Одновременно считаем production baseline
    baseline_pred, baseline_proba = (
        train_predict(
            outer_train,
            test,
            CANDIDATES["baseline"],
        )
    )

    y_test = test[
        "target"
    ].to_numpy(dtype=int)

    selected_acc = accuracy_score(
        y_test,
        selected_pred,
    )

    selected_ll = log_loss(
        y_test,
        selected_proba,
        labels=[0, 1, 2],
    )

    baseline_acc = accuracy_score(
        y_test,
        baseline_pred,
    )

    baseline_ll = log_loss(
        y_test,
        baseline_proba,
        labels=[0, 1, 2],
    )

    print(
        f"SELECTED OUTER: "
        f"ACC={selected_acc:.4f} | "
        f"LL={selected_ll:.4f}"
    )

    print(
        f"BASELINE OUTER: "
        f"ACC={baseline_acc:.4f} | "
        f"LL={baseline_ll:.4f}"
    )

    rows.append({
        "season": test_season,
        "selected_model": selected_name,
        "selected_inner_logloss":
            candidate_scores[selected_name],
        "selected_accuracy":
            selected_acc,
        "selected_logloss":
            selected_ll,
        "baseline_accuracy":
            baseline_acc,
        "baseline_logloss":
            baseline_ll,
        "accuracy_change":
            selected_acc - baseline_acc,
        "logloss_change":
            selected_ll - baseline_ll,
    })

    all_true.extend(
        y_test.tolist()
    )

    all_selected_pred.extend(
        selected_pred.tolist()
    )

    all_selected_proba.extend(
        selected_proba.tolist()
    )

    all_baseline_pred.extend(
        baseline_pred.tolist()
    )

    all_baseline_proba.extend(
        baseline_proba.tolist()
    )


# ============================================================
# OVERALL
# ============================================================

all_true = np.array(
    all_true,
    dtype=int,
)

all_selected_pred = np.array(
    all_selected_pred,
    dtype=int,
)

all_selected_proba = np.array(
    all_selected_proba,
)

all_baseline_pred = np.array(
    all_baseline_pred,
    dtype=int,
)

all_baseline_proba = np.array(
    all_baseline_proba,
)


selected_accuracy = accuracy_score(
    all_true,
    all_selected_pred,
)

selected_logloss = log_loss(
    all_true,
    all_selected_proba,
    labels=[0, 1, 2],
)

baseline_accuracy = accuracy_score(
    all_true,
    all_baseline_pred,
)

baseline_logloss = log_loss(
    all_true,
    all_baseline_proba,
    labels=[0, 1, 2],
)


results = pd.DataFrame(rows)

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 100)
print("NESTED OUT-OF-SAMPLE OVERALL")
print("=" * 100)

print(
    f"SELECTED: "
    f"Accuracy={selected_accuracy:.4f} | "
    f"LogLoss={selected_logloss:.4f}"
)

print(
    f"BASELINE: "
    f"Accuracy={baseline_accuracy:.4f} | "
    f"LogLoss={baseline_logloss:.4f}"
)

print()
print(
    "Δ Accuracy:",
    round(
        selected_accuracy
        - baseline_accuracy,
        4,
    ),
)

print(
    "Δ LogLoss:",
    round(
        selected_logloss
        - baseline_logloss,
        4,
    ),
)


print()
print("=" * 100)
print("MODEL SELECTION COUNTS")
print("=" * 100)

print(
    results[
        "selected_model"
    ]
    .value_counts()
    .to_string()
)


print()
print("=" * 100)
print("PER-SEASON RESULTS")
print("=" * 100)

print(
    results.to_string(
        index=False
    )
)

print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
