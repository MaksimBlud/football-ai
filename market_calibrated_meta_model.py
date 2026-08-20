from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "experiments"
    / "challenger_walk_forward_predictions.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "market_calibrated_meta_model_results.csv"
)

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)


FIXED_ALPHAS = [
    0.05,
    0.10,
    0.20,
]


df = pd.read_csv(INPUT_FILE)


required = [
    "season",
    "actual",

    "p_home",
    "p_draw",
    "p_away",

    "home_odds",
    "draw_odds",
    "away_odds",
]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:
    raise SystemExit(
        f"❌ Missing columns: {missing}"
    )


# ============================================================
# NORMALIZE MODEL
# ============================================================

model_p = df[
    [
        "p_home",
        "p_draw",
        "p_away",
    ]
].to_numpy(dtype=np.float64)

model_p = (
    model_p
    / model_p.sum(
        axis=1,
        keepdims=True,
    )
)


# ============================================================
# FAIR BOOKMAKER PROBABILITIES
# ============================================================

odds = df[
    [
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
].to_numpy(dtype=np.float64)

raw_book = (
    1.0
    / odds
)

book_p = (
    raw_book
    / raw_book.sum(
        axis=1,
        keepdims=True,
    )
)


df["model_h"] = model_p[:, 0]
df["model_d"] = model_p[:, 1]
df["model_a"] = model_p[:, 2]

df["book_h"] = book_p[:, 0]
df["book_d"] = book_p[:, 1]
df["book_a"] = book_p[:, 2]


# ============================================================
# DISAGREEMENT FEATURES
# ============================================================

df["edge_h"] = (
    df["model_h"]
    - df["book_h"]
)

df["edge_d"] = (
    df["model_d"]
    - df["book_d"]
)

df["edge_a"] = (
    df["model_a"]
    - df["book_a"]
)


df["abs_edge_h"] = (
    df["edge_h"].abs()
)

df["abs_edge_d"] = (
    df["edge_d"].abs()
)

df["abs_edge_a"] = (
    df["edge_a"].abs()
)


df["max_abs_edge"] = df[
    [
        "abs_edge_h",
        "abs_edge_d",
        "abs_edge_a",
    ]
].max(axis=1)


# ============================================================
# META FEATURES
# ============================================================

META_FEATURES = [
    "book_h",
    "book_d",
    "book_a",

    "model_h",
    "model_d",
    "model_a",

    "edge_h",
    "edge_d",
    "edge_a",

    "abs_edge_h",
    "abs_edge_d",
    "abs_edge_a",

    "max_abs_edge",
]


SEASONS = sorted(
    df["season"]
    .dropna()
    .unique()
)


print("=" * 125)
print("MARKET-CALIBRATED META MODEL — WALK FORWARD")
print("=" * 125)

print(
    "Матчей:",
    len(df),
)

print(
    "Сезоны:",
    SEASONS,
)


rows = []

all_y = []

all_book = []
all_model = []
all_meta = []

all_fixed = {
    alpha: []
    for alpha in FIXED_ALPHAS
}


# ============================================================
# WALK FORWARD
# ============================================================

for i in range(
    1,
    len(SEASONS),
):

    test_season = (
        SEASONS[i]
    )

    train_seasons = (
        SEASONS[:i]
    )


    train = df[
        df["season"].isin(
            train_seasons
        )
    ].copy()

    test = df[
        df["season"]
        == test_season
    ].copy()


    X_train = train[
        META_FEATURES
    ].to_numpy(dtype=float)

    X_test = test[
        META_FEATURES
    ].to_numpy(dtype=float)

    y_train = train[
        "actual"
    ].to_numpy(dtype=int)

    y_test = test[
        "actual"
    ].to_numpy(dtype=int)


    # ========================================================
    # META MODEL
    # ========================================================

    meta = LogisticRegression(
        solver="lbfgs",
        C=0.1,
        max_iter=5000,
        random_state=42,
    )

    meta.fit(
        X_train,
        y_train,
    )

    meta_p = meta.predict_proba(
        X_test
    )

    meta_p = (
        meta_p
        / meta_p.sum(
            axis=1,
            keepdims=True,
        )
    )


    test_book = test[
        [
            "book_h",
            "book_d",
            "book_a",
        ]
    ].to_numpy(dtype=float)

    test_model = test[
        [
            "model_h",
            "model_d",
            "model_a",
        ]
    ].to_numpy(dtype=float)


    # ========================================================
    # BASELINES
    # ========================================================

    book_ll = log_loss(
        y_test,
        test_book,
        labels=[0, 1, 2],
    )

    model_ll = log_loss(
        y_test,
        test_model,
        labels=[0, 1, 2],
    )

    meta_ll = log_loss(
        y_test,
        meta_p,
        labels=[0, 1, 2],
    )


    book_acc = accuracy_score(
        y_test,
        np.argmax(
            test_book,
            axis=1,
        ),
    )

    model_acc = accuracy_score(
        y_test,
        np.argmax(
            test_model,
            axis=1,
        ),
    )

    meta_acc = accuracy_score(
        y_test,
        np.argmax(
            meta_p,
            axis=1,
        ),
    )


    print()
    print("-" * 125)
    print(test_season)
    print("-" * 125)

    print(
        f"BOOK  | ACC={book_acc:.4f} | "
        f"LL={book_ll:.6f}"
    )

    print(
        f"MODEL | ACC={model_acc:.4f} | "
        f"LL={model_ll:.6f}"
    )

    print(
        f"META  | ACC={meta_acc:.4f} | "
        f"LL={meta_ll:.6f} | "
        f"EDGE vs BOOK="
        f"{book_ll - meta_ll:+.6f}"
    )


    row = {
        "season":
            test_season,

        "matches":
            len(test),

        "book_accuracy":
            book_acc,

        "model_accuracy":
            model_acc,

        "meta_accuracy":
            meta_acc,

        "book_logloss":
            book_ll,

        "model_logloss":
            model_ll,

        "meta_logloss":
            meta_ll,

        "meta_edge_vs_book":
            book_ll
            - meta_ll,
    }


    # ========================================================
    # FIXED BLENDS
    # ========================================================

    for alpha in FIXED_ALPHAS:

        blend = (
            alpha
            * test_model
            +
            (
                1.0
                - alpha
            )
            * test_book
        )

        blend = (
            blend
            / blend.sum(
                axis=1,
                keepdims=True,
            )
        )

        blend_ll = log_loss(
            y_test,
            blend,
            labels=[0, 1, 2],
        )

        blend_acc = accuracy_score(
            y_test,
            np.argmax(
                blend,
                axis=1,
            ),
        )

        print(
            f"BLEND {alpha:.0%} MODEL | "
            f"ACC={blend_acc:.4f} | "
            f"LL={blend_ll:.6f} | "
            f"EDGE={book_ll - blend_ll:+.6f}"
        )


        key = (
            f"blend_{int(alpha*100)}"
        )

        row[
            f"{key}_logloss"
        ] = blend_ll

        row[
            f"{key}_edge"
        ] = (
            book_ll
            - blend_ll
        )

        all_fixed[
            alpha
        ].extend(
            blend.tolist()
        )


    rows.append(
        row
    )


    all_y.extend(
        y_test.tolist()
    )

    all_book.extend(
        test_book.tolist()
    )

    all_model.extend(
        test_model.tolist()
    )

    all_meta.extend(
        meta_p.tolist()
    )


# ============================================================
# OVERALL
# ============================================================

all_y = np.asarray(
    all_y,
    dtype=int,
)

all_book = np.asarray(
    all_book,
    dtype=float,
)

all_model = np.asarray(
    all_model,
    dtype=float,
)

all_meta = np.asarray(
    all_meta,
    dtype=float,
)


book_ll = log_loss(
    all_y,
    all_book,
    labels=[0, 1, 2],
)

model_ll = log_loss(
    all_y,
    all_model,
    labels=[0, 1, 2],
)

meta_ll = log_loss(
    all_y,
    all_meta,
    labels=[0, 1, 2],
)


print()
print("=" * 125)
print("OVERALL OUT-OF-SAMPLE RESULT")
print("=" * 125)

print(
    "OOS матчей:",
    len(all_y),
)

print()

print(
    f"BOOK LogLoss:  "
    f"{book_ll:.6f}"
)

print(
    f"MODEL LogLoss: "
    f"{model_ll:.6f}"
)

print(
    f"META LogLoss:  "
    f"{meta_ll:.6f}"
)

print(
    f"META EDGE:     "
    f"{book_ll - meta_ll:+.6f}"
)


# ============================================================
# OVERALL FIXED BLENDS
# ============================================================

blend_results = []

print()
print("=" * 125)
print("FIXED BLEND OVERALL")
print("=" * 125)


for alpha in FIXED_ALPHAS:

    arr = np.asarray(
        all_fixed[alpha],
        dtype=float,
    )

    ll = log_loss(
        all_y,
        arr,
        labels=[0, 1, 2],
    )

    edge = (
        book_ll
        - ll
    )

    blend_results.append(
        (
            alpha,
            ll,
            edge,
        )
    )

    print(
        f"MODEL {alpha:.0%} + "
        f"BOOK {1-alpha:.0%} | "
        f"LL={ll:.6f} | "
        f"EDGE={edge:+.6f}"
    )


# ============================================================
# SEASON CONSISTENCY
# ============================================================

result = pd.DataFrame(
    rows
)

positive_meta = int(
    (
        result[
            "meta_edge_vs_book"
        ] > 0
    ).sum()
)


print()
print("=" * 125)
print("SEASON CONSISTENCY")
print("=" * 125)

print(
    "META positive seasons:",
    positive_meta,
    "/",
    len(result),
)


for alpha in FIXED_ALPHAS:

    col = (
        f"blend_{int(alpha*100)}_edge"
    )

    positive = int(
        (
            result[
                col
            ] > 0
        ).sum()
    )

    print(
        f"Blend {alpha:.0%} model "
        f"positive seasons: "
        f"{positive}/{len(result)}"
    )


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 125)
print("VERDICT")
print("=" * 125)


best_fixed = max(
    blend_results,
    key=lambda x: x[2],
)


candidates = [
    (
        "meta",
        meta_ll,
        book_ll - meta_ll,
        positive_meta,
    ),

    (
        f"fixed_blend_{best_fixed[0]:.0%}",
        best_fixed[1],
        best_fixed[2],
        int(
            (
                result[
                    f"blend_{int(best_fixed[0]*100)}_edge"
                ] > 0
            ).sum()
        ),
    ),
]


best = max(
    candidates,
    key=lambda x: x[2],
)


print(
    "Лучший calibrated candidate:",
    best[0],
)

print(
    "LogLoss:",
    f"{best[1]:.6f}",
)

print(
    "Edge vs bookmaker:",
    f"{best[2]:+.6f}",
)

print(
    "Positive seasons:",
    best[3],
    "/",
    len(result),
)


if (
    best[2] > 0
    and best[3]
    >= len(result) - 1
):
    print(
        "⚠️ Найден потенциальный "
        "market-calibrated OOS signal."
    )

    print(
        "Следующий этап — nested "
        "selection/calibration test."
    )

else:
    print(
        "❌ Market calibration "
        "не улучшила bookmaker "
        "достаточно устойчиво."
    )


print()
print(
    "Сохранено:"
)

print(
    OUTPUT_FILE
)

print()
print(
    "Production-файлы НЕ изменены."
)
