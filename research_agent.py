"""Manual-dispatch, research-only coordinator for Football AI Research Agent V1.

V1 does not execute arbitrary model-generated commands. It validates a requested
research hypothesis against the frozen signal registry and emits a deterministic
research specification for a later implementation/evaluation step.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from research_agent_safety import merge_results, validate_commands, validate_mode
from signal_research_registry_check import REGISTRY, validate_registry


@dataclass(frozen=True)
class ResearchSpec:
    agent_version: str
    task: str
    hypothesis_family: str
    mode: str
    decision: str
    existing_block_id: str | None
    research_only: bool
    automatic_promotion: bool
    supabase_writes: bool
    paid_odds_api_requests: bool
    arbitrary_command_execution: bool
    next_action: str


def _registry_payload(root: Path) -> dict:
    return json.loads((root / REGISTRY).read_text(encoding="utf-8"))


def find_existing_family(payload: dict, hypothesis_family: str) -> dict | None:
    target = hypothesis_family.strip().lower()
    for block in payload.get("blocks", []):
        if str(block.get("hypothesis_family", "")).strip().lower() == target:
            return block
    return None


def build_spec(
    task: str,
    hypothesis_family: str,
    mode: str = "historical_read_only",
    root: Path = Path("."),
) -> ResearchSpec:
    task = task.strip()
    hypothesis_family = hypothesis_family.strip()
    if not task:
        raise ValueError("task must be non-empty")
    if not hypothesis_family:
        raise ValueError("hypothesis_family must be non-empty")

    registry_errors = validate_registry(root)
    if registry_errors:
        raise ValueError("signal research registry is invalid: " + "; ".join(registry_errors))

    safety = merge_results(validate_mode(mode), validate_commands(()))
    if not safety.ok:
        raise ValueError("; ".join(safety.errors))

    existing = find_existing_family(_registry_payload(root), hypothesis_family)
    if existing is not None:
        return ResearchSpec(
            agent_version="RESEARCH_AGENT_V1",
            task=task,
            hypothesis_family=hypothesis_family,
            mode=mode,
            decision="REJECT_EXISTING_HYPOTHESIS_FAMILY",
            existing_block_id=str(existing["id"]),
            research_only=True,
            automatic_promotion=False,
            supabase_writes=False,
            paid_odds_api_requests=False,
            arbitrary_command_execution=False,
            next_action="Do not retune on the seen sample. Propose an independently justified hypothesis family.",
        )

    return ResearchSpec(
        agent_version="RESEARCH_AGENT_V1",
        task=task,
        hypothesis_family=hypothesis_family,
        mode=mode,
        decision="READY_FOR_PREREGISTRATION",
        existing_block_id=None,
        research_only=True,
        automatic_promotion=False,
        supabase_writes=False,
        paid_odds_api_requests=False,
        arbitrary_command_execution=False,
        next_action="Create a frozen preregistration before any outcome-reading evaluation.",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--hypothesis-family", required=True)
    parser.add_argument("--mode", default="historical_read_only")
    parser.add_argument("--output", type=Path, default=Path("artifacts/research_agent_v1/spec.json"))
    args = parser.parse_args()

    spec = build_spec(args.task, args.hypothesis_family, args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(asdict(spec), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(asdict(spec), indent=2))


if __name__ == "__main__":
    main()
