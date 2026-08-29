"""Adaptive scheduler for Serie A h2h snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

from database import supabase
import save_serie_a_odds_snapshot as collector
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

TABLE = "odds_snapshots"
NO_FUTURE_MATCH_COOLDOWN_HOURS = 24


def parse_dt(value):
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def required_interval_hours(hours_to_match: float) -> int:
    if hours_to_match > 72:
        return 12
    if hours_to_match > 24:
        return 6
    if hours_to_match > 6:
        return 4
    return 2


def should_collect(rows: list[dict], *, now: datetime) -> tuple[bool, str]:
    if not rows:
        return True, "NO_EXISTING_SERIE_A_SNAPSHOTS"
    snapshot_times = [parse_dt(row.get("snapshot_time_utc")) for row in rows if row.get("snapshot_time_utc")]
    snapshot_times = [dt for dt in snapshot_times if dt is not None]
    if not snapshot_times:
        return True, "NO_VALID_SERIE_A_SNAPSHOT_TIMES"
    last_snapshot = max(snapshot_times)
    hours_since_snapshot = (now - last_snapshot).total_seconds() / 3600.0
    commence_times = [parse_dt(row.get("commence_time_utc")) for row in rows if row.get("commence_time_utc")]
    future = [dt for dt in commence_times if dt is not None and dt > now]
    if not future:
        due = hours_since_snapshot >= NO_FUTURE_MATCH_COOLDOWN_HOURS
        return due, "NO_FUTURE_FIXTURES_COOLDOWN_EXPIRED" if due else "NO_FUTURE_FIXTURES_COOLDOWN"
    nearest = min(future)
    interval = required_interval_hours((nearest - now).total_seconds() / 3600.0)
    due = hours_since_snapshot >= interval
    return due, f"NEAREST_KICKOFF_INTERVAL_{interval}H"


def fetch_recent_serie_a_snapshots() -> list[dict]:
    response = (
        supabase.table(TABLE)
        .select("snapshot_time_utc,commence_time_utc,league")
        .eq("league", SERIE_A_RUNTIME_CONFIG.identity.identifier)
        .order("snapshot_time_utc", desc=True)
        .limit(500)
        .execute()
    )
    return list(response.data or [])


def main() -> None:
    now = datetime.now(timezone.utc)
    rows = fetch_recent_serie_a_snapshots()
    due, reason = should_collect(rows, now=now)
    print("UTC now:", now.isoformat())
    print("Serie A snapshot rows inspected:", len(rows))
    print("decision:", reason)
    print("snapshot required:", due)
    if not due:
        print("The Odds API not called.")
        return
    collector.main()


if __name__ == "__main__":
    main()
