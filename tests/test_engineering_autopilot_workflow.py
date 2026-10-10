"""No-model engineering schedule contract: heartbeat cannot masquerade as coding."""
from pathlib import Path


WORKFLOW = Path(".github/workflows/football-ai-engineering-autopilot.yml")


def read():
    return WORKFLOW.read_text(encoding="utf-8")


def test_scheduled_runner_never_calls_external_ai_models():
    workflow = read().lower()
    for forbidden in (
        "gemini_api_key", "groq_api_key", "openai_api_key", "run-gemini-cli",
        "research_agent_groq.py", "secrets.", "free_tier_enabled",
    ):
        assert forbidden not in workflow, forbidden


def test_checkpoint_is_read_only_and_not_marked_as_autonomous_coding():
    workflow = read()
    assert "contents: read" in workflow
    assert "issues: read" in workflow
    assert "pull-requests: read" in workflow
    assert "contents: write" not in workflow
    assert "git push" not in workflow
    assert "gh pr create" not in workflow
    assert "gh issue comment" not in workflow
    assert "not** proof of autonomous coding" in workflow
    assert "Code modifications: 0" in workflow


def test_checkpoint_runs_on_schedule_and_is_dispatchable_without_ai():
    workflow = read()
    assert "schedule:" in workflow
    assert "cron: '17 * * * *'" in workflow
    assert "workflow_dispatch:" in workflow
    assert "role:" in workflow
    assert "options: [frontend, backend, both]" in workflow
    assert "ref: main" in workflow
    assert "timeout-minutes: 6" in workflow


def test_checkpoint_reports_real_tasks_and_open_prs():
    workflow = read()
    assert "frontend:582 backend:581" in workflow
    assert "gh issue view" in workflow
    assert "gh pr list" in workflow
    assert "git rev-parse HEAD" in workflow
    assert 'GITHUB_STEP_SUMMARY' in workflow


def test_workflow_contract_runs_protection_suite_on_pull_requests():
    workflow = read()
    assert "github.event_name == 'pull_request'" in workflow
    assert "tests/test_engineering_autopilot_guard.py" in workflow
    assert "tests/test_engineering_autopilot_workflow.py" in workflow
    assert "python -m py_compile engineering_autopilot_guard.py" in workflow
