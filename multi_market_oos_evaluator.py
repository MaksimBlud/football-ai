"""Frozen, outcome-agnostic Multi-Market V2 OOS evaluator.

Pure research logic only: no provider calls, no database writes, no model
promotion. Inputs are immutable snapshot rows and immutable settlement rows.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import math
from typing import Any, Iterable

PROTOCOL_VERSION = "MULTI_MARKET_V2_OOS_PROTOCOL_V1"
SNAPSHOT_SCHEMA = "MULTI_MARKET_V1"
SETTLEMENT_SCHEMA = "MULTI_MARKET_SETTLEMENT_V2"
MIN_CELL_OBSERVATIONS = 30

TARGETS = {
    "WIN": 1.0,
    "HALF_WIN": 0.75,
    "PUSH": 0.5,
    "HALF_LOSS": 0.25,
    "LOSS": 0.0,
}

MARKETS = {
    "handicap_home": (
        ("handicap", "home_probability"),
        ("handicap", "home"),
    ),
    "total_goals_over": (
        ("total_goals", "over_probability"),
        ("total_goals", "over"),
    ),
    "total_corners_over": (
        ("total_corners", "over_probability"),
        ("total_corners", "over"),
    ),
    "home_team_corners_over": (
        ("team_corners", "home", "over_probability"),
        ("team_corners", "home", "over"),
    ),
    "away_team_corners_over": (
        ("team_corners", "away", "over_probability"),
        ("team_corners", "away", "over"),
    ),
}


class EvaluationContractError(ValueError):
    """Input violates the frozen evaluator identity or schema contract."""


def _iso_utc(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvaluationContractError(f"{field} must be an ISO datetime") from exc
    else:
        raise EvaluationContractError(f"{field} must be an ISO datetime")
    if parsed.tzinfo is None:
        raise EvaluationContractError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _dig(value: Any, path: tuple[str, ...]) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _payload(row: dict) -> dict:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise EvaluationContractError("row payload must be an object")
    return payload


def _snapshot_card(snapshot: dict) -> dict:
    payload = _payload(snapshot)
    if payload.get("schema_version") != SNAPSHOT_SCHEMA or payload.get("research_only") is not True:
        raise EvaluationContractError("snapshot is not research-only MULTI_MARKET_V1")
    card = payload.get("card")
    if not isinstance(card, dict) or card.get("schema_version") != SNAPSHOT_SCHEMA or card.get("research_only") is not True:
        raise EvaluationContractError("snapshot card is not research-only MULTI_MARKET_V1")
    return card


def _settlement_payload(settlement: dict) -> dict:
    payload = _payload(settlement)
    if payload.get("schema_version") != SETTLEMENT_SCHEMA or payload.get("research_only") is not True:
        raise EvaluationContractError("settlement is not research-only MULTI_MARKET_SETTLEMENT_V2")
    body = payload.get("settlement")
    if not isinstance(body, dict) or body.get("schema_version") != SETTLEMENT_SCHEMA or body.get("research_only") is not True:
        raise EvaluationContractError("settlement payload body has wrong schema")
    return body


def _validate_snapshot_time(snapshot: dict) -> tuple[datetime, datetime]:
    snapshot_time = _iso_utc(snapshot.get("snapshot_time_utc"), "snapshot_time_utc")
    kickoff = _iso_utc(snapshot.get("kickoff_utc"), "kickoff_utc")
    if snapshot_time >= kickoff:
        raise EvaluationContractError("snapshot_time_utc must be strictly before kickoff_utc")
    return snapshot_time, kickoff


def _identity(snapshot: dict) -> tuple[str, str]:
    league = str(snapshot.get("league") or "")
    event_id = str(snapshot.get("event_id") or "")
    if not league or not event_id:
        raise EvaluationContractError("snapshot league and event_id are required")
    return league, event_id


def _validate_pair(snapshot: dict, settlement: dict) -> None:
    fields = ("snapshot_key", "league", "event_id", "home_team", "away_team", "kickoff_utc", "snapshot_time_utc")
    mismatches = [field for field in fields if str(snapshot.get(field)) != str(settlement.get(field))]
    if mismatches:
        raise EvaluationContractError("snapshot/settlement identity mismatch: " + ", ".join(mismatches))


def select_settlement_revisions(settlements: Iterable[dict]) -> dict[str, dict]:
    """Choose one immutable revision per snapshot, preferring corner-complete."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in settlements:
        key = str(row.get("snapshot_key") or "")
        if not key:
            raise EvaluationContractError("settlement snapshot_key is required")
        grouped[key].append(dict(row))

    chosen: dict[str, dict] = {}
    rank = {"GOALS_ONLY": 1, "GOALS_AND_CORNERS": 2}
    for key, rows in grouped.items():
        best_rank = max(rank.get(str(row.get("outcome_completeness") or ""), 0) for row in rows)
        if best_rank == 0:
            raise EvaluationContractError(f"unsupported settlement completeness for {key}")
        candidates = [row for row in rows if rank.get(str(row.get("outcome_completeness") or ""), 0) == best_rank]
        if len(candidates) != 1:
            raise EvaluationContractError(f"ambiguous settlement revisions for {key}")
        chosen[key] = candidates[0]
    return chosen


def select_latest_event_snapshots(snapshots: Iterable[dict]) -> dict[tuple[str, str], dict]:
    """Select exactly one latest strictly-pre-kickoff snapshot per event."""
    selected: dict[tuple[str, str], tuple[datetime, dict]] = {}
    seen_snapshot_keys: set[str] = set()
    for raw in snapshots:
        row = dict(raw)
        key = str(row.get("snapshot_key") or "")
        if not key:
            raise EvaluationContractError("snapshot_key is required")
        if key in seen_snapshot_keys:
            raise EvaluationContractError(f"duplicate snapshot_key: {key}")
        seen_snapshot_keys.add(key)
        snapshot_time, _ = _validate_snapshot_time(row)
        identity = _identity(row)
        previous = selected.get(identity)
        if previous is None or snapshot_time > previous[0]:
            selected[identity] = (snapshot_time, row)
        elif snapshot_time == previous[0]:
            raise EvaluationContractError(f"ambiguous latest snapshot for {identity!r}")
    return {identity: row for identity, (_, row) in selected.items()}


def settlement_target(status: Any) -> float | None:
    return TARGETS.get(str(status or ""))


def _probability(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        p = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(p) or not 0.0 < p < 1.0:
        return None
    return p


def _losses(probability: float, target: float) -> tuple[float, float]:
    brier = (probability - target) ** 2
    logloss = -(target * math.log(probability) + (1.0 - target) * math.log(1.0 - probability))
    return brier, logloss


def evaluate(snapshots: Iterable[dict], settlements: Iterable[dict]) -> dict:
    """Evaluate frozen market probabilities under the preregistered protocol."""
    latest = select_latest_event_snapshots(snapshots)
    revisions = select_settlement_revisions(settlements)
    exclusions: Counter[str] = Counter()
    observations: list[dict] = []

    for (league, event_id), snapshot in sorted(latest.items()):
        snapshot_key = str(snapshot["snapshot_key"])
        settlement = revisions.get(snapshot_key)
        if settlement is None:
            exclusions["MISSING_SETTLEMENT"] += len(MARKETS)
            continue
        _validate_pair(snapshot, settlement)
        card = _snapshot_card(snapshot)
        settled = _settlement_payload(settlement)

        for market_name, (probability_path, settlement_path) in MARKETS.items():
            probability = _probability(_dig(card, probability_path))
            settlement_row = _dig(settled, settlement_path)
            if not isinstance(settlement_row, dict):
                exclusions["MISSING_SETTLEMENT_MARKET"] += 1
                continue
            status = str(settlement_row.get("status") or "")
            target = settlement_target(status)
            if target is None:
                exclusions[status or "UNKNOWN_SETTLEMENT_STATUS"] += 1
                continue
            if probability is None:
                exclusions["INVALID_OR_MISSING_PROBABILITY"] += 1
                continue
            brier, logloss = _losses(probability, target)
            observations.append({
                "league": league,
                "event_id": event_id,
                "snapshot_key": snapshot_key,
                "market": market_name,
                "probability": probability,
                "target": target,
                "settlement_status": status,
                "brier": brier,
                "logloss": logloss,
            })

    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in observations:
        cells[(row["league"], row["market"])].append(row)

    per_cell = []
    for (league, market), rows in sorted(cells.items()):
        unique_events = len({row["event_id"] for row in rows})
        count = len(rows)
        per_cell.append({
            "league": league,
            "market": market,
            "observations": count,
            "unique_events": unique_events,
            "sample_status": "READY" if count >= MIN_CELL_OBSERVATIONS and unique_events >= MIN_CELL_OBSERVATIONS else "INSUFFICIENT_SAMPLE",
            "mean_brier": sum(row["brier"] for row in rows) / count,
            "mean_logloss": sum(row["logloss"] for row in rows) / count,
        })

    if observations:
        micro_brier = sum(row["brier"] for row in observations) / len(observations)
        micro_logloss = sum(row["logloss"] for row in observations) / len(observations)
    else:
        micro_brier = micro_logloss = None

    ready_cells = [cell for cell in per_cell if cell["sample_status"] == "READY"]
    if ready_cells:
        macro_brier = sum(cell["mean_brier"] for cell in ready_cells) / len(ready_cells)
        macro_logloss = sum(cell["mean_logloss"] for cell in ready_cells) / len(ready_cells)
    else:
        macro_brier = macro_logloss = None

    return {
        "protocol_version": PROTOCOL_VERSION,
        "research_only": True,
        "selection": "LATEST_STRICTLY_PRE_KICKOFF_PER_LEAGUE_EVENT",
        "min_cell_observations": MIN_CELL_OBSERVATIONS,
        "selected_events": len(latest),
        "usable_observations": len(observations),
        "per_league_market": per_cell,
        "micro": {"mean_brier": micro_brier, "mean_logloss": micro_logloss},
        "macro_ready_cells": {"cells": len(ready_cells), "mean_brier": macro_brier, "mean_logloss": macro_logloss},
        "exclusions": dict(sorted(exclusions.items())),
        "observations": observations,
    }
