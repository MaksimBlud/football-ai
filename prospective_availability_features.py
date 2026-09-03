"""Frozen V1 count-only availability features for paired market evaluation."""
from __future__ import annotations

import pandas as pd

FEATURE_COLUMNS = (
    "home_injury_count",
    "away_injury_count",
    "injury_count_difference",
    "home_suspension_count",
    "away_suspension_count",
    "suspension_count_difference",
    "home_unavailable_count",
    "away_unavailable_count",
    "unavailable_count_difference",
)


def _utc(series):
    return pd.to_datetime(series, utc=True, errors="coerce")


def build_availability_features(
    market_rows: pd.DataFrame,
    polls: pd.DataFrame,
    observations: pd.DataFrame,
    *,
    cutoff_column: str = "snapshot_time_utc",
) -> pd.DataFrame:
    required_market = {"league", "home_team", "away_team", "commence_time_utc", cutoff_column}
    missing = required_market.difference(market_rows.columns)
    if missing:
        raise ValueError(f"Market rows missing columns: {sorted(missing)}")
    result = market_rows.copy().reset_index(drop=True)
    for column in FEATURE_COLUMNS:
        result[column] = pd.NA
    result["availability_covered"] = False
    result["availability_poll_key"] = pd.NA
    result["availability_poll_observed_at_utc"] = pd.Series(
        pd.NaT,
        index=result.index,
        dtype="datetime64[ns, UTC]",
    )
    if polls.empty:
        return result

    poll_frame = polls.copy()
    poll_frame["commence_time_utc"] = _utc(poll_frame["commence_time_utc"])
    poll_frame["observed_at_utc"] = _utc(poll_frame["observed_at_utc"])
    observation_frame = observations.copy()

    for index, row in result.iterrows():
        cutoff = pd.to_datetime(row[cutoff_column], utc=True, errors="coerce")
        kickoff = pd.to_datetime(row["commence_time_utc"], utc=True, errors="coerce")
        if pd.isna(cutoff) or pd.isna(kickoff) or cutoff >= kickoff:
            continue
        eligible = poll_frame.loc[
            (poll_frame["league"].astype(str) == str(row["league"]))
            & (poll_frame["home_team"].astype(str) == str(row["home_team"]))
            & (poll_frame["away_team"].astype(str) == str(row["away_team"]))
            & (poll_frame["commence_time_utc"] == kickoff)
            & (poll_frame["observed_at_utc"] <= cutoff)
        ].sort_values("observed_at_utc")
        if eligible.empty:
            continue
        poll = eligible.iloc[-1]
        poll_key = str(poll["poll_key"])
        active = observation_frame.loc[
            observation_frame.get("poll_key", pd.Series(dtype=str)).astype(str) == poll_key
        ].copy()
        home_name = str(row["home_team"])
        away_name = str(row["away_team"])

        def distinct_count(team_name: str, kind: str | None = None) -> int:
            frame = active.loc[active.get("team_name", pd.Series(dtype=str)).astype(str) == team_name]
            if kind is not None:
                frame = frame.loc[frame.get("availability_type", pd.Series(dtype=str)).astype(str) == kind]
            return int(frame.get("provider_player_id", pd.Series(dtype=object)).nunique())

        home_injury = distinct_count(home_name, "Injury")
        away_injury = distinct_count(away_name, "Injury")
        home_suspension = distinct_count(home_name, "Suspension")
        away_suspension = distinct_count(away_name, "Suspension")
        home_total = distinct_count(home_name)
        away_total = distinct_count(away_name)
        values = (
            home_injury,
            away_injury,
            home_injury - away_injury,
            home_suspension,
            away_suspension,
            home_suspension - away_suspension,
            home_total,
            away_total,
            home_total - away_total,
        )
        for column, value in zip(FEATURE_COLUMNS, values):
            result.at[index, column] = value
        result.at[index, "availability_covered"] = True
        result.at[index, "availability_poll_key"] = poll_key
        result.at[index, "availability_poll_observed_at_utc"] = poll["observed_at_utc"]
    return result
