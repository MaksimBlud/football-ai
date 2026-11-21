"""Independent fail-closed rights gate for automated original-V2 source capture.

Source capture, frozen inference, and AI training are distinct permissions.
This module validates only an explicit provider-issued automated-capture grant;
it never treats inference permission or a public URL as capture authorization.
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
EXPECTED_CAPTURE_SCOPE = "AUTOMATED_SOURCE_CAPTURE_AND_NONCOMMERCIAL_RESEARCH"
REQUIRED_AUTHORIZATION_SCOPES = {"AUTOMATED_SOURCE_CAPTURE", "NONCOMMERCIAL_RESEARCH"}
DOWNLOAD_BUDGET_POLICY = "TWO_AUTOMATED_SESSIONS_PER_ROLLING_7_DAYS"


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"source-capture rights {field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PermissionError(f"source-capture rights {field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermissionError(f"source-capture rights {field} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def require_personal_research_source_capture_scope(
    manifest_path: Path = DEFAULT_RIGHTS_MANIFEST_PATH,
    *,
    now: datetime | None = None,
    repo_root: Path | None = None,
) -> dict:
    """Require a provider-issued, SHA-pinned, time-valid automated-capture grant.

    The current repository manifest deliberately denies automated capture. A
    synthetic grant can be used by offline tests only; no network access occurs
    in this function and no permission is inferred from a separate inference
    scope.
    """
    path = Path(manifest_path)
    root = Path(repo_root) if repo_root is not None else REPOSITORY_ROOT
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError(
            "source-capture rights manifest is missing or invalid; automated capture is blocked"
        ) from exc

    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise PermissionError("source-capture rights manifest schema is not approved")
    if manifest.get("provider") != EXPECTED_PROVIDER:
        raise PermissionError("source-capture rights provider does not match the configured source")
    if manifest.get("research_source_capture_permitted") is not True:
        raise PermissionError("automated source capture is not permitted by the current provider manifest")
    if manifest.get("provider_issued_source_capture_license") is not True:
        raise PermissionError("provider-issued automated source-capture permission is missing")
    if manifest.get("rights_status") != "GRANTED":
        raise PermissionError("provider-issued source-capture permission is not recorded as GRANTED")
    if manifest.get("research_use_permitted") is not True:
        raise PermissionError("noncommercial research use is outside the provider-authorized scope")
    if manifest.get("research_source_capture_scope") != EXPECTED_CAPTURE_SCOPE:
        raise PermissionError("automated source-capture scope is not explicitly authorized")
    if manifest.get("ai_model_training_permitted") is not False:
        raise PermissionError("source-capture permission must not silently grant AI model training")
    if manifest.get("commercial_use_permitted") is not False:
        raise PermissionError("commercial use is outside the permitted source-capture scope")
    if manifest.get("public_product_use_permitted") is not False:
        raise PermissionError("public product use is outside the permitted source-capture scope")
    if type(manifest.get("max_automated_download_sessions_per_week")) is not int:
        raise PermissionError("automated source-capture download ceiling is missing")
    if manifest["max_automated_download_sessions_per_week"] != 2:
        raise PermissionError("automated source capture must remain limited to at most two sessions per rolling week")
    if manifest.get("download_budget_policy") != DOWNLOAD_BUDGET_POLICY:
        raise PermissionError("shared rolling-week source-capture budget policy is not recorded")

    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict) or authorization.get("provider_issued") is not True:
        raise PermissionError("provider-issued source-capture authorization evidence is missing")
    if authorization.get("kind") not in {"written_permission", "open_license"}:
        raise PermissionError("source-capture authorization kind is not approved")
    scope = authorization.get("scope")
    if not isinstance(scope, list) or not REQUIRED_AUTHORIZATION_SCOPES.issubset(set(scope)):
        raise PermissionError("authorization does not cover automated source capture and noncommercial research")
    for field in ("license_name", "rights_holder", "reviewed_by"):
        value = authorization.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PermissionError(f"source-capture authorization is missing {field}")

    evidence_url = authorization.get("evidence_url")
    parts = urlsplit(evidence_url if isinstance(evidence_url, str) else "")
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
    ):
        raise PermissionError("source-capture evidence URL must be a direct HTTPS reference")

    evidence_file = authorization.get("evidence_file")
    if not isinstance(evidence_file, str) or not evidence_file.strip():
        raise PermissionError("source-capture authorization is missing its local evidence file")
    relative = Path(evidence_file)
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError("source-capture evidence file must stay inside the repository")
    root_resolved = root.resolve()
    candidate = root_resolved / relative
    if candidate.is_symlink():
        raise PermissionError("source-capture evidence file cannot be a symbolic link")
    try:
        evidence_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise PermissionError("source-capture authorization evidence file is missing") from exc
    if root_resolved not in evidence_path.parents or not evidence_path.is_file():
        raise PermissionError("source-capture evidence file is outside the repository or is not a file")

    expected_sha = authorization.get("evidence_sha256")
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise PermissionError("source-capture authorization evidence SHA-256 is invalid")
    actual_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise PermissionError("source-capture authorization evidence SHA-256 mismatch")

    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise PermissionError("source-capture verification clock must have a UTC offset")
    now_utc = now.astimezone(timezone.utc)
    reviewed_at = _parse_utc(authorization.get("reviewed_at_utc"), "reviewed_at_utc")
    if reviewed_at > now_utc:
        raise PermissionError("source-capture authorization review time is in the future")
    valid_from = authorization.get("valid_from_utc")
    if valid_from is not None and _parse_utc(valid_from, "valid_from_utc") > now_utc:
        raise PermissionError("source-capture authorization is not yet valid")
    valid_until = authorization.get("valid_until_utc")
    if valid_until is not None and _parse_utc(valid_until, "valid_until_utc") <= now_utc:
        raise PermissionError("source-capture authorization has expired")

    policy_url = manifest.get("policy_url")
    policy_parts = urlsplit(policy_url if isinstance(policy_url, str) else "")
    if (
        policy_parts.scheme != "https"
        or policy_parts.hostname != "football-data.co.uk"
        or policy_parts.path != "/data"
    ):
        raise PermissionError("source-capture policy reference is not the official provider data page")
    checked = _parse_utc(manifest.get("policy_checked_at_utc"), "policy_checked_at_utc")
    page_updated_raw = manifest.get("policy_page_updated_date")
    if not isinstance(page_updated_raw, str) or not page_updated_raw.strip():
        raise PermissionError("source-capture policy page update date is missing")
    try:
        page_updated = date.fromisoformat(page_updated_raw)
    except ValueError as exc:
        raise PermissionError("source-capture policy page update date is invalid") from exc
    if page_updated.isoformat() != page_updated_raw:
        raise PermissionError("source-capture policy page update date must use YYYY-MM-DD")
    if checked > now_utc:
        raise PermissionError("source-capture policy check time is in the future")
    if page_updated > checked.date():
        raise PermissionError("source-capture policy page update date is later than policy review")
    if (now_utc - checked).total_seconds() > 90 * 86400:
        raise PermissionError("source-capture policy review is stale")

    return {
        "provider": EXPECTED_PROVIDER,
        "rights_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "scope_status": manifest["rights_status"],
        "research_source_capture_scope": manifest["research_source_capture_scope"],
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
        "provider_issued_source_capture_license": True,
    }
