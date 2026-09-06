from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_paid_market_cycle_does_not_import_or_sync_finished_results():
    source = (ROOT / "turkey_portugal_operational_cycle.py").read_text()
    assert "update_turkey_portugal_results" not in source
    assert "sync_results(" not in source
    assert '"results_sync":"SEPARATE_PROVIDER_FREE_WORKFLOW"' in source.replace(" ", "")


def test_provider_free_results_have_a_separate_scheduled_workflow():
    workflow = (ROOT / ".github/workflows/turkey-portugal-results.yml").read_text()
    assert "schedule:" in workflow
    assert "THE_ODDS_API_KEY" not in workflow
    assert "update_turkey_portugal_results.py" in workflow
    assert "--write" in workflow
