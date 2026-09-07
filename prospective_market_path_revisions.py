"""Provider schedule-revision helpers for prospective market-path research.

A league home/away pairing should have one currently observed provider event.
When the provider re-keys or reschedules a fixture, stale event ids may remain in
immutable snapshot history. This module marks clearly superseded event ids and
quarantines deterministic same-event schedule revisions without choosing a
kickoff for frozen research.
"""
from __future__ import annotations

import pandas as pd

from team_names import normalize_team_name

STATUS_SUPERSEDED = "SUPERSEDED"
STATUS_QUARANTINED_REVISION = "QUARANTINED_REVISION"


def _monotonic_schedule_revision_ids(snapshots: pd.DataFrame) -> set[tuple[str, str]]:
    """Return event ids whose kickoff variants form non-overlapping time blocks.

    This is an operational classification only. It never selects a canonical
    kickoff: the entire event remains excluded from frozen market-path research.
    If a kickoff reappears after another revision, or variant observation windows
    overlap, the event stays a hard CONFLICT.
    """
    required = {"league", "event_id", "commence_time_utc", "snapshot_time_utc"}
    missing = required - set(snapshots.columns)
    if missing:
        return set()

    work = snapshots.copy()
    work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    work = work.dropna(subset=["snapshot_time_utc", "commence_time_utc"])

    quarantined: set[tuple[str, str]] = set()
    for (league, event_id), group in work.groupby(["league", "event_id"], sort=False):
        variants = (
            group.groupby("commence_time_utc", as_index=False)["snapshot_time_utc"]
            .agg(first_seen_utc="min", last_seen_utc="max")
            .sort_values("first_seen_utc")
            .reset_index(drop=True)
        )
        if len(variants) < 2:
            continue
        non_overlapping = all(
            variants.loc[i, "last_seen_utc"] < variants.loc[i + 1, "first_seen_utc"]
            for i in range(len(variants) - 1)
        )
        if non_overlapping:
            quarantined.add((str(league), str(event_id)))
    return quarantined


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
    quarantined_ids = _monotonic_schedule_revision_ids(snap)

    result = coverage.copy()
    if "reason" not in result.columns or "status" not in result.columns:
        raise ValueError("coverage missing status/reason columns")

    stale_mask = result.apply(lambda row: (str(row["league"]), str(row["event_id"])) in stale_ids, axis=1)
    stale_mask &= result["status"].astype(str) != "CONFLICT"
    result.loc[stale_mask, "status"] = STATUS_SUPERSEDED
    result.loc[stale_mask, "reason"] = "OLDER_PROVIDER_REVISION_FOR_SAME_FIXTURE_PAIR"

    quarantine_mask = result.apply(
        lambda row: (str(row["league"]), str(row["event_id"])) in quarantined_ids,
        axis=1,
    )
    quarantine_mask &= result["status"].astype(str) == "CONFLICT"
    result.loc[quarantine_mask, "status"] = STATUS_QUARANTINED_REVISION
    result.loc[quarantine_mask, "reason"] = "MONOTONIC_PROVIDER_SCHEDULE_REVISION_RESEARCH_EXCLUDED"
    if "operationally_active" in result.columns:
        result.loc[quarantine_mask, "operationally_active"] = False
    if "refresh_due" in result.columns:
        result.loc[quarantine_mask, "refresh_due"] = False
    if "refresh_reason" in result.columns:
        result.loc[quarantine_mask, "refresh_reason"] = "RESEARCH_QUARANTINED_PROVIDER_REVISION"
    return result
