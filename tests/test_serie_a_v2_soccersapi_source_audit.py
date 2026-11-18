from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research" / "source_rights" / "soccersapi.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"


class SoccersAPISourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rights = json.loads(RIGHTS.read_text(encoding="utf-8"))
        cls.candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_provider_remains_on_hold_until_written_clearance(self):
        rights = self.rights
        self.assertEqual(rights["decision"], "HOLD")
        self.assertTrue(rights["rights"]["written_clarification_required_before_project_ingestion"])
        self.assertFalse(rights["rights"]["internal_noncommercial_ml_training_explicitly_permitted"])
        self.assertFalse(rights["rights"]["private_raw_source_retention_explicitly_permitted"])
        self.assertFalse(rights["project_authorization"]["account_creation_authorized"])
        self.assertEqual(rights["free_access"]["api_requests_performed"], 0)
        self.assertFalse(rights["project_authorization"]["inference_performed"])

    def test_free_plan_claims_are_pinned_without_resolving_the_conflict(self):
        access = self.rights["free_access"]
        self.assertEqual(access["free_plan_league_limit"], 3)
        self.assertEqual(access["free_plan_requests_per_day"], 100)
        self.assertTrue(access["fixture_match_detail_stats_include_available_on_free"])
        self.assertTrue(access["italy_page_claims_free_key_reaches_all_31_italy_competitions"])
        self.assertFalse(access["free_plan_scope_is_consistent_across_pages"])

    def test_feature_coverage_is_candidate_only_not_proven(self):
        coverage = self.rights["coverage"]
        self.assertTrue(coverage["serie_a_2026_27_public_page_exists"])
        self.assertEqual(coverage["candidate_feature_mapping_count"], 19)
        self.assertFalse(coverage["full_frozen_19_feature_parity_verified"])
        self.assertFalse(coverage["per_match_statistics_coverage_verified"])
        self.assertFalse(coverage["current_season_red_card_completeness_verified"])

    def test_project_receipt_sha_is_not_misrepresented_as_provider_first_observation(self):
        provenance = self.rights["provenance"]
        self.assertFalse(provenance["per_match_first_observation_time_documented"])
        self.assertFalse(provenance["per_field_correction_time_documented"])
        self.assertTrue(provenance["project_receipt_time_can_be_recorded_on_future_authorized_capture"])
        self.assertTrue(provenance["project_receipt_before_quote_would_not_prove_provider_first_observation"])
        self.assertFalse(provenance["source_before_quote_proven"])

    def test_original_frozen_candidate_is_unchanged(self):
        candidate = self.candidate
        self.assertEqual(candidate["experiment_id"], "MARKET_ANCHOR_1X2_V2")
        self.assertEqual(candidate["artifact_sha256"], self.rights["frozen_candidate"]["candidate_sha256"])
        self.assertEqual(candidate["training_fingerprint_sha256"], self.rights["frozen_candidate"]["training_fingerprint_sha256"])
        self.assertEqual(len(candidate["features"]), 19)
        self.assertEqual(len(candidate["weights"]), 20)
        self.assertTrue(all(isinstance(row, list) and len(row) == 2 for row in candidate["weights"]))
        self.assertEqual(candidate["active_lambda"], 0.0)
        self.assertEqual(candidate["shadow_residual_lambda"], 1.0)
        self.assertIs(candidate["stability_gate_passed"], False)
        self.assertIs(candidate["automatic_promotion"], False)


if __name__ == "__main__":
    unittest.main()
