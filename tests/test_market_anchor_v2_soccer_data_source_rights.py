"""Offline rights and frozen-contract guard for the Soccer Data source audit."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "source_rights" / "soccer_data_co.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-v2-soccer-data-source-audit.yml"

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


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_soccer_data_candidate_is_fail_closed_until_rights_and_coverage_clear():
    manifest = _json(MANIFEST)
    assert manifest["decision"] == "HOLD"
    assert manifest["free_plan"]["price_usd"] == 0
    assert manifest["free_plan"]["requests_per_day"] == 50
    assert manifest["free_plan"]["requests_per_minute"] == 10
    assert manifest["free_plan"]["current_season_only"] is True
    assert manifest["free_plan"]["odds_available"] is False

    terms = manifest["terms"]
    assert terms["explicit_internal_ml_training_permission_found"] is False
    assert terms["explicit_internal_ml_inference_permission_found"] is False
    assert terms["upstream_provider_names_disclosed"] is False
    assert terms["retention_after_account_or_plan_termination_permitted"] is False

    coverage = manifest["coverage"]
    assert coverage["current_2026_27_serie_a_per_match_stats_coverage_verified"] is False
    assert coverage["free_plan_satisfies_existing_11_file_contract"] is False

    provenance = manifest["provenance"]
    assert provenance["per_field_upstream_observation_timestamp_documented"] is False
    assert provenance["per_field_correction_history_documented"] is False
    assert provenance["raw_response_receipt_timestamp_and_sha_can_prove_project_possession_before_quote"] is True
    assert provenance["source_before_quote_approved"] is False

    privacy = manifest["private_storage"]
    assert privacy["private_raw_archive_required"] is True
    assert privacy["public_github_raw_artifact_allowed"] is False
    assert privacy["private_archive_storage_authorized"] is False

    authorization = manifest["project_authorization"]
    assert all(value is False for value in authorization.values())
    assert manifest["request_budget_estimate"]["provider_api_calls_made"] == 0
    assert manifest["non_results"]["model_inference_run"] is False
    assert manifest["non_results"]["target_outcomes_read"] is False


def test_original_market_anchor_v2_candidate_is_unchanged_and_pinned():
    candidate = _json(CANDIDATE)
    manifest = _json(MANIFEST)
    frozen = manifest["frozen_candidate"]

    assert candidate["artifact_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert candidate["features"] == EXPECTED_FEATURES
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0
    assert candidate["shadow_residual_lambda"] == 1
    assert candidate["stability_gate_passed"] is False

    assert frozen["candidate_sha256"] == candidate["artifact_sha256"]
    assert frozen["features"] == candidate["features"]
    assert frozen["feature_count"] == 19
    assert frozen["weights_shape"] == [20, 2]
    assert frozen["active_lambda"] == 0
    assert frozen["shadow_residual_lambda"] == 1
    assert frozen["stability_gate_passed"] is False


def test_free_quota_estimate_is_conservative_and_does_not_create_extra_accounts():
    manifest = _json(MANIFEST)
    budget = manifest["request_budget_estimate"]
    assert budget["project_serie_a_canonical_completed_fixture_metadata_count"] == 110
    assert budget["estimated_match_stats_calls"] == 110
    assert budget["free_requests_per_day"] == 50
    assert budget["minimum_utc_days_for_110_stats_calls"] == math.ceil(110 / 50) == 3
    assert budget["estimate_only"] is True
    assert budget["provider_api_calls_made"] == 0


def test_audit_workflow_is_offline_only_and_has_no_schedule_or_credentials():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "schedule:" not in workflow
    assert "workflow_dispatch:" not in workflow
    assert "secrets." not in workflow
    assert "SUPABASE" not in workflow
    assert "SOCCER_DATA_KEY" not in workflow
    assert "curl " not in workflow
    assert "requests.get" not in workflow
    assert "actions/upload-artifact" not in workflow
    assert "permissions:\n  contents: read" in workflow
