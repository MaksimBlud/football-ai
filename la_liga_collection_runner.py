"""Safe scheduled-style La Liga collection runner.

Default behavior is read-only / dry-run.

Live collection requires explicit --live.

Safety:
- no training;
- no model promotion;
- no git staging/commit/push;
- no Odds API request without --live;
- enforces minimum interval between real La Liga snapshots;
- after a successful live snapshot, refreshes the research pipeline.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from database import supabase
from league_config import LA_LIGA


ROOT = Path(__file__).resolve().parent

DEFAULT_MIN_INTERVAL_MINUTES = 120

DOWNSTREAM_STEPS = (
    (
        "fixture export",
        [
            sys.executable,
            "export_la_liga_upcoming_matches.py",
        ],
    ),
    (
        "market shadow",
        [
            sys.executable,
            "generate_la_liga_market_shadow.py",
        ],
    ),
    (
        "movement classifier",
        [
            sys.executable,
            "classify_la_liga_market_movements.py",
        ],
    ),
    (
        "transition tracker",
        [
            sys.executable,
            "track_la_liga_market_transitions.py",
        ],
    ),
    (
        "temporal behavior",
        [
            sys.executable,
            "analyze_la_liga_temporal_behavior.py",
        ],
    ),
)


def fetch_la_liga_snapshot_times() -> pd.Series:
    response = (
        supabase
        .table("odds_snapshots")
        .select(
            "snapshot_time_utc"
        )
        .eq(
            "league",
            LA_LIGA.identifier,
        )
        .limit(10000)
        .execute()
    )

    frame = pd.DataFrame(
        response.data or []
    )

    if frame.empty:
        return pd.Series(
            dtype="datetime64[ns, UTC]"
        )

    times = pd.to_datetime(
        frame["snapshot_time_utc"],
        utc=True,
        errors="coerce",
    ).dropna()

    return times.sort_values()


def latest_snapshot_time():
    times = (
        fetch_la_liga_snapshot_times()
    )

    if times.empty:
        return None

    return times.iloc[-1]


def minutes_since_latest(
    *,
    now: datetime | None = None,
) -> float | None:
    latest = latest_snapshot_time()

    if latest is None:
        return None

    if now is None:
        now = datetime.now(
            timezone.utc
        )

    now_ts = pd.Timestamp(
        now
    )

    delta = (
        now_ts
        - latest
    )

    return (
        delta.total_seconds()
        / 60.0
    )


def collection_due(
    *,
    minimum_interval_minutes: int,
    now: datetime | None = None,
) -> tuple[bool, str]:
    elapsed = minutes_since_latest(
        now=now
    )

    if elapsed is None:
        return (
            True,
            "no_previous_la_liga_snapshot",
        )

    if elapsed >= minimum_interval_minutes:
        return (
            True,
            (
                f"elapsed_minutes={elapsed:.1f} "
                f">= minimum={minimum_interval_minutes}"
            ),
        )

    return (
        False,
        (
            f"elapsed_minutes={elapsed:.1f} "
            f"< minimum={minimum_interval_minutes}"
        ),
    )


def run_command(
    label: str,
    command: list[str],
) -> bool:
    print()
    print("=" * 72)
    print(label.upper())
    print("=" * 72)
    print("$", " ".join(command))

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
    )

    print(
        f"{label} rc={completed.returncode}"
    )

    return (
        completed.returncode
        == 0
    )


def run_downstream() -> bool:
    for label, command in (
        DOWNSTREAM_STEPS
    ):
        if not run_command(
            label,
            command,
        ):
            print(
                "STOP: downstream pipeline failed"
            )
            return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Permit one real La Liga Odds API "
            "snapshot/write if collection is due."
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Ignore minimum interval. "
            "Requires --live."
        ),
    )

    parser.add_argument(
        "--minimum-interval-minutes",
        type=int,
        default=DEFAULT_MIN_INTERVAL_MINUTES,
    )

    parser.add_argument(
        "--skip-downstream",
        action="store_true",
    )

    args = parser.parse_args()

    if (
        args.minimum_interval_minutes
        < 1
    ):
        print(
            "ERROR: minimum interval must be >= 1 minute"
        )
        return 2

    if (
        args.force
        and not args.live
    ):
        print(
            "ERROR: --force requires --live"
        )
        return 2

    due, reason = collection_due(
        minimum_interval_minutes=(
            args.minimum_interval_minutes
        )
    )

    print("=" * 72)
    print(
        "LA LIGA COLLECTION RUNNER"
    )
    print("=" * 72)

    print(
        "league:",
        LA_LIGA.identifier,
    )

    print(
        "sport key:",
        LA_LIGA.odds_api_sport_key,
    )

    print(
        "minimum interval:",
        args.minimum_interval_minutes,
        "minutes",
    )

    latest = latest_snapshot_time()

    print(
        "latest snapshot:",
        latest
        if latest is not None
        else "none",
    )

    print(
        "due:",
        due,
    )

    print(
        "reason:",
        reason,
    )

    if not args.live:
        print()
        print(
            "DRY RUN: no Odds API request "
            "and no Supabase write."
        )

        return 0

    if (
        not due
        and not args.force
    ):
        print()
        print(
            "HOLD: snapshot not due."
        )
        print(
            "The Odds API will NOT be called."
        )

        return 0

    print()
    print(
        "LIVE collection permitted."
    )

    if not run_command(
        "La Liga live snapshot",
        [
            sys.executable,
            "save_la_liga_odds_snapshot.py",
        ],
    ):
        return 1

    if args.skip_downstream:
        print(
            "PASS: snapshot collected; "
            "downstream skipped."
        )
        return 0

    if not run_downstream():
        return 1

    print()
    print(
        "PASS: La Liga live collection "
        "and downstream refresh completed."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
