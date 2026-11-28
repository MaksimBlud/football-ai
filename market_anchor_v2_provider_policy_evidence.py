"""Verify SHA-pinned evidence for both official Football-Data policy pages offline."""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit

EXPECTED_POLICY_URL = "https://football-data.co.uk/data"
EXPECTED_FAIR_USE_POLICY_URL = "https://football-data.co.uk/contact.php"
EXPECTED_EVIDENCE_KIND = "LOCAL_PARAPHRASE_NOTE_NOT_PROVIDER_PAGE_BYTES"
MAX_POLICY_REVIEW_AGE_SECONDS = 90 * 86400


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"{field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PermissionError(f"{field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermissionError(f"{field} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _verify_page_evidence(
    manifest: dict,
    *,
    prefix: str,
    expected_url: str,
    label: str,
    now: datetime,
    repo_root: Path,
) -> dict:
    """Verify one official page's URL, review clock, update date, local note, and SHA."""
    url_field = f"{prefix}_url"
    checked_field = f"{prefix}_checked_at_utc"
    updated_field = f"{prefix}_page_updated_date"
    evidence_file_field = f"{prefix}_evidence_file"
    evidence_kind_field = f"{prefix}_evidence_kind"
    evidence_sha_field = f"{prefix}_evidence_sha256"

    url = manifest.get(url_field)
    parts = urlsplit(url if isinstance(url, str) else "")
    if (
        url != expected_url
        or parts.scheme != "https"
        or parts.hostname != "football-data.co.uk"
        or parts.path != ("/data" if prefix == "policy" else "/contact.php")
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
    ):
        raise PermissionError(f"{label} URL must be the exact official Football-Data page")

    checked = _parse_utc(manifest.get(checked_field), f"{label} checked_at_utc")
    updated_raw = manifest.get(updated_field)
    if not isinstance(updated_raw, str) or not updated_raw.strip():
        raise PermissionError(f"{label} page update date is missing")
    try:
        updated = date.fromisoformat(updated_raw)
    except ValueError as exc:
        raise PermissionError(f"{label} page update date is invalid") from exc
    if updated.isoformat() != updated_raw:
        raise PermissionError(f"{label} page update date must use canonical YYYY-MM-DD")
    if checked > now:
        raise PermissionError(f"{label} review time is in the future")
    if updated > checked.date():
        raise PermissionError(f"{label} page was updated later than policy review")
    if (now - checked).total_seconds() > MAX_POLICY_REVIEW_AGE_SECONDS:
        raise PermissionError(f"{label} review is stale")

    if manifest.get(evidence_kind_field) != EXPECTED_EVIDENCE_KIND:
        raise PermissionError(
            f"{label} evidence kind must identify a local paraphrase note, not provider page bytes"
        )

    relative = manifest.get(evidence_file_field)
    if not isinstance(relative, str) or not relative.strip():
        raise PermissionError(f"{label} evidence file is missing")
    rel_path = Path(relative)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise PermissionError(f"{label} evidence file must stay inside the repository")
    root = Path(repo_root).resolve()
    candidate = root / rel_path
    if candidate.is_symlink():
        raise PermissionError(f"{label} evidence file cannot be a symbolic link")
    try:
        evidence_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise PermissionError(f"{label} evidence file is missing") from exc
    if root not in evidence_path.parents or not evidence_path.is_file():
        raise PermissionError(f"{label} evidence file is outside the repository or is not a file")

    expected_sha = manifest.get(evidence_sha_field)
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise PermissionError(f"{label} evidence SHA-256 is invalid")
    actual_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise PermissionError(f"{label} evidence SHA-256 mismatch")

    return {
        url_field: url,
        checked_field: checked.isoformat(),
        updated_field: updated.isoformat(),
        evidence_file_field: relative,
        evidence_sha_field: actual_sha,
    }


def verify_fair_use_policy_evidence(
    manifest: object,
    *,
    now_utc: datetime,
    repo_root: Path,
) -> dict:
    """Require fresh, SHA-pinned local reviews of both official policy pages.

    This verifies project-held evidence only. It makes no network request and
    grants no provider rights. The data page and fair-use/contact page are
    independently dated and hashed so a changed page cannot be represented by
    a stale note for the other page.
    """
    if not isinstance(manifest, dict):
        raise PermissionError("fair-use policy manifest is malformed")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        raise PermissionError("fair-use policy verification clock must be timezone-aware")
    now = now_utc.astimezone(timezone.utc)
    root = Path(repo_root)

    data_page = _verify_page_evidence(
        manifest,
        prefix="policy",
        expected_url=EXPECTED_POLICY_URL,
        label="data-page policy",
        now=now,
        repo_root=root,
    )
    fair_use_page = _verify_page_evidence(
        manifest,
        prefix="fair_use_policy",
        expected_url=EXPECTED_FAIR_USE_POLICY_URL,
        label="fair-use policy",
        now=now,
        repo_root=root,
    )
    return {**data_page, **fair_use_page}
