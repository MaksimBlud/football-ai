from pathlib import Path


ROOT = Path(__file__).parents[1]
STATUS = ROOT / "docs" / "TURKEY_PORTUGAL_MARKET_ONLY_STATUS.md"
PAID_WORKFLOW = ROOT / ".github" / "workflows" / "turkey-portugal-market-only-cycle.yml"
RESULTS_WORKFLOW = ROOT / ".github" / "workflows" / "turkey-portugal-results.yml"


def test_status_matches_manual_only_paid_collection_contract():
    status = STATUS.read_text()
    paid = PAID_WORKFLOW.read_text()

    assert "PAID ACQUISITION MANUAL-ONLY" in status
    assert "Paid h2h acquisition is intentionally `MANUAL_ONLY`" in status
    assert "The 500-request start floor is a necessary runtime gate, not a scheduler trigger." in status
    assert "workflow_dispatch:" in paid
    assert "schedule:" not in paid
    assert "push:" not in paid


def test_status_matches_scheduled_provider_free_results_contract():
    status = STATUS.read_text()
    results = RESULTS_WORKFLOW.read_text()

    assert "Provider-free finished-result ingestion remains automated separately" in status
    assert "schedule:" in results
    assert "cron:" in results
    assert "THE_ODDS_API_KEY" not in results


def test_status_does_not_promise_automatic_paid_collection():
    status = STATUS.read_text()

    stale_promises = (
        "a two-hour scheduled matrix workflow for both leagues",
        "Actual h2h snapshot/results collection starts automatically",
        "The first future run above the threshold will exercise",
    )
    for phrase in stale_promises:
        assert phrase not in status
