"""Deterministic state and retry helpers for Research Orchestrator V4."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

VALID_STATUSES = {"CONTINUE", "DONE", "BLOCKED"}
TRANSIENT_MARKERS = (
    "429",
    "503",
    "quota",
    "resource_exhausted",
    "high demand",
    "unavailable",
    "retry after",
    "rate limit",
    "exhausted your daily quota",
)
PERMANENT_MARKERS = (
    "invalid api key",
    "api key not valid",
    "permission denied",
    "unauthenticated",
    "forbidden",
    "billing required",
)


@dataclass(frozen=True)
class AgentState:
    status: str
    summary: str
    next_step: str | None
    blocker: str | None


def branch_name(issue_number: int) -> str:
    return f"agent/v4-issue-{issue_number}"


def issue_root(issue_number: int, root: Path = Path(".")) -> Path:
    return root / "research" / "agent_runs" / f"issue_{issue_number}"


def docs_root(issue_number: int, root: Path = Path(".")) -> Path:
    return root / "docs" / "agent_runs" / f"issue_{issue_number}"


def classify_model_errors(texts: list[str]) -> str:
    blob = "\n".join(texts).lower()
    if any(marker in blob for marker in PERMANENT_MARKERS):
        return "BLOCKED"
    if any(marker in blob for marker in TRANSIENT_MARKERS):
        return "QUOTA_WAIT"
    # The official Gemini action does not reliably expose gemini_errors on failed\n    # steps. Unknown model-only failures are therefore treated as retryable.\n    return "QUOTA_WAIT"\n\n\ndef load_state(issue_number: int, root: Path = Path(".")) -> AgentState:
    path = issue_root(issue_number, root) / "STATE.json"
    if not path.is_file():
        raise ValueError(f"missing required state file: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    status = str(payload.get("status", "")).upper().strip()
    summary = str(payload.get("summary", "")).strip()
    next_step = payload.get("next_step")
    blocker = payload.get("blocker")
    next_step = str(next_step).strip() if next_step is not None else None
    blocker = str(blocker).strip() if blocker is not None else None

    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status {status!r}; expected one of {sorted(VALID_STATUSES)}")
    if not summary:
        raise ValueError("STATE.json requires a non-empty summary")
    if status == "CONTINUE" and not next_step:
        raise ValueError("CONTINUE requires a non-empty next_step")
    if status == "BLOCKED" and not blocker:
        raise ValueError("BLOCKED requires a non-empty blocker")
    if status == "DONE":
        report = docs_root(issue_number, root) / "FINAL_REPORT.md"
        if not report.is_file() or not report.read_text(encoding="utf-8").strip():
            raise ValueError(f"DONE requires a non-empty final report: {report}")

    return AgentState(status=status, summary=summary, next_step=next_step, blocker=blocker)


def _main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    classify = sub.add_parser("classify-errors")
    classify.add_argument("--env", action="append", default=[])

    state = sub.add_parser("validate-state")
    state.add_argument("--issue-number", type=int, required=True)
    state.add_argument("--root", type=Path, default=Path("."))
    state.add_argument("--github-output", type=Path)

    branch = sub.add_parser("branch-name")
    branch.add_argument("--issue-number", type=int, required=True)

    args = parser.parse_args()

    if args.command == "classify-errors":
        texts = [os.environ.get(name, "") for name in args.env]
        print(classify_model_errors(texts))
        return

    if args.command == "branch-name":
        print(branch_name(args.issue_number))
        return

    result = load_state(args.issue_number, args.root)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"status={result.status}\n")


if __name__ == "__main__":
    _main()
