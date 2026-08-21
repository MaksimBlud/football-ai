from pathlib import Path

import numpy as np
import pandas as pd

from database import supabase


ROOT = Path(__file__).resolve().parent

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "true_closing_convergence.csv"
)

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)


# ============================================================
# LOAD ALL SNAPSHOTS
# ============================================================

rows = []
offset = 0
page_size = 1000

while True:

    response = (
        supabase
        .table("odds_snapshots")
        .select("*")
        .order(
            "snapshot_time_utc",
            desc=False,
        )
        .range(
            offset,
            offset + page_size - 1,
        )
        .execute()
    )

    batch = response.data or []

    rows.extend(batch)

    if len(batch) < page_size:
        break

    offset += page_size


df = pd.DataFrame(rows)

if df.empty:
    raise SystemExit(
        "❌ odds_snapshots пуст."
    )


# ============================================================
# TIME
# ============================================================

df["snapshot_time_utc"] = pd.to_datetime(
    df["snapshot_time_utc"],
    utc=True,
    errors="coerce",
)

df["commence_time_utc"] = pd.to_datetime(
    df["commence_time_utc"],
    utc=True,
    errors="coerce",
)


df = df.dropna(
    subset=[
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
).copy()


# ============================================================
# IMPORTANT:
# ONLY PRE-KICKOFF SNAPSHOTS
# ============================================================

df = df[
    df["snapshot_time_utc"]
    < df["commence_time_utc"]
].copy()


# ============================================================
# FAIR PROBABILITIES
# ============================================================

odds = df[
    [
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
].to_numpy(dtype=float)

raw = 1.0 / odds

probs = (
    raw
    / raw.sum(
        axis=1,
        keepdims=True,
    )
)

df["p_home"] = probs[:, 0]
df["p_draw"] = probs[:, 1]
df["p_away"] = probs[:, 2]


df["hours_to_kickoff"] = (
    (
        df["commence_time_utc"]
        - df["snapshot_time_utc"]
    )
    .dt.total_seconds()
    / 3600
)


# ============================================================
# SORT + NUMBER
# ============================================================

df = df.sort_values(
    [
        "event_id",
        "snapshot_time_utc",
    ]
).copy()

df["snapshot_number"] = (
    df.groupby("event_id")
    .cumcount()
    + 1
)


# ============================================================
# EVENT STATUS
#
# We only call something TRUE CLOSE
# when kickoff has already passed.
# ============================================================

now_utc = pd.Timestamp.now(
    tz="UTC"
)

event_info = (
    df.groupby("event_id")
    .agg(
        home_team=(
            "home_team",
            "first",
        ),

        away_team=(
            "away_team",
            "first",
        ),

        kickoff=(
            "commence_time_utc",
            "first",
        ),

        snapshots=(
            "snapshot_number",
            "max",
        ),

        last_snapshot_time=(
            "snapshot_time_utc",
            "max",
        ),

        last_hours_to_kickoff=(
            "hours_to_kickoff",
            "min",
        ),
    )
    .reset_index()
)

event_info["kickoff_passed"] = (
    event_info["kickoff"]
    <= now_utc
)


print("=" * 125)
print("TRUE CLOSING SNAPSHOT READINESS")
print("=" * 125)

print(
    event_info[
        [
            "home_team",
            "away_team",
            "snapshots",
            "kickoff",
            "last_snapshot_time",
            "last_hours_to_kickoff",
            "kickoff_passed",
        ]
    ]
    .sort_values("kickoff")
    .to_string(
        index=False,
        formatters={
            "last_hours_to_kickoff":
                lambda x:
                    f"{x:.2f}",
        },
    )
)


completed_ids = set(
    event_info.loc[
        event_info[
            "kickoff_passed"
        ],
        "event_id",
    ]
)


# ============================================================
# NO COMPLETED EVENTS YET
# ============================================================

if not completed_ids:

    print()
    print("=" * 125)
    print("STATUS")
    print("=" * 125)

    print(
        "⏳ Пока ни один матч не начался."
    )

    print(
        "True closing convergence "
        "ещё нельзя рассчитывать."
    )

    print()
    print(
        "Сбор snapshots должен "
        "продолжать работать."
    )

    print()
    print(
        "Production-файлы НЕ изменены."
    )

    raise SystemExit(0)


# ============================================================
# TRUE CLOSE =
# LAST SNAPSHOT STRICTLY BEFORE KICKOFF
# ============================================================

completed = df[
    df["event_id"].isin(
        completed_ids
    )
].copy()


close = (
    completed
    .groupby("event_id")
    .tail(1)
    [
        [
            "event_id",
            "snapshot_number",
            "snapshot_time_utc",
            "hours_to_kickoff",
            "p_home",
            "p_draw",
            "p_away",
        ]
    ]
    .rename(
        columns={
            "snapshot_number":
                "close_snapshot_number",

            "snapshot_time_utc":
                "close_snapshot_time",

            "hours_to_kickoff":
                "close_hours_to_kickoff",

            "p_home":
                "close_p_home",

            "p_draw":
                "close_p_draw",

            "p_away":
                "close_p_away",
        }
    )
)


work = completed.merge(
    close,
    on="event_id",
    how="left",
    validate="many_to_one",
)


# ============================================================
# DISTANCE TO TRUE CLOSE
# ============================================================

work["mae_to_close"] = (
    np.abs(
        work[
            [
                "p_home",
                "p_draw",
                "p_away",
            ]
        ].to_numpy(dtype=float)
        -
        work[
            [
                "close_p_home",
                "close_p_draw",
                "close_p_away",
            ]
        ].to_numpy(dtype=float)
    )
    .mean(axis=1)
)


work["max_diff_to_close"] = (
    np.abs(
        work[
            [
                "p_home",
                "p_draw",
                "p_away",
            ]
        ].to_numpy(dtype=float)
        -
        work[
            [
                "close_p_home",
                "close_p_draw",
                "close_p_away",
            ]
        ].to_numpy(dtype=float)
    )
    .max(axis=1)
)


# ============================================================
# SAVE MATCH-LEVEL PATH
# ============================================================

work.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SUMMARY BY SNAPSHOT NUMBER
# ============================================================

print()
print("=" * 125)
print("TRUE CONVERGENCE BY SNAPSHOT NUMBER")
print("=" * 125)

summary = (
    work.groupby(
        "snapshot_number"
    )
    .agg(
        events=(
            "event_id",
            "nunique",
        ),

        avg_hours_to_kickoff=(
            "hours_to_kickoff",
            "mean",
        ),

        mean_mae_to_close=(
            "mae_to_close",
            "mean",
        ),

        median_mae_to_close=(
            "mae_to_close",
            "median",
        ),

        mean_max_diff_to_close=(
            "max_diff_to_close",
            "mean",
        ),
    )
    .reset_index()
)

print(
    summary.to_string(
        index=False,
        formatters={
            "avg_hours_to_kickoff":
                lambda x:
                    f"{x:.1f}",

            "mean_mae_to_close":
                lambda x:
                    f"{x:.4%}",

            "median_mae_to_close":
                lambda x:
                    f"{x:.4%}",

            "mean_max_diff_to_close":
                lambda x:
                    f"{x:.4%}",
        },
    )
)


# ============================================================
# QUALITY OF ACTUAL CLOSING SNAPSHOT
# ============================================================

print()
print("=" * 125)
print("CLOSING SNAPSHOT QUALITY")
print("=" * 125)

quality = (
    close[
        [
            "event_id",
            "close_snapshot_number",
            "close_hours_to_kickoff",
        ]
    ]
    .merge(
        event_info[
            [
                "event_id",
                "home_team",
                "away_team",
            ]
        ],
        on="event_id",
        how="left",
    )
)

print(
    quality[
        [
            "home_team",
            "away_team",
            "close_snapshot_number",
            "close_hours_to_kickoff",
        ]
    ]
    .sort_values(
        "close_hours_to_kickoff"
    )
    .to_string(
        index=False,
        formatters={
            "close_hours_to_kickoff":
                lambda x:
                    f"{x:.2f}",
        },
    )
)


print()
print(
    "Completed events:",
    len(completed_ids),
)

print(
    "Сохранено:",
    OUTPUT_FILE,
)

print()
print(
    "Supabase только прочитан."
)

print(
    "Production-файлы НЕ изменены."
)
