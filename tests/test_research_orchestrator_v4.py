from pathlib import Path
from types import SimpleNamespace

import pytest

import research_orchestrator_v4 as v4
from research_v4_api import RetryableGeminiError, gemini_json, parse_json_text, retry_seconds
from research_v4_sandbox import collect_context, docker_command, run_sandbox, validate_changed_paths_v4, validate_code


class FakeResponse:
    def __init__(self, status_code, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_parse_json_text_accepts_fenced_json():
    assert parse_json_text('```json\n{"decision":"DONE"}\n```') == {"decision": "DONE"}


def test_gemini_direct_api_is_single_bounded_request():
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(
            200,
            {"candidates": [{"content": {"parts": [{"text": '{"action":"WRITE_ANALYSIS"}'}]}}]},
        )

    result = gemini_json(
        api_key="secret", system_instruction="system", prompt="small prompt", post=post
    )
    assert result["action"] == "WRITE_ANALYSIS"
    assert len(calls) == 1
    assert "gemini-3.5-flash-lite:generateContent" in calls[0][0]
    assert calls[0][1]["headers"]["x-goog-api-key"] == "secret"
    assert calls[0][1]["json"]["generationConfig"]["responseMimeType"] == "application/json"


def test_retryable_quota_failure_becomes_checkpointable():
    def post(url, **kwargs):
        return FakeResponse(429, text="Please retry in 2h3m.")

    with pytest.raises(RetryableGeminiError) as exc:
        gemini_json(
            api_key="secret", system_instruction="s", prompt="p", post=post,
            sleep=lambda _: None,
        )
    assert exc.value.retry_at_utc.endswith("Z")
    assert retry_seconds("Please retry in 2h3m.") == 7380


def test_generated_code_blocks_network_and_process_imports():
    ok, errors = validate_code("import requests\nimport subprocess\n")
    assert not ok
    assert "import not allowed: requests" in errors
    assert "import not allowed: subprocess" in errors


def test_generated_code_allows_data_science_analysis():
    code = "import json\nimport pandas as pd\nfrom pathlib import Path\n"
    ok, errors = validate_code(code)
    assert ok
    assert errors == ()


def test_sandbox_is_networkless_readonly_and_secretless(tmp_path):
    cmd = docker_command("football-ai-research-v4", tmp_path, tmp_path / "work")
    joined = " ".join(cmd)
    assert "--network none" in joined
    assert "--read-only" in joined
    assert "--cap-drop ALL" in joined
    assert f"{tmp_path.resolve()}:/repo:ro" in joined
    assert "GEMINI_API_KEY" not in joined


def test_static_safety_rejection_does_not_execute_runner(tmp_path):
    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_sandbox(
        code="import requests\n", repo_root=tmp_path, iteration_root=tmp_path / "it",
        image="image", runner=runner,
    )
    assert result["status"] == "SAFETY_REJECTED"
    assert not called


def test_v4_changed_paths_are_issue_scoped():
    ok, errors = validate_changed_paths_v4(
        ["research/autonomous/issue_428/state.json", "research/autonomous/issue_428/FINAL_REPORT.md"],
        428,
    )
    assert ok
    ok, errors = validate_changed_paths_v4(["api.py"], 428)
    assert not ok
    assert "outside issue sandbox" in errors[0]


def test_context_is_bounded_and_skips_prior_autonomous_checkpoints(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "matches.csv").write_text("kickoff,total\n12:00,2.5\n", encoding="utf-8")
    old = tmp_path / "research" / "autonomous" / "issue_1"
    old.mkdir(parents=True)
    (old / "context.txt").write_text("SHOULD_NOT_RECURSE", encoding="utf-8")
    state = {"task": "kickoff time total market", "hypothesis_family": "kickoff_calendar_context", "next_focus": ""}
    context = collect_context(tmp_path, state, limit=1200)
    assert "matches.csv" in context
    assert "SHOULD_NOT_RECURSE" not in context
    assert len(context) <= 1200


def test_issue_fingerprint_blocks_silent_retuning(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "build_issue_plan", lambda *a, **k: {"decision": "READY_FOR_PREREGISTRATION", "mode": "historical_read_only"})
    monkeypatch.setattr(v4, "parse_issue", lambda title, body: {
        "research_question": body, "hypothesis_family": "new_family",
        "independent_information_justification": "independent",
    })
    issue = {"number": 77, "title": "[AGENT-RESEARCH] test", "body": "frozen question"}
    state = v4.initialize_state(issue, tmp_path)
    assert state["status"] == "NEW"
    issue["body"] = "retuned question"
    state = v4.initialize_state(issue, tmp_path)
    assert state["status"] == "BLOCKED"
    assert state["blocker"] == "ISSUE_CHANGED_AFTER_FREEZE"


def test_done_decision_writes_final_report(tmp_path):
    state = {
        "issue_number": 88, "iteration": 0, "max_iterations": 12, "history": [],
        "pending_result": "x", "task": "test", "hypothesis_family": "family",
    }
    decision = {
        "decision": "DONE", "summary": "No robust incremental signal.",
        "final_report_markdown": "# Final\n\nNegative result.",
    }
    out = v4.apply_decision(
        state, {"analysis_name": "oos", "rationale": "test"},
        {"status": "OK", "summary": "none", "metrics": {}, "sample_size": 100},
        decision, tmp_path,
    )
    assert out["status"] == "DONE"
    report = tmp_path / "research" / "autonomous" / "issue_88" / "FINAL_REPORT.md"
    assert report.read_text(encoding="utf-8").startswith("# Final")
