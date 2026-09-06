"""Frozen row selection for EPL_AI_MARKET_PAIR_V1 evaluation.

This module is outcome-free. It selects the single preregistered paired row per event
*before* any caller may join target results. It performs no fitting or threshold search.
"""
from __future__ import annotations

import pandas as pd

EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
LEAGUE = "EPL"
FROZEN_MODEL_SHA256 = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"

REQUIRED_COLUMNS = {
    "pair_key",
    "experiment_id",
    "league",
    "event_id",
    "provider_home_team",
    "provider_away_team",
    "kickoff_utc",
    "market_snapshot_time_utc",
    "model_generated_at_utc",
    "model_artifact_sha256",
    "market_home_prob",
    "market_draw_prob",
    "market_away_prob",
    "model_home_prob",
    "model_draw_prob",
    "model_away_prob",
}


def select_frozen_evaluation_pairs(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Select exactly one preregistered pair per unambiguous event.

    Rules frozen before target outcomes are used:
    - only EPL_AI_MARKET_PAIR_V1 rows from the first live model SHA are eligible;
    - both market snapshot and model generation must be pre-kickoff;
    - any event_id carrying multiple kickoff/home/away identities is excluded entirely;
    - otherwise choose maximum market_snapshot_time_utc;
    - exact timestamp ties resolve by pair_key ascending.
    """
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"paired evidence missing columns: {sorted(missing)}")
    if frame.empty:
        return frame.copy(), []

    work = frame.copy()
    for column in ("kickoff_utc", "market_snapshot_time_utc", "model_generated_at_utc"):
        work[column] = pd.to_datetime(work[column], utc=True, errors="coerce")
    if work[["kickoff_utc", "market_snapshot_time_utc", "model_generated_at_utc"]].isna().any(axis=None):
        raise ValueError("paired evidence contains invalid timestamps")

    work = work.loc[
        (work["experiment_id"].astype(str) == EXPERIMENT_ID)
        & (work["league"].astype(str) == LEAGUE)
        & (work["model_artifact_sha256"].astype(str) == FROZEN_MODEL_SHA256)
        & (work["market_snapshot_time_utc"] < work["kickoff_utc"])
        & (work["model_generated_at_utc"] < work["kickoff_utc"])
    ].copy()
    if work.empty:
        return work, []

    identity = work.groupby("event_id").agg(
        kickoff_count=("kickoff_utc", "nunique"),
        home_count=("provider_home_team", "nunique"),
        away_count=("provider_away_team", "nunique"),
    )
    ambiguous_ids = sorted(identity.index[(identity > 1).any(axis=1)].astype(str))
    excluded = [
        {"event_id": event_id, "reason": "AMBIGUOUS_EVENT_IDENTITY"}
        for event_id in ambiguous_ids
    ]
    if ambiguous_ids:
        work = work.loc[~work["event_id"].astype(str).isin(ambiguous_ids)].copy()
    if work.empty:
        return work, excluded

    if work["pair_key"].duplicated().any():
        raise RuntimeError("duplicate pair_key in paired evidence")

    selected = (
        work.sort_values(
            ["event_id", "market_snapshot_time_utc", "pair_key"],
            ascending=[True, False, True],
        )
        .groupby("event_id", as_index=False, sort=False)
        .head(1)
        .sort_values(["kickoff_utc", "event_id"])
        .reset_index(drop=True)
    )
    return selected, excluded
