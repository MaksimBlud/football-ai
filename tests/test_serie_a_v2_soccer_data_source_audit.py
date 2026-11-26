from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research" / "source_rights" / "soccer_data_20261123.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"

EXPECTED_FEATURES = [
    "diff_points_5", "diff_points_10", "diff_points_venue5",
    "diff_goals_for_5", "diff_goals_for_10", "diff_goals_against_5",
    "diff_goals_against_10", "diff_corners_for_5", "diff_corners_for_10",
    "diff_corners_against_5", "diff_corners_against_10", "diff_yellow_5",
    "diff_yellow_10", "diff_red_5", "diff_red_10",
    "diff_goals_for_venue5", "diff_goals_against_venue5",
    "diff_corners_for_venue5", "diff_corners_against_venue5",
]


def _load():
    return json.loads(RIGHTS.read_text(encoding="utf-8"))


def test_free_plan_is_current_season_only_no_odds_and_bounded():
    free = _load()["free_plan"]
    assert free["monthly_price_usd"] == 0
    assert free["requests_per_day"] == 50
    assert free["requests_per_minute"] == 10
    assert free["season_scope"] == "current season only"
    assert free["all_stats_endpoints_included"] is True
    assert free["betting_odds_available"] is False
    assert free["api_key_required"] is True


def test_schema_fields_are_present_but_fixture_completeness_is_not_proven():
    fields = _load()["documented_fields"]
    assert all(fields[k] is True for k in (
        "match_results_and_goals", "standings_points", "corner_kicks",
        "yellow_cards", "red_cards", "schema_level_original_v2_feature_families_present",
    ))
    assert fields["exact_serie_a_2026_27_per_fixture_statistics_coverage_verified"] is False
    assert fields["all_19_feature_values_complete_for_every_required_fixture_verified"] is False


def test_rights_remain_hold_without_explicit_ml_and_upstream_clearance():
    audit = _load()
    rights = audit["rights"]
    assert audit["candidate_status"] == "HOLD_NO_INTEGRATION"
    assert rights["data_owned_by_provider_or_licensed_third_parties"] is True
    assert rights["license_nonexclusive_and_nontransferable"] is True
    assert rights["cache_and_store_while_account_and_plan_active"] is True
    assert rights["display_in_own_websites_apps_and_services_permitted"] is True
    assert rights["raw_data_redistribution_permitted"] is False
    assert rights["license_ends_when_account_or_terms_end"] is True
    assert rights["explicit_internal_ml_training_permission"] is False
    assert rights["explicit_internal_ml_inference_permission"] is False
    assert rights["upstream_provider_identity_verified"] is False
    assert rights["upstream_field_level_rights_verified"] is False
    assert rights["authorization"] is None


def test_local_receipt_time_and_sha_do_not_prove_upstream_first_observation():
    provenance = _load()["provenance"]
    assert provenance["provider_first_observed_timestamp_documented"] is False
    assert provenance["per_field_correction_timestamp_documented"] is False
    assert provenance["stats_may_arrive_late_or_change_after_event"] is True
    assert provenance["project_receipt_time_and_sha256_can_be_recorded_if_later_authorized"] is True
    assert provenance["source_before_quote_proven"] is False


def test_free_plan_does_not_resolve_original_training_corpus_rights():
    corpus = _load()["original_training_corpus"]
    assert corpus["source"] == "Football-Data.co.uk"
    assert corpus["training_corpus_rights_resolved"] is False
    assert corpus["free_plan_can_replace_2016_2026_training_history"] is False
    assert corpus["model_refit_or_weight_change_allowed"] is False


def test_original_frozen_candidate_is_pinned_and_unchanged():
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


def test_no_provider_specific_access_was_performed():
    auth = _load()["project_authorization"]
    assert auth["account_created"] is False
    assert auth["api_key_created"] is False
    assert auth["api_requests"] == 0
    assert auth["source_download_performed"] is False
    assert auth["raw_source_sha256_captured"] is False
    assert auth["provider_audit_supabase_reads"] == 0
    assert auth["supabase_writes"] == 0
    assert auth["supabase_ddl"] == 0
    assert auth["protected_2026_27_evaluation_outcomes_read"] is False
    assert auth["model_inference_performed"] is False
    assert auth["production_pickle_changed"] is False


def test_candidate_audit_does_not_authorize_integration():
    decision = _load()["decision"]
    assert decision["status"] == "HOLD_NO_INTEGRATION"
    assert decision["integration_allowed"] is False
    assert len(decision["reasons"]) >= 6
