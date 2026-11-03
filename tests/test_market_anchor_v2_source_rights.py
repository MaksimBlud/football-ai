from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from market_anchor_v2_source_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    require_ai_model_training_permission,
    require_ai_usage_permission,
    write_ai_usage_blocked_report,
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



def test_default_football_data_policy_manifest_blocks_ai_usage():
    with pytest.raises(PermissionError, match="AI-usage permission is not granted"):
        require_ai_usage_permission(DEFAULT_RIGHTS_MANIFEST_PATH)


def test_ai_usage_grant_is_separate_from_model_training_permission(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "ai_model_training_permitted": False,
        "ai_usage_permitted": True,
        "authorization": {"scope": ["AI_USAGE", "NONCOMMERCIAL_RESEARCH"]},
    })
    result = require_ai_usage_permission(
        path,
        repo_root=tmp_path,
        now=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc),
    )
    assert result["provider"] == "Football-Data.co.uk"
    assert result["scope"] == ["AI_USAGE", "NONCOMMERCIAL_RESEARCH"]
    assert result["ai_model_training_permitted"] is False


def test_ai_usage_permission_requires_explicit_ai_usage_scope(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "ai_model_training_permitted": False,
        "ai_usage_permitted": True,
        "authorization": {"scope": ["NONCOMMERCIAL_RESEARCH"]},
    })
    with pytest.raises(PermissionError, match="does not cover AI usage"):
        require_ai_usage_permission(path, repo_root=tmp_path)


def test_ai_usage_permission_rejects_tampered_evidence(tmp_path):
    path = _write_grant(tmp_path, overrides={
        "ai_model_training_permitted": False,
        "ai_usage_permitted": True,
        "authorization": {"scope": ["AI_USAGE", "NONCOMMERCIAL_RESEARCH"]},
    })
    (tmp_path / "permission-evidence.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(PermissionError, match="SHA-256 mismatch"):
        require_ai_usage_permission(path, repo_root=tmp_path)


def test_ai_usage_block_report_is_explicitly_no_io_and_no_inference(tmp_path):
    output = tmp_path / "reports" / "blocked.json"
    report = write_ai_usage_blocked_report(
        output, "SYNTHETIC_TEST", "permission not granted"
    )
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved == report
    assert report["mode"] == "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["public_http_requests"] == 0
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["forecasts_created"] == 0
    assert report["target_outcomes_read"] is False
    assert report["no_bet"] is True


def test_live_v2_entrypoints_check_ai_usage_before_external_reads():
    cases = {
        "serie_a_v2_live_diagnostic_report.py": (
            "from database import supabase",
            "fetch_saved_upcoming_serie_a_quotes(",
            "fetch_public_history(",
        ),
        "serie_a_v2_current_form_source_capture.py": (
            "create_client(",
            "capture_source_archive(",
        ),
        "serie_a_v2_current_form_forward_capture.py": (
            "discover_archives(",
            "create_client(",
            "fetch_saved_upcoming_serie_a_quotes(",
        ),
        "serie_a_v2_forward_capture.py": (
            "from database import supabase",
            "discover_archives(",
            "fetch_saved_upcoming_serie_a_quotes(",
        ),
    }
    for path, side_effects in cases.items():
        source = (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")
        main = source[source.index("def main()"):]
        guard = main.find("require_ai_usage_permission()")
        assert guard >= 0, f"{path} lacks the AI-usage rights guard"
        for side_effect in side_effects:
            position = main.find(side_effect)
            assert position >= 0, f"{path} lost expected runtime step {side_effect!r}"
            assert guard < position, f"{path} reaches {side_effect!r} before the rights guard"
