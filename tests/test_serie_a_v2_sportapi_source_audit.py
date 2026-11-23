from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research" / "source_rights" / "sportapi_20261123.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"

EXPECTED_FEATURES = [
    "diff_points_5",
    "diff_points_10",
    "diff_points_venue5",
    "diff_goals_for_5",
    "diff_goals_for_10",
    "diff_goals_against_5",
    "diff_goals_against_10",
    "diff_corners_for_5",
    "diff_corners_for_10",
    "diff_corners_against_5",
    "diff_corners_against_10",
    "diff_yellow_5",
    "diff_yellow_10",
    "diff_red_5",
    "diff_red_10",
    "diff_goals_for_venue5",
    "diff_goals_against_venue5",
    "diff_corners_for_venue5",
    "diff_corners_against_venue5",
]


def _load():
    return json.loads(RIGHTS.read_text(encoding="utf-8"))


def test_sportapi_remains_hold_until_ml_upstream_and_retention_rights_are_clear():
    audit = _load()
    assert audit["candidate_status"] == "HOLD_NO_INTEGRATION"
    rights = audit["rights"]
    assert rights["own_websites_apps_analysis_and_products_listed_as_permitted"] is True
    assert rights["explicit_internal_ml_training_permission"] is False
    assert rights["explicit_internal_ml_inference_permission"] is False
    assert rights["explicit_private_raw_response_retention_permission"] is False
    assert rights["upstream_provider_identity_verified"] is False
    assert rights["upstream_field_level_rights_verified"] is False
    assert rights["written_ai_use_upstream_and_retention_clarification_required"] is True


def test_free_plan_is_zero_cost_but_has_no_odds_and_a_december_limit_change():
    free = _load()["free_plan"]
    assert free["monthly_price_usd"] == 0
    assert free["requests_per_day_through_2026_11_30"] == 2000
    assert free["requests_per_month_through_2026_11_30"] == 14000
    assert free["requests_per_day_from_2026_12_01"] == 1000
    assert free["requests_per_month_from_2026_12_01"] == 7000
    assert free["all_endpoints_and_leagues_advertised"] is True
    assert free["betting_odds_available"] is False
    assert free["api_key_required"] is True


def test_documented_fields_do_not_prove_full_original_19_feature_parity():
    fields = _load()["documented_fields"]
    assert "points" in fields["standings"]
    assert "goals_for" in fields["standings"]
    assert "goals_against" in fields["standings"]
    assert "red_card" in fields["match_events"]
    assert "yellow_cards" in fields["fixture_stats"]
    assert fields["corners_documented_in_reviewed_match_stats_or_event_schema"] is False
    assert fields["original_v2_corner_feature_parity"] is False
    assert fields["original_v2_full_19_feature_parity_verified"] is False


def test_updated_at_is_not_misrepresented_as_first_observed_or_correction_time():
    provenance = _load()["provenance"]
    assert provenance["fixture_updated_at_utc_field_documented"] is True
    assert provenance["per_match_first_observation_timestamp_documented"] is False
    assert provenance["per_field_correction_timestamp_documented"] is False
    assert provenance["cache_age_or_provider_first_observed_semantics_documented"] is False
    assert provenance["source_before_quote_proven"] is False
    assert provenance["receipt_time_and_sha_would_prove_project_possession_not_provider_first_observation"] is True


def test_exact_original_candidate_is_pinned_and_unchanged():
    audit = _load()["frozen_candidate"]
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == audit["candidate_sha256"]
    assert candidate["training_fingerprint_sha256"] == audit["training_fingerprint_sha256"]
    assert candidate["features"] == EXPECTED_FEATURES
    assert len(candidate["features"]) == audit["feature_count"] == 19
    assert len(candidate["weights"]) == 20
    assert all(isinstance(row, list) and len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == audit["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == audit["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is audit["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is audit["automatic_promotion"] is False


def test_no_account_api_source_or_protected_outcome_access_was_performed():
    auth = _load()["project_authorization"]
    assert auth["account_created"] is False
    assert auth["api_key_created"] is False
    assert auth["api_requests"] == 0
    assert auth["source_download_performed"] is False
    assert auth["raw_source_sha256_captured"] is False
    assert auth["supabase_reads"] == 0
    assert auth["supabase_writes"] == 0
    assert auth["supabase_ddl"] == 0
    assert auth["protected_2026_27_outcomes_read"] is False
    assert auth["model_inference_performed"] is False
    assert auth["production_pickle_changed"] is False


def test_candidate_audit_does_not_authorize_integration():
    decision = _load()["decision"]
    assert decision["status"] == "HOLD_NO_INTEGRATION"
    assert decision["integration_allowed"] is False
    assert len(decision["reasons"]) >= 6
