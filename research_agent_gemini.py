"""Deterministic post-edit gates for the Gemini research agent."""
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from research_agent_safety import SafetyResult, merge_results, validate_changed_paths


@dataclass(frozen=True)
class StatusEntry:
    status: str
    path: str


def parse_porcelain(text: str) -> list[StatusEntry]:
    entries: list[StatusEntry] = []
    for raw in text.splitlines():
        if not raw:
            continue
        if len(raw) < 4:
            raise ValueError(f"invalid git status line: {raw!r}")
        status = raw[:2]
        path = raw[3:]
        entries.append(StatusEntry(status=status, path=path))
    return entries


def allowed_roots(issue_number: int) -> tuple[str, ...]:
    suffix = f"issue_{issue_number}/"
    return (
        f"research/agent_runs/{suffix}",
        f"tests/agent_runs/{suffix}",
        f"docs/agent_runs/{suffix}",
    )


def validate_gemini_status(text: str, issue_number: int) -> SafetyResult:
    try:
        entries = parse_porcelain(text)
    except ValueError as exc:
        return SafetyResult(False, (str(exc),))

    errors: list[str] = []
    roots = allowed_roots(issue_number)
    destructive = {"D", "R", "C"}

    for entry in entries:
        if any(code in destructive for code in entry.status):
            errors.append(f"Gemini V3 forbids delete/rename/copy status: {entry.status} {entry.path}")
        if not entry.path.startswith(roots):
            errors.append(
                f"Gemini V3 path outside issue sandbox: {entry.path}; "
                f"allowed roots={roots}"
            )

    base = validate_changed_paths(entry.path for entry in entries)
    return merge_results(base, SafetyResult(not errors, tuple(errors)))


def stage_validated_status(text: str, issue_number: int) -> None:
    result = validate_gemini_status(text, issue_number)
    if not result.ok:
        raise RuntimeError("\n".join(result.errors))
    for entry in parse_porcelain(text):
        subprocess.run(["git", "add", "--", entry.path], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-status")
    validate.add_argument("--issue-number", type=int, required=True)
    validate.add_argument("--status-file", type=Path, required=True)

    stage = sub.add_parser("stage-status")
    stage.add_argument("--issue-number", type=int, required=True)
    stage.add_argument("--status-file", type=Path, required=True)

    args = parser.parse_args()
    text = args.status_file.read_text(encoding="utf-8")

    if args.command == "validate-status":
        result = validate_gemini_status(text, args.issue_number)
        if not result.ok:
            raise SystemExit("GEMINI_RESEARCH_SANDBOX_VIOLATION\n" + "\n".join(result.errors))
        print("PASS: Gemini changes confined to issue sandbox")
    else:
        stage_validated_status(text, args.issue_number)
        print("PASS: staged validated Gemini issue-sandbox changes only")


if __name__ == "__main__":
    main()
