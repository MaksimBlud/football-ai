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
    / "nested_closing_edge_segments.csv"
)

OUTPUT_FILE.parent.mkdir(exist_ok=True)


df = pd.read_csv(DATA_FILE)

df["target"] = pd.to_numeric(
    df["target"],
    errors="coerce",
)

required = [
    "target",
    "season",

    "open_p_home",
    "open_p_draw",
    "open_p_away",

    "close_p_home",
    "close_p_draw",
    "close_p_away",

    "elo_difference",
    "form_difference",
]

df = df.dropna(
    subset=required
).copy()

df["target"] = df[
    "target"
].astype(int)


SEASONS = sorted(
    df["season"].unique()
)


# ============================================================
# BUILD PRE-MATCH SEGMENT LABELS
#
# Никаких closing/movement данных здесь нет.
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

df["seg_opening_favorite"] = (
    pd.Series(
        favorite,
        index=df.index,
    )
    .map(favorite_map)
)


df["seg_favorite_strength"] = pd.cut(
    open_probs.max(axis=1),
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
).astype(str)


df["seg_draw_probability"] = pd.cut(
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
).astype(str)


df["seg_elo"] = pd.cut(
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
).astype(str)


df["seg_form"] = pd.cut(
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
).astype(str)


market_pick = favorite

elo_pick = np.where(
    df["elo_difference"] > 25,
    0,
    np.where(
        df["elo_difference"] < -25,
        2,
        1,
    ),
)

df["seg_market_elo"] = np.where(
    market_pick == elo_pick,
    "AGREE",
    "DISAGREE",
)


SEGMENT_COLUMNS = {
    "opening_favorite":
        "seg_opening_favorite",

    "favorite_strength":
        "seg_favorite_strength",

    "draw_probability":
        "seg_draw_probability",

    "elo_difference":
        "seg_elo",

    "form_difference":
        "seg_form",

    "market_elo_agreement":
        "seg_market_elo",
}


# ============================================================
# METRIC
# ============================================================

def calculate_edge(frame):

    if len(frame) == 0:
        return np.nan, np.nan, np.nan

    y = frame[
        "target"
    ].to_numpy(dtype=int)

    open_p = frame[
        [
            "open_p_home",
            "open_p_draw",
            "open_p_away",
        ]
    ].to_numpy(dtype=float)

    close_p = frame[
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

    return (
        open_ll,
        close_ll,
        open_ll - close_ll,
    )


# ============================================================
# NESTED WALK FORWARD
# ============================================================

MIN_TRAIN_MATCHES = 100
MIN_TEST_MATCHES = 20

rows = []


print("=" * 120)
print(
    "NESTED CLOSING EDGE SEGMENT TEST"
)
print("=" * 120)


for outer_i in range(
    2,
    len(SEASONS),
):

    test_season = (
        SEASONS[outer_i]
    )

    train_seasons = (
        SEASONS[:outer_i]
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


    candidates = []


    # ========================================================
    # SEGMENT SELECTION ON PAST ONLY
    # ========================================================

    for segment_type, col in (
        SEGMENT_COLUMNS.items()
    ):

        for segment_value, group in (
            train.groupby(col)
        ):

            if (
                segment_value == "nan"
                or len(group)
                < MIN_TRAIN_MATCHES
            ):
                continue


            open_ll, close_ll, edge = (
                calculate_edge(group)
            )


            candidates.append({
                "segment_type":
                    segment_type,

                "segment":
                    str(segment_value),

                "train_matches":
                    len(group),

                "train_open_ll":
                    open_ll,

                "train_close_ll":
                    close_ll,

                "train_edge":
                    edge,
            })


    candidates = pd.DataFrame(
        candidates
    )


    if candidates.empty:
        print(
            test_season,
            "— no candidates",
        )
        continue


    candidates = candidates.sort_values(
        [
            "train_edge",
            "train_matches",
        ],
        ascending=[
            False,
            False,
        ],
    )


    selected = candidates.iloc[0]

    segment_type = selected[
        "segment_type"
    ]

    segment_value = selected[
        "segment"
    ]

    col = SEGMENT_COLUMNS[
        segment_type
    ]


    outer = test[
        test[col].astype(str)
        == segment_value
    ].copy()


    print()
    print("-" * 120)

    print(
        "OUTER:",
        test_season,
    )

    print(
        "SELECTED:",
        segment_type,
        "=",
        segment_value,
    )

    print(
        f"TRAIN N={int(selected['train_matches'])} | "
        f"EDGE={selected['train_edge']:+.6f}"
    )


    if len(outer) < MIN_TEST_MATCHES:

        print(
            "OUTER N=",
            len(outer),
            "— слишком мало",
        )

        rows.append({
            "season":
                test_season,

            "segment_type":
                segment_type,

            "segment":
                segment_value,

            "train_matches":
                int(
                    selected[
                        "train_matches"
                    ]
                ),

            "train_edge":
                selected[
                    "train_edge"
                ],

            "test_matches":
                len(outer),

            "test_open_ll":
                np.nan,

            "test_close_ll":
                np.nan,

            "test_edge":
                np.nan,
        })

        continue


    open_ll, close_ll, edge = (
        calculate_edge(outer)
    )


    print(
        f"OUTER N={len(outer)}"
    )

    print(
        f"OPEN LL={open_ll:.6f}"
    )

    print(
        f"CLOSE LL={close_ll:.6f}"
    )

    print(
        f"OOS EDGE={edge:+.6f}"
    )


    rows.append({
        "season":
            test_season,

        "segment_type":
            segment_type,

        "segment":
            segment_value,

        "train_matches":
            int(
                selected[
                    "train_matches"
                ]
            ),

        "train_edge":
            selected[
                "train_edge"
            ],

        "test_matches":
            len(outer),

        "test_open_ll":
            open_ll,

        "test_close_ll":
            close_ll,

        "test_edge":
            edge,
    })


result = pd.DataFrame(
    rows
)

result.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# OVERALL TRUE OOS RESULT
# ============================================================

valid = result.dropna(
    subset=[
        "test_edge",
    ]
).copy()


print()
print("=" * 120)
print(
    "NESTED SEGMENT — FINAL OOS RESULT"
)
print("=" * 120)


if valid.empty:

    print(
        "❌ Нет валидных outer tests."
    )

else:

    total_matches = (
        valid[
            "test_matches"
        ].sum()
    )

    weighted_open = (
        (
            valid[
                "test_open_ll"
            ]
            * valid[
                "test_matches"
            ]
        ).sum()
        / total_matches
    )

    weighted_close = (
        (
            valid[
                "test_close_ll"
            ]
            * valid[
                "test_matches"
            ]
        ).sum()
        / total_matches
    )

    edge = (
        weighted_open
        - weighted_close
    )


    positive = int(
        (
            valid[
                "test_edge"
            ] > 0
        ).sum()
    )


    print(
        valid.to_string(
            index=False
        )
    )

    print()

    print(
        "OOS selected matches:",
        int(total_matches),
    )

    print(
        "Opening LogLoss:",
        f"{weighted_open:.6f}",
    )

    print(
        "Closing LogLoss:",
        f"{weighted_close:.6f}",
    )

    print(
        "OOS closing edge:",
        f"{edge:+.6f}",
    )

    print(
        "Positive outer seasons:",
        positive,
        "/",
        len(valid),
    )


    print()
    print("=" * 120)
    print("VERDICT")
    print("=" * 120)

    if (
        edge > 0
        and positive
        >= max(
            2,
            len(valid) - 1,
        )
    ):

        print(
            "✅ Segment-specific closing edge "
            "подтвердился OOS."
        )

    else:

        print(
            "❌ Лучшие historical segments "
            "не подтвердили устойчивый OOS edge."
        )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
