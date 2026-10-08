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
    assert "corner_cross_market_match_shape_cross_league_transfer_v1" in registry
    assert "corner_cross_market_match_shape_cross_league_transfer_v1.py" in v5
    assert "devig_method_oos_v1" in registry
    assert "devig_method_oos_v1.py" in v5
    assert "favourite_longshot_bias_v1" in registry
    assert "favourite_longshot_bias_v1.py" in v5
    assert "power_devig_cross_league_transport_v1" in registry
    assert "power_devig_cross_league_transport_v1.py" in v5
    assert "favourite_longshot_cross_league_v1" in registry
    assert "favourite_longshot_cross_league_v1.py" in v5
    assert "bookmaker_margin_structure_v1" in registry
    assert "bookmaker_margin_structure_v1.py" in v5
    assert "bookmaker_price_formation_v1" in registry
    assert "bookmaker_price_formation_v1.py" in v5
    assert "bookmaker_price_formation_cross_book_transport_v1" in registry
    assert "bookmaker_price_formation_cross_book_transport_v1.py" in v5
    assert "bookmaker_margin_market_type_transport_v1" in registry
    assert "bookmaker_margin_market_type_transport_v1.py" in v5
    assert "market_residual_process_divergence_v1" in registry
    assert "market_residual_process_divergence_v1.py" in v5
    assert "website_goal_total_oos_readiness_v1" in registry
    assert "website_goal_total_oos_readiness_v1.py" in v5
    assert "website_btts_oos_readiness_v1" in registry
    assert "website_btts_oos_readiness_v1.py" in v5
    assert "kickoff_calendar_context|" not in v5
    assert "kickoff_calendar_context|" not in v4


def test_v5_unknown_family_fails_closed_without_model_api():
    text = Path(".github/workflows/research-orchestrator-v5-local.yml").read_text(encoding="utf-8")
    assert "research-v5-needs-recipe" in text
    assert "has no deterministic V5 recipe; creating no-API scaffold" in text
    assert "research-v4-model-opt-in" in text
    assert "Groq" not in text
    assert "Gemini" not in text


def test_v5_auto_scaffolds_unknown_no_api_families():
    text = Path(".github/workflows/research-orchestrator-v5-local.yml").read_text(encoding="utf-8")
    assert "scaffold_required" in text
    assert "agent/v5-scaffold-" in text
    assert "research_v5_recipe_scaffold.py" in text
    assert "research/v5_recipe_requests/issue_" in text
    assert "docs/v5_recipe_requests/issue_" in text
    assert "The Issue remains fail-closed" in text
