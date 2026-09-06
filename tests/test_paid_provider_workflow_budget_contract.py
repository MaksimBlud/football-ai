from pathlib import Path

WORKFLOW_DIR = Path(__file__).parents[1] / ".github" / "workflows"

GUARDED_PAID_WORKFLOWS = {
    "odds-snapshots.yml": 1,
    "la-liga-live-cycle.yml": 1,
    "serie-a-odds-snapshots.yml": 1,
    "bundesliga-odds-snapshots.yml": 1,
    "ligue1-odds-snapshots.yml": 1,
    "eredivisie-odds-snapshots.yml": 1,
    "rpl-odds-snapshots.yml": 1,
    "rpl-results.yml": 2,
    "turkey-portugal-market-only-cycle.yml": 2,
    "multi-market-coverage-audit.yml": 63,
    "multi-market-corner-capability-probe.yml": 2,
}

SPECIALIZED_PAID_WORKFLOWS = {"multi-market-cycle.yml"}
ZERO_COST_QUOTA_WORKFLOWS = {
    "multi-market-activation-status.yml",
    "turkey-portugal-bootstrap-audit.yml",
}


def _read(name: str) -> str:
    return (WORKFLOW_DIR / name).read_text(encoding="utf-8")


def _uses_provider_secret(source: str) -> bool:
    """Detect credential exposure, not defensive mentions of the variable name."""
    return "secrets.THE_ODDS_API_KEY" in source


def test_all_guarded_paid_workflows_are_manual_only_and_guarded():
    for name, max_cost in GUARDED_PAID_WORKFLOWS.items():
        source = _read(name)
        assert _uses_provider_secret(source), name
        assert "workflow_dispatch:" in source, name
        assert "cron:" not in source, name
        assert "push:" not in source, name
        assert f"python odds_api_budget_guard.py --max-cost {max_cost}" in source, name


def test_multi_market_keeps_its_specialized_paid_latch_and_credit_cap():
    source = _read("multi-market-cycle.yml")
    assert "MULTI_MARKET_COLLECTION_ENABLED" in source
    assert "MULTI_MARKET_MAX_PAID_REQUESTS" in source
    assert "MULTI_MARKET_MAX_PAID_CREDITS" in source
    assert "allow_paid_collection" in source
    assert "paid_provider_requests" in source


def test_every_workflow_with_provider_secret_has_an_explicit_safety_classification():
    classified = GUARDED_PAID_WORKFLOWS.keys() | SPECIALIZED_PAID_WORKFLOWS | ZERO_COST_QUOTA_WORKFLOWS
    with_secret = {
        path.name
        for path in WORKFLOW_DIR.glob("*.yml")
        if _uses_provider_secret(path.read_text(encoding="utf-8"))
    }
    assert with_secret == classified


def test_defensive_provider_name_mentions_do_not_count_as_secret_exposure():
    source = _read("epl-ai-market-pair-pr-validation.yml")
    assert "THE_ODDS_API_KEY" in source
    assert not _uses_provider_secret(source)


def test_zero_cost_quota_workflows_have_explicit_zero_cost_contracts():
    readiness = _read("multi-market-activation-status.yml")
    assert "paid_provider_requests']==0" in readiness or 'paid_provider_requests\"]==0' in readiness

    bootstrap = _read("turkey-portugal-bootstrap-audit.yml")
    assert "audit_turkey_portugal_bootstrap.py" in bootstrap
    assert "workflow_dispatch:" in bootstrap
