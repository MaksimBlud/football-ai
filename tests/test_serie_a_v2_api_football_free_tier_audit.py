import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "source_rights" / "api_football.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"
PROTOCOL = ROOT / "experiments" / "market_anchor_1x2_v2_protocol.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_api_football_free_plan_does_not_cover_current_form_season():
    manifest = _json(MANIFEST)
    free = manifest["free_plan"]

    assert manifest["decision"] == "HOLD"
    assert free["price_usd_per_month"] == 0
    assert free["requests_per_day"] == 100
    assert free["season_access_rule"] == "Year-4 through Year-2"
    assert free["available_season_years_at_review"] == [2022, 2023, 2024]
    assert free["current_2026_2027_season_available"] is False


def test_api_football_rights_and_source_clock_remain_unapproved():
    manifest = _json(MANIFEST)

    assert manifest["serie_a_exact_19_feature_mapping_verified"] is False
    assert manifest["per_field_upstream_observation_or_correction_clock_verified"] is False
    assert manifest["rights"]["direct_data_resale_permitted"] is False
    assert manifest["rights"]["explicit_internal_ml_training_grant_found"] is False
    assert manifest["rights"]["explicit_private_raw_response_retention_grant_found"] is False
    assert manifest["rights"]["upstream_field_rights_verified"] is False
    assert manifest["authorization"] == {
        "account_created": False,
        "api_key_created": False,
        "api_requests_made": 0,
        "source_capture_permitted": False,
        "feature_inference_permitted": False,
        "quote_access_performed": False,
        "target_outcomes_read": False,
    }


def test_api_football_audit_cannot_mutate_original_v2_contract():
    manifest = _json(MANIFEST)
    candidate = _json(CANDIDATE)
    protocol = _json(PROTOCOL)

    assert manifest["original_v2_contract"]["candidate_sha256"] == candidate["artifact_sha256"]
    assert candidate["artifact_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["training_rows"] == 3799
    assert candidate["training_fingerprint_sha256"] == "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    assert candidate["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is False
    assert protocol["first_outcome_read_gate"]["completed_primary_events"] == 30
    assert protocol["first_outcome_read_gate"]["outcome_read_before_gate"] is False
    assert protocol["decision_policy"]["automatic_promotion"] is False
