"""Pure secondary market-only evaluator for original old-season-only MARKET_ANCHOR_1X2_V2.

This does NOT alter the original frozen prospective cohort or make its rows
eligible. It compares the exact original candidate's lambda=1 research shadow
with the de-vigged market under a separately preregistered secondary protocol.
No incumbent model is run. This module has no network, database, or filesystem
access. Outcome loading is a lazy callback and is not invoked until both
independent gates pass.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
import math
import random
import re
from statistics import fmean
from typing import Any, Callable, Iterable, Mapping
from zoneinfo import ZoneInfo

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

POLICY_ID = "MARKET_ANCHOR_1X2_V2_OLD_SEASON_ONLY_MARKET_COMPARISON_SECONDARY_V1"
SCHEMA_VERSION = "MARKET_ANCHOR_1X2_V2_ORIGINAL_MARKET_ONLY_SECONDARY_V1"
EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V2"
CANDIDATE_SHA256 = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
PRIMARY_LEAGUE = "SERIE_A"
PRIMARY_SEASON = "2026-2027"
PRIMARY_SEASON_START = date(2026, 7, 1)
PRIMARY_SEASON_END = date(2027, 6, 30)
LOCAL_TIMEZONE = ZoneInfo("Europe/Rome")
ACTIVE_LAMBDA = 0.0
SHADOW_RESIDUAL_LAMBDA = 1.0
MIN_COMPLETED_PRIMARY_FIXTURES = 30
MIN_ELIGIBLE_COMPLETED_FORECASTS = 30
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 20261106

FORWARD_ARTIFACT_NAME = "serie-a-v2-original-forward-source-checked"
FORWARD_WORKFLOW_NAME = "Serie A V2 Original Forward-Only Preview"
FORWARD_WORKFLOW_PATH = ".github/workflows/serie-a-v2-forward-preview.yml"
SOURCE_ARTIFACT_NAME = "serie-a-v2-free-real-quote-diagnostic"
SOURCE_WORKFLOW_NAME = "Serie A V2 Free Real-Quote Diagnostic"
SOURCE_WORKFLOW_PATH = ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml"
SOURCE_LOADER_BLOB_SHA1 = "d3b717ea03570413f1d0b6b6f9821b2be0db16a3"
SOURCE_RIGHTS_HELPER_BLOB_SHA1 = "538ae477995c3b70ba5d4adafa8e4e7516072b98"
SOURCE_RIGHTS_MANIFEST_BLOB_SHA1 = "a8795adce411fad4679491be36867dad2565a89c"

COMPLETED_FIXTURE_GATE_SOURCE_TABLE = "public.league_finished_results"
COMPLETED_FIXTURE_GATE_COLUMNS = ("match_date", "home_team", "away_team")
COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID = "SERIE_A_COMPLETED_FIXTURE_IDENTITIES_V1"
COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256 = (
    "181d76b75c092d46b57535591abbb4e625c3e54e9b0f876402c9a3e0ed2457fb"
)
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED_SOURCE_EVENTS = {"schedule", "workflow_dispatch"}
_ALLOWED_FORWARD_EVENTS = {"schedule", "workflow_dispatch"}
_OUTCOME_KEYS = {
    "result", "outcome", "score", "finalscore", "homegoals", "awaygoals",
    "fthg", "ftag", "ftr", "winner", "winningteam", "settlement",
    "settledresult", "homewin", "awaywin", "isdraw", "drawresult",
}


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


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} is missing")
    normalized = value.removeprefix("sha256:")
    if _SHA256.fullmatch(normalized) is None:
        raise ValueError(f"{field} is not a lowercase SHA-256")
    return normalized


def _positive_int(value: Any, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _guard_no_outcomes(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if (
                normalized in _OUTCOME_KEYS
                or normalized.endswith(("outcome", "result", "score", "goals"))
            ):
                raise ValueError(f"target outcome/score field forbidden before gate: {path}.{key}")
            _guard_no_outcomes(child, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _guard_no_outcomes(child, path=f"{path}[{index}]")


def _canonical_team(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("fixture team identity must be a non-empty string")
    value = value.strip()
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
        raise ValueError("fixture team identity contains control characters")
    configured = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    canonical = {"Atalanta BC": "Atalanta"}.get(configured, configured)
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in canonical):
        raise ValueError("canonical team identity contains control characters")
    return canonical


def _fixture_identity(match_date: Any, home: Any, away: Any) -> tuple[str, str, str]:
    if isinstance(match_date, datetime):
        parsed_date = match_date.date()
    elif isinstance(match_date, date):
        parsed_date = match_date
    elif isinstance(match_date, str):
        try:
            parsed_date = date.fromisoformat(match_date)
        except ValueError as exc:
            raise ValueError("fixture match_date must use YYYY-MM-DD") from exc
        if parsed_date.isoformat() != match_date:
            raise ValueError("fixture match_date must use canonical YYYY-MM-DD")
    else:
        raise ValueError("fixture match_date is missing")
    home_name, away_name = _canonical_team(home), _canonical_team(away)
    if home_name.casefold() == away_name.casefold():
        raise ValueError("fixture identity has identical canonical teams")
    return parsed_date.isoformat(), home_name, away_name


def _probabilities(value: Any, field: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{field} must contain [home, draw, away]")
    result = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field} contains a non-numeric probability")
        number = float(item)
        if not math.isfinite(number) or not 0.0 < number < 1.0:
            raise ValueError(f"{field} probabilities must be finite and inside (0,1)")
        result.append(number)
    if not math.isclose(sum(result), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{field} probabilities must sum to one")
    return result[0], result[1], result[2]


def _sha_fixture_set(identities: Iterable[tuple[str, str, str]]) -> str:
    canonical = sorted(tuple(item) for item in identities)
    raw = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_run_metadata(
    metadata: Mapping[str, Any],
    *,
    expected_id: int,
    expected_path: str,
    expected_name: str,
    allowed_events: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{label} parent run metadata is missing")
    if metadata.get("id") != expected_id:
        raise ValueError(f"{label} parent run ID mismatch")
    if metadata.get("path") != expected_path or metadata.get("name") != expected_name:
        raise ValueError(f"{label} parent workflow identity mismatch")
    if metadata.get("head_branch") != "main":
        raise ValueError(f"{label} parent run must be from main")
    head_sha = metadata.get("head_sha")
    if not isinstance(head_sha, str) or _SHA1.fullmatch(head_sha) is None:
        raise ValueError(f"{label} parent HEAD SHA is malformed")
    if metadata.get("event") not in allowed_events:
        raise ValueError(f"{label} parent event is not allowed")
    if metadata.get("status") != "completed" or metadata.get("conclusion") != "success":
        raise ValueError(f"{label} parent run did not complete successfully")
    created = _utc(metadata.get("created_at_utc"), f"{label} run created_at")
    completed = _utc(metadata.get("completed_at_utc"), f"{label} run completed_at")
    if completed < created:
        raise ValueError(f"{label} parent run clocks are reversed")
    return {
        "id": expected_id,
        "path": expected_path,
        "name": expected_name,
        "head_branch": "main",
        "head_sha": head_sha,
        "event": metadata["event"],
        "status": "completed",
        "conclusion": "success",
        "created_at_utc": created.isoformat(),
        "completed_at_utc": completed.isoformat(),
    }


def _validate_artifact_metadata(
    metadata: Mapping[str, Any],
    *,
    expected_name: str,
    expected_path: str,
    expected_workflow_name: str,
    allowed_events: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{label} artifact metadata is missing")
    artifact_id = _positive_int(metadata.get("artifact_id"), f"{label} artifact_id")
    if metadata.get("name") != expected_name:
        raise ValueError(f"{label} artifact name mismatch")
    digest = _digest(metadata.get("sha256"), f"{label} artifact SHA-256")
    if metadata.get("zip_sha256_verified") is not True:
        raise ValueError(f"{label} artifact ZIP bytes have not been independently SHA-verified")
    if metadata.get("run_metadata_verified") is not True or metadata.get("code_contract_verified") is not True:
        raise ValueError(f"{label} parent run metadata and exact code contract have not been independently verified")
    created = _utc(metadata.get("created_at_utc"), f"{label} artifact created_at")
    parent = _validate_run_metadata(
        metadata.get("parent_run"),
        expected_id=_positive_int(metadata.get("parent_run_id"), f"{label} parent_run_id"),
        expected_path=expected_path,
        expected_name=expected_workflow_name,
        allowed_events=allowed_events,
        label=label,
    )
    if not (
        _utc(parent["created_at_utc"], f"{label} run created")
        <= created
        <= _utc(parent["completed_at_utc"], f"{label} run completed")
    ):
        raise ValueError(f"{label} artifact was created outside its parent run interval")
    return {
        "artifact_id": artifact_id,
        "name": expected_name,
        "sha256": digest,
        "created_at_utc": created.isoformat(),
        "parent_run": parent,
    }


def normalize_original_forward_report(
    report: Mapping[str, Any],
    *,
    forward_artifact_metadata: Mapping[str, Any],
    source_artifacts_by_id: Mapping[int, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Validate source-before-quote original-V2 rows for the secondary analysis.

    The caller must independently authenticate the forward/source GitHub
    artifact ZIP bytes and parent-run metadata before calling this function.
    """
    if not isinstance(report, Mapping):
        raise ValueError("forward report must be an object")
    _guard_no_outcomes(report)
    forward_artifact = _validate_artifact_metadata(
        forward_artifact_metadata,
        expected_name=FORWARD_ARTIFACT_NAME,
        expected_path=FORWARD_WORKFLOW_PATH,
        expected_workflow_name=FORWARD_WORKFLOW_NAME,
        allowed_events=_ALLOWED_FORWARD_EVENTS,
        label="forward",
    )
    if report.get("schema_version") != "SERIE_A_ORIGINAL_V2_FORWARD_SOURCE_BEFORE_QUOTE_V1":
        raise ValueError("wrong original V2 forward report schema")
    if report.get("mode") != "RESTORED_ORIGINAL_V2_RESEARCH_ONLY_NO_BET":
        raise ValueError("wrong original V2 forward report mode")
    if report.get("uses_original_frozen_v2") is not True:
        raise ValueError("forward report is not the original frozen V2")
    if report.get("uses_2026_27_results") is not False:
        raise ValueError("protected 2026/27 results were used in original V2 capture")
    if report.get("independent_incumbent_asof_verified") is not False:
        raise ValueError("secondary evaluator must preserve the original missing-incumbent status")
    if report.get("eligible_for_frozen_prospective_cohort") is not False:
        raise ValueError("secondary evaluator must not rewrite original cohort eligibility")
    if report.get("eligible_for_product_publication") is not False or report.get("no_bet") is not True:
        raise ValueError("original V2 forward report must remain non-publishable and NO_BET")
    if report.get("training_or_promotion") is not False:
        raise ValueError("training/refit/promotion is forbidden")
    if report.get("paid_provider_calls") != 0 or report.get("supabase_writes") != 0:
        raise ValueError("paid calls and Supabase writes are forbidden")
    if not isinstance(report.get("rows"), list):
        raise ValueError("forward report rows must be a list")
    captured = _utc(report.get("captured_at_utc"), "forward captured_at_utc")
    forward_run = forward_artifact["parent_run"]
    if not (
        _utc(forward_run["created_at_utc"], "forward run created")
        <= captured
        <= _utc(forward_run["completed_at_utc"], "forward run completed")
    ):
        raise ValueError("forward report capture time is outside its parent run")

    used_archives = report.get("archived_sources_used")
    if not isinstance(used_archives, Mapping):
        raise ValueError("forward report lacks its source artifact digest map")
    normalized: list[dict[str, Any]] = []
    seen_event_ids: dict[str, tuple[str, str, str]] = {}
    for index, row in enumerate(report["rows"]):
        if not isinstance(row, Mapping):
            raise ValueError(f"forward row {index} is malformed")
        _guard_no_outcomes(row, path=f"rows[{index}]")
        if row.get("status") != "SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY":
            continue
        if row.get("no_bet") is not True:
            raise ValueError("original forward row must remain NO_BET")
        preview = row.get("v2_preview")
        if not isinstance(preview, Mapping):
            raise ValueError("source-before-quote row lacks a V2 preview")
        event_id = row.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("forward event_id is missing")
        quote_time = _utc(row.get("quote_time_utc"), "quote_time_utc")
        kickoff = _utc(row.get("kickoff_utc"), "kickoff_utc")
        if not quote_time < kickoff:
            raise ValueError("market quote is not strictly pre-kickoff")
        if not captured < kickoff or quote_time > captured:
            raise ValueError("V2 preview was not captured between quote and kickoff")
        if not captured <= _utc(forward_artifact["created_at_utc"], "forward artifact created_at") < kickoff:
            raise ValueError("forward forecast artifact was not persisted after capture and before kickoff")
        if preview.get("event_id") != event_id:
            raise ValueError("forward event identity differs from its V2 preview")
        if _utc(preview.get("market_snapshot_time_utc"), "preview market snapshot") != quote_time:
            raise ValueError("V2 preview market time differs from the saved quote")
        if _utc(preview.get("kickoff_utc"), "preview kickoff") != kickoff:
            raise ValueError("V2 preview kickoff differs from the saved quote")
        feature_cutoff = _utc(preview.get("feature_history_cutoff_utc"), "feature history cutoff")
        if feature_cutoff > quote_time or feature_cutoff >= kickoff:
            raise ValueError("original 19-feature history cutoff is not pre-quote")
        if preview.get("model_candidate_sha256") != CANDIDATE_SHA256:
            raise ValueError("V2 preview candidate SHA differs from the frozen original")
        if preview.get("eligible_for_frozen_prospective_cohort") is not False:
            raise ValueError("secondary row must retain original cohort ineligibility")
        if preview.get("eligible_for_product_publication") is not False or preview.get("no_bet") is not True:
            raise ValueError("V2 preview must remain NO_BET and non-publishable")
        market = _probabilities(preview.get("market_1x2"), "market_1x2")
        active = _probabilities(preview.get("active_market_fallback_1x2"), "active_market_fallback_1x2")
        shadow = _probabilities(preview.get("shadow_v2_residual_1x2"), "shadow_v2_residual_1x2")
        if any(abs(a - b) > 1e-12 for a, b in zip(market, active)):
            raise ValueError("active_lambda=0 must remain exactly the de-vigged market")

        source_id = _positive_int(row.get("source_artifact_id"), "source_artifact_id")
        source_sha = _digest(row.get("source_artifact_sha256"), "source_artifact_sha256")
        source_artifact = _validate_artifact_metadata(
            source_artifacts_by_id.get(source_id),
            expected_name=SOURCE_ARTIFACT_NAME,
            expected_path=SOURCE_WORKFLOW_PATH,
            expected_workflow_name=SOURCE_WORKFLOW_NAME,
            allowed_events=_ALLOWED_SOURCE_EVENTS,
            label=f"source-{source_id}",
        )
        if source_artifact["artifact_id"] != source_id or source_artifact["sha256"] != source_sha:
            raise ValueError("source artifact ID/SHA differs from independently verified GitHub metadata")
        if not source_artifact["created_at_utc"] < quote_time.isoformat():
            raise ValueError("source artifact was not created before the quote")
        source_run = source_artifact["parent_run"]
        if not source_run["completed_at_utc"] < quote_time.isoformat():
            raise ValueError("source parent workflow did not finish before the quote")
        verified_source = row.get("verified_source_workflow_run")
        if not isinstance(verified_source, Mapping):
            raise ValueError("forward row lacks verified source parent-run attestation")
        if (
            verified_source.get("run_id") != source_run["id"]
            or verified_source.get("run_head_sha") != source_run["head_sha"]
            or verified_source.get("workflow_path") != SOURCE_WORKFLOW_PATH
            or _utc(verified_source.get("run_completed_at_utc"), "source run completion")
            != _utc(source_run["completed_at_utc"], "source run completion")
            or verified_source.get("source_loader_blob_sha1") != SOURCE_LOADER_BLOB_SHA1
            or verified_source.get("source_rights_helper_blob_sha1") != SOURCE_RIGHTS_HELPER_BLOB_SHA1
            or verified_source.get("source_rights_manifest_blob_sha1") != SOURCE_RIGHTS_MANIFEST_BLOB_SHA1
        ):
            raise ValueError("source run attestation does not match the frozen source/rights pins")
        if used_archives.get(str(source_id)) != source_sha:
            raise ValueError("source artifact SHA is absent from the forward report digest map")

        local_date = kickoff.astimezone(LOCAL_TIMEZONE).date()
        identity = _fixture_identity(local_date, preview.get("home_team"), preview.get("away_team"))
        prior_identity = seen_event_ids.get(event_id)
        if prior_identity is not None and prior_identity != identity:
            raise ValueError("one provider event ID maps to multiple fixture identities")
        seen_event_ids[event_id] = identity
        normalized.append({
            "fixture_identity": identity,
            "event_id": event_id,
            "home_team": identity[1],
            "away_team": identity[2],
            "match_date": identity[0],
            "quote_time_utc": quote_time.isoformat(),
            "capture_time_utc": captured.isoformat(),
            "kickoff_utc": kickoff.isoformat(),
            "feature_history_cutoff_utc": feature_cutoff.isoformat(),
            "market_1x2": market,
            "active_market_fallback_1x2": active,
            "shadow_v2_residual_1x2": shadow,
            "candidate_sha256": CANDIDATE_SHA256,
            "source_artifact_id": source_id,
            "source_artifact_sha256": source_sha,
            "source_artifact_created_at_utc": source_artifact["created_at_utc"],
            "source_parent_run_id": source_run["id"],
            "source_parent_run_head_sha": source_run["head_sha"],
            "source_parent_run_created_at_utc": source_run["created_at_utc"],
            "source_parent_run_completed_at_utc": source_run["completed_at_utc"],
            "source_parent_run_path": source_run["path"],
            "source_parent_run_name": source_run["name"],
            "source_parent_run_branch": source_run["head_branch"],
            "source_parent_run_event": source_run["event"],
            "source_parent_run_status": source_run["status"],
            "source_parent_run_conclusion": source_run["conclusion"],
            "source_loader_blob_sha1": SOURCE_LOADER_BLOB_SHA1,
            "source_rights_helper_blob_sha1": SOURCE_RIGHTS_HELPER_BLOB_SHA1,
            "source_rights_manifest_blob_sha1": SOURCE_RIGHTS_MANIFEST_BLOB_SHA1,
            "source_artifact_metadata_verified": True,
            "source_code_contract_verified": True,
            "forward_artifact_id": forward_artifact["artifact_id"],
            "forward_artifact_sha256": forward_artifact["sha256"],
            "forward_artifact_created_at_utc": forward_artifact["created_at_utc"],
            "forward_parent_run_id": forward_run["id"],
            "forward_parent_run_head_sha": forward_run["head_sha"],
            "forward_parent_run_created_at_utc": forward_run["created_at_utc"],
            "forward_parent_run_completed_at_utc": forward_run["completed_at_utc"],
            "forward_parent_run_path": forward_run["path"],
            "forward_parent_run_name": forward_run["name"],
            "forward_parent_run_branch": forward_run["head_branch"],
            "forward_parent_run_event": forward_run["event"],
            "forward_parent_run_status": forward_run["status"],
            "forward_parent_run_conclusion": forward_run["conclusion"],
            "forward_artifact_metadata_verified": True,
            "source_before_quote_provenance_verified": True,
            "original_frozen_cohort_eligible": False,
            "secondary_market_only_eligible": True,
            "no_bet": True,
        })
    return normalized


def select_first_eligible_forecast_per_fixture(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Select the earliest pre-kickoff secondary capture without outcome/price selection."""
    chosen: dict[tuple[str, str, str], dict[str, Any]] = {}
    event_to_fixture: dict[str, tuple[str, str, str]] = {}
    for raw in rows:
        row = dict(raw)
        _guard_no_outcomes(row)
        identity = row.get("fixture_identity")
        if not isinstance(identity, (tuple, list)) or len(identity) != 3:
            raise ValueError("secondary forecast lacks a canonical fixture identity")
        fixture = _fixture_identity(*identity)
        event_id = row.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("secondary forecast event_id is missing")
        prior = event_to_fixture.get(event_id)
        if prior is not None and prior != fixture:
            raise ValueError("one provider event ID maps to multiple fixtures")
        event_to_fixture[event_id] = fixture
        if row.get("candidate_sha256") != CANDIDATE_SHA256 or row.get("secondary_market_only_eligible") is not True:
            raise ValueError("row is not eligible for this frozen secondary protocol")
        if row.get("original_frozen_cohort_eligible") is not False or row.get("no_bet") is not True:
            raise ValueError("secondary selection cannot rewrite original eligibility or NO_BET")
        required_provenance = (
            "source_artifact_id", "source_artifact_sha256", "source_artifact_created_at_utc",
            "source_parent_run_id", "source_parent_run_head_sha",
            "source_parent_run_created_at_utc", "source_parent_run_completed_at_utc",
            "forward_artifact_id", "forward_artifact_sha256", "forward_artifact_created_at_utc",
            "forward_parent_run_id", "forward_parent_run_head_sha",
            "forward_parent_run_created_at_utc", "forward_parent_run_completed_at_utc",
            "source_parent_run_path", "source_parent_run_name", "source_parent_run_branch",
            "source_parent_run_event", "source_parent_run_status", "source_parent_run_conclusion",
            "source_loader_blob_sha1", "source_rights_helper_blob_sha1",
            "source_rights_manifest_blob_sha1", "source_artifact_metadata_verified",
            "source_code_contract_verified",
            "forward_parent_run_path", "forward_parent_run_name", "forward_parent_run_branch",
            "forward_parent_run_event", "forward_parent_run_status", "forward_parent_run_conclusion",
            "forward_artifact_metadata_verified", "feature_history_cutoff_utc",
        )
        missing_provenance = [field for field in required_provenance if field not in row]
        if missing_provenance or row.get("source_before_quote_provenance_verified") is not True:
            raise ValueError("secondary forecast lacks normalized source-before-quote provenance")
        if (
            row.get("source_artifact_metadata_verified") is not True
            or row.get("source_code_contract_verified") is not True
            or row.get("source_parent_run_path") != SOURCE_WORKFLOW_PATH
            or row.get("source_parent_run_name") != SOURCE_WORKFLOW_NAME
            or row.get("source_parent_run_branch") != "main"
            or row.get("source_parent_run_event") not in _ALLOWED_SOURCE_EVENTS
            or row.get("source_parent_run_status") != "completed"
            or row.get("source_parent_run_conclusion") != "success"
            or row.get("source_loader_blob_sha1") != SOURCE_LOADER_BLOB_SHA1
            or row.get("source_rights_helper_blob_sha1") != SOURCE_RIGHTS_HELPER_BLOB_SHA1
            or row.get("source_rights_manifest_blob_sha1") != SOURCE_RIGHTS_MANIFEST_BLOB_SHA1
        ):
            raise ValueError("secondary forecast source parent/workflow/code attestation is invalid")
        if (
            row.get("forward_artifact_metadata_verified") is not True
            or row.get("forward_parent_run_path") != FORWARD_WORKFLOW_PATH
            or row.get("forward_parent_run_name") != FORWARD_WORKFLOW_NAME
            or row.get("forward_parent_run_branch") != "main"
            or row.get("forward_parent_run_event") not in _ALLOWED_FORWARD_EVENTS
            or row.get("forward_parent_run_status") != "completed"
            or row.get("forward_parent_run_conclusion") != "success"
        ):
            raise ValueError("secondary forecast forward parent/workflow attestation is invalid")
        _positive_int(row.get("source_artifact_id"), "source_artifact_id")
        _digest(row.get("source_artifact_sha256"), "source_artifact_sha256")
        _positive_int(row.get("source_parent_run_id"), "source_parent_run_id")
        if _SHA1.fullmatch(str(row.get("source_parent_run_head_sha", ""))) is None:
            raise ValueError("source parent run HEAD SHA is malformed")
        _positive_int(row.get("forward_artifact_id"), "forward_artifact_id")
        _digest(row.get("forward_artifact_sha256"), "forward_artifact_sha256")
        _positive_int(row.get("forward_parent_run_id"), "forward_parent_run_id")
        if _SHA1.fullmatch(str(row.get("forward_parent_run_head_sha", ""))) is None:
            raise ValueError("forward parent run HEAD SHA is malformed")
        capture = _utc(row.get("capture_time_utc"), "capture_time_utc")
        quote = _utc(row.get("quote_time_utc"), "quote_time_utc")
        kickoff = _utc(row.get("kickoff_utc"), "kickoff_utc")
        source_created = _utc(row.get("source_artifact_created_at_utc"), "source_artifact_created_at_utc")
        source_run_created = _utc(row.get("source_parent_run_created_at_utc"), "source_parent_run_created_at_utc")
        source_run_completed = _utc(row.get("source_parent_run_completed_at_utc"), "source_parent_run_completed_at_utc")
        forward_created = _utc(row.get("forward_artifact_created_at_utc"), "forward_artifact_created_at_utc")
        forward_run_created = _utc(row.get("forward_parent_run_created_at_utc"), "forward_parent_run_created_at_utc")
        forward_run_completed = _utc(row.get("forward_parent_run_completed_at_utc"), "forward_parent_run_completed_at_utc")
        feature_cutoff = _utc(row.get("feature_history_cutoff_utc"), "feature_history_cutoff_utc")
        if not source_run_created <= source_created <= source_run_completed < quote:
            raise ValueError("source archive and successful source workflow must both precede the quote")
        if not forward_run_created <= forward_created <= forward_run_completed:
            raise ValueError("forward artifact is outside its successful parent workflow interval")
        if not forward_run_created <= capture <= forward_run_completed:
            raise ValueError("forward capture is outside its successful parent workflow interval")
        if not capture <= forward_created < kickoff:
            raise ValueError("forward forecast artifact was not persisted after capture and before kickoff")
        if feature_cutoff > quote or feature_cutoff >= kickoff:
            raise ValueError("original feature history cutoff is not pre-quote")
        if not quote <= capture < kickoff:
            raise ValueError("secondary forecast must be captured after quote and before kickoff")
        market = _probabilities(row.get("market_1x2"), "market_1x2")
        active = _probabilities(row.get("active_market_fallback_1x2"), "active_market_fallback_1x2")
        _probabilities(row.get("shadow_v2_residual_1x2"), "shadow_v2_residual_1x2")
        if any(abs(a - b) > 1e-12 for a, b in zip(market, active)):
            raise ValueError("active_lambda=0 must equal market in selected rows")
        old = chosen.get(fixture)
        if old is None:
            chosen[fixture] = row
            continue
        old_capture = _utc(old["capture_time_utc"], "existing capture_time_utc")
        if capture == old_capture:
            raise ValueError("equal capture timestamps for one fixture fail closed")
        if capture < old_capture:
            chosen[fixture] = row
    return [chosen[key] for key in sorted(chosen)]


def _validate_completed_gate(
    completed_identities: Iterable[tuple[str, str, str]],
    attestation: Mapping[str, Any],
) -> set[tuple[str, str, str]]:
    identities = {_fixture_identity(*item) for item in completed_identities}
    for match_date, home, away in identities:
        if (match_date, away, home) in identities:
            raise ValueError("completed-fixture gate contains a reversed duplicate fixture identity")
    required = {
        "schema_version", "source_table", "selected_columns", "league", "season",
        "query_contract_id", "query_contract_sha256", "captured_at_utc",
        "cutoff_date_exclusive_utc", "completed_fixture_identity_count",
        "completed_fixture_identity_sha256", "outcome_columns_selected", "target_outcomes_read",
    }
    if not isinstance(attestation, Mapping) or set(attestation) != required:
        raise ValueError("completed-fixture gate attestation has unapproved or missing fields")
    captured = _utc(attestation.get("captured_at_utc"), "completed gate captured_at_utc")
    cutoff_raw = attestation.get("cutoff_date_exclusive_utc")
    if not isinstance(cutoff_raw, str):
        raise ValueError("completed gate cutoff date is missing")
    cutoff = date.fromisoformat(cutoff_raw)
    if cutoff.isoformat() != cutoff_raw or cutoff != captured.date():
        raise ValueError("completed gate cutoff must equal its UTC capture date")
    if attestation.get("schema_version") != "MARKET_ANCHOR_1X2_V2_COMPLETED_FIXTURE_IDENTITY_GATE_V1":
        raise ValueError("wrong completed-fixture gate schema")
    if attestation.get("source_table") != COMPLETED_FIXTURE_GATE_SOURCE_TABLE:
        raise ValueError("wrong completed-fixture gate source table")
    if attestation.get("selected_columns") != list(COMPLETED_FIXTURE_GATE_COLUMNS):
        raise ValueError("completed-fixture gate must select identity metadata only")
    if attestation.get("league") != PRIMARY_LEAGUE or attestation.get("season") != PRIMARY_SEASON:
        raise ValueError("completed-fixture gate is not the frozen Serie A primary season")
    if attestation.get("query_contract_id") != COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID:
        raise ValueError("completed-fixture gate query contract ID mismatch")
    if attestation.get("query_contract_sha256") != COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256:
        raise ValueError("completed-fixture gate query contract SHA mismatch")
    if attestation.get("outcome_columns_selected") is not False or attestation.get("target_outcomes_read") is not False:
        raise ValueError("completed-fixture gate must be identity-only and outcome-blind")
    if type(attestation.get("completed_fixture_identity_count")) is not int:
        raise ValueError("completed-fixture gate count is malformed")
    if attestation["completed_fixture_identity_count"] != len(identities):
        raise ValueError("completed-fixture gate count does not match returned identities")
    if attestation.get("completed_fixture_identity_sha256") != _sha_fixture_set(identities):
        raise ValueError("completed-fixture gate identity SHA mismatch")
    for match_date, _, _ in identities:
        day = date.fromisoformat(match_date)
        if not PRIMARY_SEASON_START <= day <= PRIMARY_SEASON_END or day >= cutoff:
            raise ValueError("completed-fixture identity falls outside the frozen primary season/cutoff")
    return identities


def _brier(probabilities: tuple[float, float, float], outcome: str) -> float:
    index = {"H": 0, "D": 1, "A": 2}[outcome]
    return sum((p - (1.0 if i == index else 0.0)) ** 2 for i, p in enumerate(probabilities))


def _log_loss(probabilities: tuple[float, float, float], outcome: str) -> float:
    index = {"H": 0, "D": 1, "A": 2}[outcome]
    return -math.log(probabilities[index])


def _percentile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("cannot calculate percentile of an empty bootstrap sample")
    return sorted_values[round((len(sorted_values) - 1) * probability)]


def _paired_bootstrap(
    market_brier: list[float],
    shadow_brier: list[float],
    market_logloss: list[float],
    shadow_logloss: list[float],
) -> dict[str, Any]:
    n = len(market_brier)
    rng = random.Random(BOOTSTRAP_SEED)
    brier_delta, logloss_delta = [], []
    for _ in range(BOOTSTRAP_REPLICATES):
        indices = [rng.randrange(n) for _ in range(n)]
        brier_delta.append(fmean(shadow_brier[i] - market_brier[i] for i in indices))
        logloss_delta.append(fmean(shadow_logloss[i] - market_logloss[i] for i in indices))
    brier_delta.sort()
    logloss_delta.sort()
    return {
        "replicates": BOOTSTRAP_REPLICATES,
        "seed": BOOTSTRAP_SEED,
        "confidence_level": 0.95,
        "brier_delta_shadow_minus_market_ci95": [
            _percentile(brier_delta, 0.025), _percentile(brier_delta, 0.975)
        ],
        "log_loss_delta_shadow_minus_market_ci95": [
            _percentile(logloss_delta, 0.025), _percentile(logloss_delta, 0.975)
        ],
        "probability_shadow_better_brier": sum(value < 0 for value in brier_delta) / BOOTSTRAP_REPLICATES,
        "probability_shadow_better_log_loss": sum(value < 0 for value in logloss_delta) / BOOTSTRAP_REPLICATES,
    }


def evaluate_market_only_secondary_cohort(
    forecasts: Iterable[Mapping[str, Any]],
    *,
    completed_fixture_identities: Iterable[tuple[str, str, str]],
    completed_gate_attestation: Mapping[str, Any],
    load_outcomes: Callable[[tuple[tuple[str, str, str], ...]], Mapping[tuple[str, str, str], str]],
) -> dict[str, Any]:
    """Evaluate only after 30 completed identities and 30 completed forecasts.

    The callback is not called if either gate is closed. The original frozen
    prospective-cohort eligibility flag remains false throughout.
    """
    completed = _validate_completed_gate(completed_fixture_identities, completed_gate_attestation)
    selected = select_first_eligible_forecast_per_fixture(forecasts)
    completed_forecasts = [row for row in selected if row["fixture_identity"] in completed]
    base = {
        "schema_version": SCHEMA_VERSION,
        "policy_id": POLICY_ID,
        "experiment_id": EXPERIMENT_ID,
        "candidate_sha256": CANDIDATE_SHA256,
        "primary_league": PRIMARY_LEAGUE,
        "primary_season": PRIMARY_SEASON,
        "active_lambda": ACTIVE_LAMBDA,
        "shadow_residual_lambda": SHADOW_RESIDUAL_LAMBDA,
        "completed_primary_fixture_identities": len(completed),
        "eligible_completed_forecasts": len(completed_forecasts),
        "protected_30_completed_forecast_gate_passed": len(completed_forecasts) >= MIN_ELIGIBLE_COMPLETED_FORECASTS,
        "minimum_completed_primary_fixtures": MIN_COMPLETED_PRIMARY_FIXTURES,
        "minimum_eligible_completed_forecasts": MIN_ELIGIBLE_COMPLETED_FORECASTS,
        "original_frozen_cohort_eligible": False,
        "secondary_market_only_analysis": True,
        "incumbent_used": False,
        "no_bet": True,
        "automatic_promotion": False,
        "production_writes": 0,
        "supabase_writes": 0,
        "paid_provider_calls": 0,
    }
    if len(completed) < MIN_COMPLETED_PRIMARY_FIXTURES:
        return {
            **base,
            "status": "COMPLETED_PRIMARY_IDENTITY_PREFLIGHT_CLOSED_NO_OUTCOME_READ",
            "target_outcomes_read": False,
            "outcomes_scored": False,
        }
    if len(completed_forecasts) < MIN_ELIGIBLE_COMPLETED_FORECASTS:
        return {
            **base,
            "status": "PROTECTED_30_PRIMARY_COMPLETED_FORECAST_GATE_CLOSED_NO_OUTCOME_READ",
            "target_outcomes_read": False,
            "outcomes_scored": False,
        }

    identities = tuple(row["fixture_identity"] for row in completed_forecasts)
    # Capture the real UTC evaluation clock before invoking the lazy outcome loader.
    # A timestamp later than this observation cannot be treated as already-persisted evidence.
    evaluation_observed_at = datetime.now(timezone.utc)
    outcomes = load_outcomes(identities)
    if not isinstance(outcomes, Mapping) or set(outcomes) != set(identities):
        raise ValueError("outcome loader must return exactly the selected completed fixture identities")
    for identity, payload in outcomes.items():
        if not isinstance(payload, Mapping) or set(payload) != {"result", "persisted_at_utc"}:
            raise ValueError("post-gate outcome payload must contain only result and persisted_at_utc")
        if payload.get("result") not in {"H", "D", "A"}:
            raise ValueError("outcome loader returned an invalid 1X2 result")
        persisted_at = _utc(payload.get("persisted_at_utc"), "persisted_at_utc")
        kickoff = _utc(
            next(row["kickoff_utc"] for row in completed_forecasts if row["fixture_identity"] == identity),
            "forecast kickoff",
        )
        if persisted_at <= kickoff:
            raise ValueError("persisted_at_utc must be strictly after kickoff")
        if persisted_at > evaluation_observed_at:
            raise ValueError("persisted_at_utc cannot be later than evaluation observation time")

    market_brier, shadow_brier, market_logloss, shadow_logloss = [], [], [], []
    for row in completed_forecasts:
        outcome = outcomes[row["fixture_identity"]]["result"]
        market = tuple(row["market_1x2"])
        shadow = tuple(row["shadow_v2_residual_1x2"])
        market_brier.append(_brier(market, outcome))
        shadow_brier.append(_brier(shadow, outcome))
        market_logloss.append(_log_loss(market, outcome))
        shadow_logloss.append(_log_loss(shadow, outcome))
    bootstrap = _paired_bootstrap(market_brier, shadow_brier, market_logloss, shadow_logloss)
    return {
        **base,
        "status": "EVALUATED_SECONDARY_MARKET_ONLY",
        "target_outcomes_read": True,
        "outcomes_scored": True,
        "post_kickoff_persistence_verified": True,
        "sample_size": len(completed_forecasts),
        "market": {
            "brier_score": fmean(market_brier),
            "log_loss": fmean(market_logloss),
        },
        "shadow_lambda_1": {
            "brier_score": fmean(shadow_brier),
            "log_loss": fmean(shadow_logloss),
        },
        "delta_shadow_minus_market": {
            "brier_score": fmean(shadow_brier) - fmean(market_brier),
            "log_loss": fmean(shadow_logloss) - fmean(market_logloss),
        },
        "paired_bootstrap": bootstrap,
        "superiority_claim_permitted": False,
        "note": "Secondary market-only evidence; does not alter or satisfy the original frozen V2 cohort contract.",
    }
