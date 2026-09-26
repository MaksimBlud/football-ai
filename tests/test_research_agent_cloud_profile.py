from pathlib import Path


PROFILE = Path(".github/agents/football-ai-research.agent.md")


def test_cloud_agent_profile_exists_and_is_manually_invoked():
    text = PROFILE.read_text(encoding="utf-8")
    assert "name: football-ai-research" in text
    assert "target: github-copilot" in text
    assert 'tools: ["read", "search", "edit", "execute"]' in text
    assert "disable-model-invocation: true" in text
    assert "user-invocable: true" in text


def test_cloud_agent_requires_v2_gate_before_implementation():
    text = PROFILE.read_text(encoding="utf-8")
    assert "READY_FOR_PREREGISTRATION" in text
    assert "REJECT_EXISTING_HYPOTHESIS_FAMILY" in text
    assert "NEEDS_INDEPENDENT_INFORMATION_JUSTIFICATION" in text
    assert "INVALID_ISSUE" in text


def test_cloud_agent_forbids_production_and_paid_side_effects():
    text = PROFILE.read_text(encoding="utf-8")
    required = [
        "artifact_lifecycle.py promote",
        "Never modify, replace, stage, or delete production",
        "Never push directly to `main`",
        "Never merge your own pull request",
        "Never write to Supabase",
        "Never spend The Odds API credits",
        "Never activate runtime calibration",
    ]
    for marker in required:
        assert marker in text
