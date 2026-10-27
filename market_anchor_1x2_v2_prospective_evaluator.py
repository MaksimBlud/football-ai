"""Gate-controlled evaluator for the preregistered original V2 prospective cohort.

This module is deliberately pure: it has no database, network, model-file, or
filesystem access. Outcome access is a lazy callback that is invoked only after
30 unique completed primary-cohort forecasts pass all frozen eligibility checks.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
import re
from typing import Any, Callable, Iterable, Mapping

EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY"
PRIMARY_LEAGUE = "SERIE_A"
EVIDENCE_CLASS = "PROSPECTIVE_SHADOW"
FROZEN_CANDIDATE_SHA256 = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
ACTIVE_LAMBDA = 0.0
SHADOW_RESIDUAL_LAMBDA = 1.0
MIN_COMPLETED_ELIGIBLE_FORECASTS = 30
MAX_SOURCE_AGE = timedelta(hours=24)
MAX_QUOTE_AGE = timedelta(hours=24)
RESULT_INDEX = {"H": 0, "D": 1, "A": 2}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
REQUIRED_FIELDS = frozenset({
    "experiment_id", "evidence_class", "league", "event_id",
    "match_date", "home_team", "away_team", "candidate_sha256",
    "active_lambda", "shadow_residual_lambda", "no_bet",
    "eligible_for_current_form_forward_shadow", "eligible_for_product_publication",
    "shadow_evidence_status",
    "source_artifact_id", "source_archive_sha256", "source_observed_at_utc",
    "source_archive_created_at_utc", "source_parent_run_id", "source_parent_run_sha",
    "source_parent_run_completed_at_utc", "quote_time_utc",
    "forecast_captured_at_utc", "kickoff_utc", "market_1x2",
    "active_market_fallback_1x2", "incumbent_1x2", "shadow_v2_residual_1x2",
})


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp with an explicit UTC offset")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must have a real UTC offset")
    return parsed.astimezone(timezone.utc)


def _identity(value: Any, *, label: str) -> tuple[str, str, str]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{label} must be (ISO date, canonical home team, canonical away team)")
    raw_date, home, away = value
    if not isinstance(raw_date, str):
        raise ValueError(f"{label} date must be an ISO date")
    try:
        parsed_date = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise ValueError(f"{label} date must be an ISO date") from exc
    if parsed_date.isoformat() != raw_date:
        raise ValueError(f"{label} date must use canonical YYYY-MM-DD form")
    if not isinstance(home, str) or not home.strip() or not isinstance(away, str) or not away.strip():
        raise ValueError(f"{label} teams must be non-empty canonical strings")
    home, away = home.strip(), away.strip()
    if home.casefold() == away.casefold():
        raise ValueError(f"{label} cannot have identical teams")
    return raw_date, home, away


def _guard_no_outcomes(value: Any, *, path: str = "forecast") -> None:
    """Reject result/score fields recursively in forecast-only input payloads."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if any(token in normalized for token in ("result", "outcome", "score")) or normalized in {
                "fthg", "ftag", "ftr", "homegoals", "awaygoals", "finalscore",
                "settlement", "settledresult",
            }:
                raise ValueError(f"outcome/score field forbidden in forecast input: {path}.{key}")
            _guard_no_outcomes(child, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _guard_no_outcomes(child, path=f"{path}[{index}]")


def _probabilities(value: Any, *, field: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{field} must contain exactly [home, draw, away] probabilities")
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field} contains a non-numeric probability")
        number = float(item)
        if not math.isfinite(number) or not 0.0 < number < 1.0:
            raise ValueError(f"{field} probabilities must be finite and strictly between 0 and 1")
        out.append(number)
    if not math.isclose(sum(out), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{field} probabilities must sum to one")
    return out[0], out[1], out[2]


def _sha_fixture_set(identities: Iterable[tuple[str, str, str]]) -> str:
    canonical = sorted(tuple(item) for item in identities)
    payload = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_forecast(row: Any) -> tuple[tuple[str, str, str], dict[str, tuple[float, float, float]]]:
    if not isinstance(row, Mapping):
        raise ValueError("each forecast must be a mapping")
    _guard_no_outcomes(row)
    missing = REQUIRED_FIELDS - set(row)
    if missing:
        raise ValueError("forecast missing required fields: " + ", ".join(sorted(missing)))
    if row["experiment_id"] != EXPERIMENT_ID or row["evidence_class"] != EVIDENCE_CLASS:
        raise ValueError("forecast is outside the preregistered original V2 prospective cohort")
    if row["league"] != PRIMARY_LEAGUE:
        raise ValueError("only the preregistered Serie A primary cohort counts toward this gate")
    if row["candidate_sha256"] != FROZEN_CANDIDATE_SHA256:
        raise ValueError("forecast frozen candidate SHA differs from the preregistered V2 candidate")
    if (isinstance(row["active_lambda"], bool) or row["active_lambda"] != ACTIVE_LAMBDA
            or isinstance(row["shadow_residual_lambda"], bool)
            or row["shadow_residual_lambda"] != SHADOW_RESIDUAL_LAMBDA):
        raise ValueError("frozen V2 lambda semantics changed")
    if row["no_bet"] is not True:
        raise ValueError("prospective evaluation input must remain NO_BET")
    if row["eligible_for_current_form_forward_shadow"] is not True:
        raise ValueError("forecast is not marked eligible for the current-form research shadow")
    if row["eligible_for_product_publication"] is not False:
        raise ValueError("research forecast cannot claim product-publication eligibility")
    if row["shadow_evidence_status"] != "SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE":
        raise ValueError("forecast lacks the verified source-archive/parent-before-quote evidence marker")
    if not isinstance(row["event_id"], str) or not row["event_id"].strip():
        raise ValueError("forecast event_id is missing")
    if type(row["source_artifact_id"]) is not int or row["source_artifact_id"] <= 0:
        raise ValueError("source artifact ID must be a positive integer")
    if type(row["source_parent_run_id"]) is not int or row["source_parent_run_id"] <= 0:
        raise ValueError("source parent run ID must be a positive integer")
    if not isinstance(row["source_archive_sha256"], str) or not _SHA256.fullmatch(row["source_archive_sha256"]):
        raise ValueError("source archive SHA-256 is missing or malformed")
    if not isinstance(row["source_parent_run_sha"], str) or not _SHA1.fullmatch(row["source_parent_run_sha"]):
        raise ValueError("source parent run SHA is missing or malformed")

    identity = _identity((row["match_date"], row["home_team"], row["away_team"]), label="forecast identity")
    observed = _utc(row["source_observed_at_utc"], "source_observed_at_utc")
    archive_created = _utc(row["source_archive_created_at_utc"], "source_archive_created_at_utc")
    parent_completed = _utc(row["source_parent_run_completed_at_utc"], "source_parent_run_completed_at_utc")
    quote_time = _utc(row["quote_time_utc"], "quote_time_utc")
    captured = _utc(row["forecast_captured_at_utc"], "forecast_captured_at_utc")
    kickoff = _utc(row["kickoff_utc"], "kickoff_utc")
    if not (observed <= archive_created <= parent_completed < quote_time <= captured < kickoff):
        raise ValueError("source observation/archive/parent/quote/capture/kickoff ordering is invalid")
    if quote_time - observed > MAX_SOURCE_AGE:
        raise ValueError("source observation is older than the frozen 24-hour quote-time limit")
    if captured - quote_time > MAX_QUOTE_AGE:
        raise ValueError("market quote is older than the frozen 24-hour capture-time limit")

    market = _probabilities(row["market_1x2"], field="market_1x2")
    active = _probabilities(row["active_market_fallback_1x2"], field="active_market_fallback_1x2")
    incumbent = _probabilities(row["incumbent_1x2"], field="incumbent_1x2")
    shadow = _probabilities(row["shadow_v2_residual_1x2"], field="shadow_v2_residual_1x2")
    if any(not math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12) for a, b in zip(market, active)):
        raise ValueError("active_lambda=0 must remain exactly the de-vigged market vector")
    return identity, {"market": market, "incumbent": incumbent, "shadow": shadow}


def _score(probabilities: tuple[float, float, float], outcome: str) -> tuple[float, float]:
    if outcome not in RESULT_INDEX:
        raise ValueError("outcome loader returned a value outside H/D/A")
    target = RESULT_INDEX[outcome]
    brier = sum((probabilities[i] - (1.0 if i == target else 0.0)) ** 2 for i in range(3))
    log_loss = -math.log(probabilities[target])
    return brier, log_loss


def evaluate_after_gate(
    forecast_rows: Iterable[Mapping[str, Any]],
    completed_fixture_identities: Iterable[tuple[str, str, str]],
    outcome_loader: Callable[[frozenset[tuple[str, str, str]]], Mapping[tuple[str, str, str], str]],
) -> dict[str, Any]:
    """Score only after >=30 unique eligible completed primary-cohort fixtures.

    completed_fixture_identities must come from a metadata-only query selecting
    match_date, home_team, away_team. outcome_loader must be lazy: it is called
    exactly once only after the gate opens, with only the matched forecast keys.
    """
    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")
    if isinstance(completed_fixture_identities, (str, bytes, Mapping)):
        raise ValueError("completed gate input must be fixture identities only, not outcome rows")
    completed = {_identity(item, label="completed metadata identity") for item in completed_fixture_identities}
    normalized: list[tuple[tuple[str, str, str], dict[str, tuple[float, float, float]]]] = []
    seen_ids: set[str] = set()
    seen_fixtures: set[tuple[str, str, str]] = set()
    for row in forecast_rows:
        identity, vectors = _validate_forecast(row)
        event_id = row["event_id"].strip()
        if event_id in seen_ids:
            raise ValueError("duplicate provider event_id in prospective forecast cohort")
        if identity in seen_fixtures:
            raise ValueError("duplicate canonical fixture identity in prospective forecast cohort")
        seen_ids.add(event_id)
        seen_fixtures.add(identity)
        normalized.append((identity, vectors))

    eligible_completed = [(identity, vectors) for identity, vectors in normalized if identity in completed]
    completed_ids = frozenset(identity for identity, _ in eligible_completed)
    common = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "PROSPECTIVE_FROZEN_GATE_EVALUATION",
        "primary_league": PRIMARY_LEAGUE,
        "frozen_candidate_sha256": FROZEN_CANDIDATE_SHA256,
        "active_lambda": ACTIVE_LAMBDA,
        "shadow_residual_lambda": SHADOW_RESIDUAL_LAMBDA,
        "minimum_completed_eligible_forecasts": MIN_COMPLETED_ELIGIBLE_FORECASTS,
        "eligible_completed_forecasts": len(eligible_completed),
        "completed_fixture_identity_sha256": _sha_fixture_set(completed_ids),
        "no_bet": True,
        "automatic_promotion": False,
        "production_or_supabase_writes": 0,
    }
    if len(eligible_completed) < MIN_COMPLETED_ELIGIBLE_FORECASTS:
        return {
            **common,
            "status": "OUTCOME_READ_GATE_CLOSED",
            "reason": "FEWER_THAN_30_UNIQUE_ELIGIBLE_COMPLETED_PRIMARY_FORECASTS",
            "outcome_read_gate_open": False,
            "target_outcomes_read": False,
            "target_outcomes_scored": False,
            "metrics": None,
            "review_signal": False,
        }

    # The first point at which this function may request target outcomes.
    outcomes = outcome_loader(completed_ids)
    if not isinstance(outcomes, Mapping) or set(outcomes) != set(completed_ids):
        raise ValueError("outcome loader must return exactly one outcome for every gated fixture and no extras")
    if any(not isinstance(value, str) or value not in RESULT_INDEX for value in outcomes.values()):
        raise ValueError("outcome loader returned malformed H/D/A outcomes")

    sums = {
        name: {"brier": 0.0, "log_loss": 0.0}
        for name in ("market", "incumbent", "shadow")
    }
    for identity, vectors in eligible_completed:
        outcome = outcomes[identity]
        for name, probabilities in vectors.items():
            brier, log_loss = _score(probabilities, outcome)
            sums[name]["brier"] += brier
            sums[name]["log_loss"] += log_loss
    n = len(eligible_completed)
    metrics = {
        name: {metric: value / n for metric, value in values.items()}
        for name, values in sums.items()
    }
    shadow_beats_market = (
        metrics["shadow"]["brier"] < metrics["market"]["brier"]
        and metrics["shadow"]["log_loss"] < metrics["market"]["log_loss"]
    )
    shadow_beats_incumbent = (
        metrics["shadow"]["brier"] < metrics["incumbent"]["brier"]
        and metrics["shadow"]["log_loss"] < metrics["incumbent"]["log_loss"]
    )
    return {
        **common,
        "status": "EVALUATED_RESEARCH_ONLY",
        "outcome_read_gate_open": True,
        "target_outcomes_read": True,
        "target_outcomes_scored": True,
        "scored_forecasts": n,
        "metrics": metrics,
        "deltas_shadow_minus_market": {
            metric: metrics["shadow"][metric] - metrics["market"][metric]
            for metric in ("brier", "log_loss")
        },
        "deltas_shadow_minus_incumbent": {
            metric: metrics["shadow"][metric] - metrics["incumbent"][metric]
            for metric in ("brier", "log_loss")
        },
        "shadow_beats_market_on_both_metrics": shadow_beats_market,
        "shadow_beats_incumbent_on_both_metrics": shadow_beats_incumbent,
        "review_signal": shadow_beats_market and shadow_beats_incumbent,
        "review_signal_policy": (
            "diagnostic only: shadow Brier AND LogLoss must each be lower than "
            "both the de-vigged market and frozen incumbent; no fitting, selection, "
            "threshold tuning, promotion, or betting"
        ),
        "no_bet": True,
        "automatic_promotion": False,
        "production_or_supabase_writes": 0,
    }
