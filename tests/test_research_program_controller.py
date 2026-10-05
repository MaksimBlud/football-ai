import json
from pathlib import Path

import pytest

from research_program_controller import (
    ProgramRegistryError,
    build_brain_context,
    validate_registry,
)


def _registry() -> dict:
    return {
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
                "objective": "Test a deterministic independent question.",
                "completed_issue_numbers": [7],
                "current_frontier": "Primary frozen test is complete.",
                "allowed_follow_up_classes": ["temporal_stability"],
                "stop_rules": [
                    "Do not weaken frozen gates.",
                    "Stop when no independent follow-up remains.",
                ],
            }
        ],
    }


def _write(root: Path, payload: dict) -> None:
    path = root / "research/programs/registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_program_registry_and_brain_context(tmp_path: Path):
    _write(tmp_path, _registry())
    state = tmp_path / "research/agent_runs/issue_7/STATE.json"
    state.parent.mkdir(parents=True)
    state.write_text(
        json.dumps(
            {
                "status": "DONE",
                "summary": "Frozen result complete.",
                "engine": "V5_DETERMINISTIC_NO_API",
            }
        ),
        encoding="utf-8",
    )

    payload = validate_registry(tmp_path)
    assert payload["controller"] == "CHATGPT_RESEARCH_BRAIN_V1"

    context = build_brain_context(tmp_path)
    program = context["programs"][0]
    assert program["status"] == "ACTIVE"
    assert program["completed_issue_numbers"] == [7]
    assert program["merged_completed_issue_states"][0]["status"] == "DONE"


def test_program_registry_rejects_model_api_default(tmp_path: Path):
    payload = _registry()
    payload["portfolio_policy"]["default_model_api_fallback"] = True
    _write(tmp_path, payload)
    with pytest.raises(ProgramRegistryError, match="unsafe portfolio policy"):
        validate_registry(tmp_path)


def test_program_registry_rejects_duplicate_program(tmp_path: Path):
    payload = _registry()
    payload["programs"].append(dict(payload["programs"][0]))
    _write(tmp_path, payload)
    with pytest.raises(ProgramRegistryError, match="duplicate program_id"):
        validate_registry(tmp_path)


def test_program_registry_rejects_invalid_followup_class(tmp_path: Path):
    payload = _registry()
    payload["programs"][0]["allowed_follow_up_classes"] = ["../escape"]
    _write(tmp_path, payload)
    with pytest.raises(ProgramRegistryError, match="invalid follow-up class"):
        validate_registry(tmp_path)
