from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research" / "source_rights" / "bigballsdata_20261124.json"
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


def test_free_plan_is_zero_cost_but_does_not_replace_original_training_or_odds():
    free = _load()["free_plan"]
    assert free["monthly_price_usd"] == 0
    assert free["requests_per_day"] == 1000
    assert free["bookmaker_odds_available"] is False
    assert free["free_season_scope_conflict_between_official_pages"] is True
    assert free["historical_training_corpus_2014_2026_available_on_free_plan"] is False


def test_schema_level_fields_map_to_original_feature_families_without_claiming_completeness():
    fields = _load()["documented_fields"]
    assert fields["score_supplies_goals_for_and_against"] is True
    assert fields["points_can_be_derived_from_completed_match_score"] is True
    assert fields["corner_kicks_field_documented"] is True
    assert fields["yellow_cards_field_documented"] is True
    assert fields["red_cards_field_documented"] is True
    assert fields["all_fixture_team_stat_fields_nullable"] is True
    assert fields["exact_serie_a_2026_27_per_fixture_completeness_verified"] is False
    assert fields["original_v2_full_19_feature_parity_verified"] is False


def test_provider_terms_allow_internal_models_but_upstream_rights_remain_unverified():
    rights = _load()["rights"]
    assert rights["private_api_response_storage_and_retention_permitted_by_provider_terms"] is True
    assert rights["internal_model_training_evaluation_and_backtesting_permitted_by_provider_terms"] is True
    assert rights["internal_model_use_as_input_permitted"] is True
    assert rights["internal_model_inference_explicitly_named_in_terms"] is False
    assert rights["derived_models_scores_predictions_and_aggregates_owned_by_customer_under_terms"] is True
    assert rights["raw_data_feed_redistribution_permitted"] is False
    assert rights["upstream_provider_identity_verified"] is False
    assert rights["upstream_field_level_rights_verified"] is False
    assert rights["written_upstream_rights_confirmation_required"] is True


def test_opaque_source_tier_and_missing_soccer_stats_timestamps_do_not_prove_provenance():
    provenance = _load()["provenance"]
    assert provenance["response_meta_source_is_opaque_tier_label"] is True
    assert provenance["response_meta_source_reveals_vendor_identity"] is False
    assert provenance["soccer_match_statistics_route_exposes_per_record_as_of"] is False
    assert provenance["provider_first_observed_timestamp_documented"] is False
    assert provenance["per_field_correction_timestamp_documented"] is False
    assert provenance["local_receipt_time_and_raw_sha256_can_prove_project_possession_before_quote_if_later_authorized"] is True
    assert provenance["source_before_quote_proven"] is False


def test_frozen_candidate_is_exact_and_unchanged():
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


def test_no_provider_access_or_model_operation_was_performed():
    auth = _load()["project_authorization"]
    assert auth["account_created"] is False
    assert auth["api_key_created"] is False
    assert auth["provider_api_requests"] == 0
    assert auth["source_download_performed"] is False
    assert auth["raw_source_sha256_captured"] is False
    assert auth["provider_specific_supabase_reads"] == 0
    assert auth["general_read_only_serie_a_prematch_odds_queries"] == 1
    assert auth["supabase_writes"] == 0
    assert auth["supabase_ddl"] == 0
    assert auth["protected_2026_27_outcomes_read"] is False
    assert auth["model_inference_performed"] is False
    assert auth["production_pickle_changed"] is False


def test_official_serie_a_page_has_cross_sport_and_count_integrity_red_flags():
    flags = _load()["public_page_integrity_flags"]
    assert flags["serie_a_page_latest_match_tile_contains_american_football_score_20_10"] is True
    assert flags["serie_a_page_latest_match_tile_mentions_soldier_field"] is True
    assert flags["serie_a_page_latest_match_tile_contains_q4_drive_and_nfl_team_text"] is True
    assert flags["serie_a_page_fantasy_tile_displays_nfl_player_names_and_metrics"] is True
    assert flags["serie_a_match_count_top_summary"] == 4941
    assert flags["serie_a_finished_match_count_archive_table"] == 4671
    assert flags["match_count_difference"] == 270
    assert flags["current_season_scheduled_unplayed_fixtures_explain_difference"] is True
    assert flags["published_match_count_conflict"] is False
    assert flags["severe_public_page_data_integrity_red_flag"] is True


def test_candidate_audit_does_not_authorize_integration():
    decision = _load()["decision"]
    assert decision["status"] == "HOLD_NO_INTEGRATION"
    assert decision["integration_allowed"] is False
    assert len(decision["reasons"]) >= 7
