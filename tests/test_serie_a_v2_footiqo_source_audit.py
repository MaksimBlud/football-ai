"""Offline guard for the Footiqo source audit; never accesses Footiqo."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
MANIFEST_PATH = ROOT / "research/source_rights/footiqo.json"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-footiqo-source-audit.yml"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_footiqo_audit_preserves_exact_frozen_v2_contract():
    candidate = _load(CANDIDATE_PATH)
    manifest = _load(MANIFEST_PATH)
    frozen = manifest["frozen_candidate"]

    assert candidate["experiment_id"] == "MARKET_ANCHOR_1X2_V2"
    assert candidate["artifact_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert candidate["training_fingerprint_sha256"] == "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    assert candidate["features"] == frozen["features"]
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is False


def test_visible_serie_a_fields_map_to_17_but_not_all_19_frozen_features():
    candidate = _load(CANDIDATE_PATH)
    manifest = _load(MANIFEST_PATH)
    mapping = manifest["feature_mapping"]
    assert [item["feature"] for item in mapping] == candidate["features"]

    results = [item for item in mapping if "points" in item["feature"] or "goals" in item["feature"]]
    corners = [item for item in mapping if "corners" in item["feature"]]
    yellow = [item for item in mapping if "yellow" in item["feature"]]
    red = [item for item in mapping if "red" in item["feature"]]

    assert len(results) == 9
    assert len(corners) == 6
    assert len(yellow) == 2
    assert len(red) == 2
    assert all(item["candidate_source_fields"] == ["FTHG", "FTAG", "FTR"] for item in results)
    assert all(item["candidate_source_fields"] == ["HCFT", "ACFT"] for item in corners)
    assert all(item["candidate_source_fields"] == ["HYCFT", "AYCFT"] for item in yellow)
    assert all(item["candidate_source_fields"] == [] for item in red)
    assert all(item["status"] == "not_documented_in_reviewed_serie_a_corners_cards_table" for item in red)

    coverage = manifest["coverage"]
    assert coverage["feature_mapping_candidate_count"] == 17
    assert coverage["full_19_feature_parity_verified"] is False
    assert coverage["red_card_field_documented_in_reviewed_serie_a_table"] is False


def test_dataset_policy_permits_noncommercial_ml_and_private_storage_but_not_unapproved_automation():
    manifest = _load(MANIFEST_PATH)
    rights = manifest["rights"]

    assert rights["dataset_policy_explicitly_permits_personal_noncommercial_research"] is True
    assert rights["dataset_policy_explicitly_permits_predictive_model_development_and_testing"] is True
    assert rights["dataset_policy_explicitly_permits_machine_learning_experiments"] is True
    assert rights["dataset_policy_explicitly_permits_calculated_features_and_probabilities"] is True
    assert rights["dataset_policy_explicitly_permits_private_storage_of_legitimately_obtained_files"] is True
    assert rights["dataset_policy_permits_manual_exports"] is True
    assert rights["dataset_policy_requires_written_authorization_for_automated_extraction"] is True
    assert rights["explicit_commercial_product_use_permission"] is False
    assert rights["upstream_field_level_rights_verified"] is False
    assert manifest["decision"] == "HOLD"


def test_free_public_pages_do_not_mean_automated_or_complete_data_access():
    manifest = _load(MANIFEST_PATH)
    access = manifest["free_access"]
    coverage = manifest["coverage"]

    assert access["public_serie_a_database_page"] is True
    assert access["current_season_2026_27_rows_visible"] is True
    assert access["manual_csv_excel_export_available"] is True
    assert access["manual_export_permitted_by_dataset_policy"] is True
    assert access["automated_export_without_written_authorization"] is False
    assert access["public_api_available"] is False
    assert access["free_downloads_are_samples"] is True
    assert access["complete_multiseason_historical_archive_free"] is False
    assert coverage["all_serie_a_2026_27_matches_complete_for_every_field_verified"] is False


def test_no_source_before_quote_or_sha_capture_is_claimed():
    manifest = _load(MANIFEST_PATH)
    provenance = manifest["provenance"]
    authorization = manifest["project_authorization"]

    assert provenance["public_statistics_page_claims_daily_updates"] is True
    assert provenance["per_match_source_observation_timestamp_documented"] is False
    assert provenance["per_field_source_observation_timestamp_documented"] is False
    assert provenance["per_match_correction_timestamp_documented"] is False
    assert provenance["project_receipt_timestamp_captured"] is False
    assert provenance["raw_source_sha256_captured"] is False
    assert provenance["source_before_quote_verified"] is False
    assert all(value is False for value in authorization.values())


def test_audit_workflow_is_secret_free_offline_and_has_no_schedule_or_provider_access():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" not in workflow
    assert "schedule:" not in workflow
    assert "secrets." not in workflow
    assert "footiqo.com" not in workflow
    assert "requests" not in workflow
    assert "curl " not in workflow
    assert "pytest -q tests/test_serie_a_v2_footiqo_source_audit.py" in workflow
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in workflow
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
