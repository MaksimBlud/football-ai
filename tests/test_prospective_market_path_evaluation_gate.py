from pathlib import Path

import prospective_market_path_cycle as cycle


def test_default_run_uses_readiness_only(monkeypatch):
    calls = {"readiness": 0, "evaluation": 0}

    def fake_growth():
        calls["readiness"] += 1
        return {"readiness": []}

    def fake_evaluation():
        calls["evaluation"] += 1
        return {"status": "unexpected"}

    monkeypatch.setattr(cycle, "_run_sample_growth", fake_growth)
    monkeypatch.setattr(cycle, "run_explicit_evaluation", fake_evaluation)

    result = cycle.run()
    assert result["status"] == "ACCUMULATING"
    assert calls["readiness"] == 1
    assert calls["evaluation"] == 0


def test_explicit_evaluate_routes_to_evaluation(monkeypatch):
    calls = {"evaluation": 0}

    def fake_evaluation():
        calls["evaluation"] += 1
        return {"status": "SCORED_RESEARCH_ONLY_EXPLICIT", "blocks": 2}

    monkeypatch.setattr(cycle, "run_explicit_evaluation", fake_evaluation)
    result = cycle.run(evaluate=True)
    assert result["status"] == "SCORED_RESEARCH_ONLY_EXPLICIT"
    assert calls["evaluation"] == 1


def test_workflow_requires_manual_explicit_evaluation():
    text = Path(".github/workflows/prospective-market-path-cycle.yml").read_text()
    assert "type: boolean" in text
    assert "default: false" in text
    assert "Run outcome-free readiness cycle" in text
    assert "run: python prospective_market_path_cycle.py\n" in text
    assert "Run explicit preregistered outcome evaluation" in text
    assert "run: python prospective_market_path_cycle.py --evaluate" in text
    assert "github.event_name == 'workflow_dispatch' && inputs.evaluate == true" in text
    assert "github.event_name != 'workflow_dispatch' || inputs.evaluate != true" in text


def test_cycle_source_separates_readiness_and_outcome_loading():
    source = Path("prospective_market_path_cycle.py").read_text()
    assert "def load_results_for_explicit_evaluation" in source
    assert "def run_readiness_only" in source
    assert "def _run_sample_growth" in source
    assert "--evaluate" in source
    assert "from database import supabase" in source
