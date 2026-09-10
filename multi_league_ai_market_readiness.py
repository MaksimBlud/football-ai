"""Outcome-free readiness audit for cross-league AI-vs-market evidence.

This module exists to keep two different things separate:

* ``league_prediction_ledger`` is canonical multi-league MARKET_ONLY research data.
* ``epl_ai_market_pair_ledger`` is the current paired Football-AI-vs-market evidence
  with explicit model/code provenance.

The audit never reads outcomes, settlements, or finished-result tables and never
promotes a model.  In particular, historical MARKET_ONLY rows are not silently
reclassified as prospective AI evidence.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


OPERATIONAL_TABLE = "league_prediction_ledger"
EPL_PAIR_TABLE = "epl_ai_market_pair_ledger"
EPL_EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"

OPERATIONAL_REQUIRED = {
    "league",
    "event_id",
    "prediction_mode",
    "structural_status",
    "structural_applied",
}
PAIR_REQUIRED = {
    "pair_key",
    "experiment_id",
    "league",
    "event_id",
    "kickoff_utc",
    "market_snapshot_time_utc",
    "model_generated_at_utc",
    "history_cutoff_utc",
    "model_home_prob",
    "model_draw_prob",
    "model_away_prob",
    "model_artifact_sha256",
    "code_commit_sha",
}


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def _nonempty_text(series: pd.Series) -> pd.Series:
    return series.notna() & series.astype(str).str.strip().ne("")


def validate_pair_provenance(pairs: pd.DataFrame) -> pd.Series:
    """Return a boolean validity mask without consulting target outcomes."""
    _require_columns(pairs, PAIR_REQUIRED, "AI-market pair ledger")
    if pairs.empty:
        return pd.Series(dtype=bool, index=pairs.index)

    kickoff = pd.to_datetime(pairs["kickoff_utc"], utc=True, errors="coerce")
    market = pd.to_datetime(pairs["market_snapshot_time_utc"], utc=True, errors="coerce")
    generated = pd.to_datetime(pairs["model_generated_at_utc"], utc=True, errors="coerce")
    history = pd.to_datetime(pairs["history_cutoff_utc"], utc=True, errors="coerce")

    probs = pairs[["model_home_prob", "model_draw_prob", "model_away_prob"]].apply(
        pd.to_numeric, errors="coerce"
    )
    prob_ok = (
        probs.notna().all(axis=1)
        & probs.ge(0.0).all(axis=1)
        & probs.le(1.0).all(axis=1)
        & probs.sum(axis=1).sub(1.0).abs().le(1e-6)
    )

    return (
        kickoff.notna()
        & market.notna()
        & generated.notna()
        & history.notna()
        & market.lt(kickoff)
        & generated.lt(kickoff)
        & history.le(market)
        & prob_ok
        & _nonempty_text(pairs["model_artifact_sha256"])
        & _nonempty_text(pairs["code_commit_sha"])
        & _nonempty_text(pairs["pair_key"])
    )


def build_readiness_report(
    operational: pd.DataFrame,
    epl_pairs: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize what the current prospective rows can honestly prove.

    ``eligible_for_new_multileague_primary`` is deliberately false for every row.
    A future multi-league primary cohort must be frozen after league-specific AI
    provenance is available; already-collected MARKET_ONLY rows cannot be admitted
    retroactively by this audit.
    """
    _require_columns(operational, OPERATIONAL_REQUIRED, "operational ledger")
    _require_columns(epl_pairs, PAIR_REQUIRED, "AI-market pair ledger")

    valid_pair_mask = validate_pair_provenance(epl_pairs)
    valid_pairs = epl_pairs.loc[valid_pair_mask].copy()

    leagues = sorted(
        set(operational["league"].dropna().astype(str))
        | set(epl_pairs["league"].dropna().astype(str))
    )
    rows: list[dict[str, Any]] = []

    for league in leagues:
        op = operational.loc[operational["league"].astype(str) == league]
        pair = epl_pairs.loc[epl_pairs["league"].astype(str) == league]
        valid_pair = valid_pairs.loc[valid_pairs["league"].astype(str) == league]

        operational_events = int(op["event_id"].astype(str).nunique())
        market_only_events = int(
            op.loc[op["prediction_mode"].astype(str) == "MARKET_ONLY", "event_id"]
            .astype(str)
            .nunique()
        )
        calibration_required_events = int(
            op.loc[
                op["structural_status"].astype(str) == "CALIBRATION_REQUIRED",
                "event_id",
            ]
            .astype(str)
            .nunique()
        )
        structural_applied_events = int(
            op.loc[op["structural_applied"].fillna(False).astype(bool), "event_id"]
            .astype(str)
            .nunique()
        )
        paired_ai_events = int(pair["event_id"].astype(str).nunique())
        valid_paired_ai_events = int(valid_pair["event_id"].astype(str).nunique())

        if valid_paired_ai_events:
            evidence_status = "EXISTING_EPL_PAIRED_AI_EVIDENCE" if league == "EPL" else "PAIRED_AI_PROVENANCE_PRESENT"
        elif operational_events and market_only_events == operational_events:
            evidence_status = "MARKET_ONLY_NO_PAIRED_AI_PROVENANCE"
        else:
            evidence_status = "NO_VALIDATED_PAIRED_AI_EVIDENCE"

        rows.append(
            {
                "league": league,
                "operational_events": operational_events,
                "market_only_events": market_only_events,
                "calibration_required_events": calibration_required_events,
                "structural_applied_events": structural_applied_events,
                "paired_ai_events": paired_ai_events,
                "valid_paired_ai_events": valid_paired_ai_events,
                "evidence_status": evidence_status,
                "eligible_for_new_multileague_primary": False,
            }
        )

    return pd.DataFrame(rows)


def assert_no_false_ai_promotion(report: pd.DataFrame) -> None:
    """Fail if MARKET_ONLY coverage is being represented as paired AI evidence."""
    required = {
        "operational_events",
        "market_only_events",
        "valid_paired_ai_events",
        "eligible_for_new_multileague_primary",
    }
    _require_columns(report, required, "readiness report")
    if report["eligible_for_new_multileague_primary"].astype(bool).any():
        raise RuntimeError("Readiness audit must not activate a prospective cohort")
    impossible = report["valid_paired_ai_events"] > report["operational_events"]
    # EPL pair collection can theoretically outlive canonical operational retention,
    # but that is not true of the current contract and should be reviewed explicitly.
    if impossible.any():
        raise RuntimeError("Paired AI event count exceeds operational event coverage")
