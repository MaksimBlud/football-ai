import sys
from pathlib import Path
from subprocess import CompletedProcess

import scheduled_la_liga_live_cycle as scheduled


def _expected_commands():
    return [
        [sys.executable, "la_liga_collection_runner.py", "--live", "--skip-downstream"],
        [sys.executable, "la_liga_live_cycle.py", "--skip-collection", "--persistence", "supabase"],
        [sys.executable, "persist_la_liga_prediction_ledger.py"],
        [sys.executable, "persist_la_liga_finished_results.py"],
        [sys.executable, "evaluate_league_predictions.py", "--league", "LA_LIGA"],
    ]


def test_scheduled_cycle_runs_full_canonical_path():
    commands = []

    def runner(command, **kwargs):
        commands.append((command, kwargs))
        return CompletedProcess(command, 0)

    assert scheduled.run_scheduled_cycle(runner=runner) == 0
    assert [command for command, _ in commands] == _expected_commands()
    assert all(kwargs == {"check": False} for _, kwargs in commands)


def test_collection_failure_prevents_all_downstream_steps():
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return CompletedProcess(command, 7)

    assert scheduled.run_scheduled_cycle(runner=runner) == 7
    assert commands == [_expected_commands()[0]]


def test_durable_cycle_failure_still_attempts_canonical_steps_and_preserves_cycle_failure():
    commands = []
    returncodes = iter((0, 9, 0, 0, 0))

    def runner(command, **kwargs):
        commands.append(command)
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 9
    assert commands == _expected_commands()


def test_cycle_and_canonical_failures_preserve_cycle_failure():
    returncodes = iter((0, 9, 11, 13, 15))

    def runner(command, **kwargs):
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 9


def test_ledger_failure_has_precedence_after_successful_cycle():
    returncodes = iter((0, 0, 11, 13, 15))

    def runner(command, **kwargs):
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 11


def test_results_bridge_failure_has_precedence_over_evaluation():
    returncodes = iter((0, 0, 0, 13, 15))

    def runner(command, **kwargs):
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 13


def test_evaluation_failure_fails_otherwise_successful_cycle():
    returncodes = iter((0, 0, 0, 0, 15))

    def runner(command, **kwargs):
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 15


def test_workflow_uses_explicit_scheduled_entrypoint():
    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "la-liga-live-cycle.yml"
    ).read_text()

    assert "python3 scheduled_la_liga_live_cycle.py" in workflow
    assert "python3 la_liga_live_cycle.py" not in workflow


def test_default_live_cycle_still_does_not_grant_live_collection():
    source = (
        Path(__file__).parents[1]
        / "la_liga_live_cycle.py"
    ).read_text()

    assert '"--live"' not in source
