"""Offline guard for TheSportsDB source audit; never calls the provider."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
MANIFEST_PATH = ROOT / "research/source_rights/thesportsdb.json"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-thesportsdb-source-audit.yml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_thesportsdb_audit_preserves_exact_frozen_v2_contract():
    candidate = _load(CANDIDATE_PATH)
    manifest = _load(MANIFEST_PATH)
    frozen = manifest["frozen_candidate"]

    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert candidate["features"] == frozen["features"]
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is False


def test_free_event_stats_sample_does_not_prove_corners_or_card_parity():
    manifest = _load(MANIFEST_PATH)
    candidate = _load(CANDIDATE_PATH)
    mapping = manifest["feature_mapping"]
    assert [x["feature"] for x in mapping] == candidate["features"]

    corners = [x for x in mapping if "corners" in x["feature"]]
    cards = [x for x in mapping if "yellow" in x["feature"] or "red" in x["feature"]]
    assert len(corners) == 6
    assert all(x["status"] == "not_documented_in_free_sample" for x in corners)
    assert len(cards) == 4
    assert all(x["status"] == "not_verified" for x in cards)

    coverage = manifest["coverage"]
    assert coverage["event_stats_documented"] is True
    assert coverage["free_event_stats_sample_row_count"] == 5
    assert coverage["free_event_stats_sample_names"] == [
        "Shots on Goal", "Shots off Goal", "Total Shots",
        "Blocked Shots", "Shots insidebox",
    ]
    assert coverage["corner_count_key_documented"] is False
    assert coverage["yellow_card_stat_key_documented"] is False
    assert coverage["red_card_stat_key_documented"] is False


def test_provider_terms_are_partial_and_third_party_rights_keep_hold():
    manifest = _load(MANIFEST_PATH)
    rights = manifest["rights"]
    assert rights["api_content_copy_modify_allowed_by_provider_terms"] is True
    assert rights["official_terms_require_third_party_owner_permission_or_legal_basis"] is True
    assert rights["third_party_identifier_field_observed"] == "idApiFootball"
    assert rights["upstream_provider_identity_verified"] is False
    assert rights["upstream_data_license_verified"] is False
    assert rights["explicit_internal_ml_training_permission"] is False
    assert rights["explicit_model_inference_permission"] is False
    assert rights["explicit_private_raw_response_retention_permission"] is False
    assert rights["rights_status"].endswith("UNKNOWN_NOT_APPROVED")
    assert manifest["decision"] == "HOLD"


def test_free_api_limits_and_serie_a_page_are_not_misrepresented_as_complete_api_coverage():
    manifest = _load(MANIFEST_PATH)
    free = manifest["free_plan"]
    coverage = manifest["coverage"]
    assert free["documented_free_rate_limit_per_minute"] == 30
    assert free["event_stats_free_limit"] == 5
    assert free["event_stats_premium_limit"] == 100
    assert free["v1_legacy"] is True
    assert free["v2_premium_only"] is True
    assert coverage["serie_a_2026_27_public_season_page_exists"] is True
    assert coverage["serie_a_2026_27_page_event_count_claimed"] == 380
    assert coverage["serie_a_2026_27_api_coverage_verified"] is False
    assert coverage["event_stats_available_for_all_serie_a_fixtures_verified"] is False


def test_no_source_before_quote_or_project_authorization_is_claimed():
    manifest = _load(MANIFEST_PATH)
    provenance = manifest["provenance"]
    auth = manifest["project_authorization"]
    assert provenance["per_field_upstream_observation_timestamp_documented"] is False
    assert provenance["per_field_correction_timestamp_documented"] is False
    assert provenance["source_before_quote_approved"] is False
    assert provenance["raw_response_sha_capture_verified"] is False
    assert all(value is False for value in auth.values())


def test_audit_workflow_is_secret_free_offline_and_has_no_schedule_or_dispatch():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" not in workflow
    assert "schedule:" not in workflow
    assert "secrets." not in workflow
    assert "api.thesportsdb.com/api/" not in workflow
    assert "requests" not in workflow
    assert "pytest -q tests/test_serie_a_v2_thesportsdb_source_audit.py" in workflow
