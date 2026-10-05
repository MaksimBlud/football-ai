"""Deterministic scaffold generator for unsupported Research V5 families.

This tool reads only Issue metadata. It never reads match outcomes, calls a model API,
writes production, or executes arbitrary code. The output is a reviewable recipe request
that tells maintainers exactly what deterministic implementation is still required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research_agent_issue import build_issue_plan, parse_issue
from research_agent_v5 import supports_family

ENGINE = "V5_DETERMINISTIC_NO_API"
SAFETY = {
    "model_api": False,
    "paid_odds_api": False,
    "supabase_writes": False,
    "production_operations": False,
    "automatic_promotion": False,
    "outcomes_read_during_scaffold": False,
}


class ScaffoldError(RuntimeError):
    pass


def build_scaffold(issue: dict[str, Any], root: Path = Path(".")) -> dict[str, Any]:
    number = issue.get("number")
    if not isinstance(number, int) or number <= 0:
        raise ScaffoldError("issue.number must be a positive integer")

    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    parsed = parse_issue(title, body)
    plan = build_issue_plan(title, body, root=root)

    if plan["decision"] != "READY_FOR_PREREGISTRATION":
        raise ScaffoldError(
            "Issue is not ready for a new deterministic recipe: "
            + str(plan["decision"])
        )

    family = parsed["hypothesis_family"]
    if supports_family(root, family):
        raise ScaffoldError(f"family {family!r} is already supported by V5")

    return {
        "schema_version": 1,
        "engine": ENGINE,
        "issue_number": number,
        "issue_title": title,
        "research_question": parsed["research_question"],
        "hypothesis_family": family,
        "independent_information_justification": parsed[
            "independent_information_justification"
        ],
        "mode": plan["mode"],
        "decision": "NEEDS_DETERMINISTIC_RECIPE",
        "safety": SAFETY,
        "required_implementation": {
            "evaluator": (
                "Add a deterministic Python evaluator that consumes only preregistered "
                "allowed inputs and returns machine-readable results."
            ),
            "handler": (
                "Add a reviewed Research V5 handler that freezes the protocol before "
                "evaluation and writes only inside the current Issue sandbox."
            ),
            "registry": (
                "Register the family in research/v5_recipe_registry.json with a bounded "
                "max_iterations and the exact no-API safety contract."
            ),
            "tests": (
                "Add unit tests for the evaluator/handler and workflow contract tests "
                "covering fail-closed safety, temporal/OOS rules, and DONE/CONTINUE state."
            ),
        },
        "expected_lifecycle": [
            "PREREGISTRATION",
            "DETERMINISTIC_EVALUATION",
            "RESULT.json",
            "FINAL_REPORT.md",
            "DONE",
        ],
        "prohibited": [
            "model-generated shell commands",
            "automatic threshold retuning on seen outcomes",
            "paid Odds API calls",
            "Supabase writes",
            "production .pkl writes",
            "automatic promotion",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    req = payload["required_implementation"]
    lines = [
        f"# Research V5 recipe request — Issue #{payload['issue_number']}",
        "",
        f"**Family:** `{payload['hypothesis_family']}`",
        "",
        f"**Question:** {payload['research_question']}",
        "",
        f"**Decision:** `{payload['decision']}`",
        "",
        "## Required deterministic implementation",
        "",
        f"- Evaluator: {req['evaluator']}",
        f"- Handler: {req['handler']}",
        f"- Registry: {req['registry']}",
        f"- Tests: {req['tests']}",
        "",
        "## Safety",
        "",
        "- model API: forbidden by default",
        "- paid Odds API: forbidden",
        "- Supabase writes: forbidden",
        "- production operations: forbidden",
        "- automatic promotion: forbidden",
        "- outcomes read during scaffold: no",
        "",
        "This scaffold is intake metadata only. It does not claim that the new hypothesis",
        "family can already execute autonomously.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    issue = json.loads(args.issue_json.read_text(encoding="utf-8"))
    payload = build_scaffold(issue, root=args.root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.output_markdown.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
