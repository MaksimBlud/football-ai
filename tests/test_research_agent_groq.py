import hashlib
import io
import urllib.error
from email.message import Message
from pathlib import Path

import pytest

from research_agent_groq import (
    GroqAgentError,
    GroqLongQuotaWait,
    GroqToolFormatError,
    _duration_seconds,
    _request,
    fetch_pinned_github_file,
    fetch_pinned_github_files,
    glob_files,
    grep_search,
    read_file,
    record_progress,
    replace_text,
    run_agent,
    write_file,
    write_quota_wait,
    write_state,
)


def test_groq_agent_write_is_issue_scoped(tmp_path: Path):
    result = write_file(
        tmp_path,
        428,
        "research/agent_runs/issue_428/STATE.json",
        '{"status":"CONTINUE"}',
    )
    assert result["chars_written"] > 0
    assert (tmp_path / "research/agent_runs/issue_428/STATE.json").is_file()


@pytest.mark.parametrize(
    "path",
    [
        "research/agent_runs/issue_481/STATE.json",
        "research/OTHER.md",
        "football_model_xgboost_elo.pkl",
        "../outside.txt",
        "/tmp/outside.txt",
    ],
)
def test_groq_agent_rejects_writes_outside_issue_sandbox(tmp_path: Path, path: str):
    with pytest.raises(GroqAgentError):
        write_file(tmp_path, 428, path, "no")


def test_fetch_pinned_github_file_verifies_blob_and_writes_only_sandbox(
    tmp_path: Path, monkeypatch
):
    data = b"Date,HomeTeam,B365H\n01/01/2026,A,2.10\n"
    expected = hashlib.sha1(
        f"blob {len(data)}\0".encode("ascii") + data,
        usedforsecurity=False,
    ).hexdigest()

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            assert limit > len(data)
            return data

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("research_agent_groq.urllib.request.urlopen", fake_urlopen)
    result = fetch_pinned_github_file(
        tmp_path,
        482,
        "owner/repo",
        "a" * 40,
        "data/raw/D1_2025-26.csv",
        "research/agent_runs/issue_482/sources/D1_2025-26.csv",
        expected,
    )

    saved = tmp_path / "research" / "agent_runs" / "issue_482" / "sources" / "D1_2025-26.csv"
    assert saved.read_bytes() == data
    assert result["git_blob_sha"] == expected
    assert captured["url"].startswith(
        "https://raw.githubusercontent.com/owner/repo/" + "a" * 40
    )
    assert captured["timeout"] == 60


def test_fetch_pinned_github_file_rejects_blob_mismatch_before_write(
    tmp_path: Path, monkeypatch
):
    data = b"not-the-pinned-blob"

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return data

    monkeypatch.setattr(
        "research_agent_groq.urllib.request.urlopen",
        lambda *args, **kwargs: Response(),
    )
    destination = "research/agent_runs/issue_482/sources/source.csv"
    with pytest.raises(GroqAgentError, match="Git blob SHA mismatch"):
        fetch_pinned_github_file(
            tmp_path,
            482,
            "owner/repo",
            "b" * 40,
            "source.csv",
            destination,
            "0" * 40,
        )
    assert not (tmp_path / destination).exists()


@pytest.mark.parametrize("commit", ["main", "abc123", "g" * 40])
def test_fetch_pinned_github_file_requires_full_commit_sha(tmp_path: Path, commit: str):
    with pytest.raises(GroqAgentError, match="full 40-hex commit SHA"):
        fetch_pinned_github_file(
            tmp_path,
            482,
            "owner/repo",
            commit,
            "source.csv",
            "research/agent_runs/issue_482/source.csv",
        )


def test_fetch_pinned_github_files_batches_up_to_four(tmp_path: Path, monkeypatch):
    calls = []

    def fake_fetch(root, issue_number, repository, commit, path, destination, expected_blob_sha=None):
        calls.append((repository, commit, path, destination, expected_blob_sha))
        return {"destination": destination}

    monkeypatch.setattr("research_agent_groq.fetch_pinned_github_file", fake_fetch)
    files = [
        {
            "repository": "owner/repo",
            "commit": "a" * 40,
            "path": f"source_{i}.csv",
            "destination": f"research/agent_runs/issue_482/sources/source_{i}.csv",
        }
        for i in range(4)
    ]
    result = fetch_pinned_github_files(tmp_path, 482, files)
    assert len(result["files"]) == 4
    assert len(calls) == 4

    with pytest.raises(GroqAgentError, match="1 to 4 files"):
        fetch_pinned_github_files(tmp_path, 482, files + [files[0]])


def test_groq_agent_read_search_and_replace(tmp_path: Path):
    source = tmp_path / "research" / "example.txt"
    source.parent.mkdir(parents=True)
    source.write_text("alpha\nbeta signal\n", encoding="utf-8")

    assert "beta signal" in read_file(tmp_path, "research/example.txt")["content"]
    assert glob_files(tmp_path, "research/*.txt")["matches"] == ["research/example.txt"]
    matches = grep_search(tmp_path, "SIGNAL", "research", "*.txt")["matches"]
    assert matches[0]["line"] == 2

    sandbox = tmp_path / "docs" / "agent_runs" / "issue_428" / "note.md"
    sandbox.parent.mkdir(parents=True)
    sandbox.write_text("old text", encoding="utf-8")
    result = replace_text(
        tmp_path,
        428,
        "docs/agent_runs/issue_428/note.md",
        "old",
        "new",
    )
    assert result["replacements"] == 1
    assert sandbox.read_text(encoding="utf-8") == "new text"


@pytest.mark.parametrize(
    ("value", "seconds"),
    [
        ("3", 3.0),
        ("750ms", 0.75),
        ("8.5s", 8.5),
        ("2m30s", 150.0),
        ("1h2m3s", 3723.0),
    ],
)
def test_groq_rate_limit_duration_parser(value: str, seconds: float):
    assert _duration_seconds(value) == pytest.approx(seconds)


def test_write_quota_wait_persists_future_not_before(tmp_path: Path):
    result = write_quota_wait(tmp_path, 482, 651.2, buffer_seconds=15)
    path = tmp_path / "research" / "agent_runs" / "issue_482" / "QUOTA_WAIT.json"
    payload = __import__("json").loads(path.read_text(encoding="utf-8"))

    assert result["provider"] == "groq"
    assert payload["retry_after_seconds"] == 652
    assert payload["buffer_seconds"] == 15
    assert payload["not_before_epoch"] > 0
    assert payload["not_before_utc"] > payload["observed_at_utc"]


def test_groq_long_retry_after_fails_fast_without_sleep(monkeypatch, capsys):
    headers = Message()
    headers["retry-after"] = "2296"
    headers["x-ratelimit-remaining-requests"] = "941"
    error = urllib.error.HTTPError(
        "https://api.groq.com/openai/v1/chat/completions",
        429,
        "Too Many Requests",
        headers,
        io.BytesIO(b'{"error":{"message":"TPD rate limit"}}'),
    )

    def fail_request(*args, **kwargs):
        raise error

    slept = []
    monkeypatch.setattr("research_agent_groq.urllib.request.urlopen", fail_request)
    monkeypatch.setattr("research_agent_groq.time.sleep", lambda seconds: slept.append(seconds))

    with pytest.raises(GroqLongQuotaWait, match="long quota wait") as exc_info:
        _request("fake", {"model": "test", "messages": []})
    assert exc_info.value.retry_after_seconds == pytest.approx(2296.0)

    assert slept == []
    stderr = capsys.readouterr().err
    assert "GROQ_LONG_QUOTA_WAIT retry_after_seconds=2296.000" in stderr


def test_existing_state_does_not_fake_new_groq_iteration(tmp_path: Path, monkeypatch):
    state = tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json"
    state.parent.mkdir(parents=True)
    state.write_text(
        '{"status":"CONTINUE","summary":"old","next_step":"x","blocker":null}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "research_agent_groq._request",
        lambda *args, **kwargs: {"choices": [{"message": {"content": "done"}}]},
    )

    with pytest.raises(GroqAgentError, match="STATE.json not updated"):
        run_agent(
            root=tmp_path,
            issue_number=428,
            issue_title="test",
            issue_body="test body",
            hypothesis_family="test_family",
            api_key="fake",
            max_turns=1,
        )


def test_state_only_does_not_count_as_research_iteration(tmp_path: Path, monkeypatch):
    tool_call = {
        "id": "call_state",
        "type": "function",
        "function": {
            "name": "write_state",
            "arguments": '{"status":"CONTINUE","summary":"new","next_step":"next"}',
        },
    }
    monkeypatch.setattr(
        "research_agent_groq._request",
        lambda *args, **kwargs: {
            "choices": [{"message": {"content": None, "tool_calls": [tool_call]}}]
        },
    )

    with pytest.raises(GroqAgentError, match="no substantive research progress"):
        run_agent(
            root=tmp_path,
            issue_number=428,
            issue_title="test",
            issue_body="test body",
            hypothesis_family="test_family",
            api_key="fake",
            max_turns=1,
        )


def test_progress_then_state_completes_iteration(tmp_path: Path, monkeypatch):
    responses = [
        {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_progress",
                        "type": "function",
                        "function": {
                            "name": "record_progress",
                            "arguments": (
                                '{"finding":"required columns are documented",'
                                '"evidence":"research/protocol.md lists B365H/B365D/B365A",'
                                '"next_action":"check target league coverage"}'
                            ),
                        },
                    }],
                }
            }]
        },
        {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_state",
                        "type": "function",
                        "function": {
                            "name": "write_state",
                            "arguments": (
                                '{"status":"CONTINUE","summary":"column contract captured",'
                                '"next_step":"check target league coverage"}'
                            ),
                        },
                    }],
                }
            }]
        },
    ]

    def fake_request(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr("research_agent_groq._request", fake_request)
    run_agent(
        root=tmp_path,
        issue_number=428,
        issue_title="test",
        issue_body="test body",
        hypothesis_family="test_family",
        api_key="fake",
        max_turns=2,
    )

    assert (tmp_path / "research" / "agent_runs" / "issue_428" / "PROGRESS.md").is_file()
    assert (tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json").is_file()


def test_final_groq_turn_is_write_only_and_required(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_request(api_key, payload, **kwargs):
        captured.update(payload)
        return {"choices": [{"message": {"content": "no write"}}]}

    monkeypatch.setattr("research_agent_groq._request", fake_request)

    with pytest.raises(GroqAgentError, match="retry after 65s"):
        run_agent(
            root=tmp_path,
            issue_number=428,
            issue_title="test",
            issue_body="test body",
            hypothesis_family="test_family",
            api_key="fake",
            max_turns=1,
        )

    assert captured["tool_choice"] == "required"
    assert captured["parallel_tool_calls"] is False
    assert [tool["function"]["name"] for tool in captured["tools"]] == ["write_state"]


def test_record_progress_appends_compact_evidence_checkpoint(tmp_path: Path):
    first = record_progress(
        tmp_path,
        428,
        "The frozen V1 statistic is alignment_dot.",
        "research/CROSS_MARKET_LEAD_LAG_V1.md defines alignment_dot as dot(lead, move).",
        "Check independent league column coverage.",
    )
    second = record_progress(
        tmp_path,
        428,
        "The checkpoint is append-only within the iteration sandbox.",
        "PROGRESS.md already exists after the first checkpoint.",
    )
    path = tmp_path / "research" / "agent_runs" / "issue_428" / "PROGRESS.md"
    text = path.read_text(encoding="utf-8")
    assert first["chars_appended"] > 0
    assert second["chars_appended"] > 0
    assert text.count("## Research checkpoint") == 2
    assert "alignment_dot" in text


def test_write_state_builds_canonical_continue_state(tmp_path: Path):
    result = write_state(
        tmp_path,
        428,
        "CONTINUE",
        "Protocol frozen and ready for the next deterministic step.",
        "Create the minimal replication script in the issue sandbox.",
    )
    state = tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json"
    payload = __import__("json").loads(state.read_text(encoding="utf-8"))
    assert result["state"]["status"] == "CONTINUE"
    assert payload == {
        "blocker": None,
        "next_step": "Create the minimal replication script in the issue sandbox.",
        "status": "CONTINUE",
        "summary": "Protocol frozen and ready for the next deterministic step.",
    }


def test_write_state_validates_status_contract(tmp_path: Path):
    with pytest.raises(GroqAgentError, match="CONTINUE requires next_step"):
        write_state(tmp_path, 428, "CONTINUE", "summary")
    with pytest.raises(GroqAgentError, match="BLOCKED requires blocker"):
        write_state(tmp_path, 428, "BLOCKED", "summary")
    with pytest.raises(GroqAgentError, match="invalid state status"):
        write_state(tmp_path, 428, "UNKNOWN", "summary")


def test_tool_format_failure_recovers_state_then_requires_progress(tmp_path: Path, monkeypatch):
    calls = []

    def fake_request(api_key, payload, **kwargs):
        calls.append((payload, kwargs))
        if len(calls) == 1:
            raise GroqToolFormatError("Groq tool_use_failed")
        if len(calls) == 2:
            tool_call = {
                "id": "call_recovery_state",
                "type": "function",
                "function": {
                    "name": "write_state",
                    "arguments": (
                        '{"status":"CONTINUE","summary":"checkpoint persisted after tool-format retry",'
                        '"next_step":"persist concrete evidence"}'
                    ),
                },
            }
        else:
            tool_call = {
                "id": "call_progress",
                "type": "function",
                "function": {
                    "name": "record_progress",
                    "arguments": (
                        '{"finding":"recovery preserved a concrete checkpoint",'
                        '"evidence":"STATE.json was written by the state-only recovery call"}'
                    ),
                },
            }
        return {"choices": [{"message": {"content": None, "tool_calls": [tool_call]}}]}

    monkeypatch.setattr("research_agent_groq._request", fake_request)

    run_agent(
        root=tmp_path,
        issue_number=428,
        issue_title="test",
        issue_body="test body",
        hypothesis_family="test_family",
        api_key="fake",
        max_turns=2,
    )

    assert len(calls) == 3
    recovery_payload, recovery_kwargs = calls[1]
    assert [tool["function"]["name"] for tool in recovery_payload["tools"]] == ["write_state"]
    assert recovery_payload["tool_choice"] == "required"
    assert recovery_payload["max_completion_tokens"] == 500
    assert recovery_kwargs["max_retries"] == 1
    final_payload, _ = calls[2]
    assert [tool["function"]["name"] for tool in final_payload["tools"]] == ["record_progress"]
    assert (tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json").is_file()
    assert (tmp_path / "research" / "agent_runs" / "issue_428" / "PROGRESS.md").is_file()


def test_final_groq_turn_forces_state_after_progress(tmp_path: Path, monkeypatch):
    captured = []
    responses = [
        {
            "id": "call_progress",
            "type": "function",
            "function": {
                "name": "record_progress",
                "arguments": (
                    '{"finding":"one concrete fact","evidence":"research/source.md line contract"}'
                ),
            },
        },
        {
            "id": "call_state",
            "type": "function",
            "function": {
                "name": "write_state",
                "arguments": (
                    '{"status":"CONTINUE","summary":"checkpoint",'
                    '"next_step":"next deterministic step","blocker":null}'
                ),
            },
        },
    ]

    def fake_request(api_key, payload, **kwargs):
        captured.append(payload)
        tool_call = responses.pop(0)
        return {"choices": [{"message": {"content": None, "tool_calls": [tool_call]}}]}

    monkeypatch.setattr("research_agent_groq._request", fake_request)

    run_agent(
        root=tmp_path,
        issue_number=428,
        issue_title="test",
        issue_body="test body",
        hypothesis_family="test_family",
        api_key="fake",
        max_turns=2,
    )

    assert captured[-1]["tool_choice"] == "required"
    assert [tool["function"]["name"] for tool in captured[-1]["tools"]] == ["write_state"]
    assert (tmp_path / "research" / "agent_runs" / "issue_428" / "PROGRESS.md").is_file()
    assert (tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json").is_file()
