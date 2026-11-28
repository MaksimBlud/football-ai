"""Offline regressions for explicit provider-issued AI-training permission."""
from datetime import datetime, timezone
import hashlib
import json

import pytest

from market_anchor_v2_source_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    require_ai_model_training_permission,
)

NOW = datetime(2026, 11, 25, 0, 10, tzinfo=timezone.utc)


def _write_grant(
    tmp_path,
    *,
    evidence_url="https://football-data.co.uk/permission.pdf",
    valid_from="2026-11-10T00:00:00Z",
    valid_until="2026-12-01T00:00:00Z",
    scope=None,
    policy_page_updated_date="2026-11-10",
    provider_issued=True,
):
    evidence = tmp_path / "provider-permission.txt"
    body = b"synthetic provider-issued AI training permission; tests only"
    evidence.write_bytes(body)
    policy_evidence = tmp_path / "football_data_contact_fair_use_20261124.md"
    policy_evidence_bytes = b"synthetic fair-use policy evidence for tests only"
    policy_evidence.write_bytes(policy_evidence_bytes)
    manifest = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_V1",
        "provider": "Football-Data.co.uk",
        "policy_url": "https://football-data.co.uk/data",
        "policy_checked_at_utc": "2026-11-10T11:57:30Z",
        "policy_page_updated_date": policy_page_updated_date,
        "fair_use_policy_url": "https://football-data.co.uk/contact.php",
        "fair_use_policy_checked_at_utc": "2026-11-24T23:52:28Z",
        "fair_use_policy_page_updated_date": "2026-11-24",
        "fair_use_policy_evidence_file": policy_evidence.name,
        "fair_use_policy_evidence_kind": "LOCAL_PARAPHRASE_NOTE_NOT_PROVIDER_PAGE_BYTES",
        "fair_use_policy_evidence_sha256": hashlib.sha256(policy_evidence_bytes).hexdigest(),
        "rights_status": "GRANTED",
        "ai_model_training_permitted": True,
        "research_use_permitted": True,
        "research_source_capture_permitted": False,
        "research_source_capture_scope": "NONE_PENDING_PROVIDER_CLARIFICATION",
        "research_inference_permitted": False,
        "research_inference_scope": "NONE_PENDING_SCOPE_CLARIFICATION",
        "provider_issued_source_capture_license": False,
        "provider_issued_ai_inference_license": False,
        "commercial_use_permitted": False,
        "public_product_use_permitted": False,
        "authorization": {
            "provider_issued": provider_issued,
            "kind": "written_permission",
            "scope": scope if scope is not None else ["AI_MODEL_TRAINING", "NONCOMMERCIAL_RESEARCH"],
            "license_name": "Synthetic training permission",
            "rights_holder": "Football-Data.co.uk",
            "reviewed_by": "synthetic-test-reviewer",
            "reviewed_at_utc": "2026-11-11T12:00:00Z",
            "valid_from_utc": valid_from,
            "valid_until_utc": valid_until,
            "evidence_url": evidence_url,
            "evidence_file": evidence.name,
            "evidence_sha256": hashlib.sha256(body).hexdigest(),
        },
    }
    path = tmp_path / "rights.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, evidence


def test_real_provider_manifest_keeps_ai_training_closed():
    with pytest.raises(PermissionError, match="AI model-training permission is not granted"):
        require_ai_model_training_permission(DEFAULT_RIGHTS_MANIFEST_PATH, now=NOW)


def test_synthetic_bounded_provider_training_grant_is_sha_verified(tmp_path):
    path, evidence = _write_grant(tmp_path)
    result = require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)
    assert result["scope_status"] == "GRANTED"
    assert result["scope"] == ["AI_MODEL_TRAINING", "NONCOMMERCIAL_RESEARCH"]
    assert result["evidence_sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
    assert result["authorization_valid_from_utc"] == "2026-11-10T00:00:00+00:00"
    assert result["authorization_valid_until_utc"] == "2026-12-01T00:00:00+00:00"


def test_tampered_training_permission_evidence_fails_sha_check(tmp_path):
    path, evidence = _write_grant(tmp_path)
    evidence.write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="evidence SHA-256 mismatch"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_training_evidence_must_be_on_provider_domain(tmp_path):
    path, _ = _write_grant(tmp_path, evidence_url="https://example.com/permission.pdf")
    with pytest.raises(PermissionError, match="on the provider domain"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


@pytest.mark.parametrize("field", ["valid_from_utc", "valid_until_utc"])
def test_training_grant_requires_both_validity_bounds(tmp_path, field):
    path, _ = _write_grant(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["authorization"][field]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(PermissionError, match="requires both valid_from_utc and valid_until_utc"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_expired_training_permission_fails_closed(tmp_path):
    path, _ = _write_grant(tmp_path, valid_until="2026-11-18T00:00:00Z")
    with pytest.raises(PermissionError, match="authorization has expired"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_reversed_training_permission_window_fails_closed(tmp_path):
    path, _ = _write_grant(
        tmp_path,
        valid_from="2026-12-02T00:00:00Z",
        valid_until="2026-12-01T00:00:00Z",
    )
    with pytest.raises(PermissionError, match="validity window is empty or reversed"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_malformed_training_scope_fails_closed_without_type_error(tmp_path):
    path, _ = _write_grant(tmp_path, scope=[["AI_MODEL_TRAINING"], "NONCOMMERCIAL_RESEARCH"])
    with pytest.raises(PermissionError, match="does not cover AI model training"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_training_grant_requires_provider_issued_evidence(tmp_path):
    path, _ = _write_grant(tmp_path, provider_issued=False)
    with pytest.raises(PermissionError, match="explicitly provider-issued"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_policy_update_cannot_postdate_training_permission_review(tmp_path):
    path, _ = _write_grant(tmp_path, policy_page_updated_date="2026-11-20")
    with pytest.raises(PermissionError, match="updated later than policy review"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)


def test_training_fair_use_policy_evidence_sha_mismatch_fails_closed(tmp_path):
    path, _ = _write_grant(tmp_path)
    (tmp_path / "football_data_contact_fair_use_20261124.md").write_text(
        "tampered", encoding="utf-8"
    )
    with pytest.raises(PermissionError, match="fair-use policy evidence SHA-256 mismatch"):
        require_ai_model_training_permission(path, repo_root=tmp_path, now=NOW)
