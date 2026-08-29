import sys
from pathlib import Path
from subprocess import CompletedProcess

import scheduled_la_liga_live_cycle as scheduled


def test_scheduled_cycle_grants_live_collection_then_runs_durable_cycle_and_ledger():
    commands = []

    def runner(command, **kwargs):
        commands.append((command, kwargs))
        return CompletedProcess(command, 0)

    result = scheduled.run_scheduled_cycle(runner=runner)

    assert result == 0
    assert commands == [
        (
            [
                sys.executable,
                "la_liga_collection_runner.py",
                "--live",
                "--skip-downstream",
            ],
            {"check": False},
        ),
        (
            [
                sys.executable,
                "la_liga_live_cycle.py",
                "--skip-collection",
                "--persistence",
                "supabase",
            ],
            {"check": False},
        ),
        (
            [
                sys.executable,
                "persist_la_liga_prediction_ledger.py",
            ],
            {"check": False},
        ),
    ]


def test_collection_failure_prevents_durable_cycle_and_ledger():
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return CompletedProcess(command, 7)

    result = scheduled.run_scheduled_cycle(runner=runner)

    assert result == 7
    assert commands == [
        [
            sys.executable,
            "la_liga_collection_runner.py",
            "--live",
            "--skip-downstream",
        ]
    ]


def test_durable_cycle_failure_still_attempts_ledger_and_preserves_cycle_failure():
    commands = []
    returncodes = iter((0, 9, 0))

    def runner(command, **kwargs):
        commands.append(command)
        return CompletedProcess(command, next(returncodes))

    result = scheduled.run_scheduled_cycle(runner=runner)

    assert result == 9
    assert commands == [
        [
            sys.executable,
            "la_liga_collection_runner.py",
            "--live",
            "--skip-downstream",
        ],
        [
            sys.executable,
            "la_liga_live_cycle.py",
            "--skip-collection",
            "--persistence",
            "supabase",
        ],
        [
            sys.executable,
            "persist_la_liga_prediction_ledger.py",
        ],
    ]


def test_cycle_and_ledger_failure_preserves_cycle_failure():
    returncodes = iter((0, 9, 11))

    def runner(command, **kwargs):
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 9


def test_ledger_failure_fails_successful_scheduled_cycle():
    returncodes = iter((0, 0, 11))

    def runner(command, **kwargs):
        return CompletedProcess(command, next(returncodes))

    assert scheduled.run_scheduled_cycle(runner=runner) == 11


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
