from pathlib import Path


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_rpl_snapshot_workflow_uses_adaptive_scheduler():
    source = read(".github/workflows/rpl-odds-snapshots.yml")
    assert 'cron: "7 */2 * * *"' in source
    assert "scheduled_rpl_odds_snapshot.py" in source
    assert "save_rpl_odds_snapshot.py" not in source


def test_rpl_live_workflow_runs_after_snapshot_window():
    source = read(".github/workflows/rpl-live-cycle.yml")
    assert 'cron: "32 */2 * * *"' in source
    assert "rpl_live_cycle.py" in source
    assert "THE_ODDS_API_KEY" not in source


def test_rpl_results_workflow_is_twice_daily_and_evaluates():
    source = read(".github/workflows/rpl-results.yml")
    assert 'cron: "52 */12 * * *"' in source
    assert "update_rpl_results.py --write" in source
    assert "evaluate_rpl_predictions.py" in source


def test_permanent_rpl_workflows_do_not_reference_production_model():
    for path in (
        ".github/workflows/rpl-odds-snapshots.yml",
        ".github/workflows/rpl-live-cycle.yml",
        ".github/workflows/rpl-results.yml",
    ):
        source = read(path)
        assert ".pkl" not in source
        assert "train_model" not in source
