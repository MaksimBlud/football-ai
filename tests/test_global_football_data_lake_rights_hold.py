"""Offline fail-closed regression for the Global Football Data Lake source audit."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research" / "source_rights" / "global_football_data_lake.json"


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_candidate_is_held_for_original_v2(manifest):
    assert manifest["schema_version"] == "MARKET_ANCHOR_1X2_V2_SOURCE_RIGHTS_AUDIT_V1"
    assert manifest["approval_status"] == "HOLD"
    assert manifest["rights"]["upstream_field_level_rights_cleared"] is False
    assert manifest["rights"]["internal_ml_use_explicitly_authorized"] is False
    assert manifest["rights"]["private_raw_archive_retention_explicitly_authorized"] is False


def test_aggregate_cc_by_claim_does_not_clear_mixed_upstream_sources(manifest):
    assert manifest["rights"]["publisher_license_claim"] == "CC-BY-4.0"
    assert manifest["rights"]["huggingface_license_metadata"] == "cc-by-4.0"
    assert manifest["rights"]["top_level_license_text_file_found"] is False
    providers = {item["provider"]: item["rights_status"] for item in manifest["upstream_sources"]}
    assert providers["API-Football"] == "HOLD"
    assert providers["Football-Data.co.uk"] == "NOT_APPROVED_FOR_AUTOMATED_AI_TRAINING"
    assert manifest["provenance"]["field_level_upstream_provider_lineage_confirmed"] is False


def test_derived_known_at_and_sparse_fetch_time_do_not_prove_source_before_quote(manifest):
    provenance = manifest["provenance"]
    assert provenance["known_at_semantics"] == "KICKOFF_PLUS_105_MINUTES_DERIVED_NOT_PROVIDER_OBSERVED"
    assert provenance["known_at_is_actual_capture_timestamp"] is False
    assert provenance["stats_fetched_at_null_fraction"] == pytest.approx(0.74)
    assert provenance["stats_fetched_at_is_complete"] is False
    assert provenance["source_observation_timestamp_available"] is False
    assert provenance["source_before_quote_proven"] is False


def test_current_season_and_exact_frozen_feature_parity_are_not_assumed(manifest):
    coverage = manifest["coverage"]
    assert coverage["current_2026_27_completed_stats_coverage_confirmed"] is False
    assert coverage["exact_original_19_feature_parity_confirmed"] is False
    assert coverage["repository_quality_report_generated_at"] == "2026-07-05T07:51:00Z"
    assert coverage["match_stats_null_percent"]["stats_fetched_at"] == 74.0


def test_original_v2_contract_and_lambdas_remain_frozen(manifest):
    v2 = manifest["frozen_v2"]
    assert v2["candidate_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert v2["candidate_git_blob_sha1"] == "ac1303f6b096664983fbf52443bd0a381b23ba21"
    assert v2["training_fingerprint_sha256"] == "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    assert v2["feature_count"] == 19
    assert v2["active_lambda"] == 0
    assert v2["shadow_lambda"] == 1
    assert v2["weights_changed"] is False
    assert v2["eligible_for_source_capture"] is False
    assert v2["eligible_for_inference"] is False
    assert v2["eligible_for_frozen_prospective_cohort"] is False
    assert v2["no_bet"] is True


def test_audit_did_not_download_data_or_access_supabase(manifest):
    actions = manifest["non_actions"]
    assert actions["provider_requests"] == 0
    assert actions["dataset_downloaded"] is False
    assert actions["api_key_created"] is False
    assert actions["supabase_accessed"] is False
    assert actions["protected_outcomes_read"] is False
    assert actions["model_inference_run"] is False
    assert actions["training_or_refit"] is False
    assert actions["production_artifact_changed"] is False
