"""Scheduled EPL H2H snapshot with research-only bookmaker-level capture.

This is the live EPL entrypoint used by ``scheduled_odds_snapshot.py``. It makes
exactly one The Odds API H2H request, preserves the established aggregate EPL
snapshot behavior, and persists bookmaker-level quotes from that same response.
"""

from __future__ import annotations

from datetime import datetime, timezone

from h2h_bookmaker_snapshot import save_h2h_bookmaker_snapshots
from league_config import EPL
from save_odds_snapshot import build_snapshot_rows, save_local_history, save_supabase
from the_odds_service import get_epl_h2h_odds


def main() -> None:
    if not EPL.collection_ready:
        raise RuntimeError("EPL odds collection is not enabled/ready")

    result = get_epl_h2h_odds()
    events = result["events"]
    snapshot_time = datetime.now(timezone.utc).isoformat()

    new_df = build_snapshot_rows(events, snapshot_time)
    if new_df.empty:
        raise RuntimeError("The Odds API returned no usable EPL h2h odds")

    combined = save_local_history(new_df)
    aggregate_rows = save_supabase(new_df)
    bookmaker_rows = save_h2h_bookmaker_snapshots(
        events,
        league=EPL.identifier,
        snapshot_time_utc=snapshot_time,
    )

    print("=" * 72)
    print("EPL ODDS SNAPSHOT SAVED")
    print("=" * 72)
    print("league:", EPL.identifier)
    print("snapshot UTC:", snapshot_time)
    print("snapshot rows:", len(new_df))
    print("local history rows:", len(combined))
    print("aggregate Supabase rows:", aggregate_rows)
    print("bookmaker research rows:", bookmaker_rows)
    print("quota:", result["quota"])
    print("provider requests for this run:", 1)
    print("extra provider requests for bookmaker capture:", 0)


if __name__ == "__main__":
    main()
