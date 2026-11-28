import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pitchapi_remains_hold_until_rights_fields_and_asof_provenance_are_verified():
    manifest = json.loads(
        (ROOT / "research/source_rights/pitchapi.json").read_text(encoding="utf-8")
    )
    assert manifest["approval_status"] == "HOLD"
    assert manifest["integration_authorized"] is False
    assert manifest["api_data_terms_url"] is None
    assert manifest["api_data_license"] is None
    assert manifest["sdk_license"] == "MIT"
    assert manifest["sdk_license_covers_returned_data"] is False
    assert manifest["upstream_provider_identity_disclosed"] is False
    assert manifest["commercial_internal_model_use_explicitly_permitted"] is False
    assert manifest["private_raw_response_retention_explicitly_permitted"] is False
    assert manifest["documented_corners_field"] is False
    assert manifest["historical_per_match_first_observed_timestamp"] is False
    assert manifest["historical_correction_timestamp"] is False
    assert manifest["source_before_quote_proven"] is False
    assert manifest["serie_a_2026_27_field_coverage_verified"] is False
    assert manifest["frozen_v2_19_feature_parity_verified"] is False
    assert manifest["api_requests_made"] == 0
    assert manifest["api_key_created"] is False
    assert manifest["data_downloads"] == 0
    assert manifest["supabase_accessed"] is False
    assert manifest["supabase_writes"] == 0
    assert manifest["supabase_ddl"] == 0
    assert manifest["protected_outcomes_read"] is False
    assert manifest["feature_calculations"] == 0
    assert manifest["inference_runs"] == 0
    assert manifest["production_pickle_changed"] is False


def test_pitchapi_free_tier_limits_and_plan_positioning_are_accurate():
    manifest = json.loads(
        (ROOT / "research/source_rights/pitchapi.json").read_text(encoding="utf-8")
    )
    assert manifest["free_price_eur"] == 0
    assert manifest["free_daily_request_limit"] == 15000
    assert manifest["free_sustained_requests_per_minute"] == 600
    assert manifest["free_live_snapshot_requests_per_minute"] == 60
    assert manifest["free_usage_scope"] == "side_projects_research_and_evaluation"
    assert manifest["paid_tier_exists"] is True
    assert manifest["pro_monthly_price_eur"] == 4.99
    assert manifest["pro_unlimited_requests_claimed"] is True
    assert manifest["pro_usage_scope"] == "products_and_daily_pipelines"
    assert manifest["pro_product_daily_pipeline_positioned"] is True
    assert manifest["pro_commercial_use_explicitly_permitted"] is False
    assert manifest["free_commercial_use_explicitly_permitted"] is False
    assert manifest["commercial_use_scope_explicitly_defined"] is False


def test_pitchapi_audit_does_not_change_the_original_v2_candidate():
    candidate = json.loads(
        (ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json").read_text(
            encoding="utf-8"
        )
    )
    assert candidate["artifact_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0.0
    assert candidate["shadow_residual_lambda"] == 1.0
    assert candidate["research_only"] is True
