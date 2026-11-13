"""Offline guard for the SportsAPI Pro source audit; never calls the provider."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
MANIFEST_PATH = ROOT / "research/source_rights/sportsapipro.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_sportsapipro_manifest_is_hold_only_and_preserves_original_v2():
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
    assert manifest["project_authorization"]["inference_authorized"] is False
    assert manifest["project_authorization"]["paid_calls_authorized"] is False
    assert manifest["project_authorization"]["supabase_writes_authorized"] is False


def test_exact_19_feature_mapping_is_ordered_and_complete():
    candidate = _load(CANDIDATE_PATH)
    manifest = _load(MANIFEST_PATH)
    mapped = [item["feature"] for item in manifest["feature_mapping"]]

    assert mapped == candidate["features"]
    assert len(mapped) == 19
    assert len(set(mapped)) == 19


def test_free_rights_do_not_override_private_storage_and_provenance_gates():
    manifest = _load(MANIFEST_PATH)

    assert manifest["free_plan"]["requests_per_day"] == 100
    assert manifest["free_plan"]["requests_per_minute"] == 10
    assert manifest["free_plan"]["all_endpoints"] is True
    assert manifest["free_plan"]["all_competitions"] is True
    assert manifest["free_plan"]["duration_status"] == "UNCONFIRMED"

    assert manifest["terms"]["applies_to_free_accounts"] is True
    assert manifest["terms"]["internal_modeling_machine_learning_backtesting_permitted"] is True
    assert manifest["terms"]["raw_response_private_internal_retention_permitted"] is True
    assert manifest["terms"]["raw_response_publication_or_bulk_redistribution_permitted"] is False

    assert manifest["provenance"]["per_field_upstream_observation_timestamp_documented"] is False
    assert manifest["provenance"]["source_before_quote_approved"] is False
    assert manifest["private_storage"]["private_archive_storage_required"] is True
    assert manifest["private_storage"]["private_archive_storage_verified"] is False
    assert manifest["private_storage"]["private_archive_storage_authorized"] is False
    assert manifest["private_storage"]["storage_inventory_checked"] is False
    assert manifest["private_storage"]["public_github_raw_artifact_allowed"] is False
    assert manifest["coverage"]["second_yellow_mapping_documented"] is False
    assert manifest["coverage"]["current_2026_27_match_statistics_completeness_verified"] is False
    assert manifest["project_authorization"]["api_requests_authorized"] is False
