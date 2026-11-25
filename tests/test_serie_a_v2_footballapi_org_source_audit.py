"""Offline contract tests for the footballapi.org source-rights audit."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/source_rights/footballapi_org_20261125.json"
AUDIT_PATH = ROOT / "research/MARKET_ANCHOR_1X2_V2_FOOTBALLAPI_ORG_SOURCE_AUDIT_20261125.md"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-footballapi-org-source-audit.yml"


class FootballApiOrgSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.audit = AUDIT_PATH.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_provider_is_distinct_from_existing_api_football_audits(self):
        self.assertEqual(
            self.manifest["provider"],
            "Football API (footballapi.org; operated by DeveloperData.net)",
        )
        self.assertIn("API-Football", self.manifest["distinct_from"])
        self.assertIn("API-Sports", self.manifest["distinct_from"])

    def test_free_plan_does_not_cover_frozen_serie_a_candidate(self):
        self.assertEqual(
            self.manifest["free_plan"]["competitions"],
            "current-season Premier League only",
        )
        self.assertEqual(self.manifest["target_model"]["league"], "SERIE_A")
        self.assertEqual(self.manifest["free_plan"]["price"], 0)
        self.assertEqual(self.manifest["free_plan"]["requests_per_day"], 50)
        self.assertEqual(self.manifest["free_plan"]["requests_per_minute"], 10)
        self.assertEqual(
            self.manifest["decision"],
            "HOLD_WRONG_LEAGUE_AND_UNPROVEN_RETENTION_RIGHTS",
        )

    def test_documented_stats_overlap_is_not_a_19_feature_coverage_claim(self):
        fields = set(self.manifest["match_stats_endpoint"]["documented_fields"])
        self.assertTrue({"corners", "yellow_cards", "red_cards"}.issubset(fields))
        self.assertEqual(self.manifest["target_model"]["frozen_feature_count"], 19)
        self.assertFalse(
            self.manifest["match_stats_endpoint"][
                "documented_per_field_first_seen_or_correction_timestamp"
            ]
        )
        self.assertIn("exact one-to-one mapping for all 19", self.audit)

    def test_terms_hold_bulk_rebuild_and_do_not_resolve_private_ml_retention(self):
        rights = self.manifest["rights"]
        self.assertEqual(rights["use_in_own_work_apps_sites"], "permitted_by_published_terms")
        self.assertEqual(rights["redistribution_or_resale_of_data"], "prohibited")
        self.assertEqual(rights["bulk_download_to_rebuild_collection"], "prohibited")
        self.assertEqual(rights["private_raw_response_retention"], "not_explicitly_resolved")
        self.assertEqual(rights["private_ml_training_or_evaluation"], "not_explicitly_resolved")
        self.assertEqual(rights["upstream_first_seen_or_correction_history"], "not_documented")

    def test_no_live_access_or_model_changes_are_authorized(self):
        for key in (
            "api_requests_made",
            "supabase_writes",
            "feature_builds",
            "inference_runs",
        ):
            self.assertEqual(self.manifest[key], 0)
        for key in (
            "account_or_key_created",
            "raw_data_downloaded",
            "supabase_accessed",
            "protected_outcomes_read",
            "production_artifact_changed",
            "model_contract_changed",
        ):
            self.assertFalse(self.manifest[key])
        self.assertEqual(self.manifest["target_model"]["active_lambda"], 0)
        self.assertEqual(self.manifest["target_model"]["shadow_lambda"], 1)

    def test_validation_is_secret_free_offline_and_unscheduled(self):
        header = self.workflow.split("jobs:", 1)[0]
        self.assertIn("push:", header)
        self.assertIn("pull_request:", header)
        self.assertNotIn("schedule:", header)
        self.assertNotIn("workflow_dispatch:", header)
        self.assertNotIn("secrets.", self.workflow)
        self.assertNotIn("api.footballapi.org", self.workflow)
        self.assertNotIn("requests.", self.workflow)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn("python tests/test_serie_a_v2_footballapi_org_source_audit.py", self.workflow)


if __name__ == "__main__":
    unittest.main()
