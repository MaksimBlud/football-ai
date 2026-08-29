"""Manual-only RPL h2h odds snapshot collector.

Uses the verified EU bookmaker region for RPL. Importing is side-effect free.
External writes occur only from main(): local RPL CSV + Supabase odds_snapshots.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from fixture_identity import require_league
from league_runtime_config import RPL_RUNTIME_CONFIG
from save_odds_snapshot import DB_COLUMNS, DB_CONFLICT_TARGET, SUPABASE_TABLE
from the_odds_service import aggregate_event_h2h, get_h2h_odds


REGION = "eu"
LEAGUE = RPL_RUNTIME_CONFIG.identity.identifier
SPORT_KEY = RPL_RUNTIME_CONFIG.identity.odds_sport_key
OUTPUT = Path("data/odds_snapshots/rpl_h2h_snapshots.csv")


def build_snapshot_rows(events, snapshot_time_utc: str) -> pd.DataFrame:
    rows = []
    for event in events:
        aggregated = aggregate_event_h2h(event)
        if aggregated is None:
            continue
        rows.append(
            {
                "league": LEAGUE,
                "snapshot_time_utc": snapshot_time_utc,
                "event_id": aggregated["event_id"],
                "commence_time_utc": aggregated["commence_time"],
                "home_team": aggregated["home_team"],
                "away_team": aggregated["away_team"],
                "bookmakers_count": aggregated["bookmakers_count"],
                "home_odds": aggregated["home_odds"],
                "draw_odds": aggregated["draw_odds"],
                "away_odds": aggregated["away_odds"],
                "home_probability": aggregated["home_probability"],
                "draw_probability": aggregated["draw_probability"],
                "away_probability": aggregated["away_probability"],
            }
        )
    return pd.DataFrame(rows, columns=DB_COLUMNS)


def merge_local_history(old_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    old_df = require_league(old_df, legacy_epl=False)
    new_df = require_league(new_df, legacy_epl=False)
    if not old_df.empty and not old_df["league"].eq(LEAGUE).all():
        raise ValueError("RPL local history contains non-RPL rows")
    if not new_df.empty and not new_df["league"].eq(LEAGUE).all():
        raise ValueError("Incoming RPL snapshot contains non-RPL rows")
    combined = pd.concat([old_df, new_df], ignore_index=True, sort=False)
    return (
        combined.drop_duplicates(
            subset=["league", "snapshot_time_utc", "event_id"], keep="last"
        )
        .sort_values(["snapshot_time_utc", "commence_time_utc", "home_team"])
        .reset_index(drop=True)
    )


def save_local_history(new_df: pd.DataFrame, *, output_path: Path = OUTPUT) -> pd.DataFrame:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        combined = merge_local_history(pd.read_csv(output_path), new_df)
    else:
        combined = merge_local_history(
            pd.DataFrame(columns=DB_COLUMNS), new_df
        )
    combined.to_csv(output_path, index=False)
    return combined


def build_db_rows(frame: pd.DataFrame) -> list[dict]:
    frame = require_league(frame, legacy_epl=False)
    if not frame.empty and not frame["league"].eq(LEAGUE).all():
        raise ValueError("Supabase RPL payload contains non-RPL rows")
    missing = set(DB_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing DB columns: {sorted(missing)}")
    return (
        frame[DB_COLUMNS]
        .where(pd.notna(frame[DB_COLUMNS]), None)
        .to_dict(orient="records")
    )


def save_supabase(frame: pd.DataFrame, *, supabase_client=None) -> int:
    if supabase_client is None:
        from database import supabase as supabase_client
    rows = build_db_rows(frame)
    response = (
        supabase_client.table(SUPABASE_TABLE)
        .upsert(rows, on_conflict=DB_CONFLICT_TARGET)
        .execute()
    )
    return len(response.data or [])


def main() -> None:
    if not SPORT_KEY:
        raise RuntimeError("RPL sport key is unresolved")
    result = get_h2h_odds(SPORT_KEY, regions=REGION)
    snapshot_time = datetime.now(timezone.utc).isoformat()
    new_df = build_snapshot_rows(result["events"], snapshot_time)
    if new_df.empty:
        raise RuntimeError("The Odds API returned no usable RPL h2h odds")

    combined = save_local_history(new_df)
    persisted = save_supabase(new_df)

    print("=" * 72)
    print("RPL ODDS SNAPSHOT SAVED")
    print("=" * 72)
    print("league:", LEAGUE)
    print("sport key:", SPORT_KEY)
    print("region:", REGION)
    print("snapshot rows:", len(new_df))
    print("local history rows:", len(combined))
    print("Supabase response rows:", persisted)
    print("quota:", result["quota"])
    print("Structural V2 used:", False)
    print("production model used:", False)


if __name__ == "__main__":
    main()
