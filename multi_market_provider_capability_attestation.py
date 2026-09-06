"""Reviewed provider-corner capability attestation contract.

A diagnostic probe artifact is evidence, not activation. This module only
accepts a separately committed, review-approved attestation that points back to
an immutable successful capability-probe run/artifact. The loader is read-only;
it never creates or updates the attestation and never calls the provider or
Supabase.

This is deliberately analogous to a manual research promotion gate: a probe
cannot promote itself. Until an approved attestation is added through normal
Git review, readiness remains fail-closed unless immutable stored snapshots
already contain corner-market evidence.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from multi_market_policy import CORNER_SOURCE_READY_LEAGUES

ATTESTATION_PATH = Path("research/multi_market_provider_corner_capability_attestation.json")
ATTESTATION_SCHEMA = "MULTI_MARKET_PROVIDER_CORNER_CAPABILITY_ATTESTATION_V1"
PROBE_SCHEMA = "MULTI_MARKET_CORNER_CAPABILITY_PROBE_V1"
PROVIDER = "the_odds_api"
REVIEW_STATUS = "APPROVED"
REVIEW_DECISION = "ACCEPT_PROVIDER_CAPABILITY_ONLY"
CORNER_MARKETS = frozenset({"alternate_totals_corners", "alternate_team_totals_corners"})
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _base_result(path: Path) -> dict[str, Any]:
    return {
        "schema_version": ATTESTATION_SCHEMA,
        "read_only": True,
        "path": str(path),
        "present": False,
        "valid": False,
        "capability_ready": False,
        "error": None,
        "workflow_run_id": None,
        "artifact_id": None,
        "artifact_sha256": None,
        "probe_head_sha": None,
        "league": None,
        "corner_market_keys": [],
        "corner_bookmaker_count": 0,
    }


def _positive_int(value: Any, *, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{field} must be a positive integer")
    return parsed


def _validate_reviewed_at(value: Any) -> str:
    text = str(value or "")
    if not text:
        raise ValueError("reviewed_at_utc is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("reviewed_at_utc must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("reviewed_at_utc must be timezone-aware")
    return text


def validate_attestation(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("attestation must be a JSON object")
    if payload.get("schema_version") != ATTESTATION_SCHEMA:
        raise ValueError("unexpected attestation schema_version")
    if payload.get("review_status") != REVIEW_STATUS:
        raise ValueError("attestation review_status is not APPROVED")
    if payload.get("review_decision") != REVIEW_DECISION:
        raise ValueError("attestation review_decision is not capability-only approval")
    if payload.get("research_only") is not True:
        raise ValueError("attestation must be research_only")
    if payload.get("production_promotion") is not False:
        raise ValueError("attestation must explicitly forbid production promotion")
    if payload.get("prospective_oos_evaluation_active") is not False:
        raise ValueError("attestation cannot activate OOS evaluation")
    if payload.get("source_probe_writes_performed") is not False:
        raise ValueError("source probe must be write-free")
    if payload.get("provider") != PROVIDER:
        raise ValueError("unexpected capability provider")
    if payload.get("probe_schema_version") != PROBE_SCHEMA:
        raise ValueError("unexpected capability probe schema")
    if payload.get("probe_status") != "CAPABILITY_CONFIRMED":
        raise ValueError("probe did not confirm provider capability")

    workflow_run_id = _positive_int(payload.get("workflow_run_id"), field="workflow_run_id")
    artifact_id = _positive_int(payload.get("artifact_id"), field="artifact_id")
    artifact_sha256 = str(payload.get("artifact_sha256") or "").lower()
    probe_head_sha = str(payload.get("probe_head_sha") or "").lower()
    if not _SHA256.fullmatch(artifact_sha256):
        raise ValueError("artifact_sha256 must be 64 lowercase hex characters")
    if not _SHA40.fullmatch(probe_head_sha):
        raise ValueError("probe_head_sha must be 40 lowercase hex characters")
    _validate_reviewed_at(payload.get("reviewed_at_utc"))

    target = payload.get("target")
    if not isinstance(target, dict):
        raise ValueError("target must be an object")
    required_target = ("league", "event_id", "home_team", "away_team", "commence_time_utc")
    if any(not str(target.get(key) or "").strip() for key in required_target):
        raise ValueError("target identity is incomplete")
    league = str(target["league"])
    if league not in set(CORNER_SOURCE_READY_LEAGUES):
        raise ValueError("attested league is not canonical corner-source-ready")

    raw_markets = payload.get("corner_market_keys")
    if not isinstance(raw_markets, list) or not raw_markets:
        raise ValueError("corner_market_keys must contain observed corner markets")
    markets = sorted({str(value) for value in raw_markets if value})
    if not markets or any(value not in CORNER_MARKETS for value in markets):
        raise ValueError("attestation contains unrecognized corner market keys")
    corner_bookmaker_count = _positive_int(
        payload.get("corner_bookmaker_count"), field="corner_bookmaker_count"
    )

    return {
        "workflow_run_id": workflow_run_id,
        "artifact_id": artifact_id,
        "artifact_sha256": artifact_sha256,
        "probe_head_sha": probe_head_sha,
        "league": league,
        "corner_market_keys": markets,
        "corner_bookmaker_count": corner_bookmaker_count,
    }


def load_attestation(path: Path = ATTESTATION_PATH) -> dict[str, Any]:
    result = _base_result(path)
    if not path.exists():
        return result
    result["present"] = True
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validated = validate_attestation(payload)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
        return result
    result.update(validated)
    result["valid"] = True
    result["capability_ready"] = True
    return result
