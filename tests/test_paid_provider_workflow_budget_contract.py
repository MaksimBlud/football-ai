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
    # Two matrix jobs can each spend h2h=1 + scores=2. Each job reserves the
    # workflow-wide worst case so concurrent preflights cannot cross reserve.
    "turkey-portugal-market-only-cycle.yml": 6,
    # Current coverage audit worst case: 9 leagues * (3 featured + 4 event).
    "multi-market-coverage-audit.yml": 63,
}

SPECIALIZED_PAID_WORKFLOWS = {"multi-market-cycle.yml"}
ZERO_COST_QUOTA_WORKFLOWS = {
    "multi-market-activation-status.yml",
    "turkey-portugal-bootstrap-audit.yml",
}


def _read(name: str) -> str:
    return (WORKFLOW_DIR / name).read_text(encoding="utf-8")


def test_all_guarded_paid_workflows_are_manual_only_and_guarded():
    for name, max_cost in GUARDED_PAID_WORKFLOWS.items():
        source = _read(name)
        assert "THE_ODDS_API_KEY" in source, name
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


def test_every_workflow_with_provider_key_has_an_explicit_safety_classification():
    classified = GUARDED_PAID_WORKFLOWS.keys() | SPECIALIZED_PAID_WORKFLOWS | ZERO_COST_QUOTA_WORKFLOWS
    with_key = {
        path.name
        for path in WORKFLOW_DIR.glob("*.yml")
        if "THE_ODDS_API_KEY" in path.read_text(encoding="utf-8")
    }
    assert with_key == classified


def test_zero_cost_quota_workflows_have_explicit_zero_cost_contracts():
    readiness = _read("multi-market-activation-status.yml")
    assert "paid_provider_requests']==0" in readiness or 'paid_provider_requests\"]==0' in readiness

    bootstrap = _read("turkey-portugal-bootstrap-audit.yml")
    assert "audit_turkey_portugal_bootstrap.py" in bootstrap
    assert "workflow_dispatch:" in bootstrap
