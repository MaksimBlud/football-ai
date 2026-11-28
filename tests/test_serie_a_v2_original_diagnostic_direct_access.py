"""Direct-entrypoint rights regressions for original MARKET_ANCHOR_1X2_V2."""
from datetime import datetime, timezone
import sys

import pytest

import serie_a_v2_live_diagnostic_report as live
import serie_a_v2_frozen_shadow_preview as frozen


NOW = datetime(2026, 11, 19, 23, 0, tzinfo=timezone.utc)


class _Poison:
    def __bool__(self):
        raise AssertionError("caller input inspected before rights gate")

    def __iter__(self):
        raise AssertionError("caller input iterated before rights gate")

    def __len__(self):
        raise AssertionError("caller input length inspected before rights gate")

    def __getitem__(self, _key):
        raise AssertionError("caller input indexed before rights gate")

    def get(self, *_args, **_kwargs):
        raise AssertionError("caller mapping inspected before rights gate")


def _deny_capture():
    raise PermissionError("source-capture scope unresolved")


def _deny_inference():
    raise PermissionError("frozen inference scope unresolved")


def test_current_provider_manifest_keeps_capture_and_inference_closed(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    with pytest.raises(PermissionError, match="automated source capture is not permitted"):
        live.require_v2_source_capture_access()
    with pytest.raises(PermissionError, match="scope remains unresolved"):
        live.require_v2_inference_access()


def test_public_history_fetch_denies_before_http_or_local_archive_creation(monkeypatch, tmp_path):
    calls = []
    archive_dir = tmp_path / "must-not-exist"
    monkeypatch.setattr(live, "require_v2_source_capture_access", _deny_capture)

    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        live.fetch_public_history(
            get=lambda *args, **kwargs: calls.append((args, kwargs)),
            capture_dir=archive_dir,
        )

    assert calls == []
    assert not archive_dir.exists()


def test_live_report_denies_before_inspecting_quotes_history_or_audit(monkeypatch):
    monkeypatch.setattr(live, "require_v2_inference_access", _deny_inference)

    with pytest.raises(PermissionError, match="frozen inference scope unresolved"):
        live.make_report(_Poison(), _Poison(), _Poison(), as_of_utc=NOW)


def test_frozen_shadow_denies_before_iterating_market_or_feature_inputs(monkeypatch):
    monkeypatch.setattr(frozen, "require_v2_inference_access", _deny_inference)

    with pytest.raises(PermissionError, match="frozen inference scope unresolved"):
        frozen.shadow_preview(_Poison(), _Poison(), as_of_utc=NOW)


def test_saved_quote_reader_denies_before_supabase_client_access(monkeypatch):
    monkeypatch.setattr(frozen, "require_v2_inference_access", _deny_inference)

    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            pytest.fail("Supabase was accessed before inference rights")

    with pytest.raises(PermissionError, match="frozen inference scope unresolved"):
        frozen.fetch_saved_upcoming_serie_a_quotes(ForbiddenClient(), now=NOW)


def test_live_diagnostic_cli_denies_before_database_import_or_source_fetch(monkeypatch, tmp_path):
    output = tmp_path / "report.json"
    raw_dir = tmp_path / "raw"
    monkeypatch.setattr(live, "require_v2_inference_access", _deny_inference)
    monkeypatch.setattr(
        live,
        "require_v2_source_capture_access",
        lambda: pytest.fail("source capture gate ran after denied inference"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["serie_a_v2_live_diagnostic_report.py", "--output", str(output),
         "--raw-source-dir", str(raw_dir)],
    )

    with pytest.raises(PermissionError, match="frozen inference scope unresolved"):
        live.main()

    assert not output.exists()
    assert not raw_dir.exists()


def test_frozen_preview_cli_denies_before_database_or_feature_file_read(monkeypatch, tmp_path):
    feature_file = tmp_path / "missing-features.json"
    monkeypatch.setattr(frozen, "require_v2_inference_access", _deny_inference)
    monkeypatch.setattr(
        sys,
        "argv",
        ["serie_a_v2_frozen_shadow_preview.py", "--features-json", str(feature_file),
         "--saved-supabase-quotes"],
    )

    with pytest.raises(PermissionError, match="frozen inference scope unresolved"):
        frozen.main()

    assert not feature_file.exists()
