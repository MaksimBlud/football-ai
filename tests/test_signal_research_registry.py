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
