"""Frozen Power de-vig transport to Bundesliga and Ligue 1 (Issue #540)."""
from __future__ import annotations

from typing import Any

import devig_method_oos_v1 as parent
from cross_league_bookmaker_source import LEAGUES, download_and_audit

EXPERIMENT_ID = "POWER_DEVIG_CROSS_LEAGUE_TRANSPORT_V1"


def _source() -> tuple[dict[tuple[str, str], bytes], dict[str, Any], list[str]]:
    return download_and_audit(parent.BOOKMAKERS)


def evaluate() -> dict[str, Any]:
    old_order = parent.LEAGUE_ORDER
    old_download = parent._download_and_audit
    old_winner = parent._validation_winner
    try:
        parent.LEAGUE_ORDER = tuple(LEAGUES)
        parent._download_and_audit = _source
        parent._validation_winner = lambda _frame: "power"
        report = parent.evaluate()
    finally:
        parent.LEAGUE_ORDER = old_order
        parent._download_and_audit = old_download
        parent._validation_winner = old_winner

    if report["decision"] == "BLOCKED_BY_SOURCE_GAP":
        report["experiment_id"] = EXPERIMENT_ID
        return report

    validation = report["validation"]["closing"]
    test = report["test"]["closing"]
    # Derive the validation delta from the already persisted paired metrics.
    validation_delta = (
        validation["pooled"]["power"]["log_loss"]
        - validation["pooled"]["multiplicative"]["log_loss"]
    )
    confirmation = report["confirmation"]
    test_leagues = confirmation["stability"]["by_league"]
    test_books = confirmation["stability"]["by_bookmaker"]
    gates = {
        "validation_closing_log_loss_improves": validation_delta < 0.0,
        "test_closing_log_loss_improves": confirmation["closing_deltas_vs_multiplicative"]["log_loss"] < 0.0,
        "test_bootstrap_ci95_upper_below_zero": confirmation["paired_fixture_cluster_bootstrap"]["ci95_high"] < 0.0,
        "test_brier_not_worse": confirmation["closing_deltas_vs_multiplicative"]["brier"] <= 0.0,
        "test_rps_not_worse": confirmation["closing_deltas_vs_multiplicative"]["rps"] <= 0.0,
        "opening_not_worse": confirmation["opening_log_loss_delta_vs_multiplicative"] <= 0.0,
        "both_leagues_improve": len(test_leagues) == 2 and all(value is not None and value < 0.0 for value in test_leagues.values()),
        "all_included_bookmakers_improve": len(test_books) >= 2 and all(value is not None and value < 0.0 for value in test_books.values()),
    }
    supported = all(gates.values())
    report.update({
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "INDEPENDENT_CROSS_LEAGUE_DEVIG_TRANSPORT",
        "parent_issue": 533,
        "validation_closing_log_loss_delta_vs_multiplicative": validation_delta,
        "transfer_gate": {"supported": supported, "gates": gates},
        "supported": supported,
        "decision": "POWER_CROSS_LEAGUE_TRANSPORT_SUPPORTED" if supported else "POWER_CROSS_LEAGUE_TRANSPORT_NOT_SUPPORTED",
        "interpretation_guard": (
            "The frozen Power transform passed every Bundesliga/Ligue 1 transport gate; this supports only a future untouched confirmation study."
            if supported else
            "The frozen Power transform did not pass every independent Bundesliga/Ligue 1 transport gate. The negative parent #533 decision remains binding."
        ),
    })
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
