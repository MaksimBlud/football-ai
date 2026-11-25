"""Offline contract tests for the Football Soccer API free-tier audit."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/source_rights/footballsoccerapi_20261125.json"
AUDIT_PATH = ROOT / "research/MARKET_ANCHOR_1X2_V2_FOOTBALLSOCCERAPI_FREE_AUDIT_20261125.md"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-footballsoccerapi-source-audit.yml"
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"

EXPECTED_FEATURES = [
    "diff_points_5", "diff_points_10", "diff_points_venue5",
    "diff_goals_for_5", "diff_goals_for_10", "diff_goals_against_5", "diff_goals_against_10",
    "diff_corners_for_5", "diff_corners_for_10", "diff_corners_against_5", "diff_corners_against_10",
    "diff_yellow_5", "diff_yellow_10", "diff_red_5", "diff_red_10",
    "diff_goals_for_venue5", "diff_goals_against_venue5",
    "diff_corners_for_venue5", "diff_corners_against_venue5",
]


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class FootballSoccerApiFreeAuditTests(unittest.TestCase):
    def test_free_plan_is_yesterday_only_and_not_a_19_feature_history_source(self):
        free = load_manifest()["free_plan"]
        self.assertEqual(free["price_usd_monthly"], 0)
        self.assertFalse(free["card_required"])
        self.assertEqual(free["calls_per_day"], 50)
        self.assertEqual(free["calls_per_minute"], 60)
        self.assertEqual(free["data_window"], "yesterday_only_one_utc_day")
        self.assertFalse(free["older_seasons_available"])
        self.assertFalse(free["statistics_available_per_pricing"] == "YES")
        self.assertFalse(load_manifest()["original_v2_feature_contract"]["free_plan_history_sufficient_for_rolling_5_and_10"])

    def test_official_endpoint_entitlement_conflict_is_preserved_as_hold(self):
        endpoint = load_manifest()["endpoint_documentation"]
        self.assertEqual(endpoint["match_detail_documented_plan"], "FREE_KEY")
        self.assertTrue(endpoint["match_detail_claims_team_figures"])
        self.assertEqual(endpoint["dedicated_match_statistics_plan"], "ARCHIVE")
        self.assertEqual(endpoint["pricing_says_free_statistics"], "NOT_AVAILABLE")
        self.assertEqual(endpoint["free_key_page_says_statistics"], "HELD_BACK")
        self.assertTrue(endpoint["official_documentation_conflict"])
        self.assertEqual(load_manifest()["decision"], "HOLD_FREE_TIER_NO_HISTORICAL_STATISTICS_AND_ENDPOINT_CONFLICT")

    def test_terms_allow_private_model_research_but_not_bulk_archive_republication(self):
        rights = load_manifest()["rights"]
        self.assertTrue(rights["use_in_own_work_apps_sites"])
        self.assertTrue(rights["model_research_and_model_building_permitted_by_acceptable_use"])
        self.assertTrue(rights["private_storage_permitted"])
        self.assertTrue(rights["retention_after_cancellation_permitted"])
        self.assertTrue(rights["raw_bulk_redistribution_or_republication_permitted"] is False)
        self.assertTrue(rights["bulk_download_to_rebuild_competing_database_permitted"] is False)

    def test_local_receipt_and_sha_do_not_claim_upstream_first_seen_proof(self):
        provenance = load_manifest()["provenance"]
        self.assertTrue(provenance["response_data_as_of_documented"])
        self.assertFalse(provenance["per_match_first_observed_timestamp_documented"])
        self.assertFalse(provenance["per_field_correction_timestamp_documented"])
        self.assertTrue(provenance["local_receipt_time_and_sha_can_prove_project_possession_before_later_quote"])
        self.assertFalse(provenance["local_receipt_time_and_sha_prove_upstream_first_observation"])

    def test_exact_original_v2_candidate_contract_is_unchanged(self):
        manifest = load_manifest()["original_v2_feature_contract"]
        candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(candidate["experiment_id"], "MARKET_ANCHOR_1X2_V2")
        self.assertEqual(candidate["artifact_sha256"], manifest["candidate_sha256"])
        self.assertEqual(candidate["features"], EXPECTED_FEATURES)
        self.assertEqual(candidate["features"], manifest["features"])
        self.assertEqual(len(candidate["features"]), 19)
        self.assertEqual(len(candidate["weights"]), 20)
        self.assertTrue(all(len(row) == 2 for row in candidate["weights"]))
        self.assertEqual(candidate["active_lambda"], 0.0)
        self.assertEqual(candidate["shadow_residual_lambda"], 1.0)
        self.assertFalse(candidate["stability_gate_passed"])
        self.assertFalse(candidate["automatic_promotion"])

    def test_no_live_access_or_model_operation_was_authorized(self):
        auth = load_manifest()["project_authorization"]
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
        self.assertEqual(auth["paid_calls"], 0)

    def test_audit_and_workflow_are_explicitly_offline_and_unscheduled(self):
        audit = AUDIT_PATH.read_text(encoding="utf-8")
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for required in (
            "HOLD_FREE_TIER_NO_HISTORICAL_STATISTICS_AND_ENDPOINT_CONFLICT",
            "private raw response retention",
            "source archive to precede the later target quote",
            "30-primary-completed-event outcome gate",
        ):
            self.assertIn(required, audit)
        for forbidden in (
            "schedule:", "workflow_run:", "workflow_dispatch:", "secrets.",
            "SUPABASE_", "upload-artifact", "download-artifact",
            "api.footballsoccerapi.com", "requests.get", "curl ",
        ):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)


if __name__ == "__main__":
    unittest.main()
