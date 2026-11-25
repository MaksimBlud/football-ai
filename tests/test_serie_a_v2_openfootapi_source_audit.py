import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "source_rights" / "openfootapi.json"
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-v2-openfootapi-source-audit.yml"
AUDIT = ROOT / "research" / "SERIE_A_V2_OPENFOOTAPI_SOURCE_AUDIT_20261125.md"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_openfootapi_is_held_for_missing_full_frozen_feature_coverage():
    m = load_manifest()
    assert m["provider"] == "OpenFootAPI"
    assert m["decision"] == "HOLD_NO_FULL_19_FEATURE_COVERAGE"
    assert m["free_plan"]["price_usd_per_month"] == 0
    assert m["free_plan"]["requests_per_month"] == 5000
    assert m["free_plan"]["credit_card_required"] is False
    assert "fixtures" in m["free_plan"]["documented_features"]
    assert "standings" in m["free_plan"]["documented_features"]
    assert "match_level_corners" in m["free_plan"]["not_documented_in_free_plan"]
    assert m["frozen_feature_gaps"]["full_19_feature_parity"] is False
    assert "corners" in m["frozen_feature_gaps"]["missing_feature_families"]


def test_provider_terms_and_upstream_licence_boundary_are_not_overstated():
    m = load_manifest()
    rights = m["data_rights"]
    assert rights["internal_statistical_research_permitted_for_lawfully_received_data"] is True
    assert rights["internal_model_training_permitted_for_lawfully_received_data"] is True
    assert rights["internal_evaluation_and_validation_permitted_for_lawfully_received_data"] is True
    assert rights["exact_response_retention_permitted_without_maximum_period"] is True
    assert rights["raw_underlying_feed_redistribution_permitted"] is False
    assert rights["upstream_competition_licences_remain_binding"] is True
    assert rights["free_plan_commercial_use"] == "NOT_EXPLICITLY_GRANTED"


def test_local_sha_can_prove_receipt_order_but_not_upstream_first_seen():
    p = load_manifest()["provenance"]
    assert p["response_source_metadata_documented"] is True
    assert p["per_competition_licence_metadata_documented"] is True
    assert p["upstream_first_seen_or_correction_timestamps_documented"] is False
    assert p["local_receipt_timestamp_and_sha256_can_prove_project_possession_before_quote"] is True
    assert p["upstream_first_publication_before_quote_proven"] is False


def test_original_market_anchor_v2_contract_is_pinned_and_unchanged():
    v2 = load_manifest()["original_model"]
    assert v2["name"] == "MARKET_ANCHOR_1X2_V2"
    assert v2["candidate_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert v2["feature_count"] == 19
    assert v2["weight_shape"] == [20, 2]
    assert v2["active_lambda"] == 0
    assert v2["shadow_lambda"] == 1
    assert v2["historical_stability"] == "FAILED"
    assert v2["prospective_outcome_gate"] == "CLOSED_0_OF_30"


def test_no_account_provider_call_data_capture_or_inference_was_authorized():
    a = load_manifest()["authorization"]
    assert a["account_created"] is False
    assert a["api_key_created"] is False
    assert a["provider_requests_made"] == 0
    assert a["raw_data_downloaded"] is False
    assert a["source_capture_approved"] is False
    assert a["feature_build_approved"] is False
    assert a["inference_approved"] is False
    assert a["supabase_access_or_write"] is False
    assert a["protected_outcomes_read"] is False
    assert a["paid_calls"] == 0


def test_audit_note_and_secret_free_offline_workflow_are_present():
    note = AUDIT.read_text(encoding="utf-8")
    assert "HOLD_NO_FULL_19_FEATURE_COVERAGE" in note
    assert "No account/key was created" in note
    assert "OpenFootball CC0-1.0" in note

    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "schedule:" not in workflow
    assert "workflow_run:" not in workflow
    assert "workflow_dispatch:" not in workflow
    assert "SUPABASE" not in workflow
    assert "PITCH" not in workflow
    assert "persist-credentials: false" in workflow
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in workflow
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
    assert "python -m pip install pytest==9.2.0" in workflow
    assert "python -m pytest -q tests/test_serie_a_v2_openfootapi_source_audit.py" in workflow
