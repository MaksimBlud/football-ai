from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research" / "source_rights" / "bigballs_sports_data_20261124.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-v2-bigballs-source-audit.yml"

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


def load_audit():
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def test_provider_terms_are_promising_but_do_not_authorize_public_raw_redistribution():
    audit = load_audit()
    terms = audit["provider_terms"]
    assert terms["api_response_storage_permitted"] is True
    assert terms["internal_model_use_permitted"] is True
    assert terms["internal_training_evaluation_backtesting_permitted"] is True
    assert terms["raw_feed_resale_or_redistribution_permitted"] is False
    assert terms["raw_field_republication_permitted"] is False
    assert terms["upstream_provider_identity_and_field_level_rights_independently_verified"] is False
    assert terms["retention_after_account_closure_explicitly_defined"] is False
    assert terms["public_licence_notice_names_football_data_org"] is True
    assert terms["upstream_field_level_rights_independently_verified"] is False
    assert terms["upstream_sublicensing_authority_independently_verified"] is False


def test_match_statistics_endpoint_entitlement_conflict_remains_hold():
    free = load_audit()["free_plan"]
    assert free["monthly_price_usd"] == 0
    assert free["requests_per_day"] == 1000
    assert free["requests_per_minute"] == 100
    assert free["odds_available"] is False
    assert free["expected_goals_available_on_free"] is False
    assert free["match_statistics_endpoint_free_status"] == "CONFLICTING_OFFICIAL_DOCUMENTATION"
    assert free["openapi_endpoint_min_plan"] == "free"
    assert free["openapi_expected_goals_field_min_plan"] == "solo"
    assert free["serie_a_page_matrix_still_labels_statistics_endpoint"] is True
    assert free["endpoint_entitlement_status"] == "HOLD_REGISTRY_FREE_BUT_SERIE_A_MATRIX_EDGE_CONFLICT"
    assert free["endpoint_plan_conflict"] is True
    assert free["soccer_hub_endpoint_min_plan"] == "free"
    assert free["serie_a_page_matrix_endpoint_min_plan"] == "edge"
    assert free["soccer_hub_route_free"] is True
    assert free["serie_a_faq_route_free"] is True
    assert free["changelog_says_statistics_endpoint_free_from"] == "2026-11-11"
    assert free["season_depth_status"] == "CONFLICTING_GLOBAL_PRICING_BULLET_VS_SUMMARY_AND_SOCCER_SERIE_A_AUTHORITY_PAGES"
    assert free["global_pricing_summary_season_scope"] == "CURRENT_ONLY"
    assert free["global_pricing_free_bullet_season_scope"] == "CURRENT_PLUS_MOST_RECENT"
    assert free["soccer_hub_season_scope"] == "CURRENT_ONLY"
    assert free["current_plus_most_recent_season_advertised_on_global_pricing"] is True
    assert free["pricing_page_summary_says_current_season"] is True
    assert free["pricing_page_plan_bullet_says_current_plus_most_recent_season"] is True
    assert free["pricing_page_internal_season_depth_conflict"] is True
    assert free["serie_a_page_says_free_covers_current_season"] is True


def test_match_statistics_route_is_stored_post_match_and_not_a_live_pre_match_feed():
    audit = load_audit()
    free = audit["free_plan"]
    provenance = audit["provenance"]
    assert free["match_statistics_endpoint_mode"] == "STORED_ONLY_POST_MATCH"
    assert free["match_statistics_endpoint_updates_hourly"] is True
    assert free["upstream_posts_after_full_time_minutes_approx"] == 30
    assert provenance["statistics_endpoint_mode"] == "STORED_ONLY_POST_MATCH"
    assert provenance["statistics_endpoint_updates_hourly"] is True
    assert provenance["upstream_post_match_availability_delay_minutes_approx"] == 30
    assert provenance["per_match_first_observed_timestamp_semantics_documented"] is False
    assert provenance["per_field_correction_timestamp_semantics_documented"] is False
    assert provenance["local_receipt_time_and_sha_can_prove_project_possession_before_quote"] is True
    assert provenance["local_receipt_time_and_sha_prove_upstream_first_observation"] is False


def test_documented_stat_fields_cover_original_families_without_claiming_exact_19_parity():
    mapping = load_audit()["original_v2_feature_mapping"]
    fields = mapping["documented_source_fields"]
    assert "final match score" in fields["points"]
    assert "final score" in fields["goals_for_against"]
    assert fields["corners_for_against"] == "FixtureTeamStatistics.corner_kicks"
    assert fields["yellow_cards"] == "FixtureTeamStatistics.yellow_cards"
    assert fields["red_cards"] == "FixtureTeamStatistics.red_cards"
    assert mapping["feature_families_documented"] is True
    assert mapping["exact_19_feature_parity_verified"] is False
    assert "expected_goals" not in EXPECTED_FEATURES


def test_aggregate_team_stats_coverage_is_not_misrepresented_as_current_season_completeness():
    coverage = load_audit()["coverage"]
    assert coverage["all_seasons_finished_matches"] == 4591
    assert coverage["all_seasons_matches_with_team_stats"] == 4210
    assert round(coverage["all_seasons_team_stats_coverage"], 3) == 0.917
    assert coverage["current_2026_27_match_level_coverage"] == "UNKNOWN"
    assert coverage["field_level_corner_yellow_red_card_coverage"] == "UNKNOWN"


def test_source_receipt_time_and_sha_are_required_but_not_claimed_as_upstream_first_observation():
    provenance = load_audit()["provenance"]
    protocol = load_audit()["private_archive_protocol_if_later_authorized"]
    assert provenance["kickoff_utc_documented"] is True
    assert provenance["per_match_first_observed_timestamp_semantics_documented"] is False
    assert provenance["per_field_correction_timestamp_semantics_documented"] is False
    assert provenance["local_receipt_time_and_sha_can_prove_project_possession_before_quote"] is True
    assert provenance["local_receipt_time_and_sha_prove_upstream_first_observation"] is False
    assert protocol["preserve_exact_response_body_bytes"] is True
    assert protocol["record_local_receipt_time_utc"] is True
    assert protocol["sha256_exact_body_bytes"] is True
    assert protocol["require_capture_time_before_later_quote_snapshot"] is True
    assert protocol["store_only_in_private_repository_or_private_storage"] is True
    assert protocol["public_raw_artifact_upload_allowed"] is False


def test_original_frozen_v2_candidate_is_exact_and_unchanged():
    audit = load_audit()
    frozen = audit["frozen_candidate"]
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == frozen["candidate_sha256"]
    assert candidate["training_fingerprint_sha256"] == frozen["training_fingerprint_sha256"]
    assert candidate["features"] == EXPECTED_FEATURES
    assert len(candidate["features"]) == frozen["feature_count"] == 19
    assert len(candidate["weights"]) == 20
    assert all(isinstance(row, list) and len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == frozen["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == frozen["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is frozen["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is frozen["automatic_promotion"] is False


def test_no_account_key_request_download_or_model_operation_was_performed():
    auth = load_audit()["project_authorization"]
    assert auth["provider_account_created"] is False
    assert auth["provider_api_key_created"] is False
    assert auth["provider_api_requests"] == 0
    assert auth["provider_source_download_performed"] is False
    assert auth["provider_response_sha256_captured"] is False
    assert auth["supabase_reads_for_provider_audit"] == 0
    assert auth["supabase_writes"] == 0
    assert auth["supabase_ddl"] == 0
    assert auth["protected_2026_27_outcomes_read"] is False
    assert auth["model_inference_performed"] is False
    assert auth["model_refit_or_training_performed"] is False
    assert auth["production_pickle_changed"] is False


def test_audit_does_not_authorize_integration_or_change_project_training_policy():
    audit = load_audit()
    assert audit["decision"] == "HOLD_NO_INTEGRATION"
    assert audit["integration_allowed"] is False
    assert audit["automated_capture_authorized"] is False
    assert audit["frozen_inference_authorized"] is False
    assert audit["model_retraining_allowed_by_project"] is False


def test_isolated_validation_workflow_is_read_only_and_has_no_live_triggers_or_secrets():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for forbidden in ("schedule:", "workflow_run:", "workflow_dispatch:", "secrets.", "SUPABASE_", "upload-artifact"):
        assert forbidden not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "d23441a48e516b6c34aea4fa41551a30e30af803" in workflow
    assert "ece7cb06caefa5fff74198d8649806c4678c61a1" in workflow


def test_provider_plan_conflict_and_rights_manifest_pin_are_explicitly_recorded():
    audit = load_audit()
    assert audit["endpoint_plan_observations"]["openapi_minimum_plan"] == "free"
    assert audit["endpoint_plan_observations"]["soccer_hub_endpoint_table_minimum_plan"] == "free"
    assert audit["endpoint_plan_observations"]["serie_a_plan_matrix_minimum_plan"] == "edge"
    assert audit["endpoint_plan_observations"]["resolution"] == "CONFLICTING_OFFICIAL_DOCUMENTATION"
    assert audit["security_controls"]["canonical_rights_manifest_pinned_by_git_blob_sha1"] is True
    assert audit["security_controls"]["caller_supplied_rights_mapping_accepted"] is False


def test_2026_11_26_official_recheck_preserves_provider_hold_and_current_plan_conflicts():
    audit = load_audit()
    free = audit["free_plan"]
    coverage = audit["coverage"]
    provenance = audit["provenance"]
    assert free["free_plan_one_selected_sport_at_a_time"] is True
    assert free["free_plan_sport_scope_required_for_new_keys_since"] == "2026-10-26"
    assert free["free_plan_existing_keys_sport_scope_grace_end"] == "2026-11-24"
    assert free["changelog_free_sport_scope_effective_date"] == "2026-10-26"
    assert free["changelog_existing_free_key_scope_grace_end"] == "2026-11-24"
    assert free["free_plan_daily_request_limit"] == 1000
    assert free["free_plan_per_minute_limit"] == 100
    assert free["pricing_page_season_scope"] == "CURRENT_PLUS_MOST_RECENT"
    assert free["serie_a_page_season_scope"] == "CURRENT_ONLY"
    assert free["season_depth_status"] == "CONFLICTING_GLOBAL_PRICING_BULLET_VS_SUMMARY_AND_SOCCER_SERIE_A_AUTHORITY_PAGES"
    assert free["global_pricing_summary_season_scope"] == "CURRENT_ONLY"
    assert free["global_pricing_free_bullet_season_scope"] == "CURRENT_PLUS_MOST_RECENT"
    assert free["soccer_hub_season_scope"] == "CURRENT_ONLY"
    assert free["serie_a_page_statistics_matrix_min_plan"] == "edge"
    assert free["serie_a_page_statistics_faq_min_plan"] == "free"
    assert free["openapi_statistics_operation_min_plan"] == "free"
    assert free["endpoint_plan_conflict"] is True
    assert coverage["serie_a_page_current_season"] == "2026-27"
    assert coverage["current_2026_27_match_level_coverage"] == "UNKNOWN"
    assert coverage["field_level_corner_yellow_red_card_coverage"] == "UNKNOWN"
    assert provenance["post_match_corrections_possible"] is True
    assert provenance["per_match_first_observed_timestamp_semantics_documented"] is False
    assert audit["decision"] == "HOLD_NO_INTEGRATION"
    assert audit["integration_allowed"] is False
    assert audit["automated_capture_authorized"] is False
    assert audit["frozen_inference_authorized"] is False


def test_bigballs_20261126_openapi_recheck_keeps_hold():
    recheck_path = ROOT / "research/source_rights/bigballs_openapi_recheck_20261126.json"
    recheck = json.loads(recheck_path.read_text(encoding="utf-8"))
    audit = load_audit()

    endpoint = recheck["endpoint"]
    provenance = recheck["provenance"]
    rights = recheck["rights"]
    authorization = recheck["project_authorization"]

    assert recheck["decision"] == "HOLD_ENDPOINT_PLAN_CONFLICT_AND_PROVENANCE_LIMITS"
    assert endpoint["path"] == "/v1/matches/{id}/statistics"
    assert endpoint["openapi_min_plan"] == "free"
    assert endpoint["dedicated_serie_a_plan_matrix_min_plan"] == "edge"
    assert endpoint["dedicated_serie_a_faq_claim"] == "free"
    assert endpoint["plan_entitlement_resolved"] is False
    assert {"corner_kicks", "yellow_cards", "red_cards"} <= set(endpoint["documented_team_fields"])
    assert endpoint["route_is_post_match"] is True
    assert endpoint["route_fetches_upstream_at_request_time"] is False
    assert endpoint["expected_goals_field_min_plan"] == "solo"
    assert endpoint["free_plan_history_scope"] == "current season only"
    assert endpoint["current_serie_a_per_fixture_field_coverage_verified"] is False

    assert provenance["local_response_receipt_time_and_sha256_can_prove_project_possession_before_a_later_quote"] is True
    assert provenance["upstream_first_observation_timestamp_documented"] is False
    assert provenance["per_field_correction_timestamp_documented"] is False
    assert provenance["separate_stored_stats_route_freshness_basis"] == "ingested_at"
    assert provenance["separate_stored_stats_route_as_of_is_not_upstream_update_time"] is True

    assert rights["private_api_response_storage_permitted_by_terms"] is True
    assert rights["internal_model_training_evaluation_backtesting_permitted_by_terms"] is True
    assert rights["raw_feed_resale_or_redistribution_permitted"] is False
    assert rights["upstream_field_level_rights_independently_verified"] is False

    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert recheck["original_v2"]["candidate_sha256"] == candidate["artifact_sha256"]
    assert recheck["original_v2"]["feature_count"] == 19
    assert recheck["original_v2"]["weight_matrix_shape"] == [20, 2]
    assert recheck["original_v2"]["active_lambda"] == 0
    assert recheck["original_v2"]["shadow_lambda"] == 1
    assert audit["decision"] == "HOLD_NO_INTEGRATION"
    assert audit["integration_allowed"] is False
    assert audit["automated_capture_authorized"] is False
    assert audit["frozen_inference_authorized"] is False

    assert authorization["account_created"] is False
    assert authorization["api_key_created"] is False
    assert authorization["provider_data_api_requests"] == 0
    assert authorization["source_data_downloads"] == 0
    assert authorization["feature_calculations"] == 0
    assert authorization["inference_runs"] == 0
    assert authorization["supabase_writes"] == 0
    assert authorization["supabase_ddl"] == 0
    assert authorization["paid_calls"] == 0


def test_2026_11_27_current_serie_a_page_recheck_keeps_coverage_and_entitlement_hold():
    recheck = json.loads(
        (ROOT / "research/source_rights/bigballs_openapi_recheck_20261126.json").read_text(
            encoding="utf-8"
        )
    )
    page = recheck["follow_up_20261127_current_serie_a_page"]
    coverage = page["coverage_page"]

    assert page["current_season"] == "2026-27"
    assert page["season_count"] == 13
    assert page["total_matches_advertised"] == 4941
    assert page["finished_games_advertised"] == 4679
    assert page["current_season_clubs_represented"] == 20
    assert page["standings_source_as_of_utc"] == "2026-11-27T06:13:00Z"
    assert page["free_plan_scope_on_serie_a_page"] == "current season only"
    assert page["statistics_plan_matrix_minimum_plan"] == "edge"
    assert page["statistics_faq_route_claim"].startswith("free")
    assert page["openapi_and_endpoint_registry_minimum_plan"] == "free"
    assert page["endpoint_plan_conflict"] is True
    assert coverage["last_refreshed"] == "2026-11-06"
    assert coverage["soccer_team_stats_status"] == "partial"
    assert coverage["current_2026_27_per_fixture_field_coverage"] == "unknown"
    assert coverage["prior_reviewed_coverage_snapshot"]["matches_with_team_stats"] == 4210
    assert coverage["finished_match_count_difference_vs_current_serie_a_page"] == 88
    assert coverage["difference_reconciled_by_public_docs"] is False
    assert page["provider_api_request_made"] is False
    assert page["source_download_performed"] is False
    assert page["authenticated_free_response_reviewed"] is False
    assert page["integration_authorized"] is False
    assert page["decision"] == "HOLD_NO_INTEGRATION"
    assert recheck["decision"] == "HOLD_ENDPOINT_PLAN_CONFLICT_AND_PROVENANCE_LIMITS"


def test_2026_11_27_live_serie_a_endpoint_registry_follow_up_keeps_integration_on_hold():
    audit = load_audit()
    recheck_path = ROOT / "research/source_rights/bigballs_openapi_recheck_20261126.json"
    recheck = json.loads(recheck_path.read_text(encoding="utf-8"))
    follow_up = recheck["follow_up_20261127"]
    registry = follow_up["league_endpoint_registry"]

    assert registry["page_slug"] == "serie-a-api"
    assert registry["endpoint_path"] == "/v1/matches/{id}/statistics"
    assert registry["minimum_plan"] == "free"
    assert registry["registry_is_described_as_same_registry_enforced_by_gateway"] is True
    assert follow_up["dedicated_serie_a_capability_matrix_minimum_plan"] == "edge"
    assert follow_up["dedicated_serie_a_faq_route_claim"] == "free"
    assert follow_up["authenticated_free_plan_response_reviewed"] is False
    assert follow_up["provider_api_request_made"] is False
    assert follow_up["source_download_performed"] is False
    assert follow_up["decision"] == "HOLD_NO_INTEGRATION"

    assert audit["free_plan"]["league_endpoint_registry_statistics_min_plan"] == "free"
    assert audit["free_plan"]["endpoint_entitlement_status"] == "HOLD_REGISTRY_FREE_BUT_SERIE_A_MATRIX_EDGE_CONFLICT"
    assert audit["free_plan"]["endpoint_plan_conflict"] is True
    assert audit["coverage"]["coverage_page_team_stats_status"] == "PARTIAL"
    assert audit["coverage"]["current_2026_27_match_level_coverage"] == "UNKNOWN"
    assert audit["decision"] == "HOLD_NO_INTEGRATION"
    assert audit["integration_allowed"] is False
    assert audit["automated_capture_authorized"] is False
    assert audit["frozen_inference_authorized"] is False
