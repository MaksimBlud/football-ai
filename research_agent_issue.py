"""Issue-driven intake for Football AI Research Agent V2."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path

from research_agent import build_spec

PREFIX = "[AGENT-RESEARCH]"
FAMILY_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def _field(body: str, key: str) -> str | None:
    prefix = key.lower() + ":"
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(prefix):
            value = stripped[len(prefix):].strip()
            return value or None
    return None


def parse_issue(title: str, body: str) -> dict:
    if not title.startswith(PREFIX):
        raise ValueError(f"title must start with {PREFIX}")
    question = _field(body, "research_question") or title[len(PREFIX):].strip()
    family = _field(body, "hypothesis_family")
    justification = _field(body, "independent_information_justification")
    if not question:
        raise ValueError("research_question is required")
    if not family:
        raise ValueError("hypothesis_family is required")
    if not FAMILY_RE.fullmatch(family):
        raise ValueError("hypothesis_family must be lower snake_case")
    return {
        "research_question": question,
        "hypothesis_family": family,
        "independent_information_justification": justification,
    }


def build_issue_plan(title: str, body: str, root: Path = Path(".")) -> dict:
    parsed = parse_issue(title, body)
    spec = build_spec(
        parsed["research_question"],
        parsed["hypothesis_family"],
        root=root,
    )
    payload = asdict(spec)
    payload["independent_information_justification"] = parsed[
        "independent_information_justification"
    ]
    if (
        payload["decision"] == "READY_FOR_PREREGISTRATION"
        and not parsed["independent_information_justification"]
    ):
        payload["decision"] = "NEEDS_INDEPENDENT_INFORMATION_JUSTIFICATION"
        payload["next_action"] = (
            "Add independent_information_justification explaining why this feature family "
            "is not a retune of a previously seen signal family."
        )
    payload["issue_triggered"] = True
    payload["outcomes_read"] = False
    return payload


def render_markdown(plan: dict) -> str:
    lines = [
        "## Football AI Research Agent V2",
        "",
        f"**Decision:** `{plan['decision']}`",
        f"**Hypothesis family:** `{plan['hypothesis_family']}`",
        f"**Mode:** `{plan['mode']}`",
        f"**Existing block:** `{plan['existing_block_id'] or 'none'}`",
        "",
        f"**Next action:** {plan['next_action']}",
        "",
        "Safety contract:",
        "- research only: yes",
        "- automatic promotion: no",
        "- Supabase writes: no",
        "- paid Odds API requests: no",
        "- arbitrary command execution: no",
        "- outcomes read during intake: no",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()

    event = json.loads(args.event.read_text(encoding="utf-8"))
    issue = event["issue"]
    plan = build_issue_plan(issue["title"], issue.get("body") or "")

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
