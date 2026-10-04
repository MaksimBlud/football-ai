from pathlib import Path

import pytest

from research_agent_groq import (
    GroqAgentError,
    _duration_seconds,
    glob_files,
    grep_search,
    read_file,
    replace_text,
    run_agent,
    write_file,
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


def test_groq_iteration_succeeds_only_after_fresh_state_write(tmp_path: Path, monkeypatch):
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "write_file",
            "arguments": (
                '{"path":"research/agent_runs/issue_428/STATE.json",'
                '"content":"{\\\"status\\\":\\\"CONTINUE\\\",'
                '\\\"summary\\\":\\\"new\\\",'
                '\\\"next_step\\\":\\\"next\\\",'
                '\\\"blocker\\\":null}"}'
            ),
        },
    }
    monkeypatch.setattr(
        "research_agent_groq._request",
        lambda *args, **kwargs: {
            "choices": [{"message": {"content": None, "tool_calls": [tool_call]}}]
        },
    )

    run_agent(
        root=tmp_path,
        issue_number=428,
        issue_title="test",
        issue_body="test body",
        hypothesis_family="test_family",
        api_key="fake",
        max_turns=1,
    )
    assert (
        tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json"
    ).is_file()


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
    assert {
        tool["function"]["name"] for tool in captured["tools"]
    } == {"write_file", "replace"}


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


def test_final_groq_turn_forces_write_state_only(tmp_path: Path, monkeypatch):
    captured = {}

    def fake_request(api_key, payload, **kwargs):
        captured.update(payload)
        tool_call = {
            "id": "call_state",
            "type": "function",
            "function": {
                "name": "write_state",
                "arguments": (
                    '{"status":"CONTINUE","summary":"checkpoint",'
                    '"next_step":"next deterministic step","blocker":null}'
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
        max_turns=1,
    )

    assert captured["tool_choice"] == {
        "type": "function",
        "function": {"name": "write_state"},
    }
    assert [tool["function"]["name"] for tool in captured["tools"]] == ["write_state"]
    assert (
        tmp_path / "research" / "agent_runs" / "issue_428" / "STATE.json"
    ).is_file()
