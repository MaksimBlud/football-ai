from pathlib import Path


WORKFLOW = Path(".github/workflows/research-agent-v3-gemini.yml")


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_gemini_v3_is_owner_gated_and_disabled_by_default():
    text = _text()
    assert "REPOSITORY_OWNER: ${{ github.repository_owner }}" in text
    assert 'if [ "$ISSUE_AUTHOR" != "$REPOSITORY_OWNER" ]' in text
    assert "READY_FOR_PREREGISTRATION" in text
    assert "RESEARCH_GEMINI_ENABLED: ${{ vars.RESEARCH_GEMINI_ENABLED }}" in text
    assert 'if [ "$RESEARCH_GEMINI_ENABLED" != \'true\' ]' in text
    assert "echo \'run_gemini=false\'" in text
    assert "echo \'run_gemini=true\'" in text


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
        "research_agent_issue.py",
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


def test_gemini_v3_pr_link_comment_uses_yaml_block_scalar():
    text = _text()
    marker = "- name: Link pull request from issue"
    block = text.split(marker, 1)[1]
    assert "run: |" in block
    assert "validated research PR: $PR_URL" in block
