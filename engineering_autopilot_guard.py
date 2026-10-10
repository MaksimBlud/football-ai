"""Fail-closed path guard for the independent GitHub Actions coding agent."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ALLOWLIST = {
    "frontend": frozenset({"static/match.html", "tests/test_product_ui_contract.py"}),
    "backend": frozenset({"product_snapshot_store.py", "tests/test_product_snapshot_store.py"}),
}
GENERATED_PREFIXES = (".gemini/", "gemini-artifacts/")
MAX_DIFF_BYTES = 120_000


class UnsafeAgentChange(ValueError):
    pass


def parse_status(status: bytes) -> list[tuple[str, str]]:
    """Decode git status --porcelain=v1 -z -uall, rejecting renames/copies."""
    entries = status.split(b"\0")
    if entries[-1] != b"":
        raise UnsafeAgentChange("incomplete NUL-delimited git status")
    result = []
    for item in entries[:-1]:
        if len(item) < 4 or item[2:3] != b" ":
            raise UnsafeAgentChange("malformed git status entry")
        flags = item[:2].decode("ascii", errors="strict")
        if any(x in flags for x in "RCDU"):
            raise UnsafeAgentChange(f"rename/copy/delete/conflict forbidden ({flags})")
        if flags not in {" M", "M ", "MM", "A ", "??"}:
            raise UnsafeAgentChange(f"unexpected git status flags ({flags})")
        path = item[3:].decode("utf-8", errors="strict")
        result.append((flags, path))
    return result


def validate_paths(role: str, entries: list[tuple[str, str]], root: Path) -> list[str]:
    if role not in ALLOWLIST:
        raise UnsafeAgentChange(f"unknown role {role!r}")
    permitted = ALLOWLIST[role]
    changes: list[str] = []
    for flags, name in entries:
        if name.startswith(GENERATED_PREFIXES):
            continue  # Runner-generated Gemini settings/logs are never staged.
        if name not in permitted:
            raise UnsafeAgentChange(f"out-of-scope change: {name}")
        target = root / name
        if target.is_symlink() or not target.is_file():
            raise UnsafeAgentChange(f"not a regular existing file: {name}")
        if flags not in {" M", "M "}:
            raise UnsafeAgentChange(f"only modifications of existing files allowed: {name} [{flags}]")
        changes.append(name)
    if not changes:
        raise UnsafeAgentChange("agent produced no allowed code changes")
    if len(changes) != len(set(changes)) or len(changes) > 2:
        raise UnsafeAgentChange("duplicate or excessive changed files")
    return sorted(changes)


def validate_worktree(role: str, root: Path) -> list[str]:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root, check=True, capture_output=True,
    ).stdout
    allowed = validate_paths(role, parse_status(status), root)
    diff = subprocess.run(
        ["git", "diff", "--", *allowed], cwd=root, check=True, capture_output=True,
    ).stdout
    if len(diff) > MAX_DIFF_BYTES:
        raise UnsafeAgentChange("diff exceeds bounded size limit")
    if not diff.strip():
        raise UnsafeAgentChange("no non-staged content changes")
    subprocess.run(["git", "diff", "--check", "--", *allowed], cwd=root, check=True)
    return allowed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=sorted(ALLOWLIST))
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        paths = validate_worktree(args.role, Path(args.root).resolve())
    except (UnsafeAgentChange, subprocess.CalledProcessError) as exc:
        print(f"ENGINEERING_AUTOPILOT_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a", encoding="utf-8") as output:
        output.write("has_changes=true\n")
    print("SAFE_CHANGED_FILES=" + ",".join(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
