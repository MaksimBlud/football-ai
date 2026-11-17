"""Offline guard for the PitchAPI source audit; never calls the provider."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
MANIFEST_PATH = ROOT / "research/source_rights/pitchapi.json"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-pitchapi-source-audit.yml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_pitchapi_candidate_is_hold_only_and_preserves_frozen_v2():
    candidate = _load(CANDIDATE_PATH)
    manifest = _load(MANIFEST_PATH)

    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert candidate["features"] == manifest["frozen_candidate"]["features"]
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is False

    assert manifest["decision"] == "HOLD"
    assert manifest["project_authorization"]["account_creation_authorized"] is False
    assert manifest["project_authorization"]["api_requests_authorized"] is False
    assert manifest["project_authorization"]["source_download_authorized"] is False
    assert manifest["project_authorization"]["inference_authorized"] is False
    assert manifest["project_authorization"]["paid_calls_authorized"] is False
    assert manifest["project_authorization"]["supabase_writes_authorized"] is False
    assert manifest["project_authorization"]["supabase_ddl_authorized"] is False


def test_pitchapi_does_not_document_all_frozen_feature_families():
    manifest = _load(MANIFEST_PATH)
    candidate = _load(CANDIDATE_PATH)

    mapped = [item["feature"] for item in manifest["feature_mapping"]]
    assert mapped == candidate["features"]
    assert len(mapped) == 19
    assert len(set(mapped)) == 19

    corner_features = [item for item in manifest["feature_mapping"] if "corners" in item["feature"]]
    assert len(corner_features) == 6
    assert all(item["status"] == "not_documented" for item in corner_features)
    assert manifest["coverage"]["corner_count_key_documented"] is False
    assert manifest["coverage"]["serie_a_2026_27_coverage_verified"] is False


def test_unknown_data_rights_and_missing_source_provenance_keep_provider_blocked():
    manifest = _load(MANIFEST_PATH)

    assert manifest["terms"]["official_service_terms_found"] is False
    assert manifest["terms"]["official_data_license_found"] is False
    assert manifest["terms"]["sdk_mit_license_covers_client_source_only"] is True
    assert manifest["terms"]["sdk_mit_license_grants_underlying_data_rights"] is False
    assert manifest["terms"]["rights_status"] == "UNKNOWN_NOT_APPROVED"
    assert manifest["terms"]["explicit_internal_ml_training_permission"] is False
    assert manifest["terms"]["explicit_model_inference_permission"] is False
    assert manifest["terms"]["explicit_private_raw_response_retention_permission"] is False

    assert manifest["provenance"]["per_field_upstream_observation_timestamp_documented"] is False
    assert manifest["provenance"]["source_before_quote_approved"] is False
    assert manifest["private_storage"]["private_storage_authorized"] is False
    assert manifest["coverage"]["match_statistics_available_pre_match"] is False
    assert manifest["coverage"]["odds_endpoint_documented"] is False


def test_audit_workflow_is_secret_free_offline_and_has_no_schedule_or_dispatch():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" not in workflow
    assert "schedule:" not in workflow
    assert "PITCHAPI_API_KEY" not in workflow
    assert "secrets." not in workflow
    assert "api.pitchapi.dev" not in workflow
    assert "pytest -q tests/test_serie_a_v2_pitchapi_source_audit.py" in workflow
