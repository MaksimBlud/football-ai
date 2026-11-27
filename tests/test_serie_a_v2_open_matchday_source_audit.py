"""Offline-only rights and coverage assertions for the original V2 source audit."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/source_rights/open_matchday_20261127.json"
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
REPORT_PATH = ROOT / "research/SERIE_A_V2_OPEN_MATCHDAY_CURRENT_FORM_SOURCE_AUDIT_20261111.md"
WORKFLOW_PATH = ROOT / ".github/workflows/market-anchor-v2-open-matchday-source-audit.yml"

EXPECTED_FEATURES = (
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
)

EXPECTED_CANDIDATE_SHA = (
    "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
)


class OpenMatchdaySourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))

    def test_source_decision_is_fail_closed_hold(self):
        self.assertEqual(
            self.manifest["decision"],
            "HOLD_NONCOMMERCIAL_AND_UPSTREAM_RIGHTS_AND_FIELD_PROVENANCE_UNRESOLVED",
        )

    def test_exact_upstream_repository_and_commit_are_pinned(self):
        provider = self.manifest["provider"]
        self.assertEqual(provider["repository"], "oladeeayo/open-matchday")
        self.assertEqual(
            provider["reviewed_commit"],
            "381875f14c1e8073d866aacb29a868e31840e37b",
        )
        self.assertEqual(
            provider["build_generated_utc"],
            "2026-11-26T07:40:37Z",
        )

    def test_latest_checkpoint_records_no_serie_a_coverage_growth(self):
        freshness = self.manifest["freshness"]
        self.assertEqual(freshness["build_generated_utc"], "2026-11-26T07:40:37Z")
        self.assertEqual(freshness["latest_serie_a_match_date"], "2026-11-23")
        self.assertEqual(freshness["result_rows_since_2026_11_25_checkpoint"], 0)
        self.assertEqual(freshness["corner_rows_since_2026_11_25_checkpoint"], 0)
        self.assertFalse(freshness["latest_match_date_advanced_since_2026_11_25_checkpoint"])
        report = REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("381875f14c1e8073d866aacb29a868e31840e37b", report)
        self.assertIn("HOLD_NO_INTEGRATION", report)

    def test_per_field_lineage_and_ai_training_rights_are_not_claimed(self):
        rights = self.manifest["rights"]
        chronology = self.manifest["chronology"]
        self.assertFalse(rights["explicit_permission_for_existing_model_inference"])
        self.assertFalse(rights["explicit_permission_for_private_raw_retention"])
        self.assertIn("NOT_GRANTED", rights["football_data_co_uk_ai_training_permission"])
        self.assertFalse(chronology["per_field_provider_lineage"])
        self.assertFalse(chronology["per_field_source_observation_timestamp"])
        self.assertFalse(chronology["per_field_source_correction_timestamp"])

    def test_audit_workflow_is_offline_read_only_and_has_no_schedule_or_secrets(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("permissions:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertIn("market-anchor-v2-open-matchday-source-audit.yml", workflow)

    def test_dataset_noncommercial_restriction_is_not_treated_as_product_permission(self):
        rights = self.manifest["rights"]
        self.assertEqual(rights["dataset_terms"], "Informational, non-commercial use only")
        self.assertIs(rights["commercial_use_permitted"], False)
        self.assertIs(rights["upstream_rights_cleared_for_private_ml_research"], False)
        self.assertIs(rights["upstream_rights_cleared_for_product_or_commercial_use"], False)

    def test_upstream_provider_gap_is_explicit(self):
        rights = self.manifest["rights"]
        notes = rights["provider_terms_notes"]
        self.assertIn("FotMob", notes)
        self.assertIn("absent", notes["FotMob"])
        self.assertIs(rights["written_permission_for_private_raw_storage"], False)
        self.assertIs(rights["written_permission_for_model_training_or_evaluation"], False)

    def test_serie_a_catalogue_claims_are_pinned_but_not_overstated(self):
        coverage = self.manifest["observed_serie_a_catalogue_metadata"]
        self.assertEqual(coverage["results_rows"], 120)
        self.assertEqual(coverage["rows_with_corner_totals_reported_by_build_summary"], 120)
        self.assertIs(coverage["per_match_completeness_of_all_six_corner_fields_verified"], False)
        self.assertIs(coverage["stable_match_id_in_results_schema"], False)

    def test_no_upstream_first_seen_or_correction_clock_is_claimed(self):
        chronology = self.manifest["chronology"]
        self.assertIs(chronology["per_field_upstream_first_observed_timestamp"], False)
        self.assertIs(chronology["per_field_upstream_correction_timestamp"], False)
        self.assertIs(chronology["upstream_first_seen_before_quote_proof"], False)
        self.assertIs(chronology["local_project_source_before_quote_proof_possible_if_archived_before_quote"], True)

    def test_exact_original_candidate_and_feature_order_are_unchanged(self):
        self.assertEqual(self.candidate["artifact_sha256"], EXPECTED_CANDIDATE_SHA)
        self.assertEqual(self.manifest["model_contract"]["candidate_sha256"], EXPECTED_CANDIDATE_SHA)
        self.assertEqual(tuple(self.candidate["features"]), EXPECTED_FEATURES)
        self.assertEqual(self.manifest["model_contract"]["feature_count"], 19)
        self.assertEqual(self.manifest["model_contract"]["weights_shape"], [20, 2])
        self.assertEqual(self.manifest["model_contract"]["active_lambda"], 0.0)
        self.assertEqual(self.manifest["model_contract"]["shadow_lambda"], 1.0)

    def test_no_live_or_production_operation_is_authorized(self):
        safety = self.manifest["safety"]
        for key in (
            "raw_dataset_downloaded",
            "raw_dataset_archived",
            "protected_2026_27_outcomes_read",
            "training_or_refit",
            "automatic_promotion",
            "betting",
        ):
            self.assertIs(safety[key], False)
        for key in (
            "provider_api_calls",
            "supabase_reads",
            "supabase_writes",
            "supabase_ddl",
            "saved_quote_reads",
            "feature_builds",
            "inference_runs",
            "production_pkl_changes",
            "schedule_changes",
            "paid_provider_calls",
        ):
            self.assertEqual(safety[key], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
