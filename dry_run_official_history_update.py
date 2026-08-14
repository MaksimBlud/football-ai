import pandas as pd

from database import supabase


OFFICIAL_FILE = (
    "data/pl_official_history_2016_2026.csv"
)

REPORT_FILE = (
    "data/official_history_update_dry_run.csv"
)

NAME_MAP = {
    "Cardiff City": "Cardiff",
    "Huddersfield Town": "Huddersfield",
    "Hull City": "Hull",
    "Leeds United": "Leeds",
    "Norwich City": "Norwich",
    "Stoke City": "Stoke",
    "Swansea City": "Swansea",
    "West Bromwich Albion": "West Brom",
}

STAT_COLUMNS = [
    "home_goals",
    "away_goals",
    "home_shots",
    "away_shots",
    "home_shots_target",
    "away_shots_target",
    "home_corners",
    "away_corners",
    "home_yellow",
    "away_yellow",
    "home_red",
    "away_red",
]


print("Загружаю официальный master-dataset...")

official = pd.read_csv(
    OFFICIAL_FILE
)

official["home_team"] = (
    official["home_team"]
    .replace(NAME_MAP)
)

official["away_team"] = (
    official["away_team"]
    .replace(NAME_MAP)
)

official["match_date"] = (
    pd.to_datetime(
        official["match_date"]
    )
    .dt.date
    .astype(str)
)

print(
    "Official:",
    len(official),
)


print()
print("Загружаю matches из Supabase...")

# Supabase/PostgREST часто ограничивает один ответ
# примерно 1000 строками, поэтому читаем страницами.
db_rows = []
start = 0
page_size = 1000

while True:
    end = start + page_size - 1

    response = (
        supabase
        .table("matches")
        .select("*")
        .range(start, end)
        .execute()
    )

    batch = response.data or []

    db_rows.extend(batch)

    print(
        f"Строк {start}-{end}:",
        len(batch),
    )

    if len(batch) < page_size:
        break

    start += page_size

db = pd.DataFrame(
    db_rows
)

print(
    "Всего в Supabase:",
    len(db),
)

if len(db) != 3800:
    print(
        "ВНИМАНИЕ: ожидалось 3800 строк "
        "в исторической базе."
    )

db["match_date"] = (
    pd.to_datetime(
        db["match_date"]
    )
    .dt.date
    .astype(str)
)


KEY = [
    "season",
    "match_date",
    "home_team",
    "away_team",
]

merged = official.merge(
    db,
    on=KEY,
    how="left",
    suffixes=(
        "_official",
        "_db",
    ),
    indicator=True,
)


not_found = merged[
    merged["_merge"] != "both"
].copy()

found = merged[
    merged["_merge"] == "both"
].copy()


print()
print("=" * 80)
print("DRY-RUN OFFICIAL HISTORY UPDATE")
print("=" * 80)

print(
    "Матчей Official:",
    len(official),
)

print(
    "Матчей найдено в DB:",
    len(found),
)

print(
    "Не найдено:",
    len(not_found),
)


change_counts = {}

changed_mask = pd.Series(
    False,
    index=found.index,
)

for column in STAT_COLUMNS:
    official_col = (
        f"{column}_official"
    )

    db_col = (
        f"{column}_db"
    )

    a = pd.to_numeric(
        found[official_col],
        errors="coerce",
    )

    b = pd.to_numeric(
        found[db_col],
        errors="coerce",
    )

    different = (
        a.fillna(-999999)
        != b.fillna(-999999)
    )

    change_counts[column] = int(
        different.sum()
    )

    changed_mask |= different


changed = found[
    changed_mask
].copy()

unchanged = found[
    ~changed_mask
].copy()


print()
print(
    "Будет обновлено:",
    len(changed),
)

print(
    "Без изменений:",
    len(unchanged),
)


print()
print("Изменений по полям:")

for column in STAT_COLUMNS:
    print(
        f"  {column:25s}",
        change_counts[column],
    )


report_rows = []

for _, row in changed.iterrows():
    changed_fields = []

    for column in STAT_COLUMNS:
        official_value = row[
            f"{column}_official"
        ]

        db_value = row[
            f"{column}_db"
        ]

        if (
            pd.isna(official_value)
            and pd.isna(db_value)
        ):
            continue

        if official_value != db_value:
            changed_fields.append(
                column
            )

    report_rows.append({
        "db_id": row["id"],
        "season": row["season"],
        "match_date": row["match_date"],
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "changed_fields": ",".join(
            changed_fields
        ),
        "changed_fields_count": len(
            changed_fields
        ),
    })


report = pd.DataFrame(
    report_rows
)

report.to_csv(
    REPORT_FILE,
    index=False,
)


print()
print(
    "Dry-run отчёт:",
    REPORT_FILE,
)

print()
print(
    "ВАЖНО: Supabase НЕ изменялся."
)
