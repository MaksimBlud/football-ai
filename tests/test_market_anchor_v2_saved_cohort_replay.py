"""Fail-closed tests for the retired, outcome-bearing V2 saved-cohort replay."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import market_anchor_v2_saved_cohort_replay as replay


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
EXPECTED_CANDIDATE_SHA256 = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"


def test_retired_saved_cohort_contains_no_embedded_target_labels():
    # Protected post-outcome labels must not remain importable from this retired module.
    assert replay.TARGETS == ()


def test_original_candidate_identity_and_frozen_contract_are_unchanged():
    artifact = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert artifact["artifact_sha256"] == EXPECTED_CANDIDATE_SHA256
    assert len(artifact["features"]) == 19
    assert artifact["active_lambda"] == 0.0
    assert artifact["shadow_residual_lambda"] == 1.0
    assert artifact["stability_gate_passed"] is False
    assert artifact["automatic_promotion"] is False


class Untouchable:
    def __getattribute__(self, name):
        raise AssertionError(f"retired replay inspected protected input: {name}")


def _forbidden(*_args, **_kwargs):
    pytest.fail("retired replay must stop before source, target, report, or filesystem access")


def test_direct_csv_download_is_denied_before_http(monkeypatch):
    monkeypatch.setattr(replay.requests, "get", _forbidden)
    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.download_csv("1617")


def test_training_frame_builder_is_denied_before_source_access():
    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.build_training_frame(Untouchable())


def test_target_feature_builder_is_denied_before_current_season_download(monkeypatch):
    monkeypatch.setattr(replay, "download_csv", _forbidden)
    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.build_target_features(Untouchable(), Untouchable())


def test_target_validator_is_denied_before_embargoed_labels_are_inspected():
    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.validate_targets()


def test_saved_report_comparator_is_denied_before_report_access():
    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.assert_same_frozen_replay(Untouchable())


def test_retired_replay_and_recovery_fail_before_target_or_source_access(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "validate_targets", _forbidden)
    monkeypatch.setattr(replay, "load_frozen_modules", _forbidden)
    monkeypatch.setattr(replay, "build_training_frame", _forbidden)

    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.replay(tmp_path)
    with pytest.raises(PermissionError, match="saved-cohort replay/refit is retired"):
        replay.restore_frozen_candidate_from_training_history(tmp_path)
