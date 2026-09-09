"""Read-only operator status for prospective market-path collection.

Combines frozen fixture coverage, provider revision classification, and the
existing manual refresh cadence. This module never calls a provider, writes
Supabase, reads match outcomes, or changes research eligibility.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from prospective_market_path import LEAGUES
from prospective_market_path_coverage import (
    build_fixture_coverage,
    summarize_fixture_coverage,
)
from prospective_market_path_refresh_priority import (
    EXCLUDED_OPERATIONAL_STATUSES,
    build_league_refresh_priority,
)
from prospective_market_path_revisions import (
    STATUS_QUARANTINED_REVISION,
    STATUS_SUPERSEDED,
    mark_superseded_revisions,
)


@dataclass(frozen=True)
class MarketStatus:
    coverage: pd.DataFrame
    leagues: pd.DataFrame
    live_refresh_queue: pd.DataFrame


LIVE_QUEUE_COLUMNS = [
    "live_priority_rank",
    "league",
    "event_id",
    "home_team",
    "away_team",
    "kickoff_utc",
    "cutoff_utc",
    "status",
    "snapshot_count_before_cutoff",
    "last_snapshot_utc",
    "hours_until_cutoff",
    "hours_since_last_snapshot",
    "refresh_interval_hours",
    "staleness_ratio",
    "refresh_reason",
]


def build_revision_aware_coverage(
    snapshots: pd.DataFrame,
    *,
    now_utc: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Build frozen coverage, then apply provider revision safety classifications."""
    coverage = build_fixture_coverage(snapshots, now_utc=now_utc)
    return mark_superseded_revisions(coverage, snapshots)


def build_live_refresh_queue(coverage: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic fixture-level manual refresh priority.

    Only active paths that are due under the already-existing league collector
    cadence are actionable. Superseded and quarantined revisions remain
    fail-closed even if malformed input marks them active/due.
    """
    if coverage.empty:
        return pd.DataFrame(columns=LIVE_QUEUE_COLUMNS)

    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "cutoff_utc",
        "status",
        "snapshot_count_before_cutoff",
        "last_snapshot_utc",
        "hours_until_cutoff",
        "hours_since_last_snapshot",
        "refresh_interval_hours",
        "refresh_due",
        "refresh_reason",
        "operationally_active",
    }
    missing = required - set(coverage.columns)
    if missing:
        raise ValueError("coverage missing live-priority columns: " + ", ".join(sorted(missing)))

    status = coverage["status"].astype(str)
    operational = coverage["operationally_active"].fillna(False).astype(bool)
    refresh_due = coverage["refresh_due"].fillna(False).astype(bool)
    due = coverage[
        operational
        & refresh_due
        & ~status.isin(EXCLUDED_OPERATIONAL_STATUSES)
    ].copy()

    if due.empty:
        return pd.DataFrame(columns=LIVE_QUEUE_COLUMNS)

    ages = pd.to_numeric(due["hours_since_last_snapshot"], errors="coerce")
    intervals = pd.to_numeric(due["refresh_interval_hours"], errors="coerce")
    due["staleness_ratio"] = ages / intervals.where(intervals > 0)
    due = due.sort_values(
        ["hours_until_cutoff", "staleness_ratio", "league", "kickoff_utc", "event_id"],
        ascending=[True, False, True, True, True],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)
    due.insert(0, "live_priority_rank", range(1, len(due) + 1))
    return due[LIVE_QUEUE_COLUMNS]


def _revision_counts(coverage: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for league in LEAGUES:
        frame = (
            coverage[coverage["league"].astype(str) == league].copy()
            if not coverage.empty
            else pd.DataFrame()
        )
        if frame.empty:
            operational = 0
            actionable = 0
            superseded = 0
            quarantined = 0
        else:
            status = frame["status"].astype(str)
            active = frame["operationally_active"].fillna(False).astype(bool)
            due = frame["refresh_due"].fillna(False).astype(bool)
            operational = int(active.sum())
            actionable = int(
                (active & due & ~status.isin(EXCLUDED_OPERATIONAL_STATUSES)).sum()
            )
            superseded = int(status.eq(STATUS_SUPERSEDED).sum())
            quarantined = int(status.eq(STATUS_QUARANTINED_REVISION).sum())
        rows.append(
            {
                "league": league,
                "operationally_active": operational,
                "actionable_refresh_due": actionable,
                "superseded": superseded,
                "quarantined_revision": quarantined,
            }
        )
    return pd.DataFrame(rows)


def build_market_status(
    snapshots: pd.DataFrame,
    *,
    now_utc: pd.Timestamp | None = None,
) -> MarketStatus:
    """Return revision-aware coverage, league status, and fixture live queue."""
    coverage = build_revision_aware_coverage(snapshots, now_utc=now_utc)
    summary = summarize_fixture_coverage(coverage)
    revisions = _revision_counts(coverage)
    priority = build_league_refresh_priority(coverage)

    leagues = (
        summary.merge(revisions, on="league", how="left", validate="one_to_one")
        .merge(priority, on="league", how="left", validate="one_to_one")
    )
    queue = build_live_refresh_queue(coverage)

    if not queue.empty:
        next_rank = (
            queue.groupby("league", as_index=False)["live_priority_rank"]
            .min()
            .rename(columns={"live_priority_rank": "next_live_priority_rank"})
        )
        leagues = leagues.merge(next_rank, on="league", how="left", validate="one_to_one")
    else:
        leagues["next_live_priority_rank"] = pd.Series(
            pd.NA, index=leagues.index, dtype="Int64"
        )

    leagues["next_live_priority_rank"] = leagues["next_live_priority_rank"].astype("Int64")
    return MarketStatus(
        coverage=coverage,
        leagues=leagues,
        live_refresh_queue=queue,
    )


def render_market_status(status: MarketStatus) -> str:
    """Render a compact operator-facing read-only status."""
    lines = [
        "PROSPECTIVE MARKET STATUS",
        "Read-only. Provider-free. No writes. Frozen research eligibility unchanged.",
        "",
    ]
    for row in status.leagues.itertuples(index=False):
        rank = "-" if pd.isna(row.refresh_priority_rank) else str(int(row.refresh_priority_rank))
        next_fixture = "-" if pd.isna(row.next_live_priority_rank) else str(int(row.next_live_priority_rank))
        lines.append(
            f"{row.league}: active={row.operationally_active}, "
            f"ready={row.ready}, recoverable={row.recoverable}, "
            f"irrecoverable={row.irrecoverable}, conflict={row.conflict}, "
            f"superseded={row.superseded}, quarantined={row.quarantined_revision}, "
            f"due={row.actionable_refresh_due}, league_priority={rank}, "
            f"next_fixture_priority={next_fixture}"
        )

    lines.append("")
    if status.live_refresh_queue.empty:
        lines.append("NEXT: no active fixture currently requires manual refresh.")
    else:
        first = status.live_refresh_queue.iloc[0]
        lines.append(
            "NEXT: "
            f"#{int(first['live_priority_rank'])} {first['league']} "
            f"{first['home_team']} vs {first['away_team']} "
            f"(event_id={first['event_id']})"
        )
    return "\n".join(lines)
