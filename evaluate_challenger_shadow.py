"""
Historical shadow evaluation for 1X2 prediction sources.

Compares:
- BOOKMAKER
- NO_ODDS_AI
- CHALLENGER_V0

CHALLENGER_V0 intentionally equals BOOKMAKER.

NO_ODDS_AI uses the current frozen production model and calibrator.
Its historical metrics are diagnostic only and are NOT walk-forward/OOS
promotion evidence.

This script is research-only and does not modify production artifacts.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    log_loss,
)

from model_utils import FEATURES
from predict_match_no_odds import (
    calibrate_probabilities as production_calibrate_probabilities,
)


DATA = Path("data/features_with_elo.csv")
NO_ODDS_MODEL = Path("football_model_no_odds.pkl")
OUTPUT = Path(
    "experiments/challenger_shadow_evaluation.csv"
)


NO_ODDS_FEATURES = [
    feature
    for feature in FEATURES
    if feature not in {
        "home_odds",
        "draw_odds",
        "away_odds",
    }
]


def normalize(probabilities):
    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    probabilities = np.clip(
        probabilities,
        1e-12,
        None,
    )

    return (
        probabilities
        / probabilities.sum(
            axis=1,
            keepdims=True,
        )
    )


def bookmaker_probabilities(frame):
    odds = frame[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].to_numpy(dtype=float)

    return normalize(
        1.0 / odds
    )


def brier_mean_per_class(y_true, probabilities):
    onehot = np.eye(3)[
        np.asarray(
            y_true,
            dtype=int,
        )
    ]

    return float(
        np.mean(
            (
                probabilities
                - onehot
            ) ** 2
        )
    )



def metrics(y, probabilities):
    prediction = np.argmax(
        probabilities,
        axis=1,
    )

    return {
        "accuracy":
            accuracy_score(
                y,
                prediction,
            ),

        "logloss":
            log_loss(
                y,
                probabilities,
                labels=[0, 1, 2],
            ),

        "brier":
            brier_mean_per_class(
                y,
                probabilities,
            ),

        "draw_predictions":
            int(
                (
                    prediction == 1
                ).sum()
            ),

        "draw_correct":
            int(
                (
                    (prediction == 1)
                    & (y == 1)
                ).sum()
            ),

        "draw_actual":
            int(
                (
                    y == 1
                ).sum()
            ),
    }


if not DATA.exists():
    raise FileNotFoundError(DATA)

if not NO_ODDS_MODEL.exists():
    raise FileNotFoundError(
        NO_ODDS_MODEL
    )

df = pd.read_csv(DATA)

df["target"] = df["result"].map({
    "H": 0,
    "D": 1,
    "A": 2,
})

required = (
    NO_ODDS_FEATURES
    + [
        "home_odds",
        "draw_odds",
        "away_odds",
        "target",
        "season",
    ]
)

df = df.dropna(
    subset=required
).copy()

df["target"] = (
    df["target"]
    .astype(int)
)

model = joblib.load(
    NO_ODDS_MODEL
)


seasons = sorted(
    df["season"].unique()
)

print("rows:", len(df))
print("seasons:", seasons)
print(
    "evaluation mode:",
    "FROZEN_ARTIFACT_DIAGNOSTIC",
)
print(
    "WARNING: NO_ODDS_AI historical metrics "
    "are not walk-forward/OOS promotion evidence."
)
print(
    "no-odds features:",
    len(NO_ODDS_FEATURES),
)

rows = []

all_y = []
all_book = []
all_ai = []
all_challenger = []


for season in seasons:

    test = df[
        df["season"] == season
    ].copy()

    if test.empty:
        continue

    y = test[
        "target"
    ].to_numpy(dtype=int)

    p_book = bookmaker_probabilities(
        test
    )

    raw_ai = model.predict_proba(
        test[NO_ODDS_FEATURES]
    )

    p_ai = np.asarray(
        [
            production_calibrate_probabilities(
                row
            )
            for row in raw_ai
        ],
        dtype=float,
    )

    # Challenger v0 intentionally equals market.
    p_challenger = p_book.copy()

    m_book = metrics(
        y,
        p_book,
    )

    m_ai = metrics(
        y,
        p_ai,
    )

    m_challenger = metrics(
        y,
        p_challenger,
    )

    print()
    print("=" * 100)
    print(season)
    print("=" * 100)

    for name, m in [
        ("BOOKMAKER", m_book),
        ("NO_ODDS_AI", m_ai),
        ("CHALLENGER_V0", m_challenger),
    ]:
        draw_precision = (
            m["draw_correct"]
            / m["draw_predictions"]
            if m["draw_predictions"]
            else 0.0
        )

        draw_recall = (
            m["draw_correct"]
            / m["draw_actual"]
            if m["draw_actual"]
            else 0.0
        )

        print(
            f"{name:14s} "
            f"ACC={m['accuracy']:.4f} | "
            f"LL={m['logloss']:.6f} | "
            f"BRIER={m['brier']:.6f} | "
            f"DRAW={m['draw_correct']}/"
            f"{m['draw_predictions']}/"
            f"{m['draw_actual']} | "
            f"P={draw_precision:.3f} | "
            f"R={draw_recall:.3f}"
        )

    rows.append({
        "evaluation_mode":
            "FROZEN_ARTIFACT_DIAGNOSTIC",

        "season": season,

        "book_accuracy":
            m_book["accuracy"],

        "book_logloss":
            m_book["logloss"],

        "book_brier":
            m_book["brier"],

        "ai_accuracy":
            m_ai["accuracy"],

        "ai_logloss":
            m_ai["logloss"],

        "ai_brier":
            m_ai["brier"],

        "challenger_accuracy":
            m_challenger["accuracy"],

        "challenger_logloss":
            m_challenger["logloss"],

        "challenger_brier":
            m_challenger["brier"],

        "ai_ll_edge_vs_book":
            m_book["logloss"]
            - m_ai["logloss"],

        "challenger_ll_edge_vs_book":
            m_book["logloss"]
            - m_challenger["logloss"],
    })

    all_y.extend(
        y.tolist()
    )

    all_book.extend(
        p_book.tolist()
    )

    all_ai.extend(
        p_ai.tolist()
    )

    all_challenger.extend(
        p_challenger.tolist()
    )


all_y = np.asarray(
    all_y,
    dtype=int,
)

all_book = np.asarray(
    all_book,
    dtype=float,
)

all_ai = np.asarray(
    all_ai,
    dtype=float,
)

all_challenger = np.asarray(
    all_challenger,
    dtype=float,
)


print()
print("=" * 100)
print("OVERALL")
print("=" * 100)

overall_results = {}

for name, probabilities in [
    ("BOOKMAKER", all_book),
    ("NO_ODDS_AI", all_ai),
    ("CHALLENGER_V0", all_challenger),
]:
    m = metrics(
        all_y,
        probabilities,
    )

    overall_results[name] = m

    print(
        f"{name:14s} "
        f"ACC={m['accuracy']:.6f} | "
        f"LL={m['logloss']:.6f} | "
        f"BRIER={m['brier']:.6f} | "
        f"DRAW={m['draw_correct']}/"
        f"{m['draw_predictions']}/"
        f"{m['draw_actual']}"
    )


book = overall_results[
    "BOOKMAKER"
]

ai = overall_results[
    "NO_ODDS_AI"
]

challenger = overall_results[
    "CHALLENGER_V0"
]

print()
print("AI EDGE vs BOOK:")
print(
    "Log Loss:",
    f"{book['logloss'] - ai['logloss']:+.6f}"
)
print(
    "Brier:",
    f"{book['brier'] - ai['brier']:+.6f}"
)

print()
print("CHALLENGER V0 EDGE vs BOOK:")
print(
    "Log Loss:",
    f"{book['logloss'] - challenger['logloss']:+.6f}"
)
print(
    "Brier:",
    f"{book['brier'] - challenger['brier']:+.6f}"
)

assert np.allclose(
    all_book,
    all_challenger,
    rtol=0.0,
    atol=0.0,
)

print()
print(
    "PASS: Challenger v0 equals bookmaker "
    "probabilities exactly."
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

result_df = pd.DataFrame(
    rows
)

result_df.to_csv(
    OUTPUT,
    index=False,
)

print()
print(
    "Saved:",
    OUTPUT,
)
