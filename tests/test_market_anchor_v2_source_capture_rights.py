from datetime import datetime, timezone
import json

import pytest

from market_anchor_v2_source_capture_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    SOURCE_CAPTURE_SCOPE,
    require_personal_research_source_capture_scope,
    write_source_capture_scope_blocked_report,
)


NOW = datetime(2026, 11, 10, 11, 57, 30, tzinfo=timezone.utc)


def _manifest(**overrides):
    value = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_V1",
        "provider": "Football-Data.co.uk",
        "rights_status": "V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED",
        "research_use_permitted": True,
        "research_source_capture_permitted": True,
        "research_source_capture_scope": SOURCE_CAPTURE_SCOPE,
        "research_inference_permitted": False,
        "provider_issued_ai_inference_license": False,
        "ai_model_training_permitted": False,
        "commercial_use_permitted": False,
        "public_product_use_permitted": False,
        "max_automated_download_sessions_per_week": 2,
        "download_budget_policy": "TWO_AUTOMATED_SESSIONS_PER_ROLLING_7_DAYS",
        "policy_url": "https://football-data.co.uk/data",
        "policy_checked_at_utc": "2026-11-07T01:56:17Z",
        "policy_page_updated_date": "2026-11-06",
        "policy_summary": (
            "The free CSV/Excel data are intended for private individuals' personal betting "
            "and/or academic interest and research only, via manual download or at most two "
            "light automated download sessions per week. They are not intended for commercial "
            "or AI data-training projects."
        ),
        "policy_interpretation": (
            "The project permits only private source-only archival/validation for noncommercial "
            "research. This scope does not authorize frozen-model inference. Frozen-model "
            "inference remains blocked pending separate scope clarification."
        ),
        "authorization": None,
    }
    value.update(overrides)
    return value


def _write_manifest(tmp_path, **overrides):
    path = tmp_path / "rights.json"
    path.write_text(json.dumps(_manifest(**overrides)), encoding="utf-8")
    return path


def test_current_official_manifest_blocks_automated_source_capture_after_policy_update():
    with pytest.raises(PermissionError, match="not explicitly enabled"):
        require_personal_research_source_capture_scope(
            DEFAULT_RIGHTS_MANIFEST_PATH, now=NOW
        )


def test_source_capture_scope_accepts_synthetic_research_only_manifest(tmp_path):
    path = _write_manifest(tmp_path)
    result = require_personal_research_source_capture_scope(path, now=NOW)
    assert result["source_capture_only"] is True
    assert result["research_inference_permitted"] is False


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"research_use_permitted": False}, "does not permit noncommercial research"),
        ({"research_source_capture_permitted": False}, "not explicitly enabled"),
        ({"research_source_capture_scope": "GENERAL_RESEARCH"}, "not the approved"),
        ({"research_inference_permitted": True}, "inference to remain blocked"),
        ({"provider_issued_ai_inference_license": True}, "cannot be used as an inference licence"),
        ({"ai_model_training_permitted": True}, "AI model training"),
        ({"commercial_use_permitted": True}, "commercial use"),
        ({"public_product_use_permitted": True}, "public product use"),
        ({"authorization": {"kind": "written_permission"}}, "cannot substitute"),
        ({"max_automated_download_sessions_per_week": 3}, "at most two"),
        ({"download_budget_policy": "UNBOUNDED"}, "two-session"),
        ({"policy_url": "https://example.org/contact"}, "official Football-Data"),
    ],
)
def test_source_capture_scope_rejects_broader_or_unverified_permissions(
    tmp_path, overrides, message
):
    path = _write_manifest(tmp_path, **overrides)
    with pytest.raises(PermissionError, match=message):
        require_personal_research_source_capture_scope(path, now=NOW)


def test_source_capture_scope_rejects_stale_policy_review(tmp_path):
    path = _write_manifest(tmp_path, policy_checked_at_utc="2026-01-01T00:00:00Z", policy_page_updated_date="2025-12-31")
    with pytest.raises(PermissionError, match="stale"):
        require_personal_research_source_capture_scope(path, now=NOW)


def test_source_capture_scope_rejects_future_policy_review(tmp_path):
    path = _write_manifest(tmp_path, policy_checked_at_utc="2026-11-08T00:00:00Z")
    with pytest.raises(PermissionError, match="future"):
        require_personal_research_source_capture_scope(path, now=NOW)


def test_source_capture_scope_rejects_page_update_after_review(tmp_path):
    path = _write_manifest(tmp_path, policy_page_updated_date="2026-11-08")
    with pytest.raises(PermissionError, match="later than policy review"):
        require_personal_research_source_capture_scope(path, now=NOW)


def test_source_capture_scope_rejects_offsetless_verification_clock(tmp_path):
    path = _write_manifest(tmp_path)
    with pytest.raises(PermissionError, match="real UTC offset"):
        require_personal_research_source_capture_scope(
            path, now=datetime(2026, 11, 7, 2, 0)
        )


def test_source_capture_block_report_records_no_external_io_or_inference(tmp_path):
    output = tmp_path / "reports" / "blocked.json"
    report = write_source_capture_scope_blocked_report(
        output, "SYNTHETIC_TEST", "private storage is unavailable"
    )
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert report["mode"] == "SOURCE_CAPTURE_SCOPE_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["public_http_requests"] == 0
    assert report["paid_provider_calls"] == 0
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["forecasts_created"] == 0
    assert report["source_capture_only"] is False
    assert report["model_inference_executed"] is False
    assert report["target_outcomes_read"] is False
    assert report["no_bet"] is True
