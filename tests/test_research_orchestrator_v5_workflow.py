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
    for family in (
        "kickoff_calendar_context",
        "cross_market_lead_lag_2024_25_anomaly_audit",
        "cross_market_lead_lag_independent_replication",
    ):
        assert family in v5
        assert family in v4
    assert "Run deterministic no-API research pass" in v5
