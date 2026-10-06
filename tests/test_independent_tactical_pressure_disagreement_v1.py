from __future__ import annotations

import json
from pathlib import Path
import sys
import types

import numpy as np
import pandas as pd
import pytest

import independent_tactical_pressure_disagreement_v1 as mod
from research_agent_v5 import run


def _history() -> pd.DataFrame:
    rows = []
    for index in range(6):
        rows.append(
            {
                "season_start": 2024,
                "match_date": pd.Timestamp(f"2024-08-{index + 1:02d} 20:00:00"),
                "venue": "h" if index % 2 == 0 else "a",
                "deep": 1.0 + index,
                "deep_allowed": 2.0 + index,
                "ppda": 3.0 + index,
                "ppda_allowed": 4.0 + index,
            }
        )
    rows.append(
        {
            "season_start": 2023,
            "match_date": pd.Timestamp("2024-07-31 20:00:00"),
            "venue": "h",
            "deep": 999.0,
            "deep_allowed": 999.0,
            "ppda": 999.0,
            "ppda_allowed": 999.0,
        }
    )
    return pd.DataFrame(rows)


def test_snapshot_uses_exact_prior_five_same_season_and_excludes_target_day():
    snapshot = mod._same_season_snapshot(
        _history(),
        season_start=2024,
        target_date=pd.Timestamp("2024-08-06"),
    )
    assert snapshot == {
        "deep": 3.0,
        "deep_allowed": 4.0,
        "ppda": 5.0,
        "ppda_allowed": 6.0,
    }

    # The sixth row is on the target calendar day and cannot leak into features.
    changed = _history()
    changed.loc[5, list(mod.TACTICAL_FIELDS)] = [500, 500, 500, 500]
    assert (
        mod._same_season_snapshot(
            changed,
            season_start=2024,
            target_date=pd.Timestamp("2024-08-06 23:59:00"),
        )
        == snapshot
    )


def _marked(counts: dict[tuple[int, str], int]) -> pd.DataFrame:
    rows = []
    for (season, league), count in counts.items():
        rows.extend(
            {
                "season_start": season,
                "league": league,
                "disagreement": True,
            }
            for _ in range(count)
        )
    return pd.DataFrame(rows)


def test_support_gate_is_outcome_free_and_requires_pool_and_each_league():
    counts = {
        (season, league): 10
        for season in (mod.VALIDATION, mod.TEST)
        for league in mod.LEAGUES
    }
    support = mod._support(_marked(counts))
    assert support["passed"] is True
    assert support["splits"]["test"]["disagreement_rows"] == 50

    counts[(mod.TEST, "LIGUE_1")] = 7
    failed = mod._support(_marked(counts))
    assert failed["passed"] is False
    assert failed["splits"]["test"]["support_gate_passed"] is False


def _split(*, log_loss=-0.01, brier=-0.01, ci_high=-0.001, league5=-0.001):
    values = [-0.01, -0.008, -0.006, -0.004, league5]
    return {
        "football_minus_market_log_loss": log_loss,
        "football_minus_market_brier": brier,
        "bootstrap": {"ci95_high": ci_high},
        "by_league": {
            league: {"football_minus_market_log_loss": value}
            for league, value in zip(mod.LEAGUES, values)
        },
    }


def test_formal_gate_requires_temporal_ci_and_cross_league_conditions():
    assert mod._formal_gate(_split(), _split())["supported"] is True
    assert mod._formal_gate(_split(), _split(ci_high=0.001))["supported"] is False
    four_negative = mod._formal_gate(_split(), _split(league5=0.005))
    assert four_negative["supported"] is True
    too_large = mod._formal_gate(_split(), _split(league5=0.011))
    assert too_large["supported"] is False
    assert too_large["gates"]["no_test_league_delta_above_0_01"] is False


def test_blocked_support_result_is_report_complete_and_fail_closed():
    result = mod._blocked(
        {
            "outcome_read_before_audit": False,
            "reserved_outcomes_read_before_support_gate": False,
        },
        "too few disagreements",
        "BLOCKED_LOW_DISAGREEMENT_SAMPLE",
    )
    assert result["decision"] == "BLOCKED_LOW_DISAGREEMENT_SAMPLE"
    assert result["formal_gate"]["supported"] is False
    assert result["test"]["bootstrap"]["ci95_high"] is None
    assert result["paid_odds_api_calls"] == 0
    assert result["supabase_writes"] == 0
    assert result["production_operations"] is False


def test_market_probabilities_are_multiplicatively_devigged():
    probabilities = mod._market_probabilities(
        pd.Series({"AvgH": 2.0, "AvgD": 4.0, "AvgA": 4.0})
    )
    assert probabilities is not None
    assert np.asarray(probabilities) == pytest.approx([0.5, 0.25, 0.25])


def test_registered_v5_pipeline_reaches_done_without_model_api(
    tmp_path: Path, monkeypatch
):
    registry = Path("research/v5_recipe_registry.json")
    target = tmp_path / registry
    target.parent.mkdir(parents=True)
    target.write_text(registry.read_text(encoding="utf-8"), encoding="utf-8")

    family = "independent_tactical_pressure_disagreement_v1"
    run(tmp_path, 568, family)
    state_path = tmp_path / "research/agent_runs/issue_568/STATE.json"
    assert json.loads(state_path.read_text(encoding="utf-8"))["status"] == "CONTINUE"

    fake = types.ModuleType(family)
    fake.evaluate = lambda: {
        "source_audit": {
            "outcome_read_before_audit": False,
            "reserved_outcomes_read_before_support_gate": False,
        },
        "validation": {
            "football_minus_market_log_loss": -0.01,
            "football_minus_market_brier": -0.01,
        },
        "test": {
            "football_minus_market_log_loss": -0.01,
            "football_minus_market_brier": -0.01,
            "bootstrap": {"ci95_low": -0.02, "ci95_high": -0.001},
            "by_league": {
                league: {"football_minus_market_log_loss": -0.01}
                for league in mod.LEAGUES
            },
        },
        "formal_gate": {"supported": True},
        "decision": "SUPPORTED_INDEPENDENT_TACTICAL_DISAGREEMENT_EDGE",
        "interpretation_guard": "Research-only synthetic test result.",
    }
    monkeypatch.setitem(sys.modules, family, fake)
    run(tmp_path, 568, family)
    assert json.loads(state_path.read_text(encoding="utf-8"))["status"] == "CONTINUE"
    run(tmp_path, 568, family)
    assert json.loads(state_path.read_text(encoding="utf-8"))["status"] == "DONE"
    assert (tmp_path / "docs/agent_runs/issue_568/FINAL_REPORT.md").is_file()
