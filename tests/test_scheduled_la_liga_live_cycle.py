import sys
from subprocess import CompletedProcess

import scheduled_la_liga_live_cycle as scheduled


def test_scheduled_cycle_grants_live_collection_then_runs_durable_cycle():
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
    ]


def test_collection_failure_prevents_durable_cycle():
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


def test_workflow_uses_explicit_scheduled_entrypoint():
    from pathlib import Path

    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "la-liga-live-cycle.yml"
    ).read_text()

    assert "python3 scheduled_la_liga_live_cycle.py" in workflow
    assert "python3 la_liga_live_cycle.py" not in workflow


def test_default_live_cycle_still_does_not_grant_live_collection():
    import inspect
    import la_liga_live_cycle as cycle

    source = inspect.getsource(cycle)
    assert '"--live"' not in source
