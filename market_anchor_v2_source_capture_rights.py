"""Narrow gate for private source-only Football-Data research archives.

This scope is deliberately separate from frozen-model inference. It permits
only private, noncommercial source archival/validation under the provider page's
stated personal/academic research allowance. It never authorizes feature
construction, model inference, AI training, commercial use, or publication.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from market_anchor_v2_source_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    EXPECTED_PROVIDER,
    SCHEMA_VERSION,
)

SOURCE_CAPTURE_SCOPE = "PRIVATE_NONCOMMERCIAL_RESEARCH_ARCHIVE_ONLY"
EXPECTED_POLICY_URL = "https://football-data.co.uk/data"
DOWNLOAD_BUDGET_POLICY = "TWO_AUTOMATED_SESSIONS_PER_ROLLING_7_DAYS"
MAX_POLICY_AGE_SECONDS = 90 * 24 * 60 * 60


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"source-capture {field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PermissionError(f"source-capture {field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermissionError(f"source-capture {field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def require_personal_research_source_capture_scope(
    manifest_path: Path = DEFAULT_RIGHTS_MANIFEST_PATH,
    *,
    now: datetime | None = None,
) -> dict:
    """Allow only private source archival/validation; never authorize inference."""
    path = Path(manifest_path)
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError(
            "source-capture rights manifest is missing or invalid; source access is blocked"
        ) from exc

    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise PermissionError("source-capture rights manifest schema is not approved")
    if manifest.get("provider") != EXPECTED_PROVIDER:
        raise PermissionError("source-capture provider does not match Football-Data")
    if manifest.get("rights_status") != "V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED":
        raise PermissionError("source-only capture requires the frozen-inference scope to remain unresolved")
    if manifest.get("research_use_permitted") is not True:
        raise PermissionError("provider policy does not permit noncommercial research use")
    if manifest.get("research_source_capture_permitted") is not True:
        raise PermissionError("private research source capture is not explicitly enabled in the rights manifest")
    if manifest.get("research_source_capture_scope") != SOURCE_CAPTURE_SCOPE:
        raise PermissionError("source-capture scope is not the approved private archive-only scope")
    if manifest.get("research_inference_permitted") is not False:
        raise PermissionError("source-only capture requires frozen-model inference to remain blocked")
    if manifest.get("provider_issued_ai_inference_license") is not False:
        raise PermissionError("source-only capture cannot be used as an inference licence")
    if manifest.get("ai_model_training_permitted") is not False:
        raise PermissionError("AI model training is outside the source-only research scope")
    if manifest.get("commercial_use_permitted") is not False:
        raise PermissionError("commercial use is outside the source-only research scope")
    if manifest.get("public_product_use_permitted") is not False:
        raise PermissionError("public product use is outside the source-only research scope")
    if manifest.get("authorization") is not None:
        raise PermissionError("source-only public-policy scope cannot substitute for provider-issued authorization")

    if (
        type(manifest.get("max_automated_download_sessions_per_week")) is not int
        or manifest["max_automated_download_sessions_per_week"] != 2
    ):
        raise PermissionError("source access must remain limited to at most two automated sessions per rolling week")
    if manifest.get("download_budget_policy") != DOWNLOAD_BUDGET_POLICY:
        raise PermissionError("the shared two-session source-download budget is not recorded")

    policy_url = manifest.get("policy_url")
    parts = urlsplit(policy_url if isinstance(policy_url, str) else "")
    if (
        parts.scheme != "https"
        or parts.hostname != "football-data.co.uk"
        or parts.path != "/data"
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
    ):
        raise PermissionError("source-capture policy reference is not the official Football-Data data/fair-use page")

    summary = manifest.get("policy_summary")
    if (
        not isinstance(summary, str)
        or "private individuals" not in summary
        or "academic interest and research" not in summary
        or "two light automated download sessions per week" not in summary
    ):
        raise PermissionError("source-capture policy summary does not preserve the official research/download limits")
    interpretation = manifest.get("policy_interpretation")
    if (
        not isinstance(interpretation, str)
        or "source-only archival/validation" not in interpretation
        or "frozen-model inference remains blocked" not in interpretation.lower()
    ):
        raise PermissionError("source-capture policy interpretation is missing the separate inference prohibition")

    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise PermissionError("source-capture verification clock must have a real UTC offset")
    now_utc = now.astimezone(timezone.utc)
    checked = _parse_utc(manifest.get("policy_checked_at_utc"), "policy_checked_at_utc")
    if checked > now_utc:
        raise PermissionError("source-capture policy check time is in the future")

    page_updated_raw = manifest.get("policy_page_updated_date")
    if not isinstance(page_updated_raw, str) or not page_updated_raw.strip():
        raise PermissionError("source-capture policy page update date is missing")
    try:
        page_updated = date.fromisoformat(page_updated_raw)
    except ValueError as exc:
        raise PermissionError("source-capture policy page update date is invalid") from exc
    if page_updated.isoformat() != page_updated_raw:
        raise PermissionError("source-capture policy page update date must use canonical YYYY-MM-DD")
    if page_updated > checked.date():
        raise PermissionError("source-capture policy page update date is later than policy review")
    if (now_utc - checked).total_seconds() > MAX_POLICY_AGE_SECONDS:
        raise PermissionError("source-capture policy review is stale; refresh it before source access")

    return {
        "provider": EXPECTED_PROVIDER,
        "source_capture_scope": SOURCE_CAPTURE_SCOPE,
        "rights_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "policy_url": policy_url,
        "policy_checked_at_utc": checked.isoformat(),
        "policy_page_updated_date": page_updated.isoformat(),
        "research_use_permitted": True,
        "research_inference_permitted": False,
        "provider_issued_ai_inference_license": False,
        "ai_model_training_permitted": False,
        "commercial_use_permitted": False,
        "public_product_use_permitted": False,
        "max_automated_download_sessions_per_week": 2,
        "source_capture_only": True,
    }


def write_source_capture_scope_blocked_report(
    path: Path, operation: str, reason: str
) -> dict:
    """Write an explicit no-I/O block report when source-only scope is unavailable."""
    report = {
        "schema_version": "FOOTBALL_AI_SOURCE_CAPTURE_SCOPE_BLOCK_V1",
        "mode": "SOURCE_CAPTURE_SCOPE_BLOCKED_NO_NETWORK_NO_INFERENCE",
        "operation": operation,
        "provider": EXPECTED_PROVIDER,
        "permitted_scope": "NONE",
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
        "source_capture_only": False,
        "model_inference_executed": False,
        "model_training_executed": False,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "model_refit_or_selection": False,
        "model_promotion": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
