"""Offline-only rights and frozen-contract checks for Soccer Data source audit."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research" / "source_rights" / "soccer_data_co_20261127.json"
CANDIDATE_PATH = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"
PROTOCOL_PATH = ROOT / "experiments" / "market_anchor_1x2_v2_protocol.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "market-anchor-v2-soccer-data-source-audit.yml"

FROZEN_SHA = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
PROTOCOL_BLOB_SHA1 = "65729e9639720e67624c1481190aa22ae606f151"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path.name} must contain a JSON object")
    return value


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class SoccerDataSourceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(MANIFEST_PATH)

    def test_source_remains_hold_and_no_live_access_was_performed(self) -> None:
        self.assertEqual(self.manifest["decision"], "HOLD_NO_INTEGRATION")
        self.assertIs(self.manifest["integration_authorized"], False)
        self.assertEqual(self.manifest["provider_api_requests_made"], 0)
        self.assertIs(self.manifest["api_key_created"], False)
        self.assertEqual(self.manifest["source_downloads"], 0)
        self.assertIs(self.manifest["raw_archive_created"], False)
        self.assertIs(self.manifest["supabase_accessed"], False)
        self.assertEqual(self.manifest["supabase_writes"], 0)
        self.assertEqual(self.manifest["supabase_ddl"], 0)
        self.assertIs(self.manifest["feature_calculation_performed"], False)
        self.assertIs(self.manifest["inference_performed"], False)
        self.assertIs(self.manifest["target_outcomes_read"], False)
        self.assertEqual(self.manifest["paid_provider_calls"], 0)
        self.assertEqual(self.manifest["paid_odds_calls"], 0)
        self.assertIs(self.manifest["production_pkl_changed"], False)

    def test_free_plan_scope_is_not_misrepresented(self) -> None:
        free = self.manifest["free_plan"]
        self.assertEqual(free["price_usd_per_month"], 0)
        self.assertEqual(free["requests_per_day"], 50)
        self.assertIs(free["all_stats_endpoints_claimed"], True)
        self.assertIs(free["current_season_only"], True)
        self.assertEqual(free["current_season_cache_minutes"], 5)
        self.assertIs(free["pre_match_odds_available"], False)
        self.assertIs(free["live_odds_available"], False)
        self.assertIs(free["serie_a_2026_27_field_coverage_authenticated"], False)
        self.assertIs(free["per_match_stats_endpoint"], True)
        self.assertIs(free["bulk_match_stats_endpoint_documented"], False)

    def test_rights_do_not_claim_unverified_model_or_retention_permission(self) -> None:
        rights = self.manifest["rights"]
        self.assertIs(rights["upstream_provider_identity_disclosed"], False)
        self.assertIs(rights["upstream_rights_confirmed"], False)
        self.assertIs(rights["cache_and_store_permitted_while_account_and_plan_active"], True)
        self.assertIs(rights["raw_feed_redistribution_permitted"], False)
        self.assertIs(rights["license_ends_when_account_or_terms_end"], True)
        self.assertIs(rights["retention_after_account_termination_permitted"], False)
        self.assertIs(rights["internal_model_inference_explicitly_permitted"], False)
        self.assertIs(rights["model_training_explicitly_permitted"], False)
        self.assertIs(rights["private_archive_scope_explicitly_documented"], False)

    def test_documented_fields_are_not_mistaken_for_frozen_feature_parity(self) -> None:
        fields = self.manifest["documented_stats_fields"]
        self.assertIs(fields["corner_kicks"], True)
        self.assertIs(fields["yellow_cards"], True)
        self.assertIs(fields["red_cards"], True)
        self.assertIs(fields["exact_frozen_v2_semantics_verified"], False)
        self.assertIs(fields["per_field_coverage_verified"], False)

    def test_source_before_quote_requires_local_receipt_and_raw_sha(self) -> None:
        provenance = self.manifest["provenance"]
        self.assertIs(provenance["api_source_observation_timestamp_documented"], False)
        self.assertIs(provenance["per_field_correction_timestamp_documented"], False)
        self.assertIs(provenance["local_utc_receipt_time_required"], True)
        self.assertIs(provenance["raw_response_sha256_required"], True)
        self.assertIs(provenance["source_before_quote_proven"], False)
        self.assertIs(provenance["source_before_quote_can_be_proven_by_future_local_capture"], True)
        self.assertIs(provenance["source_side_first_seen_or_correction_history_proven"], False)

    def test_original_candidate_and_protocol_are_unchanged(self) -> None:
        candidate = load_json(CANDIDATE_PATH)
        self.assertEqual(candidate["artifact_sha256"], FROZEN_SHA)
        self.assertEqual(len(candidate["features"]), 19)
        self.assertEqual(len(candidate["weights"]), 20)
        self.assertTrue(all(len(row) == 2 for row in candidate["weights"]))
        self.assertEqual(candidate["active_lambda"], 0.0)
        self.assertEqual(candidate["shadow_residual_lambda"], 1.0)
        self.assertIs(candidate["stability_gate_passed"], False)
        raw_protocol = PROTOCOL_PATH.read_bytes()
        self.assertEqual(git_blob_sha1(raw_protocol), PROTOCOL_BLOB_SHA1)
        protocol = json.loads(raw_protocol)
        self.assertEqual(protocol["first_outcome_read_gate"]["completed_primary_events"], 30)
        self.assertIs(protocol["first_outcome_read_gate"]["outcome_read_before_gate"], False)
        self.assertEqual(self.manifest["original_v2"]["candidate_sha256"], FROZEN_SHA)
        self.assertEqual(self.manifest["original_v2"]["feature_count"], 19)
        self.assertEqual(self.manifest["original_v2"]["weight_matrix_shape"], [20, 2])
        self.assertEqual(self.manifest["original_v2"]["active_lambda"], 0)
        self.assertEqual(self.manifest["original_v2"]["shadow_residual_lambda"], 1)

    def test_audit_workflow_is_offline_read_only_and_has_no_schedule_or_secrets(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("SUPABASE", workflow)
        self.assertNotIn("The Odds API", workflow)
        self.assertNotIn("upload-artifact", workflow)
        self.assertIn("python -m unittest discover", workflow)


if __name__ == "__main__":
    unittest.main()
