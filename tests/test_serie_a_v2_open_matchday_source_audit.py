"""Offline-only rights and coverage assertions for the original V2 source audit."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/source_rights/open_matchday_20261125.json"
CANDIDATE_PATH = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"

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
            "968bc4fdb0adfd2a412962793b59fda2c39bdfd9",
        )
        self.assertEqual(
            provider["build_generated_utc"],
            "2026-11-25T07:50:20Z",
        )

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
