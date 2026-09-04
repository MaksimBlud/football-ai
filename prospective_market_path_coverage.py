"""Read-only fixture-level coverage monitor for PROSPECTIVE_MARKET_PATH_V1.

This module does not change the frozen research protocol. It only reports
whether each prospective fixture already satisfies, can still satisfy, or can
no longer satisfy the preregistered path-coverage requirements.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from prospective_market_path import (
    CUTOFF_HOURS,
    FREEZE_UTC,
    LEAGUES,
    MIN_PATH_SPAN_HOURS,
    MIN_SNAPSHOTS,
)

STATUS_READY = "READY"
STATUS_RECOVERABLE = "RECOVERABLE"
STATUS_IRRECOVERABLE = "IRRECOVERABLE"
STATUS_CONFLICT = "CONFLICT"


def _utc_now() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(timezone.utc))


def build_fixture_coverage(
    snapshots: pd.DataFrame,
    *,
    now_utc: pd.Timestamp | None = None,
) -> pd.DataFrame:
    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "commence_time_utc",
        "snapshot_time_utc",
    }
    missing = required - set(snapshots.columns)
    if missing:
        raise ValueError("snapshots missing columns: " + ", ".join(sorted(missing)))

    now = pd.Timestamp(now_utc if now_utc is not None else _utc_now())
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")

    work = snapshots.copy()
    work = work[work["league"].astype(str).isin(LEAGUES)].copy()
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
    work = work.dropna(subset=["commence_time_utc", "snapshot_time_utc"])
    work = work[work["commence_time_utc"] >= FREEZE_UTC].copy()
    if work.empty:
        return pd.DataFrame(columns=[
            "league", "event_id", "home_team", "away_team", "kickoff_utc", "cutoff_utc",
            "snapshot_count_before_cutoff", "first_snapshot_utc", "last_snapshot_utc",
            "path_span_hours", "hours_until_cutoff", "status", "reason",
        ])

    rows: list[dict] = []
    for (league, event_id), group in work.groupby(["league", "event_id"], sort=False):
        kickoff_values = pd.Series(group["commence_time_utc"].dropna().unique())
        if len(kickoff_values) != 1:
            last = group.sort_values("snapshot_time_utc").iloc[-1]
            rows.append({
                "league": str(league),
                "event_id": str(event_id),
                "home_team": str(last["home_team"]),
                "away_team": str(last["away_team"]),
                "kickoff_utc": pd.NaT,
                "cutoff_utc": pd.NaT,
                "snapshot_count_before_cutoff": 0,
                "first_snapshot_utc": pd.NaT,
                "last_snapshot_utc": pd.NaT,
                "path_span_hours": 0.0,
                "hours_until_cutoff": float("nan"),
                "status": STATUS_CONFLICT,
                "reason": "MULTIPLE_KICKOFFS_FOR_EVENT_ID",
            })
            continue

        kickoff = pd.Timestamp(kickoff_values.iloc[0])
        cutoff = kickoff - pd.Timedelta(hours=CUTOFF_HOURS)
        eligible = (
            group[group["snapshot_time_utc"] <= cutoff]
            .sort_values("snapshot_time_utc")
            .drop_duplicates("snapshot_time_utc", keep="last")
        )
        count = int(len(eligible))
        first = pd.Timestamp(eligible["snapshot_time_utc"].iloc[0]) if count else pd.NaT
        last = pd.Timestamp(eligible["snapshot_time_utc"].iloc[-1]) if count else pd.NaT
        span = float((last - first).total_seconds() / 3600.0) if count >= 2 else 0.0
        hours_until_cutoff = float((cutoff - now).total_seconds() / 3600.0)

        if count >= MIN_SNAPSHOTS and span >= MIN_PATH_SPAN_HOURS:
            status = STATUS_READY
            reason = "FROZEN_PATH_REQUIREMENTS_ALREADY_MET"
        elif now > cutoff:
            status = STATUS_IRRECOVERABLE
            reason = "CUTOFF_ALREADY_PASSED"
        else:
            earliest_possible = first if count else now
            maximum_possible_span = float((cutoff - earliest_possible).total_seconds() / 3600.0)
            if maximum_possible_span < MIN_PATH_SPAN_HOURS:
                status = STATUS_IRRECOVERABLE
                reason = "INSUFFICIENT_REMAINING_SPAN_BEFORE_CUTOFF"
            else:
                status = STATUS_RECOVERABLE
                reason = "PATH_CAN_STILL_MEET_FROZEN_REQUIREMENTS"

        last_row = group.sort_values("snapshot_time_utc").iloc[-1]
        rows.append({
            "league": str(league),
            "event_id": str(event_id),
            "home_team": str(last_row["home_team"]),
            "away_team": str(last_row["away_team"]),
            "kickoff_utc": kickoff,
            "cutoff_utc": cutoff,
            "snapshot_count_before_cutoff": count,
            "first_snapshot_utc": first,
            "last_snapshot_utc": last,
            "path_span_hours": span,
            "hours_until_cutoff": hours_until_cutoff,
            "status": status,
            "reason": reason,
        })

    return pd.DataFrame(rows).sort_values(["league", "kickoff_utc", "event_id"], na_position="last").reset_index(drop=True)


def summarize_fixture_coverage(coverage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league in LEAGUES:
        frame = coverage[coverage["league"].astype(str) == league] if not coverage.empty else pd.DataFrame()
        counts = frame["status"].value_counts().to_dict() if not frame.empty else {}
        rows.append({
            "league": league,
            "fixtures_seen": int(len(frame)),
            "ready": int(counts.get(STATUS_READY, 0)),
            "recoverable": int(counts.get(STATUS_RECOVERABLE, 0)),
            "irrecoverable": int(counts.get(STATUS_IRRECOVERABLE, 0)),
            "conflict": int(counts.get(STATUS_CONFLICT, 0)),
        })
    return pd.DataFrame(rows)
