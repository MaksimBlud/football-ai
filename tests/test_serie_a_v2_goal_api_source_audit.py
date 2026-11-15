"""Offline guard for the GOAL API source audit; never calls the provider."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
MANIFEST_PATH = ROOT / "research/source_rights/goal_api.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_goal_api_source_remains_hold_and_no_live_access_is_authorized():
    manifest = _load(MANIFEST_PATH)
    assert manifest["provider"] == "GOAL API"
    assert manifest["decision"] == "HOLD"
    assert manifest["provenance"]["source_before_quote_approved"] is False
    assert manifest["private_storage"]["private_archive_storage_authorized"] is False
    assert manifest["terms"]["customer_license_to_underlying_sports_data_granted"] is False
    assert manifest["terms"]["ai_model_training_explicitly_permitted"] is False
    assert manifest["terms"]["model_inference_explicitly_permitted"] is False
    assert manifest["terms"]["private_raw_response_retention_explicitly_permitted"] is False
    assert manifest["coverage"]["current_2026_27_match_statistics_completeness_verified"] is False
    assert manifest["project_authorization"] == {
        "account_creation_authorized": False,
        "api_key_creation_authorized": False,
        "api_requests_authorized": False,
        "data_download_authorized": False,
        "raw_response_retention_authorized": False,
        "feature_build_authorized": False,
        "inference_authorized": False,
        "target_outcome_reads_authorized": False,
        "paid_calls_authorized": False,
        "supabase_writes_authorized": False,
        "supabase_ddl_authorized": False,
    }
    assert manifest["provider_api_calls_made"] == 0
    assert manifest["source_downloads_made"] == 0
    assert manifest["supabase_writes_made"] == 0
    assert manifest["target_outcomes_read"] is False
    assert manifest["model_inference_executed"] is False


def test_goal_api_audit_preserves_exact_original_v2_candidate_contract():
    candidate = _load(CANDIDATE_PATH)
    manifest = _load(MANIFEST_PATH)
    expected_features = [
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

    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert candidate["training_fingerprint_sha256"] == (
        "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    )
    assert candidate["training_rows"] == 3799
    assert candidate["features"] == expected_features
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0.0
    assert candidate["shadow_residual_lambda"] == 1.0
    assert candidate["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is False
    assert manifest["frozen_candidate"]["candidate_sha256"] == candidate["artifact_sha256"]
    assert manifest["frozen_candidate"]["feature_count"] == len(expected_features)
    assert manifest["frozen_candidate"]["weights_shape"] == [20, 2]
