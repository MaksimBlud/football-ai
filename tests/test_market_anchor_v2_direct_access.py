"""Negative regressions for direct-call source, quote, archive and inference gates."""
from datetime import datetime, timezone

import pytest

import market_anchor_v2_artifact_privacy as privacy
import market_anchor_v2_source_capture_rights as capture_rights
import market_anchor_v2_source_rights as inference_rights
import serie_a_v2_asof_feature_manifest as feature_manifest
import serie_a_v2_attest_real_source as source_attestor
import serie_a_v2_current_form_forward_capture as current_forward
import serie_a_v2_current_form_source_capture as current_source
import serie_a_v2_forward_capture as original_forward
import serie_a_v2_live_diagnostic_report as diagnostic
import serie_a_v2_prequote_source_archive_gate as archive_gate


NOW = datetime(2026, 11, 11, 6, 0, tzinfo=timezone.utc)


def _deny():
    raise PermissionError("direct-access test deny")


def _network_forbidden(*_args, **_kwargs):
    pytest.fail("network callback ran before the direct-access rights gate")


class _Forbidden:
    def __iter__(self):
        pytest.fail("input iteration occurred before the direct-access rights gate")

    def __bool__(self):
        pytest.fail("input truthiness was inspected before the direct-access rights gate")

    def __len__(self):
        pytest.fail("input length was inspected before the direct-access rights gate")

    def __getitem__(self, _key):
        pytest.fail("input indexing occurred before the direct-access rights gate")

    def get(self, _key, *_args):
        pytest.fail("mapping was inspected before the direct-access rights gate")

    def stat(self):
        pytest.fail("archive path was stat'ed before the direct-access rights gate")

    def read_bytes(self):
        pytest.fail("archive bytes were read before the direct-access rights gate")


class _ForbiddenClient:
    def table(self, *_args, **_kwargs):
        pytest.fail("Supabase was accessed before the source-capture rights gate")


def test_original_forward_direct_helpers_deny_before_quote_archive_or_network_access(monkeypatch, tmp_path):
    monkeypatch.setattr(inference_rights, "require_personal_research_inference_scope", _deny)
    blocked_dir = tmp_path / "must-not-be-created"

    with pytest.raises(PermissionError, match="direct-access test deny"):
        original_forward.discover_archives(token="synthetic", get=_network_forbidden)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        original_forward.verify_source_run(
            _Forbidden(), quote_time=NOW, token="synthetic", get=_network_forbidden
        )
    with pytest.raises(PermissionError, match="direct-access test deny"):
        original_forward.get_archive(1, token="synthetic", get=_network_forbidden)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        original_forward.prepare_forward_capture(
            _Forbidden(),
            _Forbidden(),
            as_of_utc=NOW,
            load_archive=_network_forbidden,
            verify_parent_run=_network_forbidden,
            write_archives_to=blocked_dir,
        )

    assert not blocked_dir.exists()


def test_feature_report_archive_and_attestation_helpers_deny_before_inputs(monkeypatch):
    monkeypatch.setattr(inference_rights, "require_personal_research_inference_scope", _deny)
    monkeypatch.setattr(capture_rights, "require_personal_research_source_capture_scope", _deny)

    with pytest.raises(PermissionError, match="direct-access test deny"):
        feature_manifest.build_manifest(_Forbidden(), _Forbidden())
    with pytest.raises(PermissionError, match="direct-access test deny"):
        diagnostic.make_report(_Forbidden(), _Forbidden(), _Forbidden(), as_of_utc=NOW)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        archive_gate.verify_archive(_Forbidden(), _Forbidden(), as_of_utc=NOW)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        source_attestor.attest_latest_source(
            token="synthetic",
            now=NOW,
            discover=_network_forbidden,
            load=_network_forbidden,
            verify_run=_network_forbidden,
        )


def test_current_form_forward_direct_helpers_deny_before_inputs_or_callbacks(monkeypatch, tmp_path):
    monkeypatch.setattr(inference_rights, "require_personal_research_inference_scope", _deny)
    blocked_dir = tmp_path / "must-not-be-created"

    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_forward.discover_archives(token="synthetic", get=_network_forbidden)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_forward.verify_source_run(
            _Forbidden(), quote_time=NOW, token="synthetic", get=_network_forbidden
        )
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_forward.get_archive(1, token="synthetic", get=_network_forbidden)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_forward.verify_and_load_archive(_Forbidden(), _Forbidden(), _Forbidden())
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_forward.verify_latest_source_archive(
            _Forbidden(),
            as_of_utc=NOW,
            load_archive=_network_forbidden,
            verify_parent_run=_network_forbidden,
        )
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_forward.prepare_forward_capture(
            _Forbidden(),
            _Forbidden(),
            as_of_utc=NOW,
            load_archive=_network_forbidden,
            verify_parent_run=_network_forbidden,
            current_gate_identities=_Forbidden(),
            write_sources_to=blocked_dir,
        )

    assert not blocked_dir.exists()


def test_current_form_source_capture_direct_helpers_deny_before_supabase_csv_or_network(monkeypatch, tmp_path):
    monkeypatch.setattr(capture_rights, "require_personal_research_source_capture_scope", _deny)
    blocked_dir = tmp_path / "must-not-be-created"

    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_source.read_completed_primary_event_count(_ForbiddenClient(), now=NOW)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_source.read_completed_primary_event_identities(_ForbiddenClient(), now=NOW)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_source.validate_current_season_csv(b"not-a-csv", captured_at=NOW)
    with pytest.raises(PermissionError, match="direct-access test deny"):
        current_source.capture_source_archive(
            output_dir=blocked_dir,
            client=_ForbiddenClient(),
            now=NOW,
            get=_network_forbidden,
            history_fetch=_network_forbidden,
        )
    with pytest.raises(PermissionError, match="direct-access test deny"):
        diagnostic.fetch_public_history(get=_network_forbidden, capture_dir=blocked_dir)

    assert not blocked_dir.exists()


def test_private_storage_is_required_after_provider_inference_scope(monkeypatch):
    monkeypatch.setattr(
        inference_rights,
        "require_personal_research_inference_scope",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", _deny)

    with pytest.raises(PermissionError, match="direct-access test deny"):
        original_forward.prepare_forward_capture(
            _Forbidden(),
            _Forbidden(),
            as_of_utc=NOW,
            load_archive=_network_forbidden,
            verify_parent_run=_network_forbidden,
        )
