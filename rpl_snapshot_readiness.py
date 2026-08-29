"""RPL snapshot-readiness checks for market-only research activation.

Pure helpers only: no network calls, persistence, models, or Structural V2.
"""

from __future__ import annotations

import pandas as pd

from league_runtime_config import RPL_RUNTIME_CONFIG


REQUIRED_COLUMNS = {
    "league",
    "event_id",
    "snapshot_time_utc",
    "commence_time_utc",
    "home_team",
    "away_team",
    "home_odds",
    "draw_odds",
    "away_odds",
}


def normalize_rpl_team(value: str) -> str:
    name = str(value).strip()
    if not name:
        return name
    return RPL_RUNTIME_CONFIG.aliases.get(name, name)


def audit_snapshot_readiness(snapshots: pd.DataFrame) -> dict:
    """Return deterministic readiness diagnostics for supplied RPL snapshots."""
    missing = sorted(REQUIRED_COLUMNS - set(snapshots.columns))
    if missing:
        return {
            "ready": False,
            "reason": "MISSING_COLUMNS",
            "missing_columns": missing,
            "rows": len(snapshots),
        }

    if snapshots.empty:
        return {
            "ready": False,
            "reason": "NO_SNAPSHOTS",
            "missing_columns": [],
            "rows": 0,
        }

    work = snapshots.copy()
    if not (work["league"].astype(str) == "RPL").all():
        return {
            "ready": False,
            "reason": "NON_RPL_ROWS",
            "missing_columns": [],
            "rows": len(work),
        }

    work["snapshot_time_utc"] = pd.to_datetime(
        work["snapshot_time_utc"], utc=True, errors="coerce"
    )
    work["commence_time_utc"] = pd.to_datetime(
        work["commence_time_utc"], utc=True, errors="coerce"
    )

    for column in ("home_odds", "draw_odds", "away_odds"):
        work[column] = pd.to_numeric(work[column], errors="coerce")

    invalid_time = work[
        ["snapshot_time_utc", "commence_time_utc"]
    ].isna().any(axis=1)
    invalid_odds = work[
        ["home_odds", "draw_odds", "away_odds"]
    ].isna().any(axis=1)
    post_kickoff = (
        work["snapshot_time_utc"].notna()
        & work["commence_time_utc"].notna()
        & (work["snapshot_time_utc"] >= work["commence_time_utc"])
    )

    team_values = pd.concat(
        [work["home_team"], work["away_team"]], ignore_index=True
    ).astype(str).str.strip()
    empty_team = team_values.eq("").any()

    normalized = sorted({normalize_rpl_team(value) for value in team_values if value})
    aliases_used = sorted(
        {
            value
            for value in team_values
            if value in RPL_RUNTIME_CONFIG.aliases
        }
    )

    ready = not (
        invalid_time.any()
        or invalid_odds.any()
        or post_kickoff.any()
        or empty_team
    )

    return {
        "ready": bool(ready),
        "reason": "READY" if ready else "INVALID_ROWS",
        "missing_columns": [],
        "rows": len(work),
        "unique_events": int(work["event_id"].astype(str).nunique()),
        "invalid_time_rows": int(invalid_time.sum()),
        "invalid_odds_rows": int(invalid_odds.sum()),
        "post_kickoff_rows": int(post_kickoff.sum()),
        "normalized_teams": normalized,
        "aliases_used": aliases_used,
    }
