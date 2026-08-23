"""Research-only market shadow for La Liga.

No EPL/AI model is used.

Inputs:
- data/upcoming_matches_la_liga.csv
- existing LA_LIGA odds_snapshots from Supabase

Outputs:
- experiments/la_liga_market_shadow.csv
- experiments/la_liga_market_shadow_history.csv

The latest file represents one research run.
The history file is append-only by generated_at_utc.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from database import supabase
from league_config import LA_LIGA


UPCOMING_PATH = Path(
    "data/upcoming_matches_la_liga.csv"
)

LATEST_OUTPUT = Path(
    "experiments/la_liga_market_shadow.csv"
)

HISTORY_OUTPUT = Path(
    "experiments/la_liga_market_shadow_history.csv"
)

OUTPUT_COLUMNS = [
    "league",
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "generated_at_utc",
    "snapshot_time_utc",
    "hours_before_kickoff",
    "home_odds",
    "draw_odds",
    "away_odds",
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
    "previous_snapshot_time_utc",
    "previous_market_home_probability",
    "previous_market_draw_probability",
    "previous_market_away_probability",
    "market_home_movement",
    "market_draw_movement",
    "market_away_movement",
    "maximum_absolute_market_movement",
    "market_argmax",
    "previous_market_argmax",
    "market_argmax_changed",
    "market_shadow_status",
    "market_only",
]


def normalized_market_probabilities(
    home_odds: float,
    draw_odds: float,
    away_odds: float,
) -> tuple[float, float, float]:
    """Convert decimal odds to normalized implied probabilities."""

    odds = np.array(
        [
            home_odds,
            draw_odds,
            away_odds,
        ],
        dtype=float,
    )

    if (
        not np.isfinite(odds).all()
        or (odds <= 1.0).any()
    ):
        raise ValueError(
            "Odds must be finite decimal prices greater than 1.0"
        )

    raw = 1.0 / odds
    total = raw.sum()

    if not np.isfinite(total) or total <= 0:
        raise ValueError(
            "Invalid implied probability total"
        )

    normalized = raw / total

    return (
        float(normalized[0]),
        float(normalized[1]),
        float(normalized[2]),
    )


def probability_argmax(
    home: float,
    draw: float,
    away: float,
) -> str:
    values = {
        "H": float(home),
        "D": float(draw),
        "A": float(away),
    }

    return max(
        values,
        key=values.get,
    )


def fetch_la_liga_snapshots() -> pd.DataFrame:
    response = (
        supabase
        .table("odds_snapshots")
        .select(
            "league,"
            "event_id,"
            "snapshot_time_utc,"
            "commence_time_utc,"
            "home_team,"
            "away_team,"
            "home_odds,"
            "draw_odds,"
            "away_odds"
        )
        .eq(
            "league",
            LA_LIGA.identifier,
        )
        .order(
            "snapshot_time_utc",
            desc=False,
        )
        .limit(10000)
        .execute()
    )

    return pd.DataFrame(
        response.data or []
    )


def prepare_snapshots(
    snapshots: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
        "home_odds",
        "draw_odds",
        "away_odds",
    }

    missing = required - set(
        snapshots.columns
    )

    if missing:
        raise ValueError(
            "Snapshot data missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    if snapshots.empty:
        return snapshots.copy()

    result = snapshots.copy()

    if not (
        result["league"]
        == LA_LIGA.identifier
    ).all():
        raise ValueError(
            "Non-La-Liga snapshot supplied"
        )

    result[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        result["snapshot_time_utc"],
        utc=True,
        errors="coerce",
    )

    result[
        "commence_time_utc"
    ] = pd.to_datetime(
        result["commence_time_utc"],
        utc=True,
        errors="coerce",
    )

    for column in (
        "home_odds",
        "draw_odds",
        "away_odds",
    ):
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result = result.dropna(
        subset=[
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ).copy()

    # Never use an observation at or after kickoff.
    result = result[
        result["snapshot_time_utc"]
        < result["commence_time_utc"]
    ].copy()

    return result.sort_values(
        [
            "event_id",
            "snapshot_time_utc",
        ]
    ).reset_index(
        drop=True
    )


def load_upcoming(
    path: Path = UPCOMING_PATH,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path
    )

    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "commence_time_utc",
    }

    missing = required - set(
        frame.columns
    )

    if missing:
        raise ValueError(
            "Upcoming data missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    if not (
        frame["league"]
        == LA_LIGA.identifier
    ).all():
        raise ValueError(
            "Upcoming file contains non-La-Liga rows"
        )

    frame = frame.copy()

    frame[
        "commence_time_utc"
    ] = pd.to_datetime(
        frame["commence_time_utc"],
        utc=True,
        errors="coerce",
    )

    return frame.dropna(
        subset=[
            "event_id",
            "commence_time_utc",
            "home_team",
            "away_team",
        ]
    ).copy()


def load_previous_history(
    path: Path = HISTORY_OUTPUT,
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    frame = pd.read_csv(
        path
    )

    if frame.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    required = {
        "league",
        "event_id",
        "generated_at_utc",
        "snapshot_time_utc",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "market_argmax",
    }

    missing = required - set(
        frame.columns
    )

    if missing:
        raise ValueError(
            "History missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    if not (
        frame["league"]
        == LA_LIGA.identifier
    ).all():
        raise ValueError(
            "History contains non-La-Liga rows"
        )

    frame = frame.copy()

    frame["generated_at_utc"] = (
        pd.to_datetime(
            frame["generated_at_utc"],
            utc=True,
            errors="coerce",
        )
    )

    frame["snapshot_time_utc"] = (
        pd.to_datetime(
            frame["snapshot_time_utc"],
            utc=True,
            errors="coerce",
        )
    )

    return frame


def build_market_shadow(
    upcoming: pd.DataFrame,
    snapshots: pd.DataFrame,
    *,
    previous_history: pd.DataFrame | None = None,
    generated_at_utc: datetime | None = None,
) -> pd.DataFrame:
    snapshots = prepare_snapshots(
        snapshots
    )

    if generated_at_utc is None:
        generated_at_utc = datetime.now(
            timezone.utc
        )

    generated = pd.Timestamp(
        generated_at_utc
    )

    if generated.tzinfo is None:
        generated = generated.tz_localize(
            "UTC"
        )
    else:
        generated = generated.tz_convert(
            "UTC"
        )

    if previous_history is None:
        previous_history = pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    records = []

    for _, fixture in upcoming.iterrows():
        event_id = fixture["event_id"]

        observations = snapshots[
            snapshots["event_id"]
            == event_id
        ].copy()

        row = {
            column: None
            for column in OUTPUT_COLUMNS
        }

        row.update({
            "league":
                LA_LIGA.identifier,

            "event_id":
                event_id,

            "home_team":
                fixture["home_team"],

            "away_team":
                fixture["away_team"],

            "commence_time_utc":
                fixture[
                    "commence_time_utc"
                ].isoformat(),

            "generated_at_utc":
                generated.isoformat(),

            "market_shadow_status":
                "NO_MARKET_ODDS",

            "market_only":
                True,
        })

        if observations.empty:
            records.append(
                row
            )
            continue

        current = observations.iloc[-1]

        (
            p_home,
            p_draw,
            p_away,
        ) = normalized_market_probabilities(
            current["home_odds"],
            current["draw_odds"],
            current["away_odds"],
        )

        kickoff = pd.Timestamp(
            fixture[
                "commence_time_utc"
            ]
        )

        snapshot_time = current[
            "snapshot_time_utc"
        ]

        current_argmax = probability_argmax(
            p_home,
            p_draw,
            p_away,
        )

        row.update({
            "snapshot_time_utc":
                snapshot_time.isoformat(),

            "hours_before_kickoff":
                (
                    kickoff
                    - snapshot_time
                ).total_seconds()
                / 3600,

            "home_odds":
                float(
                    current["home_odds"]
                ),

            "draw_odds":
                float(
                    current["draw_odds"]
                ),

            "away_odds":
                float(
                    current["away_odds"]
                ),

            "market_home_probability":
                p_home,

            "market_draw_probability":
                p_draw,

            "market_away_probability":
                p_away,

            "market_argmax":
                current_argmax,

            "market_shadow_status":
                "OK",
        })

        previous = previous_history[
            (
                previous_history[
                    "event_id"
                ]
                == event_id
            )
            & (
                previous_history[
                    "market_shadow_status"
                ]
                == "OK"
            )
        ].copy()

        if not previous.empty:
            previous = previous.sort_values(
                "generated_at_utc"
            )

            prev = previous.iloc[-1]

            prev_home = float(
                prev[
                    "market_home_probability"
                ]
            )

            prev_draw = float(
                prev[
                    "market_draw_probability"
                ]
            )

            prev_away = float(
                prev[
                    "market_away_probability"
                ]
            )

            movements = [
                p_home - prev_home,
                p_draw - prev_draw,
                p_away - prev_away,
            ]

            row.update({
                "previous_snapshot_time_utc":
                    str(
                        prev[
                            "snapshot_time_utc"
                        ]
                    ),

                "previous_market_home_probability":
                    prev_home,

                "previous_market_draw_probability":
                    prev_draw,

                "previous_market_away_probability":
                    prev_away,

                "market_home_movement":
                    movements[0],

                "market_draw_movement":
                    movements[1],

                "market_away_movement":
                    movements[2],

                "maximum_absolute_market_movement":
                    max(
                        abs(value)
                        for value
                        in movements
                    ),

                "previous_market_argmax":
                    prev[
                        "market_argmax"
                    ],

                "market_argmax_changed":
                    (
                        str(
                            prev[
                                "market_argmax"
                            ]
                        )
                        != current_argmax
                    ),
            })

        records.append(
            row
        )

    return pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
    )


def write_outputs(
    latest: pd.DataFrame,
    *,
    latest_path: Path = LATEST_OUTPUT,
    history_path: Path = HISTORY_OUTPUT,
) -> pd.DataFrame:
    for path in (
        latest_path,
        history_path,
    ):
        if (
            Path("experiments").resolve()
            not in path.resolve().parents
        ):
            raise ValueError(
                "Market-shadow outputs must stay under experiments/"
            )

    latest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    latest.to_csv(
        latest_path,
        index=False,
    )

    if history_path.exists():
        existing = pd.read_csv(
            history_path
        )

        combined = pd.concat(
            [
                existing,
                latest,
            ],
            ignore_index=True,
            sort=False,
        )

    else:
        combined = latest.copy()

    combined.to_csv(
        history_path,
        index=False,
    )

    return combined


def main() -> None:
    upcoming = load_upcoming()

    snapshots = (
        fetch_la_liga_snapshots()
    )

    previous_history = (
        load_previous_history()
    )

    latest = build_market_shadow(
        upcoming,
        snapshots,
        previous_history=previous_history,
    )

    history = write_outputs(
        latest
    )

    print("=" * 72)
    print(
        "LA LIGA MARKET-ONLY SHADOW"
    )
    print("=" * 72)

    print(
        "fixtures:",
        len(latest),
    )

    print(
        "history rows:",
        len(history),
    )

    print(
        "AI model used:",
        False,
    )

    print()
    print(
        "STATUS:"
    )

    print(
        latest[
            "market_shadow_status"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    ok = latest[
        latest[
            "market_shadow_status"
        ]
        == "OK"
    ]

    movements = ok[
        ok[
            "maximum_absolute_market_movement"
        ].notna()
    ]

    print()
    print(
        "fixtures with previous market observation:",
        len(movements),
    )

    if not movements.empty:
        print()
        print(
            movements.sort_values(
                "maximum_absolute_market_movement",
                ascending=False,
            )[
                [
                    "home_team",
                    "away_team",
                    "hours_before_kickoff",
                    "market_argmax",
                    "previous_market_argmax",
                    "market_argmax_changed",
                    "market_home_movement",
                    "market_draw_movement",
                    "market_away_movement",
                    "maximum_absolute_market_movement",
                ]
            ]
            .to_string(
                index=False
            )
        )

    print()
    print(
        "latest:",
        LATEST_OUTPUT,
    )

    print(
        "history:",
        HISTORY_OUTPUT,
    )


if __name__ == "__main__":
    main()
