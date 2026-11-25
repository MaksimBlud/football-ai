"""Offline contract tests for the PitchAPI source-rights audit.

These tests do not contact PitchAPI, fetch football data, or create credentials.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/source_rights/pitchapi_20261125.json"
AUDIT_PATH = ROOT / "research/MARKET_ANCHOR_1X2_V2_PITCHAPI_SOURCE_AUDIT_20261125.md"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-pitchapi-source-audit.yml"
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"

EXPECTED_FEATURES = [
    "diff_points_5", "diff_points_10", "diff_points_venue5",
    "diff_goals_for_5", "diff_goals_for_10",
    "diff_goals_against_5", "diff_goals_against_10",
    "diff_corners_for_5", "diff_corners_for_10",
    "diff_corners_against_5", "diff_corners_against_10",
    "diff_yellow_5", "diff_yellow_10", "diff_red_5", "diff_red_10",
    "diff_goals_for_venue5", "diff_goals_against_venue5",
    "diff_corners_for_venue5", "diff_corners_against_venue5",
]
CORNER_FEATURES = [
    "diff_corners_for_5", "diff_corners_for_10",
    "diff_corners_against_5", "diff_corners_against_10",
    "diff_corners_for_venue5", "diff_corners_against_venue5",
]


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class PitchApiSourceAuditTests(unittest.TestCase):
    def test_published_free_plan_is_recorded_without_authorizing_use(self):
        free = load_manifest()["free_plan"]
        self.assertEqual(free["price_usd_monthly"], 0)
        self.assertFalse(free["paid_tier_advertised"])
        self.assertFalse(free["card_required"])
        self.assertEqual(free["request_allowance"], "unlimited")
        self.assertEqual(free["documented_league_count"], 77)
        self.assertEqual(free["documented_history_start_year"], 2021)
        self.assertTrue(free["api_key_required"])
        self.assertFalse(free["serie_a_2026_27_coverage_independently_verified"])

    def test_missing_corner_documentation_blocks_full_frozen_19_feature_coverage(self):
        data = load_manifest()["documented_data"]
        self.assertTrue(data["completed_match_stats_endpoint"])
        self.assertTrue(data["shot_endpoint_has_is_on_target"])
        self.assertTrue(data["shot_endpoint_has_expected_goals"])
        self.assertFalse(data["corner_count_field_documented"])
        self.assertFalse(data["complete_original_19_feature_coverage_proven"])
        self.assertEqual(data["missing_original_feature_family"], "corners_for_and_corners_against")

    def test_original_candidate_contract_is_pinned_and_unchanged(self):
        manifest = load_manifest()["original_v2_contract"]
        candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(candidate["experiment_id"], "MARKET_ANCHOR_1X2_V2")
        self.assertEqual(candidate["artifact_sha256"], manifest["candidate_sha256"])
        self.assertEqual(candidate["features"], EXPECTED_FEATURES)
        self.assertEqual(manifest["features"], EXPECTED_FEATURES)
        self.assertEqual(manifest["corner_features"], CORNER_FEATURES)
        self.assertEqual(len(candidate["features"]), 19)
        self.assertEqual(len(candidate["weights"]), 20)
        self.assertTrue(all(len(row) == 2 for row in candidate["weights"]))
        self.assertEqual(candidate["active_lambda"], 0.0)
        self.assertEqual(candidate["shadow_residual_lambda"], 1.0)
        self.assertFalse(candidate["stability_gate_passed"])
        self.assertFalse(candidate["automatic_promotion"])
        self.assertFalse(manifest["candidate_or_feature_contract_changed"])

    def test_sdk_mit_license_is_not_mistaken_for_api_data_rights(self):
        rights = load_manifest()["rights"]
        self.assertTrue(rights["pypi_sdk_mit_license_covers_client_code_only"])
        self.assertTrue(rights["pypi_states_api_data_is_governed_separately_by_pitchapi_terms"])
        self.assertFalse(rights["official_terms_linked_from_documentation"])
        self.assertFalse(rights["official_terms_or_data_license_text_verified"])
        self.assertFalse(rights["upstream_data_providers_identified"])
        self.assertFalse(rights["private_raw_response_retention_permission_confirmed"])
        self.assertFalse(rights["ai_model_training_or_inference_permission_confirmed"])
        self.assertFalse(rights["long_term_research_archive_permission_confirmed"])
        self.assertEqual(
            load_manifest()["decision"],
            "HOLD_NO_DOCUMENTED_CORNER_FEATURES_AND_UNCLEAR_DATA_RIGHTS_AND_UPSTREAM_PROVENANCE",
        )

    def test_local_receipt_sha_is_not_upstream_first_observed_proof(self):
        provenance = load_manifest()["provenance"]
        self.assertTrue(provenance["response_timestamps_rfc3339_utc_documented"])
        self.assertTrue(provenance["match_kickoff_time_utc_documented"])
        self.assertFalse(provenance["completed_match_stats_first_observed_timestamp_documented"])
        self.assertFalse(provenance["per_field_correction_timestamp_documented"])
        self.assertTrue(provenance["live_endpoint_fetched_at_age_seconds_and_stale_documented"])
        self.assertFalse(provenance["live_timestamp_applies_to_completed_match_stats"])
        self.assertTrue(provenance["local_capture_time_and_raw_sha_can_prove_project_possession_before_a_later_quote"])
        self.assertFalse(provenance["local_capture_time_and_raw_sha_prove_upstream_first_observation"])

    def test_no_provider_or_project_data_access_was_performed(self):
        auth = load_manifest()["authorization"]
        self.assertFalse(auth["provider_account_created"])
        self.assertFalse(auth["provider_api_key_created"])
        self.assertEqual(auth["provider_api_requests"], 0)
        self.assertEqual(auth["source_downloads"], 0)
        self.assertFalse(auth["raw_response_sha256_captured"])
        self.assertFalse(auth["supabase_accessed"])
        self.assertEqual(auth["supabase_writes"], 0)
        self.assertEqual(auth["supabase_ddl"], 0)
        self.assertEqual(auth["feature_builds"], 0)
        self.assertEqual(auth["inference_runs"], 0)
        self.assertFalse(auth["protected_2026_27_outcomes_read"])
        self.assertFalse(auth["model_refit_or_training_performed"])
        self.assertFalse(auth["production_pickle_changed"])
        self.assertEqual(auth["paid_api_calls"], 0)
        self.assertFalse(auth["cron_created"])

    def test_audit_and_ci_are_offline_read_only_and_unscheduled(self):
        audit = AUDIT_PATH.read_text(encoding="utf-8")
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for required in (
            "HOLD_NO_DOCUMENTED_CORNER_FEATURES_AND_UNCLEAR_DATA_RIGHTS_AND_UPSTREAM_PROVENANCE",
            "private raw-response storage and retention duration",
            "source-before-quote",
            "CLOSED prospective outcome gate (0/30)",
        ):
            self.assertIn(required, audit)
        for forbidden in (
            "schedule:", "workflow_run:", "workflow_dispatch:", "secrets.",
            "SUPABASE_", "upload-artifact", "download-artifact",
            "api.pitchapi.dev", "requests.get", "curl ",
        ):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("git diff --name-only origin/main...HEAD", workflow)
        self.assertIn("production .pkl", workflow)


if __name__ == "__main__":
    unittest.main()
