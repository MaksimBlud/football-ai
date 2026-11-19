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


def test_free_plan_is_candidate_only_and_rights_remain_unresolved():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    assert audit["free_plan"]["price_usd_per_month"] == 0
    assert audit["free_plan"]["requests_per_day"] == 100
    assert audit["free_plan"]["statistics_endpoint_listed"] is True
    assert audit["free_plan"]["season_availability_limited"] is True
    assert audit["free_plan"]["exact_serie_a_2026_27_statistics_coverage_verified"] is False
    assert audit["free_plan"]["historical_2016_2026_coverage_verified"] is False
    assert audit["rights"]["explicit_internal_ml_training_permission"] is False
    assert audit["rights"]["explicit_model_inference_permission"] is False
    assert audit["rights"]["explicit_private_raw_response_retention_permission"] is False
    assert audit["rights"]["upstream_field_rights_identified"] is False
    assert audit["rights"]["written_provider_clearance_obtained"] is False


def test_source_before_quote_is_not_claimed_without_a_real_capture():
    audit = json.loads(RIGHTS.read_text(encoding="utf-8"))
    assert audit["provenance"]["per_match_first_observation_time_documented"] is False
    assert audit["provenance"]["per_field_correction_time_documented"] is False
    assert audit["provenance"]["source_before_quote_evidence_exists"] is False
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
    assert "Decision:** **HOLD" in document
    assert "written clarification" in document.lower()
    assert "source-before-quote" in document.lower()
    assert "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6" in document
    assert "on:" in workflow
    assert "pytest -q tests/test_serie_a_v2_api_football_source_audit.py" in workflow
    assert "schedule:" not in workflow
    assert "secrets." not in workflow
    assert "api-football.com" not in workflow
    assert "SUPABASE" not in workflow
    assert "ODDS_API" not in workflow
