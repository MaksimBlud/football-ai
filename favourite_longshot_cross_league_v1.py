"""Frozen favourite-longshot transport to Bundesliga and Ligue 1 (Issue #542)."""
from __future__ import annotations

from typing import Any

import favourite_longshot_bias_v1 as parent
from cross_league_bookmaker_source import LEAGUES, download_and_audit

EXPERIMENT_ID = "FAVOURITE_LONGSHOT_CROSS_LEAGUE_V1"


def _source() -> tuple[dict[tuple[str, str], bytes], dict[str, Any], list[str]]:
    payloads, audit, included = download_and_audit(parent.BOOKMAKERS)
    audit["intraday_snapshot_gaps"] = {
        "24h": "No exact timestamped 24h snapshot in frozen Football-Data source.",
        "6h": "No exact timestamped 6h snapshot in frozen Football-Data source.",
        "1h": "No exact timestamped 1h snapshot in frozen Football-Data source.",
    }
    return payloads, audit, included


def _positive(value: Any) -> bool:
    return value is not None and float(value) > 0.0


def evaluate() -> dict[str, Any]:
    old_order = parent.LEAGUE_ORDER
    old_download = parent._download_and_audit
    try:
        parent.LEAGUE_ORDER = tuple(LEAGUES)
        parent._download_and_audit = _source
        report = parent.evaluate()
    finally:
        parent.LEAGUE_ORDER = old_order
        parent._download_and_audit = old_download

    if report["decision"] == "BLOCKED_BY_SOURCE_GAP":
        report["experiment_id"] = EXPERIMENT_ID
        return report

    validation = report["validation"]["closing"]
    test = report["test"]["closing"]
    v_regions = validation["regions"]
    t_regions = test["regions"]
    v_leagues = validation["by_league"]
    t_leagues = test["by_league"]
    t_books = test["by_bookmaker"]
    gates = {
        "both_leagues_positive_validation_slope": len(v_leagues) == 2 and all(_positive(value["residual_slope"]) for value in v_leagues.values()),
        "both_leagues_positive_test_slope": len(t_leagues) == 2 and all(_positive(value["residual_slope"]) for value in t_leagues.values()),
        "validation_pooled_ci_above_zero": validation["residual_slope"]["ci95_low"] is not None and validation["residual_slope"]["ci95_low"] > 0.0,
        "test_pooled_ci_above_zero": test["residual_slope"]["ci95_low"] is not None and test["residual_slope"]["ci95_low"] > 0.0,
        "validation_region_direction": v_regions["longshot_p_lt_0_30"]["gap"] < 0.0 and v_regions["favourite_p_ge_0_60"]["gap"] > 0.0,
        "test_region_direction": t_regions["longshot_p_lt_0_30"]["gap"] < 0.0 and t_regions["favourite_p_ge_0_60"]["gap"] > 0.0,
        "bookmaker_signs_not_contradictory": len(t_books) >= 2 and all(_positive(value["residual_slope"]) for value in t_books.values()),
    }
    supported = all(gates.values())
    report.update({
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "INDEPENDENT_CROSS_LEAGUE_FAVOURITE_LONGSHOT_TRANSPORT",
        "parent_issue": 534,
        "transfer_gate": {"supported": supported, "gates": gates},
        "formal_gate": {"supported": supported, "gates": gates},
        "supported": supported,
        "decision": "SUPPORTED_CROSS_LEAGUE_FAVOURITE_LONGSHOT_PATTERN" if supported else "NO_CROSS_LEAGUE_FAVOURITE_LONGSHOT_CONFIRMATION",
        "interpretation_guard": (
            "The frozen favourite-longshot pattern transferred across Bundesliga and Ligue 1; this supports only a future untouched confirmation design."
            if supported else
            "The frozen favourite-longshot pattern did not clear every Bundesliga/Ligue 1 transport gate. The negative parent #534 decision remains binding."
        ),
    })
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
