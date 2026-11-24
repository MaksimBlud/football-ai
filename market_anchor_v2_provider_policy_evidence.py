"""Verify the current official Football-Data fair-use policy evidence offline."""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit

EXPECTED_FAIR_USE_POLICY_URL = "https://football-data.co.uk/contact.php"
MAX_POLICY_REVIEW_AGE_SECONDS = 90 * 86400


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"fair-use policy {field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PermissionError(f"fair-use policy {field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermissionError(f"fair-use policy {field} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def verify_fair_use_policy_evidence(
    manifest: object,
    *,
    now_utc: datetime,
    repo_root: Path,
) -> dict:
    """Require a fresh, locally SHA-pinned copy of the official fair-use review.

    This function verifies project-held evidence only. It makes no network
    request and does not grant provider rights.
    """
    if not isinstance(manifest, dict):
        raise PermissionError("fair-use policy manifest is malformed")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        raise PermissionError("fair-use policy verification clock must be timezone-aware")
    now = now_utc.astimezone(timezone.utc)

    url = manifest.get("fair_use_policy_url")
    parts = urlsplit(url if isinstance(url, str) else "")
    if (
        url != EXPECTED_FAIR_USE_POLICY_URL
        or parts.scheme != "https"
        or parts.hostname != "football-data.co.uk"
        or parts.path != "/contact.php"
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
    ):
        raise PermissionError("fair-use policy URL must be the official Football-Data contact page")

    checked = _parse_utc(manifest.get("fair_use_policy_checked_at_utc"), "checked_at_utc")
    updated_raw = manifest.get("fair_use_policy_page_updated_date")
    if not isinstance(updated_raw, str) or not updated_raw.strip():
        raise PermissionError("fair-use policy page update date is missing")
    try:
        updated = date.fromisoformat(updated_raw)
    except ValueError as exc:
        raise PermissionError("fair-use policy page update date is invalid") from exc
    if updated.isoformat() != updated_raw:
        raise PermissionError("fair-use policy page update date must use canonical YYYY-MM-DD")
    if checked > now:
        raise PermissionError("fair-use policy review time is in the future")
    if updated > checked.date():
        raise PermissionError("fair-use policy page update date is later than its review")
    if (now - checked).total_seconds() > MAX_POLICY_REVIEW_AGE_SECONDS:
        raise PermissionError("fair-use policy review is stale")

    relative = manifest.get("fair_use_policy_evidence_file")
    if not isinstance(relative, str) or not relative.strip():
        raise PermissionError("fair-use policy evidence file is missing")
    rel_path = Path(relative)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise PermissionError("fair-use policy evidence file must stay inside the repository")
    root = Path(repo_root).resolve()
    candidate = root / rel_path
    if candidate.is_symlink():
        raise PermissionError("fair-use policy evidence file cannot be a symbolic link")
    try:
        evidence_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise PermissionError("fair-use policy evidence file is missing") from exc
    if root not in evidence_path.parents or not evidence_path.is_file():
        raise PermissionError("fair-use policy evidence file is outside the repository or is not a file")

    expected_sha = manifest.get("fair_use_policy_evidence_sha256")
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise PermissionError("fair-use policy evidence SHA-256 is invalid")
    actual_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise PermissionError("fair-use policy evidence SHA-256 mismatch")

    return {
        "fair_use_policy_url": url,
        "fair_use_policy_checked_at_utc": checked.isoformat(),
        "fair_use_policy_page_updated_date": updated.isoformat(),
        "fair_use_policy_evidence_file": relative,
        "fair_use_policy_evidence_sha256": actual_sha,
    }
