import json
from pathlib import Path

from research_agent_issue import build_issue_plan, parse_issue, render_markdown


def _write_registry(root: Path, family: str = "existing_family") -> None:
    research = root / "research"
    docs = root / "docs"
    research.mkdir()
    docs.mkdir()
    (docs / "CLOSURE.md").write_text("closed", encoding="utf-8")
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
        "blocks": [{
            "id": "EXISTING",
            "status": "CLOSED_RESEARCH_ONLY",
            "hypothesis_family": family,
            "sample_family": "historical",
            "decision": "closed",
            "retune_on_seen_sample": False,
            "closure_document": "docs/CLOSURE.md",
        }],
    }), encoding="utf-8")


def test_parse_issue_fields():
    parsed = parse_issue(
        "[AGENT-RESEARCH] Test a signal",
        "hypothesis_family: new_signal\n"
        "independent_information_justification: Different information source\n",
    )
    assert parsed["research_question"] == "Test a signal"
    assert parsed["hypothesis_family"] == "new_signal"


def test_novel_family_requires_justification(tmp_path):
    _write_registry(tmp_path)
    plan = build_issue_plan(
        "[AGENT-RESEARCH] Test a signal",
        "hypothesis_family: new_signal",
        root=tmp_path,
    )
    assert plan["decision"] == "NEEDS_INDEPENDENT_INFORMATION_JUSTIFICATION"
    assert plan["outcomes_read"] is False


def test_novel_family_with_justification_is_ready(tmp_path):
    _write_registry(tmp_path)
    plan = build_issue_plan(
        "[AGENT-RESEARCH] Test a signal",
        "hypothesis_family: new_signal\n"
        "independent_information_justification: Uses independent pre-match weather data",
        root=tmp_path,
    )
    assert plan["decision"] == "READY_FOR_PREREGISTRATION"
    assert plan["automatic_promotion"] is False


def test_existing_family_is_rejected_even_with_justification(tmp_path):
    _write_registry(tmp_path)
    plan = build_issue_plan(
        "[AGENT-RESEARCH] Retest old signal",
        "hypothesis_family: existing_family\n"
        "independent_information_justification: claimed new rationale",
        root=tmp_path,
    )
    assert plan["decision"] == "REJECT_EXISTING_HYPOTHESIS_FAMILY"
    assert plan["existing_block_id"] == "EXISTING"


def test_family_must_be_snake_case():
    try:
        parse_issue(
            "[AGENT-RESEARCH] Test",
            "hypothesis_family: Bad Family",
        )
    except ValueError as exc:
        assert "snake_case" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_markdown_contains_safety_contract(tmp_path):
    _write_registry(tmp_path)
    plan = build_issue_plan(
        "[AGENT-RESEARCH] Test",
        "hypothesis_family: new_signal\n"
        "independent_information_justification: independent source",
        root=tmp_path,
    )
    text = render_markdown(plan)
    assert "automatic promotion: no" in text
    assert "Supabase writes: no" in text
