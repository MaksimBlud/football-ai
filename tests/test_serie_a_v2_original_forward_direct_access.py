"""Original V2 direct-entrypoint rights and private-storage regressions."""
from datetime import datetime, timezone

import pytest

import market_anchor_v2_artifact_privacy as privacy
import market_anchor_v2_direct_access as direct_access
import market_anchor_v2_source_rights as source_rights
import market_anchor_v2_source_capture_rights as source_capture_rights
import serie_a_v2_forward_capture as original_forward


NOW = datetime(2026, 11, 25, 0, 10, tzinfo=timezone.utc)


def _deny():
    raise PermissionError("provider inference scope is unresolved")


def _forbidden(*_args, **_kwargs):
    pytest.fail("external access occurred before the provider-rights gate")


class _Forbidden:
    def __iter__(self):
        pytest.fail("input iteration occurred before the provider-rights gate")

    def __bool__(self):
        pytest.fail("input truthiness was inspected before the provider-rights gate")

    def __len__(self):
        pytest.fail("input length was inspected before the provider-rights gate")

    def __getitem__(self, _key):
        pytest.fail("input indexing occurred before the provider-rights gate")

    def get(self, _key, *_args):
        pytest.fail("mapping access occurred before the provider-rights gate")


def test_current_source_rights_manifest_keeps_frozen_inference_closed():
    with pytest.raises(PermissionError, match="scope remains unresolved"):
        source_rights.require_personal_research_inference_scope(now=NOW)


def test_direct_access_checks_provider_rights_before_private_repository_lookup(monkeypatch):
    monkeypatch.setattr(source_rights, "require_personal_research_inference_scope", _deny)
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", _forbidden)

    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        direct_access.require_v2_inference_access()


def test_direct_access_checks_private_storage_after_rights_are_granted(monkeypatch):
    monkeypatch.setattr(
        source_rights,
        "require_personal_research_inference_scope",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", _deny)

    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        direct_access.require_v2_inference_access()


def test_original_forward_public_entrypoints_deny_before_inputs_or_callbacks(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    monkeypatch.setattr(source_rights, "require_personal_research_inference_scope", _deny)
    monkeypatch.setattr(source_capture_rights, "require_personal_research_source_capture_scope", _deny)
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", _forbidden)
    blocked_dir = tmp_path / "must-not-be-created"

    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        original_forward.prepare_forward_capture(
            _Forbidden(),
            _Forbidden(),
            as_of_utc=NOW,
            load_archive=_forbidden,
            verify_parent_run=_forbidden,
            write_archives_to=blocked_dir,
        )

    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        original_forward.capture_forward_with_source_preflight(
            _Forbidden(),
            as_of_utc=NOW,
            fetch_quotes=_forbidden,
            load_archive=_forbidden,
            verify_parent_run=_forbidden,
            write_archives_to=blocked_dir,
        )

    assert not blocked_dir.exists()


def test_original_forward_github_boundaries_deny_before_network_or_input_access(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    monkeypatch.setattr(source_rights, "require_personal_research_inference_scope", _deny)
    monkeypatch.setattr(source_capture_rights, "require_personal_research_source_capture_scope", _deny)
    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", _forbidden)

    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        original_forward._github_json(
            "https://api.github.com/repos/MaksimBlud/football-ai",
            token="synthetic-token",
            get=_forbidden,
        )
    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        original_forward.verify_source_run(
            _Forbidden(), quote_time=NOW, token="synthetic-token", get=_forbidden
        )
    with pytest.raises(PermissionError, match="provider inference scope is unresolved"):
        original_forward.get_archive(123, token="synthetic-token", get=_forbidden)
