import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "research" / "SERIE_A_V2_API_FOOTBALL_SOURCE_AUDIT_20261119.md"
RIGHTS = ROOT / "research" / "source_rights" / "api_football.json"
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-v2-api-football-source-audit.yml"


def test_audit_is_original_v2_only_and_pins_frozen_candidate():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    assert audit["provider"] == "API-FOOTBALL"
    assert audit["decision"] == "HOLD"
    assert audit["original_v2"]["candidate_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert audit["original_v2"]["training_fingerprint_sha256"] == (
        "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    )
    assert audit["original_v2"]["feature_count"] == 19
    assert audit["original_v2"]["weight_matrix_shape"] == [20, 2]
    assert audit["original_v2"]["active_lambda"] == 0.0
    assert audit["original_v2"]["shadow_residual_lambda"] == 1.0
    assert audit["original_v2"]["stability_gate_passed"] is False
    assert audit["original_v2"]["automatic_promotion"] is False


def test_free_plan_season_window_excludes_2026_27():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    free = audit["free_plan"]
    assert free["price_usd_per_month"] == 0
    assert free["requests_per_day"] == 100
    assert free["statistics_endpoint_listed"] is True
    assert free["all_endpoint_families_listed"] is True
    assert free["season_availability_limited"] is True
    assert free["covered_seasons_last_confirmed"] == [2022, 2023, 2024]
    assert free["season_window_evidence_date"] == "2026-10-26"
    assert free["current_2026_27_available"] is False
    assert free["coverage_page_last_updated"] == "2026-11-26"
    assert free["coverage_page_lists_italy_serie_a"] is True
    assert free["exact_serie_a_2026_27_statistics_coverage_verified"] is False
    assert free["historical_2016_2026_coverage_verified"] is False
    assert free["authenticated_coverage_response_obtained"] is False


def test_rights_and_private_retention_remain_unresolved():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    rights = audit["rights"]
    assert rights["data_obtained_from_partners"] is True
    assert rights["resale_prohibited"] is True
    assert rights["third_party_rights_may_apply"] is True
    assert rights["explicit_internal_ml_training_permission"] is False
    assert rights["explicit_model_inference_permission"] is False
    assert rights["explicit_private_raw_response_retention_permission"] is False
    assert rights["upstream_field_rights_identified"] is False
    assert rights["written_provider_clearance_obtained"] is False


def test_source_before_quote_is_not_claimed_without_a_real_capture():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    provenance = audit["provenance"]
    assert provenance["statistics_available_for_ongoing_or_completed_fixture"] is True
    assert provenance["statistics_available_for_target_fixture_before_kickoff"] is False
    assert provenance["per_match_first_observation_time_documented"] is False
    assert provenance["per_field_correction_time_documented"] is False
    assert provenance["project_receipt_time_and_sha256_capture_possible_if_authorized"] is True
    assert provenance["source_before_quote_evidence_exists"] is False
    assert audit["non_actions"]["api_requests"] == 0
    assert audit["non_actions"]["protected_2026_27_outcomes_read"] is False


def test_no_paid_calls_supabase_writes_or_model_mutations_are_claimed():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    non_actions = audit["non_actions"]
    assert non_actions["paid_provider_calls"] == 0
    assert non_actions["odds_requests"] == 0
    assert non_actions["supabase_reads"] == 0
    assert non_actions["supabase_writes"] == 0
    assert non_actions["feature_calculation"] is False
    assert non_actions["inference"] is False
    assert non_actions["training_or_refit"] is False
    assert non_actions["production_pickle_changes"] is False
    assert non_actions["schedule_changes"] is False
    assert non_actions["integration_authorized"] is False


def test_audit_document_and_offline_workflow_are_present_and_safe():
    document = DOC.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Audit refresh:** 2026-11-26" in document
    assert "2022, 2023 and 2024" in document
    assert "source-before-quote" in document.lower()
    assert "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6" in document
    assert "on:" in workflow
    assert "pytest -q tests/test_serie_a_v2_api_football_source_audit.py" in workflow
    assert "schedule:" not in workflow
    assert "secrets." not in workflow
    assert "api-football.com" not in workflow
    assert "SUPABASE" not in workflow
    assert "ODDS_API" not in workflow
    assert "persist-credentials: false" in workflow
    assert "de0fac2e4500dabe0009e67214ff5f5447ce83dd" in workflow
    assert "83679a892e2d95755f2dac6acb0bfd1e9ac5d548" in workflow
