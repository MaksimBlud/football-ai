from pathlib import Path
import json
import sys
import types

import numpy as np
import pandas as pd
import pytest

import multi_market_1x2_repricing_vector_v1 as mod
from research_agent_v5 import run


def test_two_way_devig_is_symmetric():
    value = mod._proportional_two_way(
        np.array([1.91]), np.array([1.91])
    )
    assert value[0] == pytest.approx(0.5)


def test_ah_line_uses_existing_fallback_without_posthoc_selection():
    frame = pd.DataFrame(
        {
            "AHh": [np.nan, -0.5, np.nan],
            "B365AH": [0.5, 1.5, -1.5],
        }
    )
    line = mod._ah_line(frame, ["AHh", "B365AH"])
    assert line.tolist() == [0.5, -0.5, -1.5]


def test_source_contract_contains_no_match_outcomes():
    forbidden = {"FTR", "FTHG", "FTAG"}
    assert forbidden.isdisjoint(set(mod.REQUIRED_FIXED_COLUMNS))


def test_bootstrap_is_zero_for_identical_paired_losses(monkeypatch):
    monkeypatch.setattr(mod, "BOOTSTRAP_DRAWS", 100)
    losses = pd.DataFrame(
        {
            "league": [
                league
                for league in ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA")
                for _ in range(5)
            ],
            "squared_error_delta": 0.0,
        }
    )
    report = mod._bootstrap(losses)
    assert report["ci95_low"] == pytest.approx(0.0)
    assert report["ci95_high"] == pytest.approx(0.0)


def _split(mse=-0.001, mae=-0.001, ci_high=-0.0001, positives=0):
    leagues = ["EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA"]
    by_league = {}
    for index, league in enumerate(leagues):
        value = 0.001 if index < positives else -0.001
        by_league[league] = {
            "candidate_minus_baseline_mse": value,
            "candidate_minus_baseline_mae": -0.001,
        }
    return {
        "candidate_minus_baseline_mse": mse,
        "candidate_minus_baseline_mae": mae,
        "by_league": by_league,
        "bootstrap": {"ci95_high": ci_high},
    }


def test_formal_gate_requires_both_splits_uncertainty_and_cross_league_stability():
    gate = mod._formal_gate(
        _split(),
        _split(),
        source_gate=True,
        eligible_leagues=4,
    )
    assert gate["supported"] is True

    failed = mod._formal_gate(
        _split(),
        _split(ci_high=0.001),
        source_gate=True,
        eligible_leagues=4,
    )
    assert failed["supported"] is False
    assert failed["gates"]["test_mse_ci95_upper_below_zero"] is False

    failed = mod._formal_gate(
        _split(),
        _split(positives=2),
        source_gate=True,
        eligible_leagues=4,
    )
    assert failed["gates"]["test_positive_mse_leagues_at_most_one"] is False


def test_blocked_result_is_complete_and_fail_closed():
    result = mod._blocked(
        {
            "eligible_leagues": ["EPL", "LA_LIGA", "SERIE_A"],
            "source_gate_passed": False,
            "closing_movement_computed_during_audit": False,
        },
        "insufficient source coverage",
    )
    assert result["decision"] == "BLOCKED_BY_SOURCE_GAP"
    assert result["supported"] is False
    assert result["match_outcomes_used"] is False
    assert result["test"]["bootstrap"]["ci95_high"] is None
    assert result["paid_odds_api_calls"] == 0
    assert result["supabase_writes"] == 0
    assert result["production_operations"] is False


def test_registered_v5_pipeline_reaches_done_without_model_api(
    tmp_path: Path, monkeypatch
):
    registry = Path("research/v5_recipe_registry.json")
    target = tmp_path / registry
    target.parent.mkdir(parents=True)
    target.write_text(registry.read_text(encoding="utf-8"), encoding="utf-8")

    family = "multi_market_1x2_repricing_vector_v1"
    run(tmp_path, 573, family)
    state_path = tmp_path / "research/agent_runs/issue_573/STATE.json"
    assert json.loads(
        state_path.read_text(encoding="utf-8")
    )["status"] == "CONTINUE"

    fake = types.ModuleType(family)
    fake.evaluate = lambda: {
        "source_audit": {
            "eligible_leagues": [
                "EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1"
            ]
        },
        "validation": {
            "candidate_minus_baseline_mse": -0.001,
            "candidate_minus_baseline_mae": -0.001,
        },
        "test": {
            "candidate_minus_baseline_mse": -0.001,
            "candidate_minus_baseline_mae": -0.001,
            "bootstrap": {
                "ci95_low": -0.002,
                "ci95_high": -0.0001,
            },
        },
        "formal_gate": {"supported": True},
        "decision": (
            "REPRICING_STATE_SUPPORTED_FOR_PROSPECTIVE_CONFIRMATION"
        ),
        "interpretation_guard": (
            "Research-only synthetic V5 lifecycle test."
        ),
    }
    monkeypatch.setitem(sys.modules, family, fake)
    run(tmp_path, 573, family)
    assert json.loads(
        state_path.read_text(encoding="utf-8")
    )["status"] == "CONTINUE"

    run(tmp_path, 573, family)
    assert json.loads(
        state_path.read_text(encoding="utf-8")
    )["status"] == "DONE"
    assert (
        tmp_path / "docs/agent_runs/issue_573/FINAL_REPORT.md"
    ).is_file()
