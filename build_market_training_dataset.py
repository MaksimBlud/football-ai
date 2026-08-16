import pandas as pd

from database import supabase
from team_names import normalize_team_name


FEATURES_PATH = (
    "data/market_movement_features.csv"
)

OUTPUT = (
    "data/market_training_dataset.csv"
)


# ============================================================
# LOAD MARKET FEATURES
# ============================================================

features = pd.read_csv(
    FEATURES_PATH
)

features["snapshot_time_utc"] = pd.to_datetime(
    features["snapshot_time_utc"],
    utc=True,
    errors="coerce",
)

features["commence_time_utc"] = pd.to_datetime(
    features["commence_time_utc"],
    utc=True,
    errors="coerce",
)

features = features.dropna(
    subset=[
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
    ]
).copy()


# ============================================================
# STRICT PRE-KICKOFF FILTER
# ============================================================

features = features[
    features["snapshot_time_utc"]
    < features["commence_time_utc"]
].copy()


# ============================================================
# LAST AVAILABLE PRE-KICKOFF ROW PER EVENT
# ============================================================

market = (
    features
    .sort_values(
        "snapshot_time_utc"
    )
    .groupby(
        "event_id",
        as_index=False,
    )
    .tail(1)
    .copy()
)

market["home_normalized"] = (
    market["home_team"]
    .map(normalize_team_name)
)

market["away_normalized"] = (
    market["away_team"]
    .map(normalize_team_name)
)

market["kickoff_date"] = (
    market["commence_time_utc"]
    .dt.date
)


# ============================================================
# LOAD ALL HISTORICAL MATCHES WITH PAGINATION
# ============================================================

page_size = 1000
offset = 0
all_rows = []

while True:

    response = (
        supabase
        .table("matches")
        .select(
            "match_date,"
            "match_time,"
            "home_team,"
            "away_team,"
            "home_goals,"
            "away_goals,"
            "result"
        )
        .range(
            offset,
            offset + page_size - 1,
        )
        .execute()
    )

    rows = response.data or []

    all_rows.extend(rows)

    if len(rows) < page_size:
        break

    offset += page_size


matches = pd.DataFrame(
    all_rows
)

if matches.empty:
    raise SystemExit(
        "Таблица matches пуста."
    )


matches["match_date_parsed"] = pd.to_datetime(
    matches["match_date"],
    errors="coerce",
).dt.date

matches["home_normalized"] = (
    matches["home_team"]
    .map(normalize_team_name)
)

matches["away_normalized"] = (
    matches["away_team"]
    .map(normalize_team_name)
)


# ============================================================
# KEEP ONLY COMPLETED MATCHES
# ============================================================

matches = matches.dropna(
    subset=[
        "match_date_parsed",
        "home_normalized",
        "away_normalized",
        "home_goals",
        "away_goals",
        "result",
    ]
).copy()


# ============================================================
# JOIN
# ============================================================

joined = market.merge(
    matches[
        [
            "match_date_parsed",
            "home_normalized",
            "away_normalized",
            "home_goals",
            "away_goals",
            "result",
        ]
    ],
    left_on=[
        "kickoff_date",
        "home_normalized",
        "away_normalized",
    ],
    right_on=[
        "match_date_parsed",
        "home_normalized",
        "away_normalized",
    ],
    how="left",
    validate="one_to_one",
)


# ============================================================
# TARGET
# ============================================================

result_map = {
    "H": "HOME",
    "D": "DRAW",
    "A": "AWAY",
    "HOME": "HOME",
    "DRAW": "DRAW",
    "AWAY": "AWAY",
}

joined["target"] = (
    joined["result"]
    .map(result_map)
)

joined["is_labeled"] = (
    joined["target"]
    .notna()
)


# ============================================================
# OUTPUT
# ============================================================

output_columns = [
    "event_id",
    "home_team",
    "away_team",
    "home_normalized",
    "away_normalized",
    "commence_time_utc",
    "snapshot_time_utc",
    "hours_to_kickoff",
    "snapshot_number",

    "home_odds",
    "draw_odds",
    "away_odds",

    "home_probability",
    "draw_probability",
    "away_probability",

    "home_move_from_first",
    "draw_move_from_first",
    "away_move_from_first",

    "home_move_from_previous",
    "draw_move_from_previous",
    "away_move_from_previous",

    "home_velocity",
    "draw_velocity",
    "away_velocity",

    "home_strict_streak",
    "draw_strict_streak",
    "away_strict_streak",

    "home_direction_changes",
    "draw_direction_changes",
    "away_direction_changes",

    "home_total_path",
    "draw_total_path",
    "away_total_path",

    "home_movement_efficiency",
    "draw_movement_efficiency",
    "away_movement_efficiency",

    "max_abs_move_from_first",
    "max_abs_move_from_previous",
    "strongest_movement_side",

    "home_goals",
    "away_goals",
    "result",
    "target",
    "is_labeled",
]

training = joined[
    output_columns
].copy()

training.to_csv(
    OUTPUT,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("=" * 100)
print("MARKET TRAINING DATASET BUILT")
print("=" * 100)

print(
    "Market events:",
    len(training),
)

print(
    "Labeled:",
    int(
        training[
            "is_labeled"
        ].sum()
    ),
)

print(
    "Unlabeled:",
    int(
        (
            ~training[
                "is_labeled"
            ]
        ).sum()
    ),
)

print(
    "Output:",
    OUTPUT,
)

print()
print("=" * 100)
print("EVENT STATUS")
print("=" * 100)

show = training[
    [
        "home_team",
        "away_team",
        "commence_time_utc",
        "snapshot_number",
        "hours_to_kickoff",
        "target",
        "is_labeled",
    ]
].copy()

print(
    show.to_string(
        index=False,
        formatters={
            "hours_to_kickoff":
                lambda x: f"{x:.1f}",
        },
    )
)


print()
print("=" * 100)
print("SANITY CHECK")
print("=" * 100)

print(
    "Snapshots after/equal kickoff:",
    int(
        (
            training["snapshot_time_utc"]
            >= training["commence_time_utc"]
        ).sum()
    ),
)

print(
    "Duplicate event_id:",
    int(
        training.duplicated(
            subset=["event_id"]
        ).sum()
    ),
)

print(
    "Unknown target values:",
    sorted(
        training.loc[
            training["target"].notna(),
            "target",
        ]
        .drop_duplicates()
        .tolist()
    ),
)


print()
print("The Odds API НЕ вызывался.")
print("Supabase только прочитан.")
print("Production model НЕ изменена.")
