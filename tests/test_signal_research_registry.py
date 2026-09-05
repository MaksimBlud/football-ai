import json
from pathlib import Path

from signal_research_registry_check import REGISTRY, validate_registry


def test_current_signal_research_registry_is_valid():
    assert validate_registry() == []


def test_registry_has_unique_ids_and_expected_active_closed_split():
    payload = json.loads(REGISTRY.read_text())
    blocks = payload["blocks"]
    ids = [block["id"] for block in blocks]
    assert len(ids) == len(set(ids))
    closed = [block for block in blocks if block["status"].startswith("CLOSED_")]
    active = [block for block in blocks if block["status"].startswith("ACTIVE_")]
    assert len(closed) >= 3
    assert {block["id"] for block in active} == {
        "PROSPECTIVE_AVAILABILITY_SIGNAL_LAB",
        "PROSPECTIVE_MARKET_PATH_V1",
        "LA_LIGA_MARKET_HOME_60_70_V1",
        "TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1",
    }


def test_closed_blocks_forbid_retuning_and_active_blocks_forbid_early_scoring():
    payload = json.loads(REGISTRY.read_text())
    for block in payload["blocks"]:
        if block["status"].startswith("CLOSED_"):
            assert block["retune_on_seen_sample"] is False
            assert Path(block["closure_document"]).is_file()
        else:
            assert block["frozen_protocol"] is True
            assert block["outcome_scoring_before_readiness"] is False
            assert Path(block["status_document"]).is_file()


def test_governance_explicitly_treats_negative_results_as_results():
    payload = json.loads(REGISTRY.read_text())
    governance = payload["governance"]
    assert governance["negative_results_are_first_class_results"] is True
    assert governance["new_retrospective_feature_family_requires_independent_information_justification"] is True
    assert governance["production_promotion_requires_separate_explicit_decision"] is True
    assert governance["prospective_outcome_evaluation_requires_explicit_action"] is True


def _block(block_id: str) -> dict:
    payload = json.loads(REGISTRY.read_text())
    return next(block for block in payload["blocks"] if block["id"] == block_id)


def test_market_path_is_operationally_closed_but_scientifically_active():
    block = _block("PROSPECTIVE_MARKET_PATH_V1")
    assert block["status"] == "ACTIVE_ACCUMULATING"
    assert block["operational_implementation"] == "CLOSED"
    assert block["scheduled_outcome_scoring"] is False
    assert block["evaluation_requires_explicit_manual_dispatch"] is True
    assert Path(block["operational_closure_document"]).is_file()


def test_availability_is_operationally_closed_but_externally_gated():
    block = _block("PROSPECTIVE_AVAILABILITY_SIGNAL_LAB")
    assert block["status"] == "ACTIVE_EXTERNALLY_GATED"
    assert block["operational_implementation"] == "CLOSED"
    assert block["scheduled_outcome_scoring"] is False
    assert block["evaluation_requires_explicit_manual_dispatch"] is True
    assert block["activation_monitor_read_only"] is True
    assert block["automatic_external_gate_bypass"] is False
    assert Path(block["operational_closure_document"]).is_file()


def test_la_liga_60_70_is_operationally_closed_but_scientifically_active():
    block = _block("LA_LIGA_MARKET_HOME_60_70_V1")
    assert block["status"] == "ACTIVE_ACCUMULATING"
    assert block["operational_implementation"] == "CLOSED"
    assert block["scheduled_outcome_scoring"] is False
    assert block["evaluation_requires_explicit_manual_dispatch"] is True
    assert Path(block["protocol_document"]).is_file()
    assert Path(block["runtime_contract"]).is_file()
    assert Path(block["operational_closure_document"]).is_file()


def test_turkey_portugal_structural_v2_is_preregistered_without_runtime_activation():
    block = _block("TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1")
    assert block["status"] == "ACTIVE_PREREGISTERED"
    assert block["frozen_protocol"] is True
    assert block["outcome_scoring_before_readiness"] is False
    assert block["cross_league_parameter_transfer"] is False
    assert block["runtime_status"] == "CALIBRATION_REQUIRED"
    assert block["automatic_promotion"] is False
    assert block["negative_result_is_valid"] is True
    assert Path(block["status_document"]).is_file()
    assert Path(block["protocol_document"]).is_file()
