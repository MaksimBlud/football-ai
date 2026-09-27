from pathlib import Path


WORKFLOW = Path(".github/workflows/research-agent-v3-gemini.yml")


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_gemini_v3_is_owner_gated_and_disabled_by_default():
    text = _text()
    assert "github.event.issue.user.login == github.repository_owner" in text
    assert "needs.validate.outputs.decision == 'READY_FOR_PREREGISTRATION'" in text
    assert "vars.RESEARCH_GEMINI_ENABLED == 'true'" in text


def test_gemini_v3_uses_official_action_and_secret():
    text = _text()
    assert "google-github-actions/run-gemini-cli@v0" in text
    assert "secrets.GEMINI_API_KEY" in text


def test_gemini_v3_does_not_expose_shell_tool_to_model():
    text = _text()
    settings = text.split("settings: |-", 1)[1].split("prompt: |-", 1)[0]
    assert "run_shell_command" not in settings
    assert '"write_file"' in settings
    assert '"replace"' in settings


def test_gemini_v3_has_deterministic_post_edit_safety_and_pr_flow():
    text = _text()
    required = [
        "research_agent_gemini.py validate-status",
        "research_agent_gemini.py stage-status",
        "git diff --check",
        "sha256sum *.pkl",
        'git push origin "$BRANCH"',
        "gh pr create",
    ]
    for marker in required:
        assert marker in text


def test_gemini_v3_never_auto_merges_or_promotes():
    text = _text()
    assert "gh pr merge" not in text
    assert "artifact_lifecycle.py promote" not in text
