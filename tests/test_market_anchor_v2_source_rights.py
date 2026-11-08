from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from market_anchor_v2_source_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    require_ai_model_training_permission,
    require_personal_research_inference_scope,
    write_research_scope_blocked_report,
)


def _write_grant(tmp_path, *, overrides=None, evidence_bytes=b"written permission for this test only"):
    evidence = tmp_path / "permission-evidence.txt"
    evidence.write_bytes(evidence_bytes)
    manifest = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_V1",
        "provider": "Football-Data.co.uk",
        "rights_status": "GRANTED",
        "research_use_permitted": True,
        "ai_model_training_permitted": True,
        "commercial_use_permitted": False,
        "authorization": {
            "kind": "written_permission",
            "license_name": "Synthetic test permission",
            "rights_holder": "Football-Data.co.uk",
            "scope": ["AI_MODEL_TRAINING", "NONCOMMERCIAL_RESEARCH"],
            "evidence_url": "https://example.org/test-permission",
            "evidence_file": "permission-evidence.txt",
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "reviewed_by": "synthetic-test-reviewer",
            "reviewed_at_utc": "2026-11-02T12:00:00Z",
            "valid_from_utc": "2026-11-02T00:00:00Z",
            "valid_until_utc": "2026-11-04T00:00:00Z"
        }
    }
    if overrides:
        for key, value in overrides.items():
            if key == "authorization" and isinstance(value, dict):
                manifest["authorization"].update(value)
            else:
                manifest[key] = value
    path = tmp_path / "rights.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_default_football_data_policy_manifest_blocks_ai_training():
    with pytest.raises(PermissionError, match="not granted"):
        require_ai_model_training_permission(DEFAULT_RIGHTS_MANIFEST_PATH)


def test_missing_rights_manifest_fails_closed(tmp_path):
    with pytest.raises(PermissionError, match="missing or invalid"):
        require_ai_model_training_permission(tmp_path / "missing.json", repo_root=tmp_path)


def test_explicit_written_permission_with_matching_local_sha_is_accepted(tmp_path):
    path = _write_grant(tmp_path)
    result = require_ai_model_training_permission(
        path,
        repo_root=tmp_path,
        now=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc),
    )
    assert result["provider"] == "Football-Data.co.uk"
    assert result["license_name"] == "Synthetic test permission"
    assert result["evidence_sha256"] == hashlib.sha256(
        (tmp_path / "permission-evidence.txt").read_bytes()
    ).hexdigest()
    assert result["commercial_use_permitted"] is False


def test_tampered_permission_evidence_fails_sha_check(tmp_path):
    path = _write_grant(tmp_path)
    (tmp_path / "permission-evidence.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="SHA-256 mismatch"):
        require_ai_model_training_permission(path, repo_root=tmp_path)


def test_permission_without_both_required_scopes_is_rejected(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "authorization": {"scope": ["NONCOMMERCIAL_RESEARCH"]}
    })
    with pytest.raises(PermissionError, match="does not cover AI model training"):
        require_ai_model_training_permission(path, repo_root=tmp_path)


def test_expired_permission_is_rejected(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "authorization": {"valid_until_utc": "2026-11-02T00:00:00Z"}
    })
    with pytest.raises(PermissionError, match="has expired"):
        require_ai_model_training_permission(
            path,
            repo_root=tmp_path,
            now=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc),
        )


def test_future_permission_is_rejected(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "authorization": {"valid_from_utc": "2026-11-04T00:00:00Z"}
    })
    with pytest.raises(PermissionError, match="not yet valid"):
        require_ai_model_training_permission(
            path,
            repo_root=tmp_path,
            now=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc),
        )


def test_permission_evidence_cannot_escape_repository(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "authorization": {"evidence_file": "../outside.txt"}
    })
    with pytest.raises(PermissionError, match="inside the repository"):
        require_ai_model_training_permission(path, repo_root=tmp_path)


def test_permission_evidence_requires_direct_https_reference(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "authorization": {"evidence_url": "http://example.org/permission"}
    })
    with pytest.raises(PermissionError, match="direct HTTPS"):
        require_ai_model_training_permission(path, repo_root=tmp_path)





def test_official_policy_manifest_blocks_ai_inference_without_provider_license():
    with pytest.raises(PermissionError, match="scope remains unresolved"):
        require_personal_research_inference_scope(
            DEFAULT_RIGHTS_MANIFEST_PATH,
            now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc),
        )


def _write_research_scope_manifest(tmp_path, **overrides):
    evidence_bytes = b"synthetic provider-issued frozen AI inference permission for tests only"
    evidence_path = tmp_path / "provider-ai-inference-permission.txt"
    evidence_path.write_bytes(evidence_bytes)
    manifest = {
        "schema_version": "FOOTBALL_AI_SOURCE_RIGHTS_V1",
        "provider": "Football-Data.co.uk",
        "policy_url": "https://football-data.co.uk/contact.php",
        "policy_checked_at_utc": "2026-11-05T10:54:00Z",
        "policy_page_updated_date": "2026-11-04",
        "rights_status": "GRANTED",
        "research_use_permitted": True,
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
            "license_name": "Synthetic provider-issued frozen inference permission",
            "rights_holder": "Football-Data.co.uk",
            "scope": ["FROZEN_AI_INFERENCE", "NONCOMMERCIAL_RESEARCH"],
            "evidence_url": "https://football-data.co.uk/contact.php",
            "evidence_file": evidence_path.name,
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "reviewed_by": "synthetic-test-reviewer",
            "reviewed_at_utc": "2026-11-05T10:00:00Z",
            "valid_from_utc": "2026-11-05T00:00:00Z",
            "valid_until_utc": "2026-11-06T00:00:00Z",
        },
    }
    for key, value in overrides.items():
        if key == "authorization" and isinstance(value, dict):
            manifest["authorization"].update(value)
        else:
            manifest[key] = value
    path = tmp_path / "research-rights.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_research_inference_accepts_only_explicit_provider_issued_frozen_ai_license(tmp_path):
    path = _write_research_scope_manifest(tmp_path)
    result = require_personal_research_inference_scope(
        path,
        repo_root=tmp_path,
        now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc),
    )
    assert result["scope_status"] == "GRANTED"
    assert result["research_inference_scope"] == "FROZEN_AI_INFERENCE_AND_NONCOMMERCIAL_RESEARCH"
    assert result["provider_issued_ai_inference_license"] is True
    assert result["authorization_evidence_sha256"] == hashlib.sha256(
        (tmp_path / "provider-ai-inference-permission.txt").read_bytes()
    ).hexdigest()
    assert result["ai_model_training_permitted"] is False
    assert result["commercial_use_permitted"] is False
    assert result["public_product_use_permitted"] is False
    assert result["max_automated_download_sessions_per_week"] == 2


def test_research_inference_rejects_personal_research_flags_without_provider_license(tmp_path):
    path = _write_research_scope_manifest(tmp_path, provider_issued_ai_inference_license=False)
    with pytest.raises(PermissionError, match="scope remains unresolved"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_unverified_authorization_marker(tmp_path):
    path = _write_research_scope_manifest(tmp_path, authorization={"provider_issued": False})
    with pytest.raises(PermissionError, match="authorization evidence is missing"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_authorization_without_frozen_ai_scope(tmp_path):
    path = _write_research_scope_manifest(tmp_path, authorization={"scope": ["NONCOMMERCIAL_RESEARCH"]})
    with pytest.raises(PermissionError, match="does not cover frozen AI inference"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_tampered_provider_permission_evidence(tmp_path):
    path = _write_research_scope_manifest(tmp_path)
    (tmp_path / "provider-ai-inference-permission.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="evidence SHA-256 mismatch"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_public_product_scope(tmp_path):
    path = _write_research_scope_manifest(tmp_path, public_product_use_permitted=True)
    with pytest.raises(PermissionError, match="public product publication"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_commercial_scope(tmp_path):
    path = _write_research_scope_manifest(tmp_path, commercial_use_permitted=True)
    with pytest.raises(PermissionError, match="commercial use"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_requires_two_session_download_budget(tmp_path):
    path = _write_research_scope_manifest(tmp_path, max_automated_download_sessions_per_week=3)
    with pytest.raises(PermissionError, match="at most two sessions"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_disabled_research_scope(tmp_path):
    path = _write_research_scope_manifest(tmp_path, research_inference_permitted=False)
    with pytest.raises(PermissionError, match="outside the provider-authorized research scope"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_scope_block_report_is_explicitly_no_io_and_no_inference(tmp_path):
    output = tmp_path / "reports" / "blocked.json"
    report = write_research_scope_blocked_report(output, "SYNTHETIC_TEST", "provider permission absent")
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved == report
    assert report["mode"] == "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["rights_status"] == "V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED"
    assert report["public_http_requests"] == 0
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["forecasts_created"] == 0
    assert report["target_outcomes_read"] is False
    assert report["no_bet"] is True


def test_live_v2_entrypoints_check_scope_before_external_reads():
    inference_cases = {
        "serie_a_v2_live_diagnostic_report.py": (
            "from database import supabase",
            "fetch_saved_upcoming_serie_a_quotes(",
            "fetch_public_history(",
        ),
        "serie_a_v2_current_form_forward_capture.py": (
            "discover_archives(", "create_client(", "fetch_saved_upcoming_serie_a_quotes(",
        ),
        "serie_a_v2_forward_capture.py": (
            "from database import supabase", "discover_archives(", "fetch_saved_upcoming_serie_a_quotes(",
        ),
        "serie_a_v2_attest_real_source.py": (
            'token = os.environ.get("GITHUB_TOKEN", "")',
            "proof = attest_latest_source(",
        ),
    }
    for path, side_effects in inference_cases.items():
        source = (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")
        main = source[source.index("def main()"): ]
        if path == "serie_a_v2_live_diagnostic_report.py":
            # Metadata-only quote preflight must pass provider rights before saved odds are read.
            preflight_start = main.index("    if args.preflight_only:")
            preflight_db = main.index("    from database import supabase", preflight_start)
            preflight = main[preflight_start:preflight_db]
            rights_guard = preflight.find("require_personal_research_inference_scope()")
            assert rights_guard >= 0
            assert "fetch_public_history(" not in preflight
            normal_start = main.index("    try:", preflight_db)
            normal = main[normal_start:]
            guard = normal.find("require_personal_research_inference_scope()")
            assert guard >= 0
            for side_effect in side_effects:
                position = normal.find(side_effect)
                assert position >= 0, "missing expected post-rights step: " + path + " / " + side_effect
                assert guard < position, "rights guard follows external read: " + path + " / " + side_effect
            continue
        guard = main.find("require_personal_research_inference_scope()")
        assert guard >= 0, f"{path} lacks the provider AI-inference permission guard"
        for side_effect in side_effects:
            position = main.find(side_effect)
            assert position >= 0, f"{path} lost expected runtime step {side_effect!r}"
            assert guard < position, f"{path} reaches {side_effect!r} before the provider AI-inference permission guard"

    source_path = Path(__file__).resolve().parents[1] / "serie_a_v2_current_form_source_capture.py"
    source_main = source_path.read_text(encoding="utf-8").split("def main()", 1)[1]
    source_guard = source_main.find("require_personal_research_source_capture_scope()")
    privacy_guard = source_main.find("require_private_repository_for_source_artifacts()")
    assert source_guard >= 0, "source capture lacks the source-only research rights gate"
    assert privacy_guard > source_guard, "source capture must verify private storage after source-only rights"
    assert "require_personal_research_inference_scope()" not in source_main
    for side_effect in ("create_client(", "capture_source_archive("):
        position = source_main.find(side_effect)
        assert position >= 0, f"source capture lost expected runtime step {side_effect!r}"
        assert privacy_guard < position, f"source capture reaches {side_effect!r} before private-storage verification"


def test_research_inference_rejects_policy_page_updated_after_review(tmp_path):
    path = _write_research_scope_manifest(tmp_path, policy_page_updated_date="2026-11-06")
    with pytest.raises(PermissionError, match="later than policy review"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_research_inference_rejects_noncanonical_policy_page_date(tmp_path):
    path = _write_research_scope_manifest(tmp_path, policy_page_updated_date="2026-W45-3")
    with pytest.raises(PermissionError, match="canonical YYYY-MM-DD"):
        require_personal_research_inference_scope(
            path, repo_root=tmp_path, now=datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
        )


def test_current_official_policy_wording_is_pinned_without_overstating_ai_usage_ban():
    manifest = json.loads(DEFAULT_RIGHTS_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["policy_page_updated_date"] == "2026-11-06"
    assert manifest["policy_checked_at_utc"] == "2026-11-07T01:56:17Z"
    assert "AI data-training projects" in manifest["policy_summary"]
    assert "AI-usage" not in manifest["policy_summary"]
    assert "does not separately define" in manifest["policy_summary"]
    assert manifest["research_use_permitted"] is True
    assert manifest["research_source_capture_permitted"] is True
    assert manifest["research_source_capture_scope"] == "PRIVATE_NONCOMMERCIAL_RESEARCH_ARCHIVE_ONLY"
    assert "source-only archival/validation" in manifest["policy_interpretation"]
    assert "frozen-model inference remains blocked" in manifest["policy_interpretation"].lower()
    assert manifest["research_inference_permitted"] is False
    assert manifest["provider_issued_ai_inference_license"] is False
    assert manifest["authorization"] is None
    with pytest.raises(PermissionError, match="scope remains unresolved"):
        require_personal_research_inference_scope(
            DEFAULT_RIGHTS_MANIFEST_PATH,
            now=datetime(2026, 11, 7, 2, 0, tzinfo=timezone.utc),
        )
