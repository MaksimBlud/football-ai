from types import SimpleNamespace

import pytest

import scheduled_epl_live_cycle as scheduled


def test_preexisting_finished_results_are_allowed(monkeypatch):
    real_counts = iter(((10, 7), (12, 7), (12, 7), (12, 7)))

    def counts():
        return next(real_counts)

    seen = []

    def fake_run_cycle():
        seen.append(scheduled.cycle.durable_counts())
        seen.append(scheduled.cycle.durable_counts())
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(scheduled.cycle, "run_cycle", fake_run_cycle)

    result = scheduled.run_scheduled_cycle(counts=counts)

    assert result.ok is True
    assert seen == [(12, 0), (12, 0)]


def test_finished_result_mutation_is_rejected_even_when_inner_cycle_succeeds(monkeypatch):
    states = iter(((10, 7), (10, 7), (10, 8)))

    def counts():
        return next(states)

    monkeypatch.setattr(
        scheduled.cycle,
        "run_cycle",
        lambda: SimpleNamespace(ok=True),
    )

    with pytest.raises(RuntimeError, match="modified finished results"):
        scheduled.run_scheduled_cycle(counts=counts)


def test_finished_result_mutation_is_rejected_even_when_inner_cycle_fails(monkeypatch):
    states = iter(((10, 7), (10, 7), (10, 8)))

    def counts():
        return next(states)

    def fail():
        raise ValueError("inner failure")

    monkeypatch.setattr(scheduled.cycle, "run_cycle", fail)

    with pytest.raises(RuntimeError, match="modified finished results") as excinfo:
        scheduled.run_scheduled_cycle(counts=counts)

    assert isinstance(excinfo.value.__cause__, ValueError)


def test_inner_failure_is_preserved_when_results_are_unchanged(monkeypatch):
    states = iter(((10, 7), (10, 7), (10, 7)))

    def counts():
        return next(states)

    def fail():
        raise ValueError("inner failure")

    monkeypatch.setattr(scheduled.cycle, "run_cycle", fail)

    with pytest.raises(ValueError, match="inner failure"):
        scheduled.run_scheduled_cycle(counts=counts)


def test_workflow_uses_scheduled_entrypoint():
    from pathlib import Path

    source = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "epl-live-cycle.yml"
    ).read_text()

    assert "python3 scheduled_epl_live_cycle.py" in source
    assert "python3 epl_live_cycle.py" not in source
