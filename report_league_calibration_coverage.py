"""Read-only canonical data coverage report for operational leagues.

This module reports how much immutable prediction/result state is available to
the shared evaluator. It deliberately does not define a statistical readiness
threshold, calibrate parameters, train models, activate Structural V2, or write
to Supabase.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Callable

import evaluate_league_predictions as evaluator
from league_config import operational_collection_ready_leagues
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG, RPL_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG


RUNTIME_CONFIGS = {
    config.identity.identifier: config
    for config in (
        EPL_RUNTIME_CONFIG,
        LA_LIGA_RUNTIME_CONFIG,
        RPL_RUNTIME_CONFIG,
        SERIE_A_RUNTIME_CONFIG,
        BUNDESLIGA_RUNTIME_CONFIG,
        LIGUE1_RUNTIME_CONFIG,
        EREDIVISIE_RUNTIME_CONFIG,
    )
}


def data_stage(*, ledger_rows: int, settled_fixtures: int) -> str:
    if ledger_rows == 0:
        return "NO_PREDICTIONS"
    if settled_fixtures == 0:
        return "AWAITING_SETTLED_RESULTS"
    return "SETTLED_DATA_AVAILABLE"


def build_coverage_report(
    *,
    evaluate: Callable = evaluator.evaluate_league,
) -> list[dict]:
    rows: list[dict] = []

    for league in operational_collection_ready_leagues():
        league_id = league.identifier
        config = RUNTIME_CONFIGS[league_id]
        report, _settled, latest = evaluate(league_id)

        latest_rows = len(latest)
        latest_fixtures = (
            int(latest["event_id"].nunique())
            if not latest.empty
            else 0
        )

        rows.append(
            {
                "league": league_id,
                "calibration_status": config.structural_v2.calibration_status,
                "structural_alpha": config.structural_v2.structural_alpha,
                "edge_threshold": config.structural_v2.edge_threshold,
                "ledger_rows": int(report.ledger_rows),
                "finished_result_rows": int(report.result_rows),
                "settled_rows": int(report.settled_rows),
                "settled_fixtures": int(report.settled_fixtures),
                "latest_pre_kickoff_rows": latest_rows,
                "latest_pre_kickoff_fixtures": latest_fixtures,
                "data_stage": data_stage(
                    ledger_rows=int(report.ledger_rows),
                    settled_fixtures=int(report.settled_fixtures),
                ),
            }
        )

    return rows


def main() -> None:
    rows = build_coverage_report()

    print("CANONICAL LEAGUE CALIBRATION DATA COVERAGE")
    print("No statistical readiness threshold is applied.")
    print()

    for row in rows:
        print(
            f"{row['league']}: "
            f"calibration={row['calibration_status']}, "
            f"ledger={row['ledger_rows']}, "
            f"results={row['finished_result_rows']}, "
            f"settled_fixtures={row['settled_fixtures']}, "
            f"latest_pre_kickoff={row['latest_pre_kickoff_fixtures']}, "
            f"data_stage={row['data_stage']}"
        )

    print()
    print("PASS: READ-ONLY COVERAGE REPORT COMPLETE")


if __name__ == "__main__":
    main()
