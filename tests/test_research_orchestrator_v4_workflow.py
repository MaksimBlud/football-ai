from pathlib import Path


V4 = Path(".github/workflows/research-orchestrator-v4.yml")
V3 = Path(".github/workflows/research-agent-v3-gemini.yml")
V2 = Path(".github/workflows/research-agent-v2-issue-intake.yml")


def _v4() -> str:
    return V4.read_text(encoding="utf-8")


def _v3() -> str:
    return V3.read_text(encoding="utf-8")


def _v2() -> str:
    return V2.read_text(encoding="utf-8")


def test_v4_serializes_one_issue_but_allows_different_issues_in_parallel():
    text = _v4()
    assert "concurrency:" in text
    assert "github.event.issue.number || inputs.issue_number || github.run_id" in text
    assert "cancel-in-progress: false" in text


def test_v4_has_issue_dispatch_schedule_and_pr_contract_triggers():
    text = _v4()
    on_block = text.split("permissions:", 1)[0]
    assert "issues:" in on_block
    assert "workflow_dispatch:" in on_block
    assert "schedule:" in on_block
    assert "pull_request:" in on_block


def test_v4_uses_three_free_model_fallbacks_and_short_sessions():
    text = _v4()
    assert "gemini_model: gemini-3.5-flash-lite" in text
    assert "gemini_model: gemini-3.6-flash" in text
    assert "gemini_model: gemini-3.7-flash" in text
    assert '"maxSessionTurns": 8' in text


def test_v4_persists_issue_branch_and_machine_state():
    text = _v4()
    assert "research_orchestrator_v4.py branch-name" in text
    assert "research_orchestrator_v4.py validate-state" in text
    assert "STATE.json" in text
    assert "FINAL_REPORT.md" in text


def test_v4_continues_without_user_and_retries_waiting_work():
    text = _v4()
    assert "source=continuation" in text
    assert "research-v4-running" in text
    assert "research-v4-waiting" in text
    assert "source=schedule" in text


def test_v4_keeps_model_tools_file_only():
    text = _v4()
    settings = text.split("GEMINI_SETTINGS: |-", 1)[1].split("AGENT_PROMPT: |-", 1)[0]
    assert "run_shell_command" not in settings
    assert '"read_file"' in settings
    assert '"write_file"' in settings
    assert '"replace"' in settings


def test_v4_has_deterministic_safety_gates():
    text = _v4()
    required = [
        "research_agent_gemini.py validate-status",
        "research_agent_gemini.py stage-status",
        "git diff --check",
        "sha256sum *.pkl",
        "pytest -q -p no:cacheprovider",
    ]
    for marker in required:
        assert marker in text


def test_v4_never_auto_merges_or_promotes():
    text = _v4()
    assert "gh pr merge" not in text
    assert "artifact_lifecycle.py promote" not in text


def test_legacy_v2_no_longer_runs_on_issue_events():
    text = _v2()
    on_block = text.split("permissions:", 1)[0]
    assert "issues:" not in on_block
    assert "pull_request:" in on_block


def test_v3_no_longer_runs_on_issue_events():
    text = _v3()
    on_block = text.split("permissions:", 1)[0]
    assert "issues:" not in on_block
    assert "pull_request:" in on_block
