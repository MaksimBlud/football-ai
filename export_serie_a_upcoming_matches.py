"""Export future Serie A fixtures from durable odds snapshots."""

from __future__ import annotations

from datetime import datetime
import pandas as pd

from database import supabase
from league_fixture_export import prepare_upcoming_fixtures as prepare_generic
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

OUTPUT_PATH = SERIE_A_RUNTIME_CONFIG.paths.upcoming_fixtures
DB_COLUMNS = "league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team"


def normalize_serie_a_team(value: str) -> str:
    value = str(value).strip()
    return SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)


def fetch_serie_a_snapshots() -> pd.DataFrame:
    response = (
        supabase.table("odds_snapshots")
        .select(DB_COLUMNS)
        .eq("league", SERIE_A_RUNTIME_CONFIG.identity.identifier)
        .order("snapshot_time_utc", desc=True)
        .limit(10000)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def prepare_upcoming_fixtures(snapshots: pd.DataFrame, *, now: datetime | None = None) -> pd.DataFrame:
    return prepare_generic(
        snapshots,
        SERIE_A_RUNTIME_CONFIG,
        normalize_team=normalize_serie_a_team,
        now=now,
    )


def main() -> None:
    s = SERIE_A_RUNTIME_CONFIG.structural_v2
    if s.calibration_status != "CALIBRATION_REQUIRED" or s.structural_alpha is not None or s.edge_threshold is not None:
        raise RuntimeError("Unexpected Serie A Structural V2 state")
    snapshots = fetch_serie_a_snapshots()
    upcoming = prepare_upcoming_fixtures(snapshots)
    if upcoming.empty:
        raise RuntimeError("No future Serie A fixtures found in Supabase")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    upcoming.to_csv(OUTPUT_PATH, index=False)
    print("SERIE A UPCOMING FIXTURES")
    print("source snapshots:", len(snapshots))
    print("fixtures:", len(upcoming))
    print("unique events:", upcoming["event_id"].nunique())
    print("Structural V2 used:", False)
    print("output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
