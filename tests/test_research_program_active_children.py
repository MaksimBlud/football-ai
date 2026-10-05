import json
from pathlib import Path

import pytest

from research_program_controller import ProgramRegistryError, build_brain_context, validate_registry


def _write(root: Path, active, completed):
    path = root / "research/programs/registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "controller": "CHATGPT_RESEARCH_BRAIN_V1",
        "portfolio_policy": {
            "max_new_child_issues_per_cycle": 4,
            "max_new_child_issues_per_program_per_cycle": 1,
            "require_independent_preregisterable_follow_up": True,
            "default_model_api_fallback": False,
            "allow_paid_data_without_user_approval": False,
            "allow_production_promotion": False,
            "allow_posthoc_gate_weakening": False,
            "stop_when_no_independent_follow_up_remains": True,
        },
        "programs": [
            {
                "program_id": "demo_program",
                "title": "Demo",
                "status": "ACTIVE",
                "objective": "Demo objective.",
                "completed_issue_numbers": completed,
                "active_child_issue_numbers": active,
                "current_frontier": "A child is active.",
                "allowed_follow_up_classes": ["temporal_stability"],
                "stop_rules": [
                    "Do not weaken frozen gates.",
                    "Stop when no independent follow-up remains.",
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_active_child_issues_are_exposed_in_brain_context(tmp_path: Path):
    _write(tmp_path, active=[8], completed=[7])
    validate_registry(tmp_path)
    context = build_brain_context(tmp_path)
    assert context["programs"][0]["active_child_issue_numbers"] == [8]


def test_active_child_cannot_also_be_completed(tmp_path: Path):
    _write(tmp_path, active=[7], completed=[7])
    with pytest.raises(ProgramRegistryError, match="active/completed child overlap"):
        validate_registry(tmp_path)
