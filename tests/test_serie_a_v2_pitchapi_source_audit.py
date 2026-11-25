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
