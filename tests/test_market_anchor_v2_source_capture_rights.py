"""Offline regressions for the separate original-V2 source-capture rights scope."""
from datetime import datetime, timezone
import hashlib
import json

import pytest

import market_anchor_v2_artifact_privacy as privacy
import market_anchor_v2_direct_access as direct_access
import market_anchor_v2_source_capture_rights as capture_rights

NOW = datetime(2026, 11, 25, 0, 0, tzinfo=timezone.utc)


def _synthetic_capture_grant(
    tmp_path,
    *,
    page_updated="2026-11-10",
    evidence_url="https://football-data.co.uk/contact.php",
    valid_from="2026-11-10T00:00:00Z",
    valid_until="2026-12-01T00:00:00Z",
    scope=None,
):
    evidence = tmp_path / "provider-capture-permission.txt"
    evidence_bytes = b"synthetic provider-issued automated source-capture permission; tests only"
    evidence.write_bytes(evidence_bytes)
    policy_evidence = tmp_path / "football_data_contact_fair_use_20261124.md"
    policy_evidence_bytes = b"synthetic fair-use policy evidence for tests only"
    policy_evidence.write_bytes(policy_evidence_bytes)
    manifest = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_V1",
        "provider": "Football-Data.co.uk",
        "rights_status": "GRANTED",
        "research_use_permitted": True,
        "research_source_capture_permitted": True,
        "research_source_capture_scope": "AUTOMATED_SOURCE_CAPTURE_AND_NONCOMMERCIAL_RESEARCH",
        "provider_issued_source_capture_license": True,
        "research_inference_permitted": False,
        "research_inference_scope": "NONE",
        "provider_issued_ai_inference_license": False,
        "ai_model_training_permitted": False,
        "commercial_use_permitted": False,
        "public_product_use_permitted": False,
        "max_automated_download_sessions_per_week": 2,
        "download_budget_policy": "TWO_AUTOMATED_SESSIONS_PER_ROLLING_7_DAYS",
        "policy_url": "https://football-data.co.uk/data",
        "policy_checked_at_utc": "2026-11-10T11:57:30Z",
        "policy_page_updated_date": page_updated,
        "fair_use_policy_url": "https://football-data.co.uk/contact.php",
        "fair_use_policy_checked_at_utc": "2026-11-24T23:52:28Z",
        "fair_use_policy_page_updated_date": "2026-11-24",
        "fair_use_policy_evidence_file": policy_evidence.name,
        "fair_use_policy_evidence_sha256": hashlib.sha256(policy_evidence_bytes).hexdigest(),
        "authorization": {
            "provider_issued": True,
            "kind": "written_permission",
            "license_name": "Synthetic capture-only permission",
            "rights_holder": "Football-Data.co.uk",
            "scope": scope if scope is not None else ["AUTOMATED_SOURCE_CAPTURE", "NONCOMMERCIAL_RESEARCH"],
            "evidence_url": evidence_url,
            "evidence_file": evidence.name,
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "reviewed_by": "synthetic-test-reviewer",
            "reviewed_at_utc": "2026-11-11T12:00:00Z",
            "valid_from_utc": valid_from,
            "valid_until_utc": valid_until,
        },
    }
    path = tmp_path / "rights.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, evidence


def test_current_provider_manifest_keeps_automated_capture_closed():
    with pytest.raises(PermissionError, match="automated source capture is not permitted"):
        capture_rights.require_personal_research_source_capture_scope(now=NOW)


def test_missing_manifest_fails_closed(tmp_path):
    with pytest.raises(PermissionError, match="missing or invalid"):
        capture_rights.require_personal_research_source_capture_scope(
            tmp_path / "missing.json", repo_root=tmp_path, now=NOW
        )


def test_synthetic_capture_only_grant_is_separately_sha_verified(tmp_path):
    path, evidence = _synthetic_capture_grant(tmp_path)
    result = capture_rights.require_personal_research_source_capture_scope(
        path, repo_root=tmp_path, now=NOW
    )
    assert result["scope_status"] == "GRANTED"
    assert result["research_source_capture_scope"] == "AUTOMATED_SOURCE_CAPTURE_AND_NONCOMMERCIAL_RESEARCH"
    assert result["authorization_evidence_sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
    assert result["ai_model_training_permitted"] is False
    assert result["commercial_use_permitted"] is False
    assert result["public_product_use_permitted"] is False


def test_tampered_capture_permission_evidence_fails_sha_check(tmp_path):
    path, evidence = _synthetic_capture_grant(tmp_path)
    evidence.write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="evidence SHA-256 mismatch"):
        capture_rights.require_personal_research_source_capture_scope(
            path, repo_root=tmp_path, now=NOW
        )


def test_policy_page_updated_after_review_fails_closed(tmp_path):
    path, _ = _synthetic_capture_grant(tmp_path, page_updated="2026-11-20")
    with pytest.raises(PermissionError, match="later than policy review"):
        capture_rights.require_personal_research_source_capture_scope(
            path, repo_root=tmp_path, now=NOW
        )


@pytest.mark.parametrize("field", ["valid_from_utc", "valid_until_utc"])
def test_missing_authorization_validity_bound_fails_closed(tmp_path, field):
    path, _ = _synthetic_capture_grant(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    del manifest["authorization"][field]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(PermissionError, match="requires both valid_from_utc and valid_until_utc"):
        capture_rights.require_personal_research_source_capture_scope(path, repo_root=tmp_path, now=NOW)


def test_expired_source_capture_grant_fails_closed(tmp_path):
    path, _ = _synthetic_capture_grant(tmp_path, valid_until="2026-11-18T00:00:00Z")
    with pytest.raises(PermissionError, match="authorization has expired"):
        capture_rights.require_personal_research_source_capture_scope(path, repo_root=tmp_path, now=NOW)


def test_reversed_source_capture_validity_window_fails_closed(tmp_path):
    path, _ = _synthetic_capture_grant(
        tmp_path,
        valid_from="2026-12-02T00:00:00Z",
        valid_until="2026-12-01T00:00:00Z",
    )
    with pytest.raises(PermissionError, match="validity window is empty or reversed"):
        capture_rights.require_personal_research_source_capture_scope(path, repo_root=tmp_path, now=NOW)


def test_source_capture_evidence_must_be_on_provider_domain(tmp_path):
    path, _ = _synthetic_capture_grant(tmp_path, evidence_url="https://example.com/provider-permission.pdf")
    with pytest.raises(PermissionError, match="on the provider domain"):
        capture_rights.require_personal_research_source_capture_scope(path, repo_root=tmp_path, now=NOW)


def test_malformed_authorization_scope_fails_closed_without_type_error(tmp_path):
    path, _ = _synthetic_capture_grant(tmp_path, scope=[["AUTOMATED_SOURCE_CAPTURE"], "NONCOMMERCIAL_RESEARCH"])
    with pytest.raises(PermissionError, match="does not cover automated source capture"):
        capture_rights.require_personal_research_source_capture_scope(path, repo_root=tmp_path, now=NOW)


def test_direct_source_capture_checks_rights_before_private_storage(monkeypatch):
    def deny():
        raise PermissionError("source-capture scope unresolved")

    def forbidden():
        pytest.fail("private-storage lookup must not run before source-capture rights")

    monkeypatch.setattr(capture_rights, "require_personal_research_source_capture_scope", deny)
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", forbidden)
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        direct_access.require_v2_source_capture_access()


def test_direct_source_capture_checks_private_storage_after_rights(monkeypatch):
    def deny_privacy():
        raise PermissionError("private storage is not approved")

    monkeypatch.setattr(
        capture_rights,
        "require_personal_research_source_capture_scope",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", deny_privacy)
    with pytest.raises(PermissionError, match="private storage is not approved"):
        direct_access.require_v2_source_capture_access()


def test_current_manifest_pins_updated_fair_use_page_and_keeps_capture_denied():
    manifest = json.loads(capture_rights.DEFAULT_RIGHTS_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["fair_use_policy_url"] == "https://football-data.co.uk/contact.php"
    assert manifest["fair_use_policy_page_updated_date"] == "2026-11-24"
    assert manifest["research_source_capture_permitted"] is False
    assert manifest["provider_issued_source_capture_license"] is False
    assert manifest["research_inference_permitted"] is False
    assert manifest["ai_model_training_permitted"] is False
    assert manifest["authorization"] is None


def test_fair_use_policy_evidence_sha_mismatch_fails_closed(tmp_path):
    path, _ = _synthetic_capture_grant(tmp_path)
    (tmp_path / "football_data_contact_fair_use_20261124.md").write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="fair-use policy evidence SHA-256 mismatch"):
        capture_rights.require_personal_research_source_capture_scope(path, repo_root=tmp_path, now=NOW)
