from pathlib import Path


WORKFLOW = Path(".github/workflows/turkey-portugal-results.yml")


def test_results_workflow_keeps_matrix_concurrency_inside_results_job():
    text = WORKFLOW.read_text(encoding="utf-8")
    jobs_pos = text.index("jobs:")
    results_pos = text.index("  results:", jobs_pos)
    strategy_pos = text.index("    strategy:", results_pos)
    concurrency_pos = text.index("    concurrency:", results_pos)
    env_pos = text.index("    env:", results_pos)

    assert "concurrency:" not in text[:jobs_pos]
    assert strategy_pos < concurrency_pos < env_pos
    assert 'group: turkey-portugal-public-results-${{ matrix.league }}' in text[concurrency_pos:env_pos]


def test_results_workflow_is_provider_free_and_scheduled_for_both_leagues():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "41 */12 * * *"' in text
    assert "TURKEY_SUPER_LIG" in text
    assert "PRIMEIRA_LIGA" in text
    assert "THE_ODDS_API_KEY" not in text
    assert "the-odds-api" not in text.lower()
    assert "update_turkey_portugal_results.py" in text
    assert "--write" in text


def test_results_workflow_self_proves_on_main_only_when_its_contract_changes():
    text = WORKFLOW.read_text(encoding="utf-8")
    on_block = text[:text.index("permissions:")]
    assert "  push:\n    branches: [main]\n    paths:\n      - \".github/workflows/turkey-portugal-results.yml\"" in on_block
    assert "update_turkey_portugal_results.py" not in on_block
