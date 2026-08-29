"""RPL market-only live shadow.

Structural V2 remains calibration-required and is never called here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from database import supabase
from league_market_shadow import (
    MARKET_SHADOW_OUTPUT_COLUMNS,
    build_market_shadow as build_generic_market_shadow,
    prepare_snapshots as prepare_generic_snapshots,
    write_market_shadow_outputs,
)
from league_runtime_config import RPL_RUNTIME_CONFIG


UPCOMING_PATH = RPL_RUNTIME_CONFIG.paths.upcoming_fixtures
LATEST_OUTPUT = RPL_RUNTIME_CONFIG.paths.market_shadow
HISTORY_OUTPUT = RPL_RUNTIME_CONFIG.paths.market_history
OUTPUT_COLUMNS = MARKET_SHADOW_OUTPUT_COLUMNS


def fetch_rpl_snapshots() -> pd.DataFrame:
    response = (
        supabase
        .table("odds_snapshots")
        .select(
            "league,event_id,snapshot_time_utc,commence_time_utc,"
            "home_team,away_team,home_odds,draw_odds,away_odds"
        )
        .eq("league", RPL_RUNTIME_CONFIG.identity.identifier)
        .order("snapshot_time_utc", desc=False)
        .limit(10000)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def prepare_snapshots(snapshots: pd.DataFrame) -> pd.DataFrame:
    return prepare_generic_snapshots(snapshots, RPL_RUNTIME_CONFIG)


def load_upcoming(path: Path = UPCOMING_PATH) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "commence_time_utc",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            "Upcoming data missing columns: " + ", ".join(sorted(missing))
        )
    if not (frame["league"] == RPL_RUNTIME_CONFIG.identity.identifier).all():
        raise ValueError("Upcoming file contains non-RPL rows")

    frame = frame.copy()
    frame["commence_time_utc"] = pd.to_datetime(
        frame["commence_time_utc"], utc=True, errors="coerce"
    )
    return frame.dropna(
        subset=["event_id", "home_team", "away_team", "commence_time_utc"]
    ).copy()


def load_previous_history(path: Path = HISTORY_OUTPUT) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    if not (frame["league"] == RPL_RUNTIME_CONFIG.identity.identifier).all():
        raise ValueError("History contains non-RPL rows")
    frame = frame.copy()
    for column in ("generated_at_utc", "snapshot_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    return frame


def build_market_shadow(
    upcoming: pd.DataFrame,
    snapshots: pd.DataFrame,
    *,
    previous_history: pd.DataFrame | None = None,
):
    return build_generic_market_shadow(
        upcoming,
        snapshots,
        RPL_RUNTIME_CONFIG,
        previous_history=previous_history,
    )


def main() -> None:
    structural = RPL_RUNTIME_CONFIG.structural_v2
    if (
        structural.calibration_status != "CALIBRATION_REQUIRED"
        or structural.structural_alpha is not None
        or structural.edge_threshold is not None
    ):
        raise RuntimeError("Unexpected RPL Structural V2 state")

    upcoming = load_upcoming()
    snapshots = fetch_rpl_snapshots()
    history = load_previous_history()
    latest = build_market_shadow(
        upcoming,
        snapshots,
        previous_history=history,
    )
    combined = write_market_shadow_outputs(
        latest,
        latest_path=LATEST_OUTPUT,
        history_path=HISTORY_OUTPUT,
    )

    print("=" * 72)
    print("RPL MARKET-ONLY SHADOW")
    print("=" * 72)
    print("fixtures:", len(latest))
    print("history rows:", len(combined))
    print("AI model used:", False)
    print("Structural V2 used:", False)
    print("latest:", LATEST_OUTPUT)
    print("history:", HISTORY_OUTPUT)


if __name__ == "__main__":
    main()
