from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from unittest.mock import patch

import market_anchor_v2_bigballs_archive_gate as gate
from market_anchor_v2_bigballs_archive_gate import (
    ArchiveGateError,
    validate_private_prequote_archive,
)

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research" / "source_rights" / "bigballs_sports_data_20261124.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"
CANDIDATE_SHA = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"


def _body(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _bundle():
    match = {
        "data": {
            "id": "source-match-1",
            "sport": "football",
            "league": "Serie A",
            "kickoff_utc": "2026-11-10T19:00:00Z",
            "status": "finished",
            "home": {"id": "team-home", "name": "Home"},
            "away": {"id": "team-away", "name": "Away"},
            "score": {"home": 2, "away": 1},
        }
    }
    statistics = {
        "data": {
            "home": {
                "team_id": "team-home",
                "corner_kicks": 5,
                "yellow_cards": 2,
                "red_cards": 0,
            },
            "away": {
                "team_id": "team-away",
                "corner_kicks": 3,
                "yellow_cards": 1,
                "red_cards": 0,
            },
        },
        "meta": {"available": True},
    }
    match_body = _body(match)
    statistics_body = _body(statistics)
    archive = {
        "provider": "Big Balls Sports Data",
        "provider_plan": "free",
        "source_match_id": "source-match-1",
        "target_match_id": "target-match-1",
        "match_endpoint": "/v1/matches/source-match-1",
        "statistics_endpoint": "/v1/matches/source-match-1/statistics",
        "match_received_at_utc": "2026-11-10T20:00:00Z",
        "statistics_received_at_utc": "2026-11-10T20:05:00Z",
        "archive_created_at_utc": "2026-11-10T20:06:00Z",
        "match_body_sha256": hashlib.sha256(match_body).hexdigest(),
        "statistics_body_sha256": hashlib.sha256(statistics_body).hexdigest(),
        "candidate_sha256": CANDIDATE_SHA,
        "storage_visibility": "private",
        "public_raw_artifact_uploaded": False,
        "paid_provider_calls": 0,
        "paid_odds_used": False,
    }
    rights = {
        "provider": "Big Balls Sports Data",
        "integration_allowed": True,
        "automated_capture_authorized": True,
        "frozen_inference_authorized": True,
    }
    return rights, archive, match_body, statistics_body, match, statistics


def _validate(bundle=None, **overrides):
    rights, archive, match_body, statistics_body, _, _ = bundle or _bundle()
    args = {
        "archive_manifest": archive,
        "match_body": match_body,
        "statistics_body": statistics_body,
        "quote_match_id": "target-match-1",
        "quote_snapshot_time_utc": "2026-11-11T08:00:00Z",
        "quote_created_at_utc": "2026-11-11T08:00:01Z",
        "target_kickoff_utc": "2026-11-11T18:00:00Z",
        "expected_candidate_sha256": CANDIDATE_SHA,
    }
    args.update(overrides)
    with patch.object(gate, "_load_verified_rights_manifest", return_value=rights):
        return validate_private_prequote_archive(**args)


def test_valid_synthetic_private_bundle_passes_and_performs_no_inference():
    result = _validate()
    assert result["status"] == "VERIFIED_PRIVATE_PREQUOTE_LAGGED_SOURCE"
    assert result["candidate_sha256"] == CANDIDATE_SHA
    assert result["missing_stat_fields"] == []
    assert result["upstream_first_observation_proven"] is False
    assert result["feature_values_imputed"] is False
    assert result["feature_calculation_performed"] is False
    assert result["model_inference_performed"] is False
    assert result["supabase_write_performed"] is False
    assert result["public_raw_artifact_uploaded"] is False
    assert result["no_bet"] is True


def test_current_provider_manifest_still_denies_integration():
    rights = gate._load_verified_rights_manifest()
    assert rights["decision"] == "HOLD_NO_INTEGRATION"
    _, archive, match_body, statistics_body, *_ = _bundle()
    with pytest.raises(ArchiveGateError, match="provider rights decision is not APPROVED"):
        validate_private_prequote_archive(
            archive_manifest=archive,
            match_body=match_body,
            statistics_body=statistics_body,
            quote_match_id="target-match-1",
            quote_snapshot_time_utc="2026-11-11T08:00:00Z",
            quote_created_at_utc="2026-11-11T08:00:01Z",
            target_kickoff_utc="2026-11-11T18:00:00Z",
            expected_candidate_sha256=CANDIDATE_SHA,
        )


def test_canonical_rights_manifest_git_blob_sha_mismatch_fails_closed(tmp_path, monkeypatch):
    copied = tmp_path / "rights.json"
    copied.write_bytes(RIGHTS.read_bytes())
    monkeypatch.setattr(gate, "RIGHTS_MANIFEST_PATH", copied)
    monkeypatch.setattr(gate, "RIGHTS_MANIFEST_GIT_BLOB_SHA1", "0" * 40)
    with pytest.raises(ArchiveGateError, match="Git blob SHA-1 mismatch"):
        gate._load_verified_rights_manifest()


def test_frozen_candidate_file_matches_the_archive_contract():
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == CANDIDATE_SHA
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == 1


def test_sha_mismatch_is_rejected():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["match_body_sha256"] = "0" * 64
    with pytest.raises(ArchiveGateError, match="match body SHA-256 mismatch"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_receipt_after_quote_is_rejected():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["statistics_received_at_utc"] = "2026-11-11T08:00:00Z"
    archive["archive_created_at_utc"] = "2026-11-11T08:00:00Z"
    with pytest.raises(ArchiveGateError, match="source receipt times must strictly precede"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_archive_created_after_quote_is_rejected():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["archive_created_at_utc"] = "2026-11-11T08:00:00Z"
    with pytest.raises(ArchiveGateError, match="private source archive must strictly precede"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_quote_must_be_saved_before_target_kickoff():
    with pytest.raises(ArchiveGateError, match="quote chronology"):
        _validate(quote_snapshot_time_utc="2026-11-11T18:00:00Z")


def test_quote_created_at_must_be_after_snapshot_and_before_kickoff():
    with pytest.raises(ArchiveGateError, match="snapshot <= created_at < target kickoff"):
        _validate(quote_created_at_utc="2026-11-11T07:59:59Z")
    with pytest.raises(ArchiveGateError, match="snapshot <= created_at < target kickoff"):
        _validate(quote_created_at_utc="2026-11-11T18:00:00Z")


def test_source_match_must_be_finished_and_have_final_scores():
    rights, archive, match_body, statistics_body, match, _ = _bundle()
    match["data"]["status"] = "live"
    match_body = _body(match)
    archive["match_body_sha256"] = hashlib.sha256(match_body).hexdigest()
    with pytest.raises(ArchiveGateError, match="source match must be finished"):
        _validate((rights, archive, match_body, statistics_body, None, None))

    rights, archive, match_body, statistics_body, match, _ = _bundle()
    match["data"]["score"] = None
    match_body = _body(match)
    archive["match_body_sha256"] = hashlib.sha256(match_body).hexdigest()
    with pytest.raises(ArchiveGateError, match="both final scores"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_statistics_unavailable_is_rejected():
    rights, archive, match_body, statistics_body, _, statistics = _bundle()
    statistics["meta"]["available"] = False
    statistics_body = _body(statistics)
    archive["statistics_body_sha256"] = hashlib.sha256(statistics_body).hexdigest()
    with pytest.raises(ArchiveGateError, match="statistics are unavailable"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_team_identity_mismatch_is_rejected():
    rights, archive, match_body, statistics_body, _, statistics = _bundle()
    statistics["data"]["home"]["team_id"] = "wrong-team"
    statistics_body = _body(statistics)
    archive["statistics_body_sha256"] = hashlib.sha256(statistics_body).hexdigest()
    with pytest.raises(ArchiveGateError, match="team IDs do not match"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_missing_stat_fields_remain_missing_and_are_never_zero_filled():
    rights, archive, match_body, statistics_body, _, statistics = _bundle()
    del statistics["data"]["home"]["corner_kicks"]
    statistics["data"]["away"]["red_cards"] = None
    statistics_body = _body(statistics)
    archive["statistics_body_sha256"] = hashlib.sha256(statistics_body).hexdigest()
    result = _validate((rights, archive, match_body, statistics_body, None, None))
    assert result["missing_stat_fields"] == ["home.corner_kicks", "away.red_cards"]
    assert result["feature_values_imputed"] is False


def test_private_storage_and_no_public_raw_artifact_are_mandatory():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["storage_visibility"] = "public"
    with pytest.raises(ArchiveGateError, match="raw source storage must be private"):
        _validate((rights, archive, match_body, statistics_body, None, None))

    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["public_raw_artifact_uploaded"] = True
    with pytest.raises(ArchiveGateError, match="public raw-source artifact"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_paid_plan_or_paid_calls_are_rejected():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["provider_plan"] = "solo"
    with pytest.raises(ArchiveGateError, match="Free plan"):
        _validate((rights, archive, match_body, statistics_body, None, None))

    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["paid_provider_calls"] = 1
    with pytest.raises(ArchiveGateError, match="paid provider calls"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_wrong_candidate_and_same_source_target_match_are_rejected():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["candidate_sha256"] = "0" * 64
    with pytest.raises(ArchiveGateError, match="candidate SHA-256"):
        _validate((rights, archive, match_body, statistics_body, None, None))

    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["target_match_id"] = archive["source_match_id"]
    with pytest.raises(ArchiveGateError, match="must differ"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_naive_timestamps_are_rejected():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["match_received_at_utc"] = "2026-11-10T20:00:00"
    with pytest.raises(ArchiveGateError, match="offset-aware UTC timestamp"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_receipt_must_follow_the_source_match_kickoff():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["match_received_at_utc"] = "2026-11-10T18:59:59Z"
    with pytest.raises(ArchiveGateError, match="source receipts must follow"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_non_serie_a_and_wrong_source_endpoint_are_rejected():
    rights, archive, match_body, statistics_body, match, _ = _bundle()
    match["data"]["league"] = "Premier League"
    match_body = _body(match)
    archive["match_body_sha256"] = hashlib.sha256(match_body).hexdigest()
    with pytest.raises(ArchiveGateError, match="Serie A"):
        _validate((rights, archive, match_body, statistics_body, None, None))

    rights, archive, match_body, statistics_body, *_ = _bundle()
    archive["statistics_endpoint"] = "/v1/matches/source-match-1/odds"
    with pytest.raises(ArchiveGateError, match="unexpected statistics endpoint"):
        _validate((rights, archive, match_body, statistics_body, None, None))


def test_quote_fixture_identity_must_match_the_target_match():
    with pytest.raises(ArchiveGateError, match="quote match ID does not match"):
        _validate(quote_match_id="different-target")


def test_provider_rights_manifest_must_name_big_balls():
    rights, archive, match_body, statistics_body, *_ = _bundle()
    rights["provider"] = "Another Provider"
    with pytest.raises(ArchiveGateError, match="does not match Big Balls"):
        _validate((rights, archive, match_body, statistics_body, None, None))
