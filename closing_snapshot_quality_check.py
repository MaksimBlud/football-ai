from database import supabase
import pandas as pd


rows = []
offset = 0
page_size = 1000

while True:
    response = (
        supabase
        .table("odds_snapshots")
        .select("*")
        .order("snapshot_time_utc", desc=False)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    batch = response.data or []
    rows.extend(batch)

    if len(batch) < page_size:
        break

    offset += page_size


df = pd.DataFrame(rows)

if df.empty:
    raise SystemExit("❌ odds_snapshots пуст.")


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
    ]
).copy()


# Только snapshots до kickoff
pre = df[
    df["snapshot_time_utc"]
    < df["commence_time_utc"]
].copy()


latest = (
    pre
    .sort_values(
        [
            "event_id",
            "snapshot_time_utc",
        ]
    )
    .groupby("event_id")
    .tail(1)
    .copy()
)


latest["hours_before_kickoff"] = (
    (
        latest["commence_time_utc"]
        - latest["snapshot_time_utc"]
    )
    .dt.total_seconds()
    / 3600
)


now = pd.Timestamp.now(tz="UTC")

latest["kickoff_passed"] = (
    latest["commence_time_utc"]
    <= now
)


def quality(hours):
    if hours <= 2:
        return "EXCELLENT"
    if hours <= 4:
        return "GOOD"
    if hours <= 6:
        return "ACCEPTABLE"
    return "TOO_EARLY"


latest["close_quality"] = (
    latest["hours_before_kickoff"]
    .map(quality)
)


print("=" * 120)
print("CLOSING SNAPSHOT QUALITY")
print("=" * 120)

cols = [
    "home_team",
    "away_team",
    "snapshot_time_utc",
    "commence_time_utc",
    "hours_before_kickoff",
    "kickoff_passed",
    "close_quality",
]

print(
    latest[cols]
    .sort_values("commence_time_utc")
    .to_string(
        index=False,
        formatters={
            "hours_before_kickoff":
                lambda x: f"{x:.2f}",
        },
    )
)


completed = latest[
    latest["kickoff_passed"]
].copy()


print()
print("=" * 120)
print("COMPLETED EVENTS")
print("=" * 120)

print("Completed:", len(completed))


if len(completed):

    print()
    print(
        completed[
            "close_quality"
        ]
        .value_counts()
        .to_string()
    )

    print()

    print(
        "Средний последний snapshot до kickoff:",
        f"{completed['hours_before_kickoff'].mean():.2f}h",
    )

    print(
        "Медиана:",
        f"{completed['hours_before_kickoff'].median():.2f}h",
    )

    good = (
        completed[
            "hours_before_kickoff"
        ]
        <= 4
    ).mean()

    print(
        "Доля closing snapshots <=4h:",
        f"{good:.1%}",
    )

else:
    print(
        "⏳ Пока сыгранных матчей нет."
    )


print()
print("Supabase только прочитан.")
print("Production-файлы НЕ изменены.")
