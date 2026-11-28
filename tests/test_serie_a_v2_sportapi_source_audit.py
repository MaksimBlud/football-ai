import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "research" / "SERIE_A_V2_SPORTAPI_FREE_SOURCE_AUDIT_20261128.md"
RIGHTS = ROOT / "research" / "source_rights" / "sportapi_ai_20261128.json"
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-v2-sportapi-source-audit.yml"


def test_audit_is_pinned_to_original_frozen_v2_only():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    model = audit["original_v2"]
    assert model["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert model["candidate_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert model["training_fingerprint_sha256"] == (
        "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    )
    assert model["training_rows"] == 3799
    assert model["feature_count"] == 19
    assert model["weight_matrix_shape"] == [20, 2]
    assert model["active_lambda"] == 0
    assert model["shadow_residual_lambda"] == 1
    assert model["stability_gate_passed"] is False
    assert model["eligible_completed_primary_forecasts_observed"] == 0
    assert model["outcome_read_gate_open"] is False


def test_free_plan_claims_are_not_mistaken_for_authenticated_serie_a_coverage():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    free = audit["free_plan"]
    assert free["price_usd_per_month"] == 0
    assert free["requests_per_day"] == 1000
    assert free["requests_per_month"] == 7000
    assert free["all_endpoints_claimed"] is True
    assert free["all_leagues_claimed"] is True
    assert free["serie_a_listed"] is True
    assert free["exact_serie_a_2026_27_match_stats_coverage_verified"] is False
    assert free["exact_historical_season_depth_verified"] is False
    assert free["per_fixture_stats_completeness_verified"] is False
    assert free["odds_available"] is False


def test_six_original_corner_features_remain_uncovered_without_substitution():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    coverage = audit["feature_coverage"]
    expected = {
        "diff_corners_for_5",
        "diff_corners_for_10",
        "diff_corners_against_5",
        "diff_corners_against_10",
        "diff_corners_for_venue5",
        "diff_corners_against_venue5",
    }
    assert coverage["required_corner_feature_count"] == 6
    assert set(coverage["required_corner_features"]) == expected
    assert coverage["documented_corner_source_fields"] == []
    assert coverage["missing_required_feature_count"] == 6
    assert coverage["exact_original_19_feature_parity_verified"] is False
    assert coverage["feature_substitution_authorized"] is False
    assert coverage["alternate_imputation_authorized"] is False
    assert audit["documented_data"]["corners_field_documented"] is False


def test_rights_and_provenance_are_not_overstated():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    rights = audit["rights"]
    assert rights["own_websites_apps_analysis_and_products_permitted_by_terms"] is True
    assert rights["raw_data_feed_redistribution_prohibited"] is True
    assert rights["explicit_internal_ml_training_permission"] is False
    assert rights["explicit_internal_model_inference_permission"] is False
    assert rights["explicit_private_raw_response_retention_permission"] is False
    assert rights["upstream_provider_identity_and_field_level_rights_verified"] is False
    provenance = audit["provenance"]
    assert provenance["fixture_updated_at_example_present"] is True
    assert provenance["source_first_observed_timestamp_documented"] is False
    assert provenance["per_field_correction_timestamp_documented"] is False
    assert provenance["source_before_quote_evidence_exists"] is False


def test_audit_is_fail_closed_and_records_no_provider_or_database_actions():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    assert audit["decision"] == "HOLD_INCOMPLETE_FEATURE_COVERAGE_AND_UPSTREAM_RIGHTS"
    assert audit["integration_authorized"] is False
    actions = audit["non_actions"]
    assert actions["account_created"] is False
    assert actions["api_key_created"] is False
    assert actions["api_requests"] == 0
    assert actions["source_downloads"] == 0
    assert actions["paid_provider_calls"] == 0
    assert actions["odds_requests"] == 0
    assert actions["supabase_accessed"] is False
    assert actions["supabase_reads"] == 0
    assert actions["supabase_writes"] == 0
    assert actions["supabase_ddl"] == 0
    assert actions["quote_reads"] == 0
    assert actions["feature_calculation"] is False
    assert actions["inference"] is False
    assert actions["target_outcomes_read"] is False
    assert actions["training_or_refit"] is False
    assert actions["production_pickle_changes"] is False
    assert actions["original_v2_contract_changes"] is False
    assert actions["schedule_changes"] is False
    assert actions["main_changes"] is False
    assert actions["merge_performed"] is False


def test_report_and_offline_ci_are_present_without_live_access():
    document = DOC.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "HOLD_INCOMPLETE_FEATURE_COVERAGE_AND_UPSTREAM_RIGHTS" in document
    assert "diff_corners_for_5" in document
    assert "source-before-quote" in document
    assert "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6" in document
    assert "schedule:" not in workflow
    assert "secrets." not in workflow
    assert "SUPABASE" not in workflow
    assert "ODDS_API" not in workflow
    assert "persist-credentials: false" in workflow
    assert "de0fac2e4500dabe0009e67214ff5f5447ce83dd" in workflow
    assert "83679a892e2d95755f2dac6acb0bfd1e9ac5d548" in workflow
    assert "pytest -q tests/test_serie_a_v2_sportapi_source_audit.py" in workflow
