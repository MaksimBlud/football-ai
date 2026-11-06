"""Pure bridge from current-form forward artifacts to the frozen V2 evaluator."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import market_anchor_1x2_v2_prospective_evaluator as evaluator

POLICY_PATH = Path(__file__).resolve().parent / "experiments" / "market_anchor_1x2_v2_prospective_selection_policy.json"
POLICY_SHA256 = "9fabe72f5aae341e758b1ce4c3fec1fa60e3ea7c8d2122f48e00f9040914842d"
POLICY_ID = "MARKET_ANCHOR_1X2_V2_FIRST_ELIGIBLE_FORECAST_PER_FIXTURE_V1"
FORWARD_WORKFLOW_PATH = ".github/workflows/serie-a-v2-current-form-forward-preview.yml"
FORWARD_WORKFLOW_NAME = "Serie A V2 Current-Form Forward-Only Preview"
SOURCE_WORKFLOW_PATH = ".github/workflows/serie-a-v2-current-form-source-capture.yml"
CAPTURED_ROW_STATUS = "CURRENT_FORM_V2_SHADOW_CAPTURED_PREKICKOFF"
SOURCE_EVIDENCE_STATUS = "SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
_ALLOWED_EVENTS = {"schedule", "workflow_dispatch", "workflow_run"}


def _utc(value: Any, field: str) -> datetime:
    return evaluator._utc(value, field)


def _positive_int(value: Any, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _sha(value: Any, pattern: re.Pattern[str], field: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{field} is missing or malformed")
    return value


def _same_time(left: Any, right: Any, field: str) -> None:
    if _utc(left, field) != _utc(right, field):
        raise ValueError(f"{field} differs between forward row and source provenance")


def load_selection_policy(path: Path = POLICY_PATH) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != POLICY_SHA256:
        raise ValueError("prospective forecast-selection policy SHA256 mismatch")
    policy = json.loads(raw.decode("utf-8"))
    selection = policy.get("selection") if isinstance(policy, dict) else None
    scope = policy.get("scope") if isinstance(policy, dict) else None
    if (
        policy.get("policy_id") != POLICY_ID
        or policy.get("candidate_sha256") != evaluator.FROZEN_CANDIDATE_SHA256
        or policy.get("minimum_completed_eligible_forecasts") != evaluator.MIN_COMPLETED_ELIGIBLE_FORECASTS
        or not isinstance(selection, Mapping)
        or selection.get("rule") != "select_the_earliest_eligible_forecast_captured_at_utc_per_fixture"
        or selection.get("tie_policy") != "fail_closed_if_two_candidates_for_one_fixture_share_the_same_forecast_captured_at_utc"
        or selection.get("performance_based_selection") is not False
        or selection.get("outcome_dependent_selection") is not False
        or selection.get("market_price_dependent_selection") is not False
        or not isinstance(scope, Mapping)
        or scope.get("active_lambda") != 0
        or scope.get("shadow_residual_lambda") != 1
        or scope.get("no_bet") is not True
        or scope.get("automatic_promotion") is not False
        or scope.get("production_or_supabase_writes") != 0
        or scope.get("paid_provider_calls") != 0
    ):
        raise ValueError("prospective forecast-selection policy differs from frozen V2 scope")
    return policy, digest


def _source_lookup(items: Any) -> dict[int, Mapping[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("forward report source_artifacts_used must be a list")
    lookup: dict[int, Mapping[str, Any]] = {}
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("forward report contains malformed source artifact metadata")
        artifact_id = _positive_int(item.get("artifact_id"), "source artifact_id")
        if artifact_id in lookup:
            raise ValueError("forward report contains duplicate source artifact IDs")
        _sha(item.get("artifact_sha256"), _SHA256, "source artifact SHA256")
        _utc(item.get("source_archive_created_at_utc"), "source archive created_at")
        _utc(item.get("latest_source_observed_at_utc"), "latest source observation")
        parent = item.get("parent_run")
        if not isinstance(parent, Mapping):
            raise ValueError("forward report source artifact lacks parent-run provenance")
        _positive_int(parent.get("run_id"), "source parent run_id")
        _sha(parent.get("run_head_sha"), _SHA1, "source parent run SHA")
        if parent.get("workflow_path") != SOURCE_WORKFLOW_PATH:
            raise ValueError("source parent workflow path is not the frozen current-form source workflow")
        created = _utc(parent.get("run_created_at_utc"), "source parent run_created_at_utc")
        completed = _utc(parent.get("run_completed_at_utc"), "source parent run_completed_at_utc")
        observed = _utc(item["latest_source_observed_at_utc"], "latest source observation")
        archived = _utc(item["source_archive_created_at_utc"], "source archive created_at")
        if not created <= observed <= archived <= completed:
            raise ValueError("source parent/archive/observation timestamps are not ordered")
        lookup[artifact_id] = item
    return lookup


def normalize_forward_report(
    report: Mapping[str, Any], *, forward_artifact_id: int, forward_run: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Map actual nested forward rows to the evaluator schema; never read outcomes."""
    _positive_int(forward_artifact_id, "forward artifact_id")
    if not isinstance(report, Mapping):
        raise ValueError("forward artifact report must be a mapping")
    if (
        forward_run.get("head_branch") != "main"
        or forward_run.get("path") != FORWARD_WORKFLOW_PATH
        or forward_run.get("name") != FORWARD_WORKFLOW_NAME
        or forward_run.get("status") != "completed"
        or forward_run.get("conclusion") != "success"
        or forward_run.get("event") not in _ALLOWED_EVENTS
    ):
        raise ValueError("forward artifact parent is not a successful allowed main workflow run")
    _positive_int(forward_run.get("run_id"), "forward run_id")
    _sha(forward_run.get("head_sha"), _SHA1, "forward run head SHA")
    run_created = _utc(forward_run.get("run_created_at_utc"), "forward run created_at")
    run_completed = _utc(forward_run.get("run_completed_at_utc"), "forward run completed_at")
    artifact_created = _utc(forward_run.get("artifact_created_at_utc"), "forward artifact created_at")
    if not run_created <= artifact_created <= run_completed:
        raise ValueError("forward artifact creation is outside its successful parent run")

    if (
        report.get("schema_version") != "SERIE_A_V2_CURRENT_FORM_FORWARD_CAPTURE_V1"
        or report.get("experiment_id") != evaluator.EXPERIMENT_ID
        or report.get("mode") != "READ_ONLY_PREKICKOFF_SHADOW_NO_BET"
        or report.get("candidate_sha256") != evaluator.FROZEN_CANDIDATE_SHA256
        or isinstance(report.get("active_lambda"), bool)
        or report.get("active_lambda") != evaluator.ACTIVE_LAMBDA
        or isinstance(report.get("shadow_residual_lambda"), bool)
        or report.get("shadow_residual_lambda") != evaluator.SHADOW_RESIDUAL_LAMBDA
        or report.get("active_model_is_exact_de_vigged_market") is not True
        or report.get("target_outcomes_read") is not False
        or report.get("target_outcomes_scored") is not False
        or report.get("target_outcome_evaluation_gate_open") is not False
        or report.get("model_refit_or_selection") is not False
        or report.get("production_or_supabase_writes") != 0
        or report.get("paid_provider_calls") != 0
        or report.get("eligible_for_frozen_original_cohort") is not False
        or report.get("eligible_for_product_publication") is not False
        or report.get("no_bet") is not True
    ):
        raise ValueError("forward report violates the frozen original V2 research-only contract")

    captured_at = _utc(report.get("as_of_utc"), "forward report as_of_utc")
    if not run_created <= captured_at <= run_completed:
        raise ValueError("forward report capture time is outside its successful main run")
    rows = report.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("forward report rows must be a list of mappings")
    captured = [row for row in rows if row.get("status") == CAPTURED_ROW_STATUS]
    count = report.get("v2_current_form_shadow_captured")
    if type(count) is not int or count != len(captured):
        raise ValueError("forward report captured-row count does not match its rows")
    if report.get("eligible_for_current_form_forward_shadow") is not bool(count):
        raise ValueError("forward report shadow eligibility flag differs from captured-row count")
    if count == 0:
        return []

    source_by_id = _source_lookup(report.get("source_artifacts_used"))
    if not source_by_id:
        raise ValueError("captured forward rows have no source artifact provenance")

    result = []
    for raw_row in captured:
        preview = raw_row.get("v2_preview")
        if not isinstance(preview, Mapping):
            raise ValueError("captured forward row lacks its V2 preview")
        evaluator._guard_no_outcomes(preview)
        source_id = _positive_int(raw_row.get("source_artifact_id"), "source artifact_id")
        source = source_by_id.get(source_id)
        if source is None:
            raise ValueError("captured row references an unlisted source artifact")
        parent = source["parent_run"]
        source_sha = _sha(raw_row.get("source_artifact_sha256"), _SHA256, "forward row source SHA256")
        if source_sha != source["artifact_sha256"]:
            raise ValueError("forward row source SHA differs from source_artifacts_used")
        _same_time(raw_row.get("source_archive_created_at_utc"), source["source_archive_created_at_utc"], "source archive created_at")
        _same_time(raw_row.get("source_observed_at_utc"), source["latest_source_observed_at_utc"], "source observation time")

        event_id, home, away = (raw_row.get(k) for k in ("event_id", "home_team", "away_team"))
        if not all(isinstance(v, str) and v.strip() for v in (event_id, home, away)):
            raise ValueError("captured forward row has incomplete fixture identity")
        if (
            preview.get("league") != evaluator.PRIMARY_LEAGUE
            or preview.get("event_id") != event_id
            or preview.get("home_team") != home
            or preview.get("away_team") != away
            or preview.get("model_candidate_sha256") != evaluator.FROZEN_CANDIDATE_SHA256
            or preview.get("shadow_evidence_status") != SOURCE_EVIDENCE_STATUS
            or preview.get("eligible_for_current_form_forward_shadow") is not True
            or preview.get("eligible_for_frozen_prospective_cohort") is not False
            or preview.get("eligible_for_product_publication") is not False
            or preview.get("no_bet") is not True
        ):
            raise ValueError("captured preview differs from frozen V2 prospective evidence contract")

        quote_time = raw_row.get("quote_time_utc")
        kickoff = raw_row.get("kickoff_utc")
        _same_time(preview.get("market_snapshot_time_utc"), quote_time, "market snapshot time")
        _same_time(preview.get("kickoff_utc"), kickoff, "kickoff time")
        match_date = _utc(kickoff, "kickoff_utc").date().isoformat()
        normalized = {
            "experiment_id": evaluator.EXPERIMENT_ID,
            "evidence_class": evaluator.EVIDENCE_CLASS,
            "league": evaluator.PRIMARY_LEAGUE,
            "event_id": event_id.strip(),
            "match_date": match_date,
            "home_team": home.strip(),
            "away_team": away.strip(),
            "candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
            "active_lambda": evaluator.ACTIVE_LAMBDA,
            "shadow_residual_lambda": evaluator.SHADOW_RESIDUAL_LAMBDA,
            "no_bet": True,
            "eligible_for_current_form_forward_shadow": True,
            "eligible_for_product_publication": False,
            "shadow_evidence_status": SOURCE_EVIDENCE_STATUS,
            "source_artifact_id": source_id,
            "source_archive_sha256": source_sha,
            "source_observed_at_utc": raw_row["source_observed_at_utc"],
            "source_archive_created_at_utc": raw_row["source_archive_created_at_utc"],
            "source_parent_run_id": parent["run_id"],
            "source_parent_run_sha": parent["run_head_sha"],
            "source_parent_run_completed_at_utc": parent["run_completed_at_utc"],
            "quote_time_utc": quote_time,
            "forecast_captured_at_utc": report["as_of_utc"],
            "kickoff_utc": kickoff,
            "market_1x2": preview.get("market_1x2"),
            "active_market_fallback_1x2": preview.get("active_market_fallback_1x2"),
            "shadow_v2_residual_1x2": preview.get("shadow_v2_residual_1x2"),
        }
        evaluator._validate_forecast(normalized)
        result.append({
            "row": normalized,
            "provenance": {
                "forward_artifact_id": forward_artifact_id,
                "forward_run_id": forward_run["run_id"],
                "forward_run_head_sha": forward_run["head_sha"],
                "forward_run_created_at_utc": forward_run["run_created_at_utc"],
                "forward_artifact_created_at_utc": forward_run["artifact_created_at_utc"],
                "source_artifact_id": source_id,
                "source_artifact_info": source,
            },
        })
    return result


def select_first_eligible_forecasts(candidates: Sequence[Mapping[str, Any]]):
    """Select the earliest eligible capture per fixture; ties and ID reuse fail closed."""
    policy, policy_sha = load_selection_policy()
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    event_to_identity: dict[str, tuple[str, str, str]] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or not isinstance(candidate.get("row"), Mapping):
            raise ValueError("candidate forecast must contain a normalized row")
        row = dict(candidate["row"])
        identity, _, _ = evaluator._validate_forecast(row)
        event_id = row["event_id"].strip()
        previous = event_to_identity.get(event_id)
        if previous is not None and previous != identity:
            raise ValueError("one provider event_id maps to multiple canonical fixtures")
        event_to_identity[event_id] = identity
        capture = _utc(row["forecast_captured_at_utc"], "forecast_captured_at_utc")
        groups.setdefault(identity, []).append({
            "row": row, "provenance": dict(candidate.get("provenance") or {}), "_capture": capture
        })

    selected = []
    duplicates = 0
    for identity, group in sorted(groups.items()):
        group.sort(key=lambda item: item["_capture"])
        if len(group) > 1 and group[0]["_capture"] == group[1]["_capture"]:
            raise ValueError("duplicate fixture forecasts share the same capture timestamp; selection is ambiguous")
        selected.append({"row": group[0]["row"], "provenance": group[0]["provenance"]})
        duplicates += len(group) - 1
    ids = [item["row"]["event_id"] for item in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("selected cohort contains duplicate provider event IDs")
    return selected, {
        "policy_id": policy["policy_id"],
        "policy_sha256": policy_sha,
        "minimum_completed_eligible_forecasts": policy["minimum_completed_eligible_forecasts"],
        "candidate_rows_validated": len(candidates),
        "selected_unique_fixture_forecasts": len(selected),
        "duplicate_forecast_rows_not_selected": duplicates,
        "selection_rule": policy["selection"]["rule"],
        "outcome_dependent_selection": False,
        "performance_based_selection": False,
    }
