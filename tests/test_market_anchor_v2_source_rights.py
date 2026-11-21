"""Offline tests for the original V2 provider inference-rights manifest."""
from datetime import datetime, timezone
import hashlib
import json

import pytest

from market_anchor_v2_source_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    require_personal_research_inference_scope,
)

NOW = datetime(2026, 11, 19, 21, 0, tzinfo=timezone.utc)


def _write_synthetic_grant(tmp_path, *, policy_page_updated_date="2026-11-10"):
    evidence = tmp_path / "provider-permission.txt"
    evidence_bytes = b"synthetic provider-issued frozen inference permission for tests only"
    evidence.write_bytes(evidence_bytes)
    manifest = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_V1",
        "provider": "Football-Data.co.uk",
        "policy_url": "https://football-data.co.uk/data",
        "policy_checked_at_utc": "2026-11-10T11:57:30Z",
        "policy_page_updated_date": policy_page_updated_date,
        "rights_status": "GRANTED",
        "research_use_permitted": True,
        "research_source_capture_permitted": False,
        "research_source_capture_scope": "NONE_PENDING_PROVIDER_CLARIFICATION",
        "research_inference_permitted": True,
        "research_inference_scope": "FROZEN_AI_INFERENCE_AND_NONCOMMERCIAL_RESEARCH",
        "ai_model_training_permitted": False,
        "provider_issued_ai_inference_license": True,
        "commercial_use_permitted": False,
        "public_product_use_permitted": False,
        "max_automated_download_sessions_per_week": 2,
        "download_budget_policy": "TWO_AUTOMATED_SESSIONS_PER_ROLLING_7_DAYS",
        "authorization": {
            "provider_issued": True,
            "kind": "written_permission",
            "license_name": "Synthetic test permission",
            "rights_holder": "Football-Data.co.uk",
            "scope": ["FROZEN_AI_INFERENCE", "NONCOMMERCIAL_RESEARCH"],
            "evidence_url": "https://football-data.co.uk/data",
            "evidence_file": evidence.name,
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "reviewed_by": "synthetic-test-reviewer",
            "reviewed_at_utc": "2026-11-11T12:00:00Z",
            "valid_from_utc": "2026-11-10T00:00:00Z",
            "valid_until_utc": "2026-12-01T00:00:00Z",
        },
    }
    path = tmp_path / "rights.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, evidence


def test_current_repository_manifest_keeps_frozen_inference_closed():
    with pytest.raises(PermissionError, match="scope remains unresolved"):
        require_personal_research_inference_scope(
            DEFAULT_RIGHTS_MANIFEST_PATH,
            now=NOW,
        )


def test_missing_manifest_fails_closed(tmp_path):
    with pytest.raises(PermissionError, match="missing or invalid"):
        require_personal_research_inference_scope(
            tmp_path / "missing.json",
            repo_root=tmp_path,
            now=NOW,
        )


def test_synthetic_provider_issued_frozen_inference_permission_is_sha_verified(tmp_path):
    path, evidence = _write_synthetic_grant(tmp_path)
    result = require_personal_research_inference_scope(
        path,
        repo_root=tmp_path,
        now=NOW,
    )
    assert result["scope_status"] == "GRANTED"
    assert result["research_inference_scope"] == "FROZEN_AI_INFERENCE_AND_NONCOMMERCIAL_RESEARCH"
    assert result["authorization_evidence_sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
    assert result["ai_model_training_permitted"] is False
    assert result["commercial_use_permitted"] is False
    assert result["public_product_use_permitted"] is False


def test_tampered_provider_permission_evidence_fails_sha_check(tmp_path):
    path, evidence = _write_synthetic_grant(tmp_path)
    evidence.write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="evidence SHA-256 mismatch"):
        require_personal_research_inference_scope(
            path,
            repo_root=tmp_path,
            now=NOW,
        )


def test_policy_page_update_cannot_postdate_its_review(tmp_path):
    path, _ = _write_synthetic_grant(tmp_path, policy_page_updated_date="2026-11-20")
    with pytest.raises(PermissionError, match="later than policy review"):
        require_personal_research_inference_scope(
            path,
            repo_root=tmp_path,
            now=NOW,
        )
