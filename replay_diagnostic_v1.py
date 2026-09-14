"""Outcome-free contract and pooled evaluator for REPLAY_DIAGNOSTIC_V1.

This module deliberately separates three evidence classes:
1. genuine prospective EPL AI-vs-market pairs;
2. reconstructed point-in-time AI predictions (only if immutable pre-kickoff
   model/code/history provenance exists); and
3. MARKET_ONLY observations, which are never promoted to AI evidence.

The current-round eligibility constants below were frozen before reading any
settlement outcome values for this diagnostic. The older frozen
EPL_AI_MARKET_PAIR_V1 outcome-read gate always has priority over this secondary
replay diagnostic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import log
from typing import Iterable, Mapping, Sequence

EXPERIMENT_ID = "REPLAY_DIAGNOSTIC_V1"
SOURCE_MAIN_SHA = "202d46796f031caa0c9d7138c402eefb0cc56971"
CAPTURE_START_UTC = "2026-09-11T00:00:00Z"
CAPTURE_END_UTC = "2026-09-12T00:00:00Z"
CURRENT_ROUND_END_UTC = "2026-09-15T00:00:00Z"
INVENTORY_SHA256 = "4934dd8f5e6f287c79ecfad4e910158650fd171d26faae66d9000b23bc5e4828"

# Imported conceptually from the older frozen EPL_AI_MARKET_PAIR_V1 contract.
# REPLAY_DIAGNOSTIC_V1 may never weaken these conditions.
EPL_PRIMARY_COHORT_SIZE = 100
EPL_FIRST_PERMITTED_OUTCOME_READ_UTC = "2026-11-01T12:16:54.672903Z"

SCOPE_LEAGUES = (
    "BUNDESLIGA",
    "EPL",
    "EREDIVISIE",
    "LA_LIGA",
    "LIGUE_1",
    "SERIE_A",
)

CURRENT_ROUND_EVENT_COUNTS = {
    "BUNDESLIGA": 9,
    "EPL": 10,
    "EREDIVISIE": 9,
    "LA_LIGA": 10,
    "LIGUE_1": 9,
    "SERIE_A": 10,
}

# This is the outcome-free eligibility decision. No later outcome may change it.
ELIGIBILITY = {
    "BUNDESLIGA": {
        "replay_eligible_events": 0,
        "prospective_ai_events": 0,
        "reason": "NO_PRE_KICKOFF_IMMUTABLE_AI_ARTIFACT",
    },
    "EPL": {
        "replay_eligible_events": 0,
        "prospective_ai_events": 10,
        "reason": "ALREADY_CAPTURED_AS_PROSPECTIVE_EPL_AI_MARKET_PAIR",
    },
    "EREDIVISIE": {
        "replay_eligible_events": 0,
        "prospective_ai_events": 0,
        "reason": "NO_PRE_KICKOFF_IMMUTABLE_AI_ARTIFACT",
    },
    "LA_LIGA": {
        "replay_eligible_events": 0,
        "prospective_ai_events": 0,
        "reason": "PRE_KICKOFF_CANDIDATE_GATE_REJECTED_NO_ARTIFACT",
    },
    "LIGUE_1": {
        "replay_eligible_events": 0,
        "prospective_ai_events": 0,
        "reason": "NO_PRE_KICKOFF_IMMUTABLE_AI_ARTIFACT",
    },
    "SERIE_A": {
        "replay_eligible_events": 0,
        "prospective_ai_events": 0,
        "reason": "NO_PRE_KICKOFF_IMMUTABLE_AI_ARTIFACT",
    },
}

PRIMARY_METRICS = (
    "ai_brier",
    "market_brier",
    "delta_brier",
    "ai_logloss",
    "market_logloss",
    "delta_logloss",
    "ai_accuracy",
    "market_accuracy",
)


@dataclass(frozen=True)
class PooledMetrics:
    n: int
    ai_brier: float
    market_brier: float
    delta_brier: float
    ai_logloss: float
    market_logloss: float
    delta_logloss: float
    ai_accuracy: float
    market_accuracy: float
    status: str


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def epl_primary_outcome_gate(*, eligible_events: int, now_utc: str) -> dict[str, object]:
    """Mirror the older frozen EPL primary gate; this contract cannot weaken it."""
    if eligible_events < EPL_PRIMARY_COHORT_SIZE:
        return {
            "open": False,
            "outcome_reads_allowed": False,
            "reason": "INSUFFICIENT_PREREGISTERED_EVENTS",
            "required_events": EPL_PRIMARY_COHORT_SIZE,
            "eligible_events": int(eligible_events),
        }
    now = _parse_utc(now_utc)
    fixed_gate = _parse_utc(EPL_FIRST_PERMITTED_OUTCOME_READ_UTC)
    if now < fixed_gate:
        return {
            "open": False,
            "outcome_reads_allowed": False,
            "reason": "PREREGISTERED_GATE_NOT_REACHED",
            "required_events": EPL_PRIMARY_COHORT_SIZE,
            "eligible_events": int(eligible_events),
            "fixed_wall_clock_gate_utc": EPL_FIRST_PERMITTED_OUTCOME_READ_UTC,
        }
    return {
        "open": True,
        "outcome_reads_allowed": True,
        "reason": "WALL_CLOCK_AND_SAMPLE_FLOORS_REACHED",
        "required_events": EPL_PRIMARY_COHORT_SIZE,
        "eligible_events": int(eligible_events),
    }


def validate_preregistered_contract() -> None:
    """Fail closed if frozen scope or eligibility is changed accidentally."""
    if tuple(CURRENT_ROUND_EVENT_COUNTS) != SCOPE_LEAGUES:
        raise RuntimeError("scope league order changed")
    if sum(CURRENT_ROUND_EVENT_COUNTS.values()) != 57:
        raise RuntimeError("current-round inventory must remain exactly 57 events")
    if sum(v["replay_eligible_events"] for v in ELIGIBILITY.values()) != 0:
        raise RuntimeError("replay cohort is frozen empty; do not backfill it")
    if ELIGIBILITY["EPL"]["prospective_ai_events"] != 10:
        raise RuntimeError("current-round EPL prospective coverage must remain 10")
    if any(
        ELIGIBILITY[league]["prospective_ai_events"]
        for league in SCOPE_LEAGUES
        if league != "EPL"
    ):
        raise RuntimeError("non-EPL rows must not be promoted to prospective AI")
    if EPL_PRIMARY_COHORT_SIZE != 100:
        raise RuntimeError("older EPL primary sample gate must remain 100")
    if EPL_FIRST_PERMITTED_OUTCOME_READ_UTC != "2026-11-01T12:16:54.672903Z":
        raise RuntimeError("older EPL wall-clock outcome gate changed")


def _normalize_probs(values: Sequence[float]) -> tuple[float, float, float]:
    if len(values) != 3:
        raise ValueError("expected three H/D/A probabilities")
    probs = tuple(float(x) for x in values)
    if any(x < 0.0 or x > 1.0 for x in probs):
        raise ValueError("probabilities must be in [0, 1]")
    if abs(sum(probs) - 1.0) > 1e-6:
        raise ValueError("probabilities must sum to one")
    return probs


def _brier(outcome: int, probs: Sequence[float]) -> float:
    p = _normalize_probs(probs)
    return sum((p[i] - (1.0 if i == outcome else 0.0)) ** 2 for i in range(3))


def _logloss(outcome: int, probs: Sequence[float]) -> float:
    p = _normalize_probs(probs)
    return -log(max(p[outcome], 1e-15))


def _accuracy(outcome: int, probs: Sequence[float]) -> float:
    p = _normalize_probs(probs)
    return float(max(range(3), key=p.__getitem__) == outcome)


def evaluate_pooled(records: Iterable[Mapping[str, object]]) -> PooledMetrics:
    """Evaluate predeclared pooled H/D/A metrics after the governing gate opens.

    Required record keys: ``outcome`` (0=H, 1=D, 2=A), ``ai_probs`` and
    ``market_probs``. Callers are responsible for satisfying the governing
    experiment's frozen outcome-read gate before obtaining any outcome values.
    This function performs no subgroup selection, threshold tuning, betting
    decision, or optional stopping.
    """
    rows = list(records)
    if not rows:
        raise ValueError("at least one settled paired prediction is required")

    ai_brier: list[float] = []
    market_brier: list[float] = []
    ai_logloss: list[float] = []
    market_logloss: list[float] = []
    ai_accuracy: list[float] = []
    market_accuracy: list[float] = []

    for row in rows:
        outcome = int(row["outcome"])
        if outcome not in (0, 1, 2):
            raise ValueError("outcome must be 0=H, 1=D, or 2=A")
        ai = row["ai_probs"]
        market = row["market_probs"]
        if not isinstance(ai, Sequence) or isinstance(ai, (str, bytes)):
            raise ValueError("ai_probs must be a sequence")
        if not isinstance(market, Sequence) or isinstance(market, (str, bytes)):
            raise ValueError("market_probs must be a sequence")
        ai_brier.append(_brier(outcome, ai))
        market_brier.append(_brier(outcome, market))
        ai_logloss.append(_logloss(outcome, ai))
        market_logloss.append(_logloss(outcome, market))
        ai_accuracy.append(_accuracy(outcome, ai))
        market_accuracy.append(_accuracy(outcome, market))

    mean = lambda xs: sum(xs) / len(xs)
    ab, mb = mean(ai_brier), mean(market_brier)
    al, ml = mean(ai_logloss), mean(market_logloss)
    aa, ma = mean(ai_accuracy), mean(market_accuracy)
    db, dl = ab - mb, al - ml

    if db < 0.0 and dl < 0.0:
        status = "EARLY_SIGNAL"
    elif db > 0.0 and dl > 0.0:
        status = "WARNING"
    else:
        status = "INCONCLUSIVE"

    return PooledMetrics(
        n=len(rows),
        ai_brier=ab,
        market_brier=mb,
        delta_brier=db,
        ai_logloss=al,
        market_logloss=ml,
        delta_logloss=dl,
        ai_accuracy=aa,
        market_accuracy=ma,
        status=status,
    )


validate_preregistered_contract()
