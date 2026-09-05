from pathlib import Path

WORKFLOW_DIR = Path(__file__).parents[1] / ".github" / "workflows"

LEGACY_PAID_WORKFLOWS = {
    "odds-snapshots.yml": 1,
    "serie-a-odds-snapshots.yml": 1,
    "bundesliga-odds-snapshots.yml": 1,
    "ligue1-odds-snapshots.yml": 1,
    "eredivisie-odds-snapshots.yml": 1,
    "rpl-odds-snapshots.yml": 1,
    "rpl-results.yml": 2,
    # Two matrix jobs can each spend h2h=1 + scores=2. Each job reserves the
    # workflow-wide worst case so concurrent preflights cannot cross reserve.
    "turkey-portugal-market-only-cycle.yml": 6,
}

SPECIALIZED_PAID_WORKFLOWS = {"multi-market-cycle.yml"}
ZERO_COST_QUOTA_WORKFLOWS = {"multi-market-activation-status.yml"}


def _read(name: str) -> str:
    return (WORKFLOW_DIR / name).read_text(encoding="utf-8")


def test_all_legacy_paid_workflows_are_manual_only_and_guarded():
    for name, max_cost in LEGACY_PAID_WORKFLOWS.items():
        source = _read(name)
        assert "THE_ODDS_API_KEY" in source, name
        assert "workflow_dispatch:" in source, name
        assert "cron:" not in source, name
        assert f"python odds_api_budget_guard.py --max-cost {max_cost}" in source, name


def test_multi_market_keeps_its_specialized_paid_latch_and_credit_cap():
    source = _read("multi-market-cycle.yml")
    assert "MULTI_MARKET_COLLECTION_ENABLED" in source
    assert "MULTI_MARKET_MAX_PAID_REQUESTS" in source
    assert "MULTI_MARKET_MAX_PAID_CREDITS" in source
    assert "allow_paid_collection" in source
    assert "paid_provider_requests" in source


def test_every_workflow_with_provider_key_has_an_explicit_safety_classification():
    classified = LEGACY_PAID_WORKFLOWS.keys() | SPECIALIZED_PAID_WORKFLOWS | ZERO_COST_QUOTA_WORKFLOWS
    with_key = {
        path.name
        for path in WORKFLOW_DIR.glob("*.yml")
        if "THE_ODDS_API_KEY" in path.read_text(encoding="utf-8")
    }
    assert with_key == classified


def test_zero_cost_quota_workflows_assert_no_paid_requests():
    for name in ZERO_COST_QUOTA_WORKFLOWS:
        source = _read(name)
        assert "paid_provider_requests']==0" in source or 'paid_provider_requests\"]==0' in source, name
