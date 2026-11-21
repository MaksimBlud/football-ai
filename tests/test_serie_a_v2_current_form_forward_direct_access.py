"""Direct-access and rights-order regressions for original V2 current-form forward capture."""
from datetime import datetime, timezone
import sys

import pytest

import serie_a_v2_current_form_forward_capture as forward


NOW = datetime(2026, 11, 20, 0, 0, tzinfo=timezone.utc)


class _Poison:
    def __bool__(self):
        raise AssertionError("input truthiness inspected before rights gate")

    def __iter__(self):
        raise AssertionError("input iterated before rights gate")

    def __len__(self):
        raise AssertionError("input length inspected before rights gate")

    def __getitem__(self, _key):
        raise AssertionError("input indexed before rights gate")

    def get(self, *_args, **_kwargs):
        raise AssertionError("mapping inspected before rights gate")


def _deny_source():
    raise PermissionError("source-capture scope unresolved")


def _deny_inference():
    raise PermissionError("frozen-inference scope unresolved")


def _forbidden(*_args, **_kwargs):
    pytest.fail("external callback ran before the required rights gate")


def test_archive_metadata_verification_denies_before_clock_or_metadata_access(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward.verify_latest_source_archive(
            _Poison(),
            as_of_utc=_Poison(),
            load_archive=_forbidden,
            verify_parent_run=_forbidden,
        )


def test_archive_bytes_are_not_parsed_before_source_capture_rights(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward.verify_and_load_archive(_Poison(), _Poison(), _Poison())


def test_github_metadata_request_is_denied_before_http(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward._github_json("https://api.github.com/repos/MaksimBlud/football-ai", token="test", get=_forbidden)


def test_parent_run_verification_is_denied_before_archive_inspection(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward.verify_source_run(_Poison(), quote_time=NOW, token="test", get=_forbidden)


def test_archive_download_is_denied_before_id_or_http_access(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward.get_archive(_Poison(), token="test", get=_forbidden)


def test_direct_quote_normalization_requires_inference_before_input_access(monkeypatch):
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_inference_access",
        _deny_inference,
    )

    with pytest.raises(PermissionError, match="frozen-inference scope unresolved"):
        forward._latest_quotes(_Poison(), now=_Poison())


def test_feature_preparation_requires_both_scopes_before_inputs(monkeypatch):
    calls = []
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_source_capture_access",
        lambda: calls.append("source"),
    )
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_inference_access",
        _deny_inference,
    )

    with pytest.raises(PermissionError, match="frozen-inference scope unresolved"):
        forward.prepare_forward_capture(
            _Poison(),
            _Poison(),
            as_of_utc=_Poison(),
            load_archive=_forbidden,
            verify_parent_run=_forbidden,
        )

    assert calls == ["source"]


def test_source_verification_remains_separate_from_inference_permission(monkeypatch):
    calls = []
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_source_capture_access",
        lambda: calls.append("source"),
    )
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_inference_access",
        lambda: pytest.fail("source-only verification must not require inference rights"),
    )

    report = forward.verify_latest_source_archive(
        [],
        as_of_utc=NOW,
        load_archive=_forbidden,
        verify_parent_run=_forbidden,
    )

    assert report["status"] == "NO_SOURCE_ARCHIVE"
    assert report["verified"] is False
    assert calls == ["source"]


def test_cli_source_rights_gate_runs_before_argument_or_environment_access(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)
    monkeypatch.setattr(
        sys,
        "argv",
        ["serie_a_v2_current_form_forward_capture.py", "--output", "/tmp/never.json",
         "--sources-output-dir", "/tmp/never-sources"],
    )

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward.main()


def test_cli_inference_rights_gate_runs_before_supabase_client_creation(monkeypatch):
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_source_capture_access",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(forward.v2_access, "require_v2_inference_access", _deny_inference)
    monkeypatch.setattr(
        sys,
        "argv",
        ["serie_a_v2_current_form_forward_capture.py", "--output", "/tmp/never.json",
         "--sources-output-dir", "/tmp/never-sources"],
    )
    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-test-token")
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_KEY", "synthetic-test-key")
    monkeypatch.setattr(forward, "discover_archives", lambda **_kwargs: [])
    monkeypatch.setattr(
        forward,
        "verify_latest_source_archive",
        lambda *_args, **_kwargs: _verified_source_mapping(),
    )
    monkeypatch.setattr(
        forward,
        "create_client",
        lambda *_args, **_kwargs: pytest.fail("Supabase client created before inference rights"),
    )

    with pytest.raises(PermissionError, match="frozen-inference scope unresolved"):
        forward.main()

def _verified_source_mapping():
    return {
        "status": "VERIFIED",
        "verified": True,
        "verified_at_utc": "2026-11-20T00:00:00Z",
        "artifact_id": 123,
        "artifact_sha256": "a" * 64,
        "source_archive_created_at_utc": "2026-11-19T23:40:00Z",
        "latest_source_observed_at_utc": "2026-11-19T23:30:00Z",
        "candidate_sha256": forward.FROZEN_SHA,
        "parent_run": {
            "run_id": 456,
            "run_head_sha": "b" * 40,
            "workflow_path": forward.SOURCE_WORKFLOW_PATH,
            "run_created_at_utc": "2026-11-19T23:35:00Z",
            "run_completed_at_utc": "2026-11-19T23:50:00Z",
        },
    }


def test_quote_reader_direct_entrypoint_requires_source_rights_before_mapping_access(monkeypatch):
    monkeypatch.setattr(forward.v2_access, "require_v2_source_capture_access", _deny_source)
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        forward.read_quotes_after_verified_source(
            _Poison(),
            quote_loader=_forbidden,
        )


def test_quote_reader_direct_entrypoint_requires_inference_rights_before_quote_loader(monkeypatch):
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_source_capture_access",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(forward.v2_access, "require_v2_inference_access", _deny_inference)
    with pytest.raises(PermissionError, match="frozen-inference scope unresolved"):
        forward.read_quotes_after_verified_source(
            _verified_source_mapping(),
            quote_loader=_forbidden,
        )


def test_quote_reader_skips_without_source_without_requesting_inference_rights(monkeypatch):
    monkeypatch.setattr(
        forward.v2_access,
        "require_v2_source_capture_access",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(forward.v2_access, "require_v2_inference_access", _deny_inference)
    quotes, gate = forward.read_quotes_after_verified_source(
        {"status": "NO_SOURCE_ARCHIVE", "verified": False},
        quote_loader=_forbidden,
    )
    assert quotes == []
    assert gate["quote_reader_called"] is False

