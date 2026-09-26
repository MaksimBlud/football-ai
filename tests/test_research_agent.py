import json
from pathlib import Path

from research_agent import build_spec


def _write_registry(root: Path, blocks: list[dict]) -> None:
    research = root / "research"
    research.mkdir()
    (research / "signal_research_registry_v1.json").write_text(json.dumps({
        "registry_version": "SIGNAL_RESEARCH_REGISTRY_V1",
        "governance": {
            "closed_hypotheses_must_not_be_retuned_on_seen_sample": True,
            "active_prospective_blocks_must_preserve_frozen_protocol": True,
            "new_retrospective_feature_family_requires_independent_information_justification": True,
            "production_promotion_requires_separate_explicit_decision": True,
            "research_runs_must_not_modify_production_artifacts": True,
            "negative_results_are_first_class_results": True,
            "prospective_outcome_evaluation_requires_explicit_action": True,
        },
        "blocks": blocks,
    }), encoding="utf-8")


def test_novel_family_is_ready_for_preregistration(tmp_path):
    _write_registry(tmp_path, [])
    spec = build_spec(
        "Test a new independent signal",
        "independent_new_signal_family",
        root=tmp_path,
    )
    assert spec.decision == "READY_FOR_PREREGISTRATION"
    assert spec.automatic_promotion is False
    assert spec.supabase_writes is False
    assert spec.paid_odds_api_requests is False
    assert spec.arbitrary_command_execution is False


def test_existing_closed_family_is_rejected(tmp_path):
    closure = tmp_path / "docs" / "CLOSURE.md"
    closure.parent.mkdir()
    closure.write_text("closed", encoding="utf-8")
    _write_registry(tmp_path, [{
        "id": "OLD_SIGNAL",
        "status": "CLOSED_RESEARCH_ONLY",
        "hypothesis_family": "rolling_shot_volume",
        "sample_family": "historical",
        "decision": "do_not_promote",
        "retune_on_seen_sample": False,
        "closure_document": "docs/CLOSURE.md",
    }])
    spec = build_spec("Try shots again", "rolling_shot_volume", root=tmp_path)
    assert spec.decision == "REJECT_EXISTING_HYPOTHESIS_FAMILY"
    assert spec.existing_block_id == "OLD_SIGNAL"


def test_empty_task_is_rejected(tmp_path):
    _write_registry(tmp_path, [])
    try:
        build_spec("", "family", root=tmp_path)
    except ValueError as exc:
        assert "task" in str(exc)
    else:
        raise AssertionError("expected ValueError")
