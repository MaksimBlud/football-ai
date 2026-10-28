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
# The frozen policy names a production incumbent but does not pin its exact model version/artifact SHA.
# Keep target-outcome evaluation fail-closed until a separately approved protocol amendment pins it.
FROZEN_INCUMBENT_REFERENCE: dict[str, str] | None = None
MIN_COMPLETED_ELIGIBLE_FORECASTS = 30
MAX_SOURCE_AGE = timedelta(hours=24)
MAX_QUOTE_AGE = timedelta(hours=24)
# Exact main commit that introduced/froze the separate current-form cohort.
COHORT_PREREGISTRATION_COMMIT_SHA = "9df6f63db10e0128aff89c38fb8c6d88703ef8b8"
COHORT_FROZEN_AT_UTC = datetime(2026, 10, 18, 8, 15, 32, tzinfo=timezone.utc)
PRIMARY_SEASON_START = date(2026, 7, 1)
PRIMARY_SEASON_END = date(2027, 6, 30)
RESULT_INDEX = {"H": 0, "D": 1, "A": 2}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")

COMPLETED_FIXTURE_GATE_SCHEMA = "MARKET_ANCHOR_1X2_V2_COMPLETED_FIXTURE_IDENTITY_GATE_V1"
COMPLETED_FIXTURE_GATE_SOURCE_TABLE = "public.league_finished_results"
COMPLETED_FIXTURE_GATE_COLUMNS = ("match_date", "home_team", "away_team")
COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID = "SERIE_A_COMPLETED_FIXTURE_IDENTITIES_V1"
COMPLETED_FIXTURE_GATE_QUERY_CONTRACT = (
    "SELECT match_date, home_team, away_team FROM public.league_finished_results "
    "WHERE league = 'SERIE_A' AND season = '2026-2027' "
    "AND match_date >= DATE '2026-07-01' AND match_date < :cutoff_date_exclusive"
)
COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256 = "181d76b75c092d46b57535591abbb4e625c3e54e9b0f876402c9a3e0ed2457fb"
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
    "active_market_fallback_1x2", "incumbent_1x2", "incumbent_evidence", "shadow_v2_residual_1x2",
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
                # Common football-data result aliases that do not contain the
                # words "result", "outcome", or "score" after normalization.
                "fthg", "ftag", "ftr", "homegoals", "awaygoals", "finalscore",
                "homegoal", "awaygoal", "goalshome", "goalsaway",
                "homeftgoal", "awayftgoal", "homeftgoals", "awayftgoals",
                "fulltimehomegoal", "fulltimeawaygoal", "fulltimehomegoals", "fulltimeawaygoals",
                "finalhomegoal", "finalawaygoal", "finalhomegoals", "finalawaygoals",
                "homefinalgoal", "awayfinalgoal", "homefinalgoals", "awayfinalgoals",
                "winner", "winningteam", "winnerteam", "matchwinner",
                "homewin", "awaywin", "ishomewin", "isawaywin", "isdraw", "draw",
                "drawresult", "matchdraw",
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


def _validate_completed_fixture_gate_attestation(
    attestation: Mapping[str, Any] | None,
    completed_identities: set[tuple[str, str, str]],
) -> dict[str, str]:
    """Require a digest-bound attestation for the frozen identity-only completed-fixture query."""
    if not isinstance(attestation, Mapping):
        raise ValueError("completed fixture gate requires an explicit metadata-only attestation")
    required = {
        "schema_version", "source_table", "selected_columns", "league", "season",
        "query_contract_id", "query_contract_sha256", "captured_at_utc",
        "cutoff_date_exclusive_utc", "completed_fixture_identity_count",
        "completed_fixture_identity_sha256", "outcome_columns_selected", "target_outcomes_read",
    }
    extra = set(attestation) - required
    missing = required - set(attestation)
    if extra or missing:
        raise ValueError(
            "completed fixture gate attestation has unapproved/missing fields: "
            f"extra={sorted(str(key) for key in extra)}, missing={sorted(missing)}"
        )
    selected_columns = attestation["selected_columns"]
    if not isinstance(selected_columns, (list, tuple)) or tuple(selected_columns) != COMPLETED_FIXTURE_GATE_COLUMNS:
        raise ValueError("completed fixture gate attestation differs from the frozen identity-only query contract")
    if (
        attestation["schema_version"] != COMPLETED_FIXTURE_GATE_SCHEMA
        or attestation["source_table"] != COMPLETED_FIXTURE_GATE_SOURCE_TABLE
        or attestation["league"] != PRIMARY_LEAGUE
        or attestation["season"] != "2026-2027"
        or attestation["query_contract_id"] != COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID
        or attestation["query_contract_sha256"] != COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256
        or attestation["outcome_columns_selected"] is not False
        or attestation["target_outcomes_read"] is not False
    ):
        raise ValueError("completed fixture gate attestation differs from the frozen identity-only query contract")
    captured_at = _utc(attestation["captured_at_utc"], "completed fixture gate captured_at_utc")
    cutoff_text = attestation["cutoff_date_exclusive_utc"]
    if not isinstance(cutoff_text, str):
        raise ValueError("completed fixture gate cutoff must be a canonical ISO date")
    try:
        cutoff_date = date.fromisoformat(cutoff_text)
    except ValueError as exc:
        raise ValueError("completed fixture gate cutoff must be a canonical ISO date") from exc
    if cutoff_date.isoformat() != cutoff_text or captured_at.date() != cutoff_date:
        raise ValueError("completed fixture gate cutoff date must match its UTC capture date")
    count = attestation["completed_fixture_identity_count"]
    digest = attestation["completed_fixture_identity_sha256"]
    if type(count) is not int or count != len(completed_identities):
        raise ValueError("completed fixture gate identity count does not match supplied identities")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ValueError("completed fixture gate identity digest is malformed")
    if digest != _sha_fixture_set(completed_identities):
        raise ValueError("completed fixture gate identity digest does not match supplied identities")
    for identity in completed_identities:
        match_day = date.fromisoformat(identity[0])
        if not (PRIMARY_SEASON_START <= match_day <= PRIMARY_SEASON_END):
            raise ValueError("completed fixture gate contains an identity outside the frozen 2026/27 primary season")
        if match_day >= cutoff_date:
            raise ValueError("completed fixture gate contains a fixture not completed before the metadata cutoff date")
    return {
        "captured_at_utc": captured_at.isoformat().replace("+00:00", "Z"),
        "cutoff_date_exclusive_utc": cutoff_text,
    }


def _validate_forecast(row: Any) -> tuple[tuple[str, str, str], dict[str, tuple[float, float, float]], dict[str, Any]]:
    if not isinstance(row, Mapping):
        raise ValueError("each forecast must be a mapping")
    _guard_no_outcomes(row)
    # This evaluator accepts a normalized, versioned forecast schema—not arbitrary
    # upstream payloads. Reject every unapproved key so an unknown target alias
    # cannot bypass a denylist and travel into the scoring cohort.
    extra_fields = set(row) - REQUIRED_FIELDS
    if extra_fields:
        raise ValueError(
            "forecast contains unapproved fields: "
            + ", ".join(sorted(str(key) for key in extra_fields))
        )
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
    evidence = row["incumbent_evidence"]
    if not isinstance(evidence, Mapping):
        raise ValueError("incumbent_evidence must include frozen model and per-event source provenance")
    allowed_evidence_fields = {
        "model_version", "artifact_sha256", "source_record_id",
        "generated_at_utc", "history_cutoff_utc", "league",
        "match_date", "home_team", "away_team", "kickoff_utc",
    }
    extra_evidence = set(evidence) - allowed_evidence_fields
    if extra_evidence:
        raise ValueError(
            "incumbent evidence contains unapproved fields: "
            + ", ".join(sorted(str(key) for key in extra_evidence))
        )
    missing_evidence = allowed_evidence_fields - set(evidence)
    if missing_evidence:
        raise ValueError("incumbent evidence missing fields: " + ", ".join(sorted(missing_evidence)))
    incumbent_version = evidence["model_version"]
    if not isinstance(incumbent_version, str) or not incumbent_version.strip():
        raise ValueError("incumbent model version is missing")
    incumbent_version = incumbent_version.strip()
    version_key = incumbent_version.casefold()
    if "xgboost" in version_key or re.search(r"(^|[-_])xgb($|[-_])", version_key):
        raise ValueError("legacy XGBoost incumbent evidence is forbidden by the V2-only research contract")
    incumbent_sha = evidence["artifact_sha256"]
    if not isinstance(incumbent_sha, str) or not _SHA256.fullmatch(incumbent_sha):
        raise ValueError("incumbent artifact SHA-256 is missing or malformed")
    incumbent_source_id = evidence["source_record_id"]
    if not isinstance(incumbent_source_id, str) or not incumbent_source_id.strip():
        raise ValueError("incumbent source record ID is missing")
    incumbent_generated = _utc(evidence["generated_at_utc"], "incumbent_evidence.generated_at_utc")
    incumbent_history_cutoff = _utc(evidence["history_cutoff_utc"], "incumbent_evidence.history_cutoff_utc")
    if incumbent_history_cutoff > observed:
        raise ValueError(
            "incumbent history cutoff must not follow the authenticated V2 source observation "
            "for same-information-time comparison"
        )
    if incumbent_history_cutoff > incumbent_generated or incumbent_generated > quote_time:
        raise ValueError("incumbent history cutoff/generated time must not follow the quote")
    if kickoff.date().isoformat() != identity[0]:
        raise ValueError("kickoff UTC date does not match canonical fixture match_date")
    fixture_date = date.fromisoformat(identity[0])
    if not PRIMARY_SEASON_START <= fixture_date <= PRIMARY_SEASON_END:
        raise ValueError("forecast fixture date is outside the frozen 2026/27 primary season")
    if quote_time <= COHORT_FROZEN_AT_UTC:
        raise ValueError("quote predates or equals the frozen cohort preregistration time")
    if not (observed <= archive_created <= parent_completed < quote_time <= captured < kickoff):
        raise ValueError("source observation/archive/parent/quote/capture/kickoff ordering is invalid")
    if quote_time - observed > MAX_SOURCE_AGE:
        raise ValueError("source observation is older than the frozen 24-hour quote-time limit")
    if captured - quote_time > MAX_QUOTE_AGE:
        raise ValueError("market quote is older than the frozen 24-hour capture-time limit")

    # Validate the comparator's event identity after the forecast's own date and
    # kickoff checks, preserving the more specific fail-closed diagnostics.
    incumbent_kickoff = _utc(evidence["kickoff_utc"], "incumbent_evidence.kickoff_utc")
    if (
        evidence["league"] != row["league"]
        or evidence["match_date"] != row["match_date"]
        or evidence["home_team"] != row["home_team"]
        or evidence["away_team"] != row["away_team"]
        or incumbent_kickoff != kickoff
    ):
        raise ValueError("incumbent evidence event identity does not match forecast")

    market = _probabilities(row["market_1x2"], field="market_1x2")
    active = _probabilities(row["active_market_fallback_1x2"], field="active_market_fallback_1x2")
    incumbent = _probabilities(row["incumbent_1x2"], field="incumbent_1x2")
    shadow = _probabilities(row["shadow_v2_residual_1x2"], field="shadow_v2_residual_1x2")
    if any(not math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12) for a, b in zip(market, active)):
        raise ValueError("active_lambda=0 must remain exactly the de-vigged market vector")
    return identity, {"market": market, "incumbent": incumbent, "shadow": shadow}, {
        "model_version": incumbent_version,
        "artifact_sha256": incumbent_sha,
        "source_record_id": incumbent_source_id.strip(),
        "generated_at_utc": incumbent_generated,
        "history_cutoff_utc": incumbent_history_cutoff,
    }


def _validated_frozen_incumbent_reference(value: Any) -> dict[str, str] | None:
    """Validate the incumbent identity pinned by a separately approved protocol."""
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"model_version", "artifact_sha256"}:
        raise ValueError("frozen incumbent reference must pin exactly model_version and artifact_sha256")
    version = value["model_version"]
    digest = value["artifact_sha256"]
    if not isinstance(version, str) or not version.strip():
        raise ValueError("frozen incumbent reference has no model_version")
    version = version.strip()
    version_key = version.casefold()
    if "xgboost" in version_key or re.search(r"(^|[-_])xgb($|[-_])", version_key):
        raise ValueError("legacy XGBoost incumbent reference is forbidden by the V2-only research contract")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ValueError("frozen incumbent reference has no valid artifact SHA-256")
    return {"model_version": version, "artifact_sha256": digest}


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
    *,
    completed_fixture_gate_attestation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Score only after >=30 unique eligible completed primary-cohort fixtures.

    completed_fixture_identities must come from a metadata-only query selecting
    match_date, home_team, away_team, accompanied by a digest-bound attestation
    for the frozen identity-only query contract. outcome_loader must be lazy:
    it is called exactly once only after the gate opens, with matched forecast keys.
    """
    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")
    if isinstance(completed_fixture_identities, (str, bytes, Mapping)):
        raise ValueError("completed gate input must be fixture identities only, not outcome rows")
    completed = {_identity(item, label="completed metadata identity") for item in completed_fixture_identities}
    gate_attestation = _validate_completed_fixture_gate_attestation(
        completed_fixture_gate_attestation, completed
    )
    normalized: list[tuple[tuple[str, str, str], dict[str, tuple[float, float, float]], dict[str, Any]]] = []
    seen_ids: set[str] = set()
    seen_fixtures: set[tuple[str, str, str]] = set()
    seen_incumbent_records: set[str] = set()
    for row in forecast_rows:
        identity, vectors, incumbent_evidence = _validate_forecast(row)
        event_id = row["event_id"].strip()
        if event_id in seen_ids:
            raise ValueError("duplicate provider event_id in prospective forecast cohort")
        if identity in seen_fixtures:
            raise ValueError("duplicate canonical fixture identity in prospective forecast cohort")
        source_record_id = incumbent_evidence["source_record_id"]
        if source_record_id in seen_incumbent_records:
            raise ValueError("duplicate incumbent source record ID in prospective forecast cohort")
        seen_ids.add(event_id)
        seen_fixtures.add(identity)
        seen_incumbent_records.add(source_record_id)
        normalized.append((identity, vectors, incumbent_evidence))

    eligible_completed = [(identity, vectors, evidence) for identity, vectors, evidence in normalized if identity in completed]
    completed_ids = frozenset(identity for identity, _, _ in eligible_completed)
    common = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "PROSPECTIVE_FROZEN_GATE_EVALUATION",
        "primary_league": PRIMARY_LEAGUE,
        "frozen_candidate_sha256": FROZEN_CANDIDATE_SHA256,
        "cohort_preregistration_commit_sha": COHORT_PREREGISTRATION_COMMIT_SHA,
        "cohort_frozen_at_utc": COHORT_FROZEN_AT_UTC.isoformat().replace("+00:00", "Z"),
        "primary_season_start": PRIMARY_SEASON_START.isoformat(),
        "primary_season_end": PRIMARY_SEASON_END.isoformat(),
        "active_lambda": ACTIVE_LAMBDA,
        "shadow_residual_lambda": SHADOW_RESIDUAL_LAMBDA,
        "frozen_incumbent_reference_pinned": FROZEN_INCUMBENT_REFERENCE is not None,
        "minimum_completed_eligible_forecasts": MIN_COMPLETED_ELIGIBLE_FORECASTS,
        "eligible_completed_forecasts": len(eligible_completed),
        "completed_metadata_fixture_count": len(completed),
        "completed_metadata_fixture_identity_sha256": _sha_fixture_set(completed),
        "completed_fixture_gate_attestation_verified": True,
        "completed_fixture_gate_source_table": COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
        "completed_fixture_gate_query_contract_sha256": COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
        "completed_fixture_gate_captured_at_utc": gate_attestation["captured_at_utc"],
        "completed_fixture_gate_cutoff_date_exclusive_utc": gate_attestation["cutoff_date_exclusive_utc"],
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

    incumbent_reference = _validated_frozen_incumbent_reference(FROZEN_INCUMBENT_REFERENCE)
    if incumbent_reference is None:
        return {
            **common,
            "status": "EVALUATION_BLOCKED_UNPINNED_INCUMBENT",
            "reason": "FROZEN_INCUMBENT_IDENTITY_NOT_PINNED_IN_PREREGISTERED_POLICY",
            "outcome_read_gate_open": False,
            "target_outcomes_read": False,
            "target_outcomes_scored": False,
            "metrics": None,
            "review_signal": False,
        }
    for _, _, evidence in eligible_completed:
        if (evidence["model_version"] != incumbent_reference["model_version"]
                or evidence["artifact_sha256"] != incumbent_reference["artifact_sha256"]):
            raise ValueError("incumbent evidence does not match the frozen incumbent reference")

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
    for identity, vectors, _evidence in eligible_completed:
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
