from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss


ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "historical_market_movement_dataset.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "closing_edge_segments.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


df = pd.read_csv(DATA_FILE)

df["target"] = pd.to_numeric(
    df["target"],
    errors="coerce",
)

required = [
    "target",
    "open_p_home",
    "open_p_draw",
    "open_p_away",
    "close_p_home",
    "close_p_draw",
    "close_p_away",
    "elo_difference",
    "form_difference",
    "max_abs_move",
]

df = df.dropna(
    subset=required
).copy()

df["target"] = df["target"].astype(int)


def ll_for_group(group):
    if len(group) < 30:
        return None

    y = group["target"].to_numpy(dtype=int)

    open_p = group[
        [
            "open_p_home",
            "open_p_draw",
            "open_p_away",
        ]
    ].to_numpy(dtype=float)

    close_p = group[
        [
            "close_p_home",
            "close_p_draw",
            "close_p_away",
        ]
    ].to_numpy(dtype=float)

    open_ll = log_loss(
        y,
        open_p,
        labels=[0, 1, 2],
    )

    close_ll = log_loss(
        y,
        close_p,
        labels=[0, 1, 2],
    )

    return {
        "matches": len(group),
        "open_logloss": open_ll,
        "close_logloss": close_ll,
        "closing_edge": open_ll - close_ll,
        "avg_abs_move": group["max_abs_move"].mean(),
    }


rows = []


def add_segments(name, series):
    temp = df.copy()
    temp["_segment"] = series

    for segment, group in temp.groupby(
        "_segment",
        dropna=False,
    ):
        if pd.isna(segment):
            continue

        metrics = ll_for_group(group)

        if metrics is None:
            continue

        rows.append({
            "segment_type": name,
            "segment": str(segment),
            **metrics,
        })


print("=" * 120)
print("CLOSING EDGE — SEGMENT ANALYSIS")
print("=" * 120)

# ============================================================
# 1. OPENING FAVORITE TYPE
# ============================================================

open_probs = df[
    [
        "open_p_home",
        "open_p_draw",
        "open_p_away",
    ]
].to_numpy(dtype=float)

favorite = np.argmax(
    open_probs,
    axis=1,
)

favorite_map = {
    0: "HOME_FAVORITE",
    1: "DRAW_HIGHEST",
    2: "AWAY_FAVORITE",
}

add_segments(
    "opening_favorite",
    pd.Series(favorite).map(
        favorite_map
    ),
)


# ============================================================
# 2. FAVORITE STRENGTH
# ============================================================

max_open = open_probs.max(axis=1)

add_segments(
    "favorite_strength",
    pd.cut(
        max_open,
        bins=[
            0.0,
            0.40,
            0.50,
            0.60,
            0.70,
            0.80,
            1.0,
        ],
        labels=[
            "<40%",
            "40-50%",
            "50-60%",
            "60-70%",
            "70-80%",
            "80%+",
        ],
        include_lowest=True,
    ),
)


# ============================================================
# 3. DRAW PROBABILITY
# ============================================================

add_segments(
    "open_draw_probability",
    pd.cut(
        df["open_p_draw"],
        bins=[
            0.0,
            0.18,
            0.21,
            0.24,
            0.27,
            0.30,
            1.0,
        ],
        labels=[
            "<18%",
            "18-21%",
            "21-24%",
            "24-27%",
            "27-30%",
            "30%+",
        ],
        include_lowest=True,
    ),
)


# ============================================================
# 4. ELO DIFFERENCE
# ============================================================

add_segments(
    "elo_difference",
    pd.cut(
        df["elo_difference"],
        bins=[
            -9999,
            -200,
            -100,
            -50,
            0,
            50,
            100,
            200,
            9999,
        ],
        labels=[
            "<-200",
            "-200:-100",
            "-100:-50",
            "-50:0",
            "0:50",
            "50:100",
            "100:200",
            "200+",
        ],
    ),
)


# ============================================================
# 5. FORM DIFFERENCE
# ============================================================

add_segments(
    "form_difference",
    pd.cut(
        df["form_difference"],
        bins=[
            -999,
            -8,
            -4,
            -2,
            0,
            2,
            4,
            8,
            999,
        ],
        labels=[
            "<-8",
            "-8:-4",
            "-4:-2",
            "-2:0",
            "0:2",
            "2:4",
            "4:8",
            "8+",
        ],
    ),
)


# ============================================================
# 6. MARKET VS ELO DISAGREEMENT
#
# Сравниваем направление opening favorite
# с направлением Elo.
# ============================================================

elo_pick = np.where(
    df["elo_difference"] > 25,
    0,
    np.where(
        df["elo_difference"] < -25,
        2,
        1,
    ),
)

market_pick = favorite

agreement = np.where(
    market_pick == elo_pick,
    "AGREE",
    "DISAGREE",
)

add_segments(
    "market_elo_agreement",
    agreement,
)


# ============================================================
# 7. ELO DISAGREEMENT STRENGTH
# ============================================================

market_home_edge = (
    df["open_p_home"]
    - df["open_p_away"]
)

elo_sign = np.sign(
    df["elo_difference"]
)

market_sign = np.sign(
    market_home_edge
)

disagree_strength = (
    np.abs(df["elo_difference"])
)

label = np.where(
    elo_sign == market_sign,
    "AGREE",
    np.where(
        disagree_strength >= 150,
        "DISAGREE_150+",
        np.where(
            disagree_strength >= 75,
            "DISAGREE_75_150",
            "DISAGREE_<75",
        ),
    ),
)

add_segments(
    "market_elo_disagreement_strength",
    label,
)


# ============================================================
# 8. ACTUAL MOVEMENT MAGNITUDE
#
# Это не pre-match deployable feature.
# Только диагностический анализ:
# где closing реально менялся сильнее.
# ============================================================

add_segments(
    "actual_move_magnitude",
    pd.cut(
        df["max_abs_move"],
        bins=[
            0.0,
            0.01,
            0.02,
            0.03,
            0.05,
            0.08,
            1.0,
        ],
        labels=[
            "<1%",
            "1-2%",
            "2-3%",
            "3-5%",
            "5-8%",
            "8%+",
        ],
        include_lowest=True,
    ),
)


# ============================================================
# 9. SEASON
# ============================================================

add_segments(
    "season",
    df["season"],
)


result = pd.DataFrame(
    rows
)

result = result.sort_values(
    [
        "closing_edge",
        "matches",
    ],
    ascending=[
        False,
        False,
    ],
).reset_index(drop=True)

result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 120)
print("TOP 30 SEGMENTS BY CLOSING EDGE")
print("=" * 120)

print(
    result[
        [
            "segment_type",
            "segment",
            "matches",
            "open_logloss",
            "close_logloss",
            "closing_edge",
            "avg_abs_move",
        ]
    ]
    .head(30)
    .to_string(index=False)
)


print()
print("=" * 120)
print("BOTTOM 20 SEGMENTS")
print("=" * 120)

print(
    result[
        [
            "segment_type",
            "segment",
            "matches",
            "open_logloss",
            "close_logloss",
            "closing_edge",
            "avg_abs_move",
        ]
    ]
    .tail(20)
    .to_string(index=False)
)


print()
print("=" * 120)
print("KEY PRE-MATCH SEGMENTS")
print("=" * 120)

deployable = result[
    ~result["segment_type"].isin(
        [
            "actual_move_magnitude",
            "season",
        ]
    )
].copy()

print(
    deployable[
        [
            "segment_type",
            "segment",
            "matches",
            "closing_edge",
            "avg_abs_move",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
