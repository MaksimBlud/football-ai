"""Provider schedule-revision helpers for prospective market-path research.

A league home/away pairing should have one currently observed provider event.
When the provider re-keys or reschedules a fixture, stale event ids may remain in
immutable snapshot history. This module marks only clearly superseded revisions:
an older event whose latest observation is strictly earlier than another event
for the same normalized league/home/away pairing.
"""
from __future__ import annotations

import pandas as pd

from team_names import normalize_team_name

STATUS_SUPERSEDED = "SUPERSEDED"


def mark_superseded_revisions(coverage: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    if coverage.empty or snapshots.empty:
        return coverage.copy()

    required = {"league", "event_id", "home_team", "away_team", "snapshot_time_utc"}
    missing = required - set(snapshots.columns)
    if missing:
        raise ValueError("snapshots missing revision columns: " + ", ".join(sorted(missing)))

    snap = snapshots.copy()
    snap["snapshot_time_utc"] = pd.to_datetime(snap["snapshot_time_utc"], utc=True, errors="coerce")
    snap = snap.dropna(subset=["snapshot_time_utc"])
    snap["_home_key"] = snap["home_team"].astype(str).map(normalize_team_name)
    snap["_away_key"] = snap["away_team"].astype(str).map(normalize_team_name)

    event_latest = (
        snap.groupby(["league", "event_id", "_home_key", "_away_key"], as_index=False)["snapshot_time_utc"]
        .max()
        .rename(columns={"snapshot_time_utc": "event_last_seen_utc"})
    )
    pair_latest = (
        event_latest.groupby(["league", "_home_key", "_away_key"], as_index=False)["event_last_seen_utc"]
        .max()
        .rename(columns={"event_last_seen_utc": "pair_last_seen_utc"})
    )
    event_latest = event_latest.merge(pair_latest, on=["league", "_home_key", "_away_key"], how="left")
    stale_ids = set(
        event_latest.loc[
            event_latest["event_last_seen_utc"] < event_latest["pair_last_seen_utc"],
            ["league", "event_id"],
        ].itertuples(index=False, name=None)
    )

    result = coverage.copy()
    if "reason" not in result.columns or "status" not in result.columns:
        raise ValueError("coverage missing status/reason columns")
    mask = result.apply(lambda row: (str(row["league"]), str(row["event_id"])) in stale_ids, axis=1)
    # Do not hide a stronger internal event-id conflict; that remains fail-closed.
    mask &= result["status"].astype(str) != "CONFLICT"
    result.loc[mask, "status"] = STATUS_SUPERSEDED
    result.loc[mask, "reason"] = "OLDER_PROVIDER_REVISION_FOR_SAME_FIXTURE_PAIR"
    return result
