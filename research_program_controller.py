"""Deterministic portfolio controller for ChatGPT Research Brain.

This module does not choose scientific follow-ups itself. It validates the durable
Research Program registry and exposes a compact machine-readable context that the
scheduled ChatGPT Research Brain can use each cycle.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REGISTRY = Path("research/programs/registry.json")
PROGRAM_ID_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
VALID_STATUS = {"ACTIVE", "PROGRAM_DONE", "BLOCKED"}
VALID_FOLLOW_UP_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class ProgramRegistryError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ProgramRegistryError(f"missing program registry: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProgramRegistryError("program registry must be a JSON object")
    return payload


def validate_registry(root: Path = Path(".")) -> dict[str, Any]:
    payload = _load(root / REGISTRY)
    if payload.get("schema_version") != 1:
        raise ProgramRegistryError("unsupported program registry schema")
    if payload.get("controller") != "CHATGPT_RESEARCH_BRAIN_V1":
        raise ProgramRegistryError("program registry controller mismatch")

    policy = payload.get("portfolio_policy")
    if not isinstance(policy, dict):
        raise ProgramRegistryError("portfolio_policy must be an object")
    required_false = (
        "default_model_api_fallback",
        "allow_paid_data_without_user_approval",
        "allow_production_promotion",
        "allow_posthoc_gate_weakening",
    )
    for key in required_false:
        if policy.get(key) is not False:
            raise ProgramRegistryError(f"unsafe portfolio policy: {key}")
    max_total = policy.get("max_new_child_issues_per_cycle")
    max_program = policy.get("max_new_child_issues_per_program_per_cycle")
    if not isinstance(max_total, int) or not 1 <= max_total <= 10:
        raise ProgramRegistryError("invalid max_new_child_issues_per_cycle")
    if not isinstance(max_program, int) or not 1 <= max_program <= 3:
        raise ProgramRegistryError("invalid max_new_child_issues_per_program_per_cycle")

    programs = payload.get("programs")
    if not isinstance(programs, list) or not programs:
        raise ProgramRegistryError("program registry must contain programs")

    seen: set[str] = set()
    for program in programs:
        if not isinstance(program, dict):
            raise ProgramRegistryError("program entry must be an object")
        program_id = str(program.get("program_id", ""))
        if not PROGRAM_ID_RE.fullmatch(program_id):
            raise ProgramRegistryError(f"invalid program_id: {program_id!r}")
        if program_id in seen:
            raise ProgramRegistryError(f"duplicate program_id: {program_id}")
        seen.add(program_id)

        if program.get("status") not in VALID_STATUS:
            raise ProgramRegistryError(f"invalid status for {program_id}")
        if not str(program.get("objective", "")).strip():
            raise ProgramRegistryError(f"missing objective for {program_id}")
        if not str(program.get("current_frontier", "")).strip():
            raise ProgramRegistryError(f"missing current_frontier for {program_id}")

        completed = program.get("completed_issue_numbers")
        if not isinstance(completed, list) or any(
            not isinstance(number, int) or number <= 0 for number in completed
        ):
            raise ProgramRegistryError(
                f"completed_issue_numbers must be positive integers for {program_id}"
            )
        if len(set(completed)) != len(completed):
            raise ProgramRegistryError(f"duplicate completed issue in {program_id}")

        followups = program.get("allowed_follow_up_classes")
        if not isinstance(followups, list) or not followups:
            raise ProgramRegistryError(
                f"allowed_follow_up_classes required for {program_id}"
            )
        if any(
            not isinstance(value, str)
            or not VALID_FOLLOW_UP_RE.fullmatch(value)
            for value in followups
        ):
            raise ProgramRegistryError(
                f"invalid follow-up class for {program_id}"
            )

        stop_rules = program.get("stop_rules")
        if not isinstance(stop_rules, list) or len(stop_rules) < 2:
            raise ProgramRegistryError(f"stop_rules required for {program_id}")
        if any(not isinstance(rule, str) or not rule.strip() for rule in stop_rules):
            raise ProgramRegistryError(f"invalid stop rule for {program_id}")

    return payload


def _merged_issue_state(root: Path, issue_number: int) -> dict[str, Any] | None:
    state_path = (
        root
        / "research"
        / "agent_runs"
        / f"issue_{issue_number}"
        / "STATE.json"
    )
    if not state_path.is_file():
        return None
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProgramRegistryError(f"invalid merged STATE for issue {issue_number}")
    return {
        "issue_number": issue_number,
        "status": payload.get("status"),
        "summary": payload.get("summary"),
        "engine": payload.get("engine"),
    }


def build_brain_context(root: Path = Path(".")) -> dict[str, Any]:
    registry = validate_registry(root)
    programs_out: list[dict[str, Any]] = []
    for program in registry["programs"]:
        merged = [
            state
            for number in program["completed_issue_numbers"]
            if (state := _merged_issue_state(root, number)) is not None
        ]
        programs_out.append(
            {
                "program_id": program["program_id"],
                "title": program["title"],
                "status": program["status"],
                "objective": program["objective"],
                "current_frontier": program["current_frontier"],
                "completed_issue_numbers": program["completed_issue_numbers"],
                "merged_completed_issue_states": merged,
                "allowed_follow_up_classes": program["allowed_follow_up_classes"],
                "stop_rules": program["stop_rules"],
            }
        )
    return {
        "controller": registry["controller"],
        "portfolio_policy": registry["portfolio_policy"],
        "programs": programs_out,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--brain-context", action="store_true")
    args = parser.parse_args()

    if args.validate:
        validate_registry(args.root)
        print("OK")
        return
    if args.brain_context:
        print(json.dumps(build_brain_context(args.root), indent=2, ensure_ascii=False))
        return
    parser.error("use --validate or --brain-context")


if __name__ == "__main__":
    main()
