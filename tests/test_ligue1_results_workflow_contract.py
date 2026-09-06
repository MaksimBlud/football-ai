from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ligue1-results.yml"


def test_ligue1_evaluator_runs_only_after_written_result_status():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "Evaluate Ligue 1 predictions only after successful result sync" in source
    assert 'if [ "$status" != "WRITTEN" ]; then' in source
    assert 'echo "SKIP evaluator: result status=$status"' in source
    assert "python evaluate_ligue1_predictions.py" in source


def test_ligue1_source_unavailable_remains_provider_free_and_non_evaluating():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "THE_ODDS_API_KEY" not in source
    assert "SOURCE_UNAVAILABLE" in source
    assert "paid_provider_requests" in source
    assert "ligue1_results_status.json" in source
