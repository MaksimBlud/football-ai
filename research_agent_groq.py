"""Groq-backed file-only research agent for Research Orchestrator V4.

The agent exposes only repository read/search tools and issue-sandbox write tools.
It uses Groq's OpenAI-compatible Chat Completions API with tool calling.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_READ_CHARS = 6_000
MAX_TOOL_RESULT_CHARS = 12_000
MAX_GREP_RESULTS = 80
MAX_LIST_ENTRIES = 120
MAX_PINNED_GITHUB_FILE_BYTES = 2_000_000
PINNED_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
GIT_BLOB_RE = re.compile(r"^[0-9a-fA-F]{40}$")

TRANSIENT_HTTP = {429, 500, 502, 503, 504}
LONG_RETRY_SECONDS = 180.0


class GroqAgentError(RuntimeError):
    pass


class GroqToolFormatError(GroqAgentError):
    """Groq rejected malformed JSON arguments for a generated tool call."""


class GroqLongQuotaWait(GroqAgentError):
    """Provider supplied a long retry-after window that should survive across runs."""

    def __init__(self, retry_after_seconds: float):
        super().__init__(f"Groq long quota wait: {retry_after_seconds:.3f}s")
        self.retry_after_seconds = retry_after_seconds



def _safe_rel(path: str) -> str:
    candidate = PurePosixPath(path.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise GroqAgentError(f"unsafe path: {path}")
    normalized = str(candidate)
    if normalized in {"", "."}:
        return "."
    if normalized == ".git" or normalized.startswith(".git/"):
        raise GroqAgentError(".git is not readable by the research agent")
    return normalized


def _resolve_repo(root: Path, path: str) -> Path:
    rel = _safe_rel(path)
    resolved = (root / rel).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise GroqAgentError(f"path escapes repository: {path}")
    return resolved


def _allowed_write_roots(issue_number: int) -> tuple[str, ...]:
    suffix = f"issue_{issue_number}/"
    return (
        f"research/agent_runs/{suffix}",
        f"tests/agent_runs/{suffix}",
        f"docs/agent_runs/{suffix}",
    )


def _resolve_write(root: Path, issue_number: int, path: str) -> Path:
    rel = _safe_rel(path)
    if not rel.startswith(_allowed_write_roots(issue_number)):
        raise GroqAgentError(
            f"write outside issue sandbox: {rel}; allowed={_allowed_write_roots(issue_number)}"
        )
    return _resolve_repo(root, rel)


def _read_text(path: Path, max_chars: int = MAX_READ_CHARS) -> str:
    if not path.is_file():
        raise GroqAgentError(f"not a file: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[truncated {len(text) - max_chars} chars]"


def list_directory(root: Path, path: str = ".") -> dict[str, Any]:
    target = _resolve_repo(root, path)
    if not target.is_dir():
        raise GroqAgentError(f"not a directory: {path}")
    entries: list[dict[str, str]] = []
    for child in sorted(target.iterdir(), key=lambda p: p.name.lower()):
        if child.name == ".git":
            continue
        entries.append(
            {
                "name": child.name,
                "type": "dir" if child.is_dir() else "file",
                "path": str(child.relative_to(root)).replace("\\", "/"),
            }
        )
        if len(entries) >= MAX_LIST_ENTRIES:
            break
    return {"entries": entries, "truncated": len(list(target.iterdir())) > len(entries)}


def read_file(root: Path, path: str) -> dict[str, Any]:
    target = _resolve_repo(root, path)
    return {"path": path, "content": _read_text(target)}


def read_many_files(root: Path, paths: list[str]) -> dict[str, Any]:
    if len(paths) > 4:
        raise GroqAgentError("read_many_files accepts at most 4 paths")
    files: list[dict[str, Any]] = []
    remaining = 8_000
    for path in paths:
        target = _resolve_repo(root, path)
        content = _read_text(target, max_chars=min(2_500, remaining))
        files.append({"path": path, "content": content})
        remaining -= len(content)
        if remaining <= 0:
            break
    return {"files": files, "truncated": len(files) < len(paths)}


def glob_files(root: Path, pattern: str) -> dict[str, Any]:
    pattern = _safe_rel(pattern)
    matches: list[str] = []
    for path in root.glob(pattern):
        try:
            rel = str(path.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if path.is_file():
            matches.append(rel)
        if len(matches) >= MAX_GREP_RESULTS:
            break
    return {"matches": sorted(matches), "truncated": len(matches) >= MAX_GREP_RESULTS}


def grep_search(
    root: Path,
    query: str,
    path: str = ".",
    file_glob: str = "*",
) -> dict[str, Any]:
    base = _resolve_repo(root, path)
    if not base.exists():
        raise GroqAgentError(f"path does not exist: {path}")
    needle = query.lower()
    results: list[dict[str, Any]] = []
    candidates = [base] if base.is_file() else base.rglob("*")
    for candidate in candidates:
        if not candidate.is_file() or ".git" in candidate.parts:
            continue
        if not fnmatch.fnmatch(candidate.name, file_glob):
            continue
        try:
            lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if needle in line.lower():
                results.append(
                    {
                        "path": str(candidate.relative_to(root)).replace("\\", "/"),
                        "line": lineno,
                        "text": line[:500],
                    }
                )
                if len(results) >= MAX_GREP_RESULTS:
                    return {"matches": results, "truncated": True}
    return {"matches": results, "truncated": False}


def fetch_pinned_github_file(
    root: Path,
    issue_number: int,
    repository: str,
    commit: str,
    path: str,
    destination: str,
    expected_blob_sha: str | None = None,
) -> dict[str, Any]:
    repository = repository.strip()
    commit = commit.strip()
    source_path = _safe_rel(path)
    if source_path == ".":
        raise GroqAgentError("pinned GitHub source path must be a file path")
    if not PINNED_GITHUB_REPO_RE.fullmatch(repository):
        raise GroqAgentError(f"invalid public GitHub repository: {repository}")
    if not FULL_COMMIT_RE.fullmatch(commit):
        raise GroqAgentError("pinned GitHub source requires a full 40-hex commit SHA")
    if expected_blob_sha is not None:
        expected_blob_sha = expected_blob_sha.strip().lower()
        if not GIT_BLOB_RE.fullmatch(expected_blob_sha):
            raise GroqAgentError("expected_blob_sha must be a 40-hex Git blob SHA")

    target = _resolve_write(root, issue_number, destination)
    owner, repo_name = repository.split("/", 1)
    encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in PurePosixPath(source_path).parts)
    url = (
        "https://raw.githubusercontent.com/"
        f"{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(repo_name, safe='')}/"
        f"{commit}/{encoded_path}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "football-ai-research-v4"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(MAX_PINNED_GITHUB_FILE_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise GroqAgentError(f"failed to fetch pinned public GitHub source: {exc}") from exc

    if len(data) > MAX_PINNED_GITHUB_FILE_BYTES:
        raise GroqAgentError(
            f"pinned public GitHub file exceeds {MAX_PINNED_GITHUB_FILE_BYTES} bytes"
        )
    git_blob_sha = hashlib.sha1(
        f"blob {len(data)}\0".encode("ascii") + data,
        usedforsecurity=False,
    ).hexdigest()
    if expected_blob_sha is not None and git_blob_sha != expected_blob_sha:
        raise GroqAgentError(
            f"Git blob SHA mismatch: expected {expected_blob_sha}, got {git_blob_sha}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        "repository": repository,
        "commit": commit.lower(),
        "source_path": source_path,
        "destination": destination,
        "bytes_written": len(data),
        "git_blob_sha": git_blob_sha,
    }


def fetch_pinned_github_files(
    root: Path,
    issue_number: int,
    files: list[dict[str, Any]],
) -> dict[str, Any]:
    if not 1 <= len(files) <= 4:
        raise GroqAgentError("fetch_pinned_github_files accepts 1 to 4 files")
    fetched = []
    for item in files:
        fetched.append(
            fetch_pinned_github_file(
                root,
                issue_number,
                str(item["repository"]),
                str(item["commit"]),
                str(item["path"]),
                str(item["destination"]),
                (
                    str(item["expected_blob_sha"])
                    if item.get("expected_blob_sha") is not None
                    else None
                ),
            )
        )
    return {"files": fetched}


def write_quota_wait(
    root: Path,
    issue_number: int,
    retry_after_seconds: float,
    *,
    buffer_seconds: int = 15,
) -> dict[str, Any]:
    if retry_after_seconds <= 0:
        raise GroqAgentError("retry_after_seconds must be positive")
    observed = datetime.now(UTC)
    delay = math.ceil(retry_after_seconds) + buffer_seconds
    not_before = observed + timedelta(seconds=delay)
    path = f"research/agent_runs/issue_{issue_number}/QUOTA_WAIT.json"
    target = _resolve_write(root, issue_number, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "provider": "groq",
        "retry_after_seconds": math.ceil(retry_after_seconds),
        "buffer_seconds": buffer_seconds,
        "observed_at_utc": observed.isoformat(),
        "not_before_utc": not_before.isoformat(),
        "not_before_epoch": int(not_before.timestamp()),
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"path": path, **payload}


def write_file(root: Path, issue_number: int, path: str, content: str) -> dict[str, Any]:
    target = _resolve_write(root, issue_number, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": path, "chars_written": len(content)}


def replace_text(
    root: Path,
    issue_number: int,
    path: str,
    old: str,
    new: str,
    count: int = 1,
) -> dict[str, Any]:
    target = _resolve_write(root, issue_number, path)
    if not target.is_file():
        raise GroqAgentError(f"replace target does not exist: {path}")
    text = target.read_text(encoding="utf-8")
    occurrences = text.count(old)
    if occurrences == 0:
        raise GroqAgentError("replace text not found")
    if count < 1:
        raise GroqAgentError("replace count must be >= 1")
    updated = text.replace(old, new, count)
    target.write_text(updated, encoding="utf-8")
    return {
        "path": path,
        "replacements": min(count, occurrences),
        "remaining_matches": updated.count(old),
    }


def record_progress(
    root: Path,
    issue_number: int,
    finding: str,
    evidence: str,
    next_action: str | None = None,
) -> dict[str, Any]:
    finding = finding.strip()
    evidence = evidence.strip()
    next_action = next_action.strip() if next_action else None
    if not finding:
        raise GroqAgentError("progress finding must be non-empty")
    if not evidence:
        raise GroqAgentError("progress evidence must be non-empty")
    if len(finding) > 1000 or len(evidence) > 1400 or (next_action and len(next_action) > 1000):
        raise GroqAgentError("progress fields must stay compact")

    path = f"research/agent_runs/issue_{issue_number}/PROGRESS.md"
    target = _resolve_write(root, issue_number, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    section = [
        "## Research checkpoint",
        "",
        f"**Finding:** {finding}",
        "",
        f"**Evidence:** {evidence}",
    ]
    if next_action:
        section.extend(["", f"**Next action:** {next_action}"])
    text = "\n".join(section) + "\n\n"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(text)
    return {"path": path, "chars_appended": len(text)}


def write_state(
    root: Path,
    issue_number: int,
    status: str,
    summary: str,
    next_step: str | None = None,
    blocker: str | None = None,
) -> dict[str, Any]:
    normalized = status.strip().upper()
    if normalized not in {"CONTINUE", "DONE", "BLOCKED"}:
        raise GroqAgentError(f"invalid state status: {status}")
    summary = summary.strip()
    if not summary:
        raise GroqAgentError("STATE summary must be non-empty")
    if normalized == "CONTINUE":
        if not next_step or not next_step.strip():
            raise GroqAgentError("CONTINUE requires next_step")
        blocker = None
    elif normalized == "BLOCKED":
        if not blocker or not blocker.strip():
            raise GroqAgentError("BLOCKED requires blocker")
        next_step = None
    else:
        next_step = None
        blocker = None

    path = f"research/agent_runs/issue_{issue_number}/STATE.json"
    target = _resolve_write(root, issue_number, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": normalized,
        "summary": summary,
        "next_step": next_step.strip() if next_step else None,
        "blocker": blocker.strip() if blocker else None,
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"path": path, "state": payload}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List a repository directory. Read-only.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read one UTF-8 repository file. Large files are truncated.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_many_files",
            "description": "Read up to six UTF-8 repository files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 4,
                    }
                },
                "required": ["paths"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find repository files using a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search case-insensitively for text in repository files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                    "file_glob": {"type": "string", "default": "*"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_pinned_github_files",
            "description": (
                "Fetch 1-4 immutable public GitHub files by full commit SHA into this Issue sandbox. "
                "Optionally verify the exact Git blob SHA. Raw GitHub GET only; no auth or paid API."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "properties": {
                                "repository": {"type": "string"},
                                "commit": {
                                    "type": "string",
                                    "pattern": "^[0-9a-fA-F]{40}$",
                                },
                                "path": {"type": "string"},
                                "destination": {"type": "string"},
                                "expected_blob_sha": {
                                    "type": "string",
                                    "pattern": "^[0-9a-fA-F]{40}$",
                                },
                            },
                            "required": ["repository", "commit", "path", "destination"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["files"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_progress",
            "description": (
                "Append one compact, concrete research checkpoint to PROGRESS.md. "
                "Use repository evidence, not a restatement of the plan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "finding": {"type": "string", "maxLength": 1000},
                    "evidence": {"type": "string", "maxLength": 1400},
                    "next_action": {"type": "string", "maxLength": 1000},
                },
                "required": ["finding", "evidence"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_state",
            "description": (
                "Write canonical STATE.json for this Issue. Use this before any long artifact. "
                "CONTINUE requires next_step; BLOCKED requires blocker."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["CONTINUE", "DONE", "BLOCKED"],
                    },
                    "summary": {"type": "string", "maxLength": 1200},
                    "next_step": {"type": "string", "maxLength": 1200},
                    "blocker": {"type": "string", "maxLength": 1200},
                },
                "required": ["status", "summary"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a UTF-8 file. Writes are restricted to this Issue sandbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace",
            "description": "Replace exact text in an existing Issue-sandbox file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                    "count": {"type": "integer", "minimum": 1, "default": 1},
                },
                "required": ["path", "old", "new"],
                "additionalProperties": False,
            },
        },
    },
]

WRITE_TOOLS = [
    tool
    for tool in TOOLS
    if tool["function"]["name"]
    in {"fetch_pinned_github_files", "record_progress", "write_file", "replace", "write_state"}
]
FINAL_TOOLS = [
    tool for tool in TOOLS if tool["function"]["name"] == "write_state"
]
PROGRESS_TOOLS = [
    tool for tool in TOOLS if tool["function"]["name"] == "record_progress"
]


def _tool_result(root: Path, issue_number: int, name: str, args: dict[str, Any]) -> Any:
    if name == "list_directory":
        return list_directory(root, args.get("path", "."))
    if name == "read_file":
        return read_file(root, args["path"])
    if name == "read_many_files":
        return read_many_files(root, args["paths"])
    if name == "glob":
        return glob_files(root, args["pattern"])
    if name == "grep_search":
        return grep_search(
            root,
            args["query"],
            args.get("path", "."),
            args.get("file_glob", "*"),
        )
    if name == "fetch_pinned_github_files":
        return fetch_pinned_github_files(root, issue_number, args["files"])
    if name == "record_progress":
        return record_progress(
            root,
            issue_number,
            args["finding"],
            args["evidence"],
            args.get("next_action"),
        )
    if name == "write_state":
        return write_state(
            root,
            issue_number,
            args["status"],
            args["summary"],
            args.get("next_step"),
            args.get("blocker"),
        )
    if name == "write_file":
        return write_file(root, issue_number, args["path"], args["content"])
    if name == "replace":
        return replace_text(
            root,
            issue_number,
            args["path"],
            args["old"],
            args["new"],
            int(args.get("count", 1)),
        )
    raise GroqAgentError(f"unknown tool: {name}")


def _duration_seconds(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip().lower()
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
        return float(value)
    total = 0.0
    found = False
    for number, unit in re.findall(r"([0-9]+(?:\.[0-9]+)?)(ms|s|m|h)", value):
        found = True
        amount = float(number)
        if unit == "ms":
            total += amount / 1000
        elif unit == "s":
            total += amount
        elif unit == "m":
            total += amount * 60
        elif unit == "h":
            total += amount * 3600
    return total if found else None


def _request(
    api_key: str,
    payload: dict[str, Any],
    *,
    max_retries: int = 2,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(max_retries + 1):
        request = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "football-ai-research-v4",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                raw = response.read().decode("utf-8")
                result = json.loads(raw)
                result["_groq_rate_limit"] = {
                    "remaining_requests": response.headers.get("x-ratelimit-remaining-requests"),
                    "reset_requests": response.headers.get("x-ratelimit-reset-requests"),
                    "remaining_tokens": response.headers.get("x-ratelimit-remaining-tokens"),
                    "reset_tokens": response.headers.get("x-ratelimit-reset-tokens"),
                }
                return result
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            retry_after = exc.headers.get("retry-after")
            remaining_requests = exc.headers.get("x-ratelimit-remaining-requests")
            reset_requests = exc.headers.get("x-ratelimit-reset-requests")
            print(
                "GROQ_HTTP_ERROR "
                f"status={exc.code} retry_after={retry_after!r} "
                f"remaining_requests={remaining_requests!r} reset_requests={reset_requests!r} "
                f"body={raw[:2000]}",
                file=sys.stderr,
            )
            lower_raw = raw.lower()
            if exc.code == 400 and (
                "tool_use_failed" in lower_raw
                or "failed to parse tool call arguments as json" in lower_raw
            ):
                print("GROQ_TOOL_FORMAT_ERROR retryable=true", file=sys.stderr)
                raise GroqToolFormatError("Groq tool_use_failed") from exc
            if exc.code not in TRANSIENT_HTTP:
                raise GroqAgentError(f"Groq API HTTP {exc.code}") from exc
            delay = _duration_seconds(retry_after)
            if delay is not None and delay > LONG_RETRY_SECONDS:
                print(
                    f"GROQ_LONG_QUOTA_WAIT retry_after_seconds={delay:.3f}",
                    file=sys.stderr,
                )
                raise GroqLongQuotaWait(delay) from exc
            if attempt >= max_retries:
                raise GroqAgentError(f"Groq API HTTP {exc.code}") from exc
            if remaining_requests == "0":
                if reset_requests:
                    print(
                        f"Groq daily/request quota exhausted. Retry after {reset_requests}.",
                        file=sys.stderr,
                    )
                raise GroqAgentError("Groq daily quota exhausted") from exc
            if delay is None:
                delay = min(65.0, 10.0 * (attempt + 1))
            delay = min(max(delay + 2.0, 2.0), 75.0)
            print(f"Please retry after {delay:.0f}s.", file=sys.stderr)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            print(f"GROQ_NETWORK_ERROR {exc}", file=sys.stderr)
            if attempt >= max_retries:
                raise GroqAgentError("Groq network error") from exc
            time.sleep(5 * (attempt + 1))
    raise GroqAgentError("Groq request failed")


def _message_from_api(message: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"role": "assistant"}
    if message.get("content") is not None:
        result["content"] = message.get("content")
    if message.get("tool_calls"):
        result["tool_calls"] = message["tool_calls"]
    return result


def _substantive_snapshot(root: Path, issue_number: int) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    excluded = {
        f"research/agent_runs/issue_{issue_number}/STATE.json",
        f"research/agent_runs/issue_{issue_number}/USAGE.json",
        f"research/agent_runs/issue_{issue_number}/QUOTA_WAIT.json",
    }
    for write_root in _allowed_write_roots(issue_number):
        base = root / write_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            if rel in excluded or "__pycache__" in path.parts:
                continue
            snapshot[rel] = path.read_bytes()
    return snapshot


def run_agent(
    *,
    root: Path,
    issue_number: int,
    issue_title: str,
    issue_body: str,
    hypothesis_family: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    max_turns: int = 4,
) -> None:
    state_path = root / "research" / "agent_runs" / f"issue_{issue_number}" / "STATE.json"
    final_path = root / "docs" / "agent_runs" / f"issue_{issue_number}" / "FINAL_REPORT.md"
    initial_state = state_path.read_bytes() if state_path.is_file() else None
    initial_substantive = _substantive_snapshot(root, issue_number)

    def state_updated() -> bool:
        if not state_path.is_file():
            return False
        current = state_path.read_bytes()
        return initial_state is None or current != initial_state

    def substantive_updated() -> bool:
        return _substantive_snapshot(root, issue_number) != initial_substantive

    def iteration_complete() -> bool:
        return state_updated() and substantive_updated()

    system = (
        "You are Football AI Research Orchestrator V4. Work on exactly one research Issue. "
        "You have repository read/search tools plus a zero-cost pinned public GitHub source fetcher, "
        "and may write ONLY inside the three issue sandbox roots. "
        "Never modify production .pkl files, runtime/deployment, Supabase, paid APIs, or closed/frozen "
        "research contracts. No post-hoc threshold tuning. Use temporal/OOS and market baseline when relevant. "
        "A negative result is valid. Do one coherent research iteration, not the entire project at once. "
        "A committed CONTINUE iteration must persist concrete progress outside STATE.json; use record_progress "
        "for a compact evidence-backed checkpoint, or write/replace a real protocol/code/result artifact. "
        "Merely rephrasing the same next_step is not progress. Before finishing you MUST write STATE.json. "
        "CONTINUE requires next_step; BLOCKED requires blocker; "
        "DONE requires a non-empty FINAL_REPORT.md with simple-language conclusion first. "
        "Prefer read_many_files/grep over broad scans to conserve free-tier tokens."
    )
    body = issue_body.strip()
    if len(body) > 9_000:
        body = body[:9_000] + "\n...[issue body truncated for Groq free-tier token budget]"
    user = f"""Issue #{issue_number}: {issue_title}
Hypothesis family: {hypothesis_family}

Binding Issue context:
{body}

Sandbox write roots:
- research/agent_runs/issue_{issue_number}/
- tests/agent_runs/issue_{issue_number}/
- docs/agent_runs/issue_{issue_number}/

Existing STATE.json: {"present" if state_path.is_file() else "absent"}
Existing FINAL_REPORT.md: {"present" if final_path.is_file() else "absent"}

Inspect only the files needed for the next logical step. Complete one meaningful iteration and write STATE.json before you stop."""

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    for turn in range(1, max_turns + 1):
        if turn == 2:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Execution phase: stop broad exploration. FIRST persist one concrete finding "
                        "using record_progress (preferred) or a small protocol/code/result write. Cite "
                        "the repository file/field/evidence you actually inspected. Do not merely "
                        "rephrase STATE.next_step. After progress is persisted, update STATE.json."
                    ),
                }
            )
        if turn >= 3 and substantive_updated() and not state_updated():
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Concrete progress is already persisted. Now call write_state with a short "
                        "CONTINUE/DONE/BLOCKED checkpoint. Do not do more exploration."
                    ),
                }
            )
        elif turn >= 3 and state_updated() and not substantive_updated():
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "STATE.json changed, but no substantive research artifact changed. Call "
                        "record_progress now with a concrete finding and repository evidence; do not "
                        "rewrite STATE again."
                    ),
                }
            )
        if turn == max_turns:
            if state_updated() and not substantive_updated():
                final_instruction = (
                    "FINAL PROGRESS TURN. STATE.json is already updated but this iteration has no "
                    "substantive artifact. Call record_progress now with a concrete evidence-backed "
                    "finding. Do not rewrite STATE."
                )
            else:
                final_instruction = (
                    "FINAL STATE TURN. No more reading or broad exploration. Call write_state now. "
                    "Use CONTINUE with a concrete next_step if work remains; use BLOCKED only for a "
                    "genuine external blocker."
                )
            messages.append({"role": "user", "content": final_instruction})

        final_turn = turn == max_turns
        if state_updated() and not substantive_updated():
            forced_tools = PROGRESS_TOOLS
        elif substantive_updated() and not state_updated():
            forced_tools = FINAL_TOOLS
        elif final_turn:
            forced_tools = FINAL_TOOLS
        else:
            forced_tools = TOOLS
        payload = {
            "model": model,
            "messages": messages,
            "tools": forced_tools,
            "tool_choice": (
                "required"
                if final_turn or forced_tools is FINAL_TOOLS or forced_tools is PROGRESS_TOOLS
                else "auto"
            ),
            "parallel_tool_calls": False,
            "temperature": 0.1,
            "max_completion_tokens": 900,
            "reasoning_effort": "low",
        }
        try:
            response = _request(api_key, payload)
        except GroqToolFormatError:
            recover_progress = state_updated() and not substantive_updated()
            recovery_mode = "record_progress_only" if recover_progress else "write_state_only"
            print(
                f"GROQ_TOOL_FORMAT_RETRY turn={turn} mode={recovery_mode}",
                file=sys.stderr,
            )
            recovery_messages = (
                list(messages)
                if len(messages) <= 6
                else list(messages[:2] + messages[-4:])
            )
            if recover_progress:
                recovery_instruction = (
                    "TOOL FORMAT RECOVERY. STATE.json is already updated. Call record_progress "
                    "only, with short finding/evidence fields grounded in what you already read."
                )
                recovery_tools = PROGRESS_TOOLS
            else:
                recovery_instruction = (
                    "TOOL FORMAT RECOVERY. The previous provider response failed while serializing "
                    "a tool call. Do not recreate a long artifact. Call write_state only, with short "
                    "fields (prefer <=500 characters each). Use CONTINUE unless a genuine external "
                    "blocker exists."
                )
                recovery_tools = FINAL_TOOLS
            recovery_messages.append({"role": "user", "content": recovery_instruction})
            recovery_payload = {
                "model": model,
                "messages": recovery_messages,
                "tools": recovery_tools,
                "tool_choice": "required",
                "parallel_tool_calls": False,
                "temperature": 0.0,
                "max_completion_tokens": 500,
                "reasoning_effort": "low",
            }
            response = _request(api_key, recovery_payload, max_retries=1)
        usage = response.get("usage") or {}
        rate = response.get("_groq_rate_limit") or {}
        print(
            "GROQ_USAGE "
            f"turn={turn} prompt_tokens={usage.get('prompt_tokens')} "
            f"completion_tokens={usage.get('completion_tokens')} "
            f"total_tokens={usage.get('total_tokens')} "
            f"remaining_tokens={rate.get('remaining_tokens')!r} "
            f"reset_tokens={rate.get('reset_tokens')!r}",
            file=sys.stderr,
        )
        choices = response.get("choices") or []
        if not choices:
            raise GroqAgentError("Groq response had no choices")
        raw_message = choices[0].get("message") or {}
        assistant = _message_from_api(raw_message)
        messages.append(assistant)

        tool_calls = raw_message.get("tool_calls") or []
        if not tool_calls:
            if iteration_complete():
                return
            if turn >= max_turns:
                break
            if substantive_updated() and not state_updated():
                reminder = "Concrete progress exists; write STATE.json now."
            elif state_updated() and not substantive_updated():
                reminder = (
                    "STATE.json exists but no concrete progress artifact changed; "
                    "call record_progress now."
                )
            else:
                reminder = (
                    "Persist one concrete progress checkpoint and update STATE.json; "
                    "both are required for a valid iteration."
                )
            messages.append({"role": "user", "content": reminder})
            continue

        remaining_tool_chars = MAX_TOOL_RESULT_CHARS
        for call in tool_calls:
            call_id = call.get("id")
            function = call.get("function") or {}
            name = function.get("name", "")
            raw_args = function.get("arguments") or "{}"
            print(f"GROQ_TOOL_CALL turn={turn} name={name}", file=sys.stderr)
            try:
                args = json.loads(raw_args)
                result = _tool_result(root, issue_number, name, args)
                content = json.dumps(result, ensure_ascii=False)
            except Exception as exc:  # returned to model as tool error
                content = json.dumps(
                    {"error": type(exc).__name__, "message": str(exc)},
                    ensure_ascii=False,
                )
            clipped = content[: max(0, remaining_tool_chars)]
            remaining_tool_chars -= len(clipped)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": clipped or '{"truncated":true}',
                }
            )

        if iteration_complete():
            return

        # Keep the original contract plus only the most recent tool exchange to stay
        # within Groq Free Tier TPM. The model can re-read a file if needed.
        if len(messages) > 8:
            messages = messages[:2] + messages[-6:]

        remaining_raw = rate.get("remaining_tokens")
        reset_raw = rate.get("reset_tokens")
        try:
            remaining_tokens = int(remaining_raw) if remaining_raw is not None else None
        except (TypeError, ValueError):
            remaining_tokens = None
        if turn < max_turns and remaining_tokens is not None and remaining_tokens < 6000:
            reset_seconds = _duration_seconds(reset_raw)
            if reset_seconds:
                delay = min(max(reset_seconds + 2.0, 2.0), 75.0)
                print(
                    f"GROQ_TPM_PACING remaining_tokens={remaining_tokens} "
                    f"retry after {delay:.0f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)

    if not state_updated():
        raise GroqAgentError(
            f"Groq agent incomplete after {max_turns} turns: STATE.json not updated. "
            "Please retry after 65s."
        )
    if not substantive_updated():
        raise GroqAgentError(
            f"Groq agent incomplete after {max_turns} turns: no substantive research progress "
            "was persisted outside STATE.json. Please retry after 65s."
        )


def _load_issue(path: Path) -> tuple[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("title", "")), str(payload.get("body", ""))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--issue-json", type=Path, required=True)
    parser.add_argument("--hypothesis-family", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-turns", type=int, default=4)
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("GROQ_API_KEY missing")

    title, body = _load_issue(args.issue_json)
    try:
        run_agent(
            root=args.root,
            issue_number=args.issue_number,
            issue_title=title,
            issue_body=body,
            hypothesis_family=args.hypothesis_family,
            api_key=api_key,
            model=args.model,
            max_turns=args.max_turns,
        )
    except GroqLongQuotaWait as exc:
        wait = write_quota_wait(args.root, args.issue_number, exc.retry_after_seconds)
        print(
            "GROQ_QUOTA_WAIT_STATE "
            f"path={wait['path']} not_before_epoch={wait['not_before_epoch']}",
            file=sys.stderr,
        )
        print(f"GROQ_AGENT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except GroqAgentError as exc:
        print(f"GROQ_AGENT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
