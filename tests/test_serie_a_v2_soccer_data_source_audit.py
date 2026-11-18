from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research" / "source_rights" / "soccer_data.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"

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
    "diff_corners_against_venue5"
]


class SoccerDataSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rights = json.loads(RIGHTS.read_text(encoding="utf-8"))
        cls.candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_provider_remains_on_hold_without_explicit_ai_and_upstream_rights(self):
        rights = self.rights
        self.assertEqual(rights["decision"], "HOLD")
        self.assertFalse(rights["rights"]["explicit_ai_model_training_permission"])
        self.assertFalse(rights["rights"]["explicit_ai_model_inference_permission"])
        self.assertFalse(rights["rights"]["upstream_provider_identity_verified"])
        self.assertFalse(rights["project_authorization"]["account_creation_authorized"])
        self.assertEqual(rights["project_authorization"]["api_requests_authorized"], False)
        self.assertEqual(rights["project_authorization"]["inference_performed"], False)

    def test_free_plan_is_current_season_only_and_has_no_odds(self):
        free = self.rights["free_access"]
        self.assertEqual(free["monthly_cost_usd"], 0)
        self.assertEqual(free["requests_per_day"], 50)
        self.assertEqual(free["history_scope"], "current season only")
        self.assertTrue(free["all_stats_endpoints_listed_for_free"])
        self.assertFalse(free["odds_endpoint_available"])
        self.assertFalse(free["historical_2016_2026_data_available_on_free_plan"])

    def test_serie_a_coverage_and_complete_feature_parity_are_unverified(self):
        coverage = self.rights["coverage"]
        self.assertTrue(coverage["match_stats_endpoint_available_on_free_plan"])
        self.assertEqual(coverage["candidate_feature_mapping_count"], 19)
        self.assertFalse(coverage["exact_serie_a_2026_27_match_coverage_verified"])
        self.assertFalse(coverage["full_frozen_19_feature_parity_verified"])
        self.assertFalse(coverage["per_match_statistics_completeness_verified"])
        self.assertFalse(coverage["red_card_completeness_verified"])

    def test_receipt_time_and_sha_are_not_misrepresented_as_provider_first_observation(self):
        provenance = self.rights["provenance"]
        self.assertFalse(provenance["per_match_first_observation_timestamp_documented"])
        self.assertFalse(provenance["per_field_correction_timestamp_documented"])
        self.assertTrue(provenance["request_receipt_time_can_be_recorded"])
        self.assertTrue(provenance["raw_response_sha256_can_be_computed_on_future_authorized_capture"])
        self.assertFalse(provenance["source_before_quote_proven"])
        self.assertTrue(provenance["receipt_before_quote_would_not_prove_provider_first_observation"])

    def test_original_frozen_candidate_is_unchanged(self):
        candidate = self.candidate
        frozen = self.rights["frozen_candidate"]
        self.assertEqual(candidate["experiment_id"], "MARKET_ANCHOR_1X2_V2")
        self.assertEqual(candidate["artifact_sha256"], frozen["candidate_sha256"])
        self.assertEqual(candidate["training_fingerprint_sha256"], frozen["training_fingerprint_sha256"])
        self.assertEqual(candidate["features"], EXPECTED_FEATURES)
        self.assertEqual(len(candidate["weights"]), 20)
        self.assertTrue(all(isinstance(row, list) and len(row) == 2 for row in candidate["weights"]))
        self.assertEqual(candidate["active_lambda"], 0.0)
        self.assertEqual(candidate["shadow_residual_lambda"], 1.0)
        self.assertIs(candidate["stability_gate_passed"], False)
        self.assertIs(candidate["automatic_promotion"], False)

    def test_no_live_or_outcome_access_is_recorded(self):
        authorization = self.rights["project_authorization"]
        self.assertEqual(authorization["source_download_performed"], False)
        self.assertEqual(authorization["raw_source_sha256_captured"], False)
        self.assertEqual(authorization["supabase_reads_for_this_source_audit"], 0)
        self.assertEqual(authorization["supabase_writes"], 0)
        self.assertEqual(authorization["supabase_ddl"], 0)
        self.assertEqual(authorization["odds_requests"], 0)
        self.assertEqual(authorization["protected_2026_27_outcomes_read"], False)
        self.assertEqual(authorization["production_pickle_changed"], False)


if __name__ == "__main__":
    unittest.main()
