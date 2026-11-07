"""Fail-closed permission gate for source data used to reconstruct AI model weights.

Integrity/provenance checks do not grant data-use rights. The recovery path must
have an explicit, auditable permission record before it reads or extracts a
training archive. This gate is intentionally independent of the frozen V2 model.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parent
DEFAULT_RIGHTS_MANIFEST_PATH = (
    REPOSITORY_ROOT / "research" / "source_rights" / "football_data_co_uk.json"
)
SCHEMA_VERSION = "FOOTBALL_AI_SOURCE_RIGHTS_V1"
EXPECTED_PROVIDER = "Football-Data.co.uk"
REQUIRED_SCOPES = {"AI_MODEL_TRAINING", "NONCOMMERCIAL_RESEARCH"}


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"source-rights {field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PermissionError(f"source-rights {field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermissionError(f"source-rights {field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def require_ai_model_training_permission(
    manifest_path: Path = DEFAULT_RIGHTS_MANIFEST_PATH,
    *,
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Require explicit evidence that the source permits AI-model training.

    The evidence file is committed locally and SHA-256 pinned by the manifest.
    No network request is made by this function. A public URL alone is not
    treated as a grant, and a valid data/archive SHA is not a rights attestation.
    """
    path = Path(manifest_path)
    root = Path(repo_root) if repo_root is not None else REPOSITORY_ROOT
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError("source-rights manifest is missing or invalid; AI training is blocked") from exc

    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise PermissionError("source-rights manifest schema is not approved")
    if manifest.get("provider") != EXPECTED_PROVIDER:
        raise PermissionError("source-rights manifest provider does not match the training source")
    if manifest.get("rights_status") != "GRANTED":
        raise PermissionError("Football-Data AI model-training permission is not granted")
    if manifest.get("ai_model_training_permitted") is not True:
        raise PermissionError("source-rights manifest does not permit AI model training")
    if manifest.get("research_use_permitted") is not True:
        raise PermissionError("source-rights manifest does not permit research use")

    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise PermissionError("source-rights verification clock must have a real UTC offset")
    now_utc = now.astimezone(timezone.utc)

    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict):
        raise PermissionError("source-rights grant has no auditable authorization evidence")
    if authorization.get("kind") not in {"written_permission", "open_license"}:
        raise PermissionError("source-rights authorization kind is not approved")

    scope = authorization.get("scope")
    if not isinstance(scope, list) or not REQUIRED_SCOPES.issubset(set(scope)):
        raise PermissionError("source-rights authorization does not cover AI model training and noncommercial research")

    for field in ("license_name", "rights_holder", "reviewed_by"):
        value = authorization.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PermissionError(f"source-rights authorization is missing {field}")

    evidence_url = authorization.get("evidence_url")
    parts = urlsplit(evidence_url if isinstance(evidence_url, str) else "")
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
    ):
        raise PermissionError("source-rights evidence URL must be a direct HTTPS reference")

    evidence_file = authorization.get("evidence_file")
    if not isinstance(evidence_file, str) or not evidence_file.strip():
        raise PermissionError("source-rights authorization is missing its local evidence file")
    relative = Path(evidence_file)
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError("source-rights evidence file must stay inside the repository")
    root_resolved = root.resolve()
    candidate = root_resolved / relative
    if candidate.is_symlink():
        raise PermissionError("source-rights evidence file cannot be a symbolic link")
    try:
        evidence_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise PermissionError("source-rights evidence file is missing") from exc
    if root_resolved not in evidence_path.parents or not evidence_path.is_file():
        raise PermissionError("source-rights evidence file is outside the repository or is not a file")

    expected_sha = authorization.get("evidence_sha256")
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise PermissionError("source-rights evidence SHA-256 is invalid")
    evidence_bytes = evidence_path.read_bytes()
    actual_sha = hashlib.sha256(evidence_bytes).hexdigest()
    if actual_sha != expected_sha:
        raise PermissionError("source-rights evidence SHA-256 mismatch")

    reviewed_at = _parse_utc(authorization.get("reviewed_at_utc"), "reviewed_at_utc")
    if reviewed_at > now_utc:
        raise PermissionError("source-rights evidence review time is in the future")
    valid_from = authorization.get("valid_from_utc")
    if valid_from is not None and _parse_utc(valid_from, "valid_from_utc") > now_utc:
        raise PermissionError("source-rights authorization is not yet valid")
    valid_until = authorization.get("valid_until_utc")
    if valid_until is not None and _parse_utc(valid_until, "valid_until_utc") <= now_utc:
        raise PermissionError("source-rights authorization has expired")

    return {
        "provider": EXPECTED_PROVIDER,
        "rights_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence_file": evidence_file,
        "evidence_sha256": actual_sha,
        "evidence_url": evidence_url,
        "license_name": authorization["license_name"],
        "rights_holder": authorization["rights_holder"],
        "scope": sorted(scope),
        "reviewed_by": authorization["reviewed_by"],
        "reviewed_at_utc": reviewed_at.isoformat(),
        "commercial_use_permitted": manifest.get("commercial_use_permitted") is True,
    }




def require_personal_research_inference_scope(
    manifest_path: Path = DEFAULT_RIGHTS_MANIFEST_PATH,
    *,
    now: datetime | None = None,
    repo_root: Path | None = None,
) -> dict:
    """Require the project's conservative clearance for frozen V2 inference.

    The latest public fair-use page (updated 2026-11-06) describes private
    personal/academic research as an intended use and excludes commercial or
    AI data-training projects. It does not separately define frozen-model
    inference. The project therefore keeps this path fail-closed until that
    narrow inference scope is clarified or an applicable licence is recorded.
    This is an internal risk-control decision, not a claim that the provider
    expressly prohibits every form of research inference. Missing clearance
    blocks before network, Supabase, archive, quote, feature, or model access.
    """
    path = Path(manifest_path)
    root = Path(repo_root) if repo_root is not None else REPOSITORY_ROOT
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError(
            "source-rights manifest is missing or invalid; V2 AI inference is blocked"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise PermissionError("source-rights manifest schema is not approved")
    if manifest.get("provider") != EXPECTED_PROVIDER:
        raise PermissionError("source-rights manifest provider does not match the inference source")
    if manifest.get("provider_issued_ai_inference_license") is not True:
        raise PermissionError(
            "the frozen-inference scope remains unresolved under the current public policy; no V2 inference or source use is allowed"
        )
    if manifest.get("rights_status") != "GRANTED":
        raise PermissionError("provider-issued AI-inference permission is not recorded as GRANTED")
    if manifest.get("research_use_permitted") is not True or manifest.get("research_inference_permitted") is not True:
        raise PermissionError("frozen AI inference is outside the provider-authorized research scope")
    if manifest.get("research_inference_scope") != "FROZEN_AI_INFERENCE_AND_NONCOMMERCIAL_RESEARCH":
        raise PermissionError("research inference scope is not the explicitly authorized frozen-AI scope")
    if manifest.get("ai_model_training_permitted") is not False:
        raise PermissionError("AI model training remains forbidden by this inference-only permission")
    if manifest.get("commercial_use_permitted") is not False:
        raise PermissionError("commercial use is outside the permitted research scope")
    if manifest.get("public_product_use_permitted") is not False:
        raise PermissionError("public product publication is outside the permitted research scope")
    if type(manifest.get("max_automated_download_sessions_per_week")) is not int or manifest["max_automated_download_sessions_per_week"] != 2:
        raise PermissionError("automated source access must remain limited to at most two sessions per rolling week")
    if manifest.get("download_budget_policy") != "TWO_AUTOMATED_SESSIONS_PER_ROLLING_7_DAYS":
        raise PermissionError("the required shared automated-download budget policy is not recorded")

    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict) or authorization.get("provider_issued") is not True:
        raise PermissionError("provider-issued AI-inference authorization evidence is missing")
    if authorization.get("kind") not in {"written_permission", "open_license"}:
        raise PermissionError("AI-inference authorization kind is not approved")
    scope = authorization.get("scope")
    if not isinstance(scope, list) or not {"FROZEN_AI_INFERENCE", "NONCOMMERCIAL_RESEARCH"}.issubset(set(scope)):
        raise PermissionError("authorization does not cover frozen AI inference and noncommercial research")
    for field in ("license_name", "rights_holder", "reviewed_by"):
        value = authorization.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PermissionError(f"AI-inference authorization is missing {field}")

    evidence_url = authorization.get("evidence_url")
    parts = urlsplit(evidence_url if isinstance(evidence_url, str) else "")
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
    ):
        raise PermissionError("AI-inference evidence URL must be a direct HTTPS reference")
    evidence_file = authorization.get("evidence_file")
    if not isinstance(evidence_file, str) or not evidence_file.strip():
        raise PermissionError("AI-inference authorization is missing its local evidence file")
    relative = Path(evidence_file)
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError("AI-inference evidence file must stay inside the repository")
    root_resolved = root.resolve()
    candidate = root_resolved / relative
    if candidate.is_symlink():
        raise PermissionError("AI-inference evidence file cannot be a symbolic link")
    try:
        evidence_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise PermissionError("AI-inference authorization evidence file is missing") from exc
    if root_resolved not in evidence_path.parents or not evidence_path.is_file():
        raise PermissionError("AI-inference evidence file is outside the repository or is not a file")
    expected_sha = authorization.get("evidence_sha256")
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise PermissionError("AI-inference authorization evidence SHA-256 is invalid")
    actual_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise PermissionError("AI-inference authorization evidence SHA-256 mismatch")

    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise PermissionError("source-rights verification clock must have a real UTC offset")
    now_utc = now.astimezone(timezone.utc)
    reviewed_at = _parse_utc(authorization.get("reviewed_at_utc"), "reviewed_at_utc")
    if reviewed_at > now_utc:
        raise PermissionError("AI-inference authorization review time is in the future")
    valid_from = authorization.get("valid_from_utc")
    if valid_from is not None and _parse_utc(valid_from, "valid_from_utc") > now_utc:
        raise PermissionError("AI-inference authorization is not yet valid")
    valid_until = authorization.get("valid_until_utc")
    if valid_until is not None and _parse_utc(valid_until, "valid_until_utc") <= now_utc:
        raise PermissionError("AI-inference authorization has expired")

    policy_url = manifest.get("policy_url")
    policy_parts = urlsplit(policy_url if isinstance(policy_url, str) else "")
    if policy_parts.scheme != "https" or policy_parts.hostname != "football-data.co.uk" or policy_parts.path != "/contact.php":
        raise PermissionError("source policy reference is not the official Football-Data fair-use page")
    checked = _parse_utc(manifest.get("policy_checked_at_utc"), "policy_checked_at_utc")
    page_updated_raw = manifest.get("policy_page_updated_date")
    if not isinstance(page_updated_raw, str) or not page_updated_raw.strip():
        raise PermissionError("source policy page update date is missing")
    try:
        page_updated = date.fromisoformat(page_updated_raw)
    except ValueError as exc:
        raise PermissionError("source policy page update date is invalid") from exc
    if page_updated.isoformat() != page_updated_raw:
        raise PermissionError("source policy page update date must use canonical YYYY-MM-DD")
    if checked > now_utc:
        raise PermissionError("source policy check time is in the future")
    if page_updated > checked.date():
        raise PermissionError("source policy page update date is later than policy review")
    if (now_utc - checked).total_seconds() > 90 * 86400:
        raise PermissionError("source policy review is stale; refresh the policy review before inference")

    return {
        "provider": EXPECTED_PROVIDER,
        "rights_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "scope_status": manifest["rights_status"],
        "research_inference_scope": manifest["research_inference_scope"],
        "policy_url": policy_url,
        "policy_checked_at_utc": checked.isoformat(),
        "policy_page_updated_date": page_updated.isoformat(),
        "authorization_kind": authorization["kind"],
        "authorization_evidence_sha256": actual_sha,
        "authorization_reviewed_at_utc": reviewed_at.isoformat(),
        "max_automated_download_sessions_per_week": 2,
        "ai_model_training_permitted": False,
        "commercial_use_permitted": False,
        "public_product_use_permitted": False,
        "provider_issued_ai_inference_license": True,
    }


def write_research_scope_blocked_report(path: Path, operation: str, reason: str) -> dict:
    """Write a no-I/O/no-inference report if the requested use exceeds research scope."""
    report = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_BLOCK_V1",
        "mode": "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE",
        "operation": operation,
        "provider": EXPECTED_PROVIDER,
        "permitted_scope": "NONE_PENDING_FROZEN_INFERENCE_SCOPE_CLARIFICATION",
        "rights_status": "V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED",
        "block_reason": str(reason),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "public_http_requests": 0,
        "paid_provider_requests": 0,
        "paid_provider_calls": 0,
        "supabase_reads": 0,
        "supabase_writes": 0,
        "quotes_read": 0,
        "quotes_seen": 0,
        "forecasts_created": 0,
        "v2_current_form_shadow_captured": 0,
        "diagnostic_scored": 0,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "model_training": False,
        "model_refit_or_selection": False,
        "model_promotion": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return report
