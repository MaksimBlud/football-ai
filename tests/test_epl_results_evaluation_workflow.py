from pathlib import Path


WORKFLOW = Path(".github/workflows/epl-results.yml")


def test_epl_results_workflow_runs_evaluator_after_result_sync():
    source = WORKFLOW.read_text(encoding="utf-8")

    sync = "python update_epl_results.py --write"
    evaluate = "python evaluate_league_predictions.py --league EPL"

    assert sync in source
    assert evaluate in source
    assert source.index(evaluate) > source.index(sync)


def test_epl_results_workflow_installs_evaluator_dependencies():
    source = WORKFLOW.read_text(encoding="utf-8")

    install_line = "pip install requests supabase python-dotenv numpy pandas"
    assert install_line in source


def test_epl_results_workflow_evaluator_is_read_only_command():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "Evaluate settled EPL predictions" in source
    assert "evaluate_league_predictions.py --league EPL" in source
    assert "evaluate_league_predictions.py --league EPL --write" not in source
