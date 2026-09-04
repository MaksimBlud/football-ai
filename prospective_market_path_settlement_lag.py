"""Read-only settlement-lag audit for PROSPECTIVE_MARKET_PATH_V1.

The audit never reads result values. It only checks whether an eligible market-path
fixture has a canonical identity present in `league_finished_results` after a
conservative post-kickoff grace period.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from league_config import get_league_config
from prospective_market_path import LEAGUES
from team_names import normalize_team_name

SETTLEMENT_GRACE_HOURS = 18
STATUS_PRESENT = "SETTLED_IDENTITY_PRESENT"
STATUS_AWAITING = "AWAITING_GRACE"
STATUS_LATE = "SETTLEMENT_LATE"


def _team_key(value) -> str:
    return normalize_team_name(str(value))


def audit_settlement_lag(paths: pd.DataFrame, results_identity: pd.DataFrame, *, now_utc: pd.Timestamp | None = None) -> pd.DataFrame:
    required_paths = {"league", "event_id", "home_team", "away_team", "kickoff_utc"}
    missing_paths = required_paths - set(paths.columns)
    if missing_paths:
        raise ValueError("paths missing columns: " + ", ".join(sorted(missing_paths)))
    required_results = {"league", "match_date", "home_team", "away_team"}
    missing_results = required_results - set(results_identity.columns)
    if missing_results:
        raise ValueError("results identity missing columns: " + ", ".join(sorted(missing_results)))

    now = pd.Timestamp(now_utc if now_utc is not None else datetime.now(timezone.utc))
    now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
    rows: list[dict] = []

    for league in LEAGUES:
        p = paths[paths["league"].astype(str) == league].copy()
        if p.empty:
            continue
        r = results_identity[results_identity["league"].astype(str) == league].copy()
        timezone_name = get_league_config(league).timezone
        p["kickoff_utc"] = pd.to_datetime(p["kickoff_utc"], utc=True, errors="coerce")
        p = p.dropna(subset=["kickoff_utc"])
        p["match_date_key"] = p["kickoff_utc"].dt.tz_convert(timezone_name).dt.date
        p["home_key"] = p["home_team"].map(_team_key)
        p["away_key"] = p["away_team"].map(_team_key)

        if r.empty:
            known: set[tuple] = set()
        else:
            r["match_date_key"] = pd.to_datetime(r["match_date"], errors="coerce").dt.date
            r["home_key"] = r["home_team"].map(_team_key)
            r["away_key"] = r["away_team"].map(_team_key)
            known = set(r[["match_date_key", "home_key", "away_key"]].dropna().itertuples(index=False, name=None))

        identity = ["match_date_key", "home_key", "away_key"]
        ambiguous = p.duplicated(identity, keep=False)
        if ambiguous.any():
            p = p.loc[~ambiguous].copy()

        for row in p.itertuples(index=False):
            key = (row.match_date_key, row.home_key, row.away_key)
            present = key in known
            grace_deadline = pd.Timestamp(row.kickoff_utc) + pd.Timedelta(hours=SETTLEMENT_GRACE_HOURS)
            if present:
                status, reason = STATUS_PRESENT, "CANONICAL_RESULT_IDENTITY_PRESENT"
            elif now <= grace_deadline:
                status, reason = STATUS_AWAITING, "WITHIN_POST_KICKOFF_GRACE"
            else:
                status, reason = STATUS_LATE, "CANONICAL_RESULT_IDENTITY_MISSING_AFTER_GRACE"
            rows.append({
                "league": league,
                "event_id": str(row.event_id),
                "home_team": str(row.home_team),
                "away_team": str(row.away_team),
                "kickoff_utc": pd.Timestamp(row.kickoff_utc),
                "grace_deadline_utc": grace_deadline,
                "status": status,
                "reason": reason,
            })
    return pd.DataFrame(rows)


def summarize_settlement_lag(audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league in LEAGUES:
        frame = audit[audit["league"].astype(str) == league] if not audit.empty else pd.DataFrame()
        counts = frame["status"].value_counts().to_dict() if not frame.empty else {}
        rows.append({
            "league": league,
            "eligible_paths": int(len(frame)),
            "settled_identity_present": int(counts.get(STATUS_PRESENT, 0)),
            "awaiting_grace": int(counts.get(STATUS_AWAITING, 0)),
            "settlement_late": int(counts.get(STATUS_LATE, 0)),
        })
    return pd.DataFrame(rows)
