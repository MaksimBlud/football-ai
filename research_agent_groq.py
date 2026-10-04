"""Groq-backed file-only research agent for Research Orchestrator V4.

The agent exposes only repository read/search tools and issue-sandbox write tools.
It uses Groq's OpenAI-compatible Chat Completions API with tool calling.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_READ_CHARS = 6_000
MAX_TOOL_RESULT_CHARS = 12_000
MAX_GREP_RESULTS = 80
MAX_LIST_ENTRIES = 120

TRANSIENT_HTTP = {429, 500, 502, 503, 504}


class GroqAgentError(RuntimeError):
    pass


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
                return json.loads(raw)
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
            if exc.code not in TRANSIENT_HTTP or attempt >= max_retries:
                raise GroqAgentError(f"Groq API HTTP {exc.code}") from exc
            if remaining_requests == "0":
                if reset_requests:
                    print(
                        f"Groq daily/request quota exhausted. Retry after {reset_requests}.",
                        file=sys.stderr,
                    )
                raise GroqAgentError("Groq daily quota exhausted") from exc
            delay = _duration_seconds(retry_after)
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


def run_agent(
    *,
    root: Path,
    issue_number: int,
    issue_title: str,
    issue_body: str,
    hypothesis_family: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    max_turns: int = 5,
) -> None:
    state_path = root / "research" / "agent_runs" / f"issue_{issue_number}" / "STATE.json"
    final_path = root / "docs" / "agent_runs" / f"issue_{issue_number}" / "FINAL_REPORT.md"
    initial_state = state_path.read_bytes() if state_path.is_file() else None

    def state_updated() -> bool:
        if not state_path.is_file():
            return False
        current = state_path.read_bytes()
        return initial_state is None or current != initial_state

    system = (
        "You are Football AI Research Orchestrator V4. Work on exactly one research Issue. "
        "You have repository read/search tools and may write ONLY inside the three issue sandbox roots. "
        "Never modify production .pkl files, runtime/deployment, Supabase, paid APIs, or closed/frozen "
        "research contracts. No post-hoc threshold tuning. Use temporal/OOS and market baseline when relevant. "
        "A negative result is valid. Do one coherent research iteration, not the entire project at once. "
        "Before finishing you MUST write STATE.json. CONTINUE requires next_step; BLOCKED requires blocker; "
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
        payload = {
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "temperature": 0.1,
            "max_completion_tokens": 1000,
            "reasoning_effort": "low",
        }
        response = _request(api_key, payload)
        choices = response.get("choices") or []
        if not choices:
            raise GroqAgentError("Groq response had no choices")
        raw_message = choices[0].get("message") or {}
        assistant = _message_from_api(raw_message)
        messages.append(assistant)

        tool_calls = raw_message.get("tool_calls") or []
        if not tool_calls:
            if state_updated():
                return
            if turn >= max_turns:
                break
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "You have not written STATE.json yet. Use the file tools now. "
                        "A valid iteration cannot finish without STATE.json."
                    ),
                }
            )
            continue

        remaining_tool_chars = MAX_TOOL_RESULT_CHARS
        for call in tool_calls:
            call_id = call.get("id")
            function = call.get("function") or {}
            name = function.get("name", "")
            raw_args = function.get("arguments") or "{}"
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

        if state_updated():
            return

        # Keep the original contract plus only the most recent tool exchange to stay
        # within Groq Free Tier TPM. The model can re-read a file if needed.
        if len(messages) > 8:
            messages = messages[:2] + messages[-6:]

    if not state_updated():
        raise GroqAgentError(
            f"Groq agent incomplete after {max_turns} turns: STATE.json not updated"
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
    parser.add_argument("--max-turns", type=int, default=5)
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
    except GroqAgentError as exc:
        print(f"GROQ_AGENT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
