"""League-level manual refresh priority for prospective market-path collection.

Read-only and provider-free. The function ranks leagues using only already
persisted coverage diagnostics. It does not change frozen research eligibility,
collector cadence, or paid workflow behavior.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from prospective_market_path import LEAGUES
from prospective_market_path_revisions import (
    STATUS_QUARANTINED_REVISION,
    STATUS_SUPERSEDED,
)

EXCLUDED_OPERATIONAL_STATUSES = {
    STATUS_SUPERSEDED,
    STATUS_QUARANTINED_REVISION,
}


def build_league_refresh_priority(coverage: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic league-level priority metrics for manual refresh.

    Ranking is intentionally policy-light: among leagues with at least one active
    due path, prefer the earliest path cutoff; then more due paths; then greater
    staleness relative to the league's existing collector cadence. No new cadence
    or spending threshold is introduced here.
    """
    rows: list[dict] = []
    for league in LEAGUES:
        frame = coverage[coverage["league"].astype(str) == league].copy() if not coverage.empty else pd.DataFrame()
        if frame.empty:
            due = pd.DataFrame()
        else:
            status = frame["status"].astype(str)
            operational = frame.get("operationally_active", pd.Series(False, index=frame.index))
            operational = operational.fillna(False).astype(bool)
            refresh_due = frame.get("refresh_due", pd.Series(False, index=frame.index))
            refresh_due = refresh_due.fillna(False).astype(bool)
            due = frame[
                operational
                & refresh_due
                & ~status.isin(EXCLUDED_OPERATIONAL_STATUSES)
            ].copy()

        earliest = float("nan")
        max_ratio = float("nan")
        if not due.empty:
            cutoff_hours = pd.to_numeric(due["hours_until_cutoff"], errors="coerce")
            ages = pd.to_numeric(due["hours_since_last_snapshot"], errors="coerce")
            intervals = pd.to_numeric(due["refresh_interval_hours"], errors="coerce")
            ratios = ages / intervals.replace(0, np.nan)
            earliest = float(cutoff_hours.min())
            max_ratio = float(ratios.max())

        rows.append({
            "league": league,
            "priority_due_paths": int(len(due)),
            "earliest_due_cutoff_hours": earliest,
            "max_due_staleness_ratio": max_ratio,
        })

    result = pd.DataFrame(rows)
    result["refresh_priority_rank"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    candidates = result[result["priority_due_paths"] > 0].copy()
    if not candidates.empty:
        ordered = candidates.sort_values(
            [
                "earliest_due_cutoff_hours",
                "priority_due_paths",
                "max_due_staleness_ratio",
                "league",
            ],
            ascending=[True, False, False, True],
            na_position="last",
        )
        for rank, idx in enumerate(ordered.index, start=1):
            result.loc[idx, "refresh_priority_rank"] = rank
    return result
