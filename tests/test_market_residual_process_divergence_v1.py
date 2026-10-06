from io import BytesIO
import json
from pathlib import Path
import sys
import types

import pandas as pd

import market_residual_process_divergence_v1 as mod
from research_agent_v5 import run


def _payload(rows: list[dict]) -> bytes:
    defaults = {
        "HS": 10,
        "AS": 8,
        "B365H": 2.0,
        "B365D": 3.5,
        "B365A": 4.0,
    }
    frame = pd.DataFrame([{**defaults, **row} for row in rows])
    buffer = BytesIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()


def _six_matches(season: str = "2023-2024") -> dict[tuple[str, str], bytes]:
    rows = []
    for day in range(1, 7):
        rows.append(
            {
                "Date": f"{day:02d}/08/2023",
                "HomeTeam": "A",
                "AwayTeam": "B",
                "FTR": "A" if day <= 5 else "D",
                "HST": 5 if day <= 5 else 99,
                "AST": 1 if day <= 5 else 0,
            }
        )
    return {("BUNDESLIGA", season): _payload(rows)}


def test_feature_uses_exact_prior_five_and_not_current_match():
    features, coverage = mod.build_features(_six_matches())
    assert len(features) == 1
    row = features.iloc[0]
    assert row.home_process_result_divergence_5 == 5 / 6
    assert row.away_process_result_divergence_5 == 1 / 6 - 1
    assert row.diff_process_result_divergence_5 == 5 / 3
    assert coverage["BUNDESLIGA:2023-2024"]["eligible_rows"] == 1

    changed = _six_matches()
    frame = pd.read_csv(BytesIO(changed[("BUNDESLIGA", "2023-2024")]))
    frame.loc[5, ["FTR", "HST", "AST"]] = ["H", 0, 100]
    changed[("BUNDESLIGA", "2023-2024")] = frame.to_csv(index=False).encode()
    changed_features, _ = mod.build_features(changed)
    for column in mod.DIVERGENCE_FEATURES:
        assert changed_features.iloc[0][column] == row[column]


def test_feature_history_resets_at_season_boundary():
    payloads = _six_matches("2023-2024")
    payloads[("BUNDESLIGA", "2024-2025")] = _payload(
        [
            {
                "Date": "01/08/2024",
                "HomeTeam": "A",
                "AwayTeam": "B",
                "FTR": "H",
                "HST": 3,
                "AST": 2,
            }
        ]
    )
    features, coverage = mod.build_features(payloads)
    assert set(features.season) == {"2023-2024"}
    assert coverage["BUNDESLIGA:2024-2025"]["eligible_rows"] == 0


def _split(log_loss=-0.01, brier=-0.02, league_b=-0.005, ci_high=-0.001):
    return {
        "candidate_minus_market_log_loss": log_loss,
        "candidate_minus_market_brier": brier,
        "by_league": {
            "BUNDESLIGA": {"candidate_minus_market_log_loss": league_b},
            "LIGUE_1": {"candidate_minus_market_log_loss": -0.004},
        },
        "bootstrap": {"ci95_high": ci_high},
    }


def test_formal_gate_requires_all_validation_test_ci_and_league_conditions():
    assert mod._formal_gate(_split(), _split(), True)["supported"] is True
    failed = mod._formal_gate(_split(), _split(ci_high=0.001), True)
    assert failed["supported"] is False
    assert failed["gates"]["test_log_loss_ci95_upper_below_zero"] is False
    failed = mod._formal_gate(_split(), _split(league_b=0.001), True)
    assert failed["gates"]["no_positive_test_league_log_loss_delta"] is False


def test_blocked_result_is_report_complete_and_fail_closed():
    result = mod._blocked({"outcome_read_before_audit": False}, "missing source")
    assert result["decision"] == "BLOCKED_BY_SOURCE_GAP"
    assert result["formal_gate"]["supported"] is False
    assert result["validation"]["rows"] == 0
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

    family = "market_residual_process_divergence_v1"
    run(tmp_path, 562, family)
    state_path = tmp_path / "research/agent_runs/issue_562/STATE.json"
    assert json.loads(state_path.read_text(encoding="utf-8"))["status"] == "CONTINUE"

    fake = types.ModuleType("market_residual_process_divergence_v1")
    fake.evaluate = lambda: {
        "source_audit": {"outcome_read_before_audit": False},
        "validation": {
            "candidate_minus_market_log_loss": -0.01,
            "candidate_minus_market_brier": -0.01,
        },
        "test": {
            "candidate_minus_market_log_loss": -0.01,
            "candidate_minus_market_brier": -0.01,
            "bootstrap": {"ci95_low": -0.02, "ci95_high": -0.001},
            "by_league": {
                "BUNDESLIGA": {"candidate_minus_market_log_loss": -0.01},
                "LIGUE_1": {"candidate_minus_market_log_loss": -0.01},
            },
        },
        "formal_gate": {"supported": True},
        "decision": "SUPPORTED_MARKET_RESIDUAL_PROCESS_DIVERGENCE",
        "interpretation_guard": "Research-only synthetic test result.",
    }
    monkeypatch.setitem(sys.modules, family, fake)
    run(tmp_path, 562, family)
    assert json.loads(state_path.read_text(encoding="utf-8"))["status"] == "CONTINUE"
    run(tmp_path, 562, family)
    assert json.loads(state_path.read_text(encoding="utf-8"))["status"] == "DONE"
    assert (tmp_path / "docs/agent_runs/issue_562/FINAL_REPORT.md").is_file()
