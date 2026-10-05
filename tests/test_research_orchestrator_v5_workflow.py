from pathlib import Path


def test_v5_workflow_does_not_require_actions_pr_permission():
    text = Path(".github/workflows/research-orchestrator-v5-local.yml").read_text(encoding="utf-8")
    assert "Publish final research reference" in text
    assert "GitHub Actions cannot create PRs in this repository" in text
    assert 'PR_URL="$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/tree/$BRANCH"' in text
    assert "Publish DONE" in text


def test_v5_routes_supported_families_without_model_api():
    v5 = Path(".github/workflows/research-orchestrator-v5-local.yml").read_text(encoding="utf-8")
    v4 = Path(".github/workflows/research-orchestrator-v4.yml").read_text(encoding="utf-8")
    registry = Path("research/v5_recipe_registry.json").read_text(encoding="utf-8")
    assert "Run deterministic no-API research pass" in v5
    assert 'research_agent_v5.py --supports-family "$FAMILY"' in v5
    assert 'research_agent_v5.py --supports-family "$FAMILY"' in v4
    assert 'research_agent_v5.py --max-iterations "$HYPOTHESIS_FAMILY"' in v5
    assert "research/v5_recipe_registry.json" in v5
    assert "kickoff_calendar_context" in registry
    assert "cross_market_lead_lag_2024_25_anomaly_audit" in registry
    assert "cross_market_lead_lag_independent_replication" in registry
    assert "kickoff_calendar_context|" not in v5
    assert "kickoff_calendar_context|" not in v4


def test_v5_unknown_family_fails_closed_without_model_api():
    text = Path(".github/workflows/research-orchestrator-v5-local.yml").read_text(encoding="utf-8")
    assert "research-v5-needs-recipe" in text
    assert "has no deterministic V5 recipe; fail-closed without model API" in text
    assert "research-v4-model-opt-in" in text
    assert "Groq" not in text
    assert "Gemini" not in text
