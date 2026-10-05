import json
import sys
import types
from pathlib import Path

import pytest

from research_agent_v5 import (
    LocalResearchError,
    load_recipe_registry,
    max_iterations_for_family,
    run,
    supports_family,
)


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_registry(root: Path) -> None:
    path = root / "research" / "v5_recipe_registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "engine": "V5_DETERMINISTIC_NO_API",
                "recipes": [
                    {
                        "hypothesis_family": "cross_market_lead_lag_independent_replication",
                        "handler": "replication",
                        "max_iterations": 2,
                        "description": "test",
                        "safety": {
                            "model_api": False,
                            "paid_odds_api": False,
                            "supabase_writes": False,
                            "production_operations": False,
                            "automatic_promotion": False,
                        },
                    },
                    {
                        "hypothesis_family": "cross_market_lead_lag_2024_25_anomaly_audit",
                        "handler": "anomaly",
                        "max_iterations": 4,
                        "description": "test",
                        "safety": {
                            "model_api": False,
                            "paid_odds_api": False,
                            "supabase_writes": False,
                            "production_operations": False,
                            "automatic_promotion": False,
                        },
                    },
                    {
                        "hypothesis_family": "kickoff_calendar_context",
                        "handler": "kickoff",
                        "max_iterations": 4,
                        "description": "test",
                        "safety": {
                            "model_api": False,
                            "paid_odds_api": False,
                            "supabase_writes": False,
                            "production_operations": False,
                            "automatic_promotion": False,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_v5_replication_closes_from_canonical_main(tmp_path: Path):
    _write_registry(tmp_path)
    canonical = {
        "experiment_id": "CROSS_MARKET_LEAD_LAG_REPLICATION_V2",
        "result": {
            "decision": "LEAD_LAG_REPLICATION_NOT_SUPPORTED",
            "result": "NO_BET",
            "validation": {
                "rows": 137,
                "mean_alignment_dot": 0.000012,
                "positive_mean_alignment_leagues": 1,
                "permutation": {"one_sided_p": 0.193},
                "bootstrap": {"ci95_low": -0.00008, "ci95_high": 0.00010},
                "admissible": False,
            },
            "test": {
                "rows": 168,
                "mean_alignment_dot": 0.000106,
                "positive_mean_alignment_leagues": 2,
                "permutation": {"one_sided_p": 0.0076},
                "bootstrap": {"ci95_low": 0.000036, "ci95_high": 0.000183},
                "gate": True,
            },
        },
        "safety": {
            "match_outcomes_used": False,
            "opened_2026_27_data_used": False,
            "paid_odds_api_calls": 0,
            "supabase_writes": 0,
            "production_model_operations": 0,
            "production_promotion": False,
        },
    }
    path = tmp_path / "experiments" / "cross_market_lead_lag_replication_v2_report.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(canonical), encoding="utf-8")

    run(tmp_path, 482, "cross_market_lead_lag_independent_replication")

    state = _read(tmp_path / "research/agent_runs/issue_482/STATE.json")
    proof = _read(tmp_path / "research/agent_runs/issue_482/CANONICAL_RESULT.json")
    assert state["status"] == "DONE"
    assert state["engine"] == "V5_DETERMINISTIC_NO_API"
    assert proof["product_decision"] == "CLOSE_DIRECTION"
    assert proof["paid_collection_justified"] is False
    assert (tmp_path / "docs/agent_runs/issue_482/FINAL_REPORT.md").is_file()


def test_v5_replication_fails_closed_on_safety_mismatch(tmp_path: Path):
    _write_registry(tmp_path)
    path = tmp_path / "experiments" / "cross_market_lead_lag_replication_v2_report.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "result": {"decision": "LEAD_LAG_REPLICATION_NOT_SUPPORTED", "result": "NO_BET"},
                "safety": {
                    "match_outcomes_used": True,
                    "opened_2026_27_data_used": False,
                    "paid_odds_api_calls": 0,
                    "supabase_writes": 0,
                    "production_model_operations": 0,
                    "production_promotion": False,
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(LocalResearchError, match="safety"):
        run(tmp_path, 482, "cross_market_lead_lag_independent_replication")


def test_v5_anomaly_state_machine(tmp_path: Path, monkeypatch):
    _write_registry(tmp_path)
    family = "cross_market_lead_lag_2024_25_anomaly_audit"
    run(tmp_path, 481, family)
    state = _read(tmp_path / "research/agent_runs/issue_481/STATE.json")
    assert state["status"] == "CONTINUE"
    assert (tmp_path / "research/agent_runs/issue_481/PREREGISTRATION.md").is_file()

    fake = types.ModuleType("cross_market_lead_lag_anomaly_audit_v1")
    fake.evaluate = lambda: {
        "diagnostic_label": "NO_OBSERVABLE_SOURCE_MARKET_EXPLANATION",
        "rows": 2920,
        "summary": {"plain_language": "No broad shift."},
    }
    monkeypatch.setitem(sys.modules, "cross_market_lead_lag_anomaly_audit_v1", fake)
    run(tmp_path, 481, family)
    state = _read(tmp_path / "research/agent_runs/issue_481/STATE.json")
    assert state["status"] == "CONTINUE"
    assert (tmp_path / "research/agent_runs/issue_481/RESULT.json").is_file()

    run(tmp_path, 481, family)
    state = _read(tmp_path / "research/agent_runs/issue_481/STATE.json")
    assert state["status"] == "DONE"
    assert (tmp_path / "docs/agent_runs/issue_481/FINAL_REPORT.md").is_file()


def test_v5_kickoff_state_machine(tmp_path: Path, monkeypatch):
    _write_registry(tmp_path)
    family = "kickoff_calendar_context"
    run(tmp_path, 428, family)
    state = _read(tmp_path / "research/agent_runs/issue_428/STATE.json")
    assert state["status"] == "CONTINUE"

    fake = types.ModuleType("kickoff_calendar_context_v1")
    fake.evaluate = lambda: {
        "decision": "NO_KICKOFF_CALENDAR_OOS_SIGNAL",
        "validation": {
            "rows": 200,
            "calendar_minus_baseline_log_loss": 0.001,
        },
        "test": {
            "rows": 210,
            "calendar_minus_baseline_log_loss": 0.002,
            "bootstrap": {"ci95_low": -0.001, "ci95_high": 0.004},
        },
    }
    monkeypatch.setitem(sys.modules, "kickoff_calendar_context_v1", fake)
    run(tmp_path, 428, family)
    assert _read(tmp_path / "research/agent_runs/issue_428/STATE.json")["status"] == "CONTINUE"

    run(tmp_path, 428, family)
    assert _read(tmp_path / "research/agent_runs/issue_428/STATE.json")["status"] == "DONE"


def test_v5_rejects_unknown_family(tmp_path: Path):
    _write_registry(tmp_path)
    with pytest.raises(LocalResearchError, match="no V5 deterministic recipe"):
        run(tmp_path, 999, "unknown")


def test_v5_recipe_registry_support_and_iteration_budget(tmp_path: Path):
    _write_registry(tmp_path)
    payload = load_recipe_registry(tmp_path)
    assert payload["schema_version"] == 1
    assert supports_family(tmp_path, "kickoff_calendar_context") is True
    assert supports_family(tmp_path, "not_registered") is False
    assert max_iterations_for_family(tmp_path, "cross_market_lead_lag_independent_replication") == 2


def test_v5_recipe_registry_fails_closed_on_unsafe_recipe(tmp_path: Path):
    _write_registry(tmp_path)
    path = tmp_path / "research" / "v5_recipe_registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["recipes"][0]["safety"]["model_api"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(LocalResearchError, match="safety contract mismatch"):
        load_recipe_registry(tmp_path)
