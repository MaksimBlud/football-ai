from pathlib import Path

import pandas as pd

import prospective_availability_research_cycle as cycle


def test_default_run_routes_to_readiness_only(monkeypatch):
    calls = {"readiness": 0, "evaluation": 0}

    def fake_readiness():
        calls["readiness"] += 1
        return {"status": "ACCUMULATING", "readiness": []}

    def fake_evaluation():
        calls["evaluation"] += 1
        return {"status": "unexpected"}

    monkeypatch.setattr(cycle, "run_readiness_only", fake_readiness)
    monkeypatch.setattr(cycle, "run_explicit_evaluation", fake_evaluation)
    result = cycle.run()
    assert result["status"] == "ACCUMULATING"
    assert calls == {"readiness": 1, "evaluation": 0}


def test_explicit_run_routes_to_evaluation(monkeypatch):
    calls = {"evaluation": 0}

    def fake_evaluation():
        calls["evaluation"] += 1
        return {"status": "SCORED_RESEARCH_ONLY_EXPLICIT", "blocks": 2}

    monkeypatch.setattr(cycle, "run_explicit_evaluation", fake_evaluation)
    result = cycle.run(evaluate=True)
    assert result["status"] == "SCORED_RESEARCH_ONLY_EXPLICIT"
    assert calls["evaluation"] == 1


def test_identity_only_readiness_can_be_ready_without_result_values():
    dates = pd.date_range("2026-09-05", periods=160, freq="D", tz="UTC")
    frames = []
    for league in cycle.RESEARCH_LEAGUES:
        frames.append(pd.DataFrame({
            "league": league,
            "commence_time_utc": dates,
            "availability_covered": True,
            "settled": True,
        }))
    state = cycle.identity_only_readiness(pd.concat(frames, ignore_index=True))
    assert bool(state["ready"].all()) is True
    assert (state["paired_finished_matches"] == 160).all()
    assert (state["eligible_evaluation_blocks"] >= 2).all()


def test_research_workflow_requires_manual_explicit_evaluation():
    text = Path(".github/workflows/prospective-availability-research-cycle.yml").read_text()
    assert "type: boolean" in text
    assert "default: false" in text
    assert "Run outcome-free availability readiness" in text
    assert "run: python prospective_availability_research_cycle.py\n" in text
    assert "Run explicit preregistered availability evaluation" in text
    assert "run: python prospective_availability_research_cycle.py --evaluate" in text
    assert "github.event_name == 'workflow_dispatch' && inputs.evaluate == true" in text
    assert "github.event_name != 'workflow_dispatch' || inputs.evaluate != true" in text


def test_default_cycle_source_never_loads_result_values():
    source = Path("prospective_availability_research_cycle.py").read_text()
    assert "def load_finished_result_identities" in source
    assert "def load_finished_results_for_explicit_evaluation" in source
    assert "READ_ONLY_AVAILABILITY_READINESS: result values not queried" in source
    assert "--evaluate" in source
