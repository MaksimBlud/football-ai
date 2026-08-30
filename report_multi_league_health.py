"""Read-only consolidated health report for canonical operational league state.

This module combines existing calibration-coverage and canonical data-quality
reports. It adds no writes, readiness threshold, training, promotion, model
loading, or Structural V2 activation.
"""

from __future__ import annotations

from typing import Callable

import audit_league_canonical_data_quality as data_quality
import report_league_calibration_coverage as coverage


def build_health_report(
    *,
    build_coverage: Callable[[], list[dict]] = coverage.build_coverage_report,
    build_audit: Callable[[], list[dict]] = data_quality.build_audit_report,
) -> list[dict]:
    coverage_rows = {row["league"]: row for row in build_coverage()}
    audit_rows = {row["league"]: row for row in build_audit()}

    if set(coverage_rows) != set(audit_rows):
        missing_audit = sorted(set(coverage_rows) - set(audit_rows))
        missing_coverage = sorted(set(audit_rows) - set(coverage_rows))
        raise ValueError(
            "Health report league mismatch: "
            f"missing_audit={missing_audit}, missing_coverage={missing_coverage}"
        )

    rows: list[dict] = []
    for league in coverage_rows:
        coverage_row = coverage_rows[league]
        audit_row = audit_rows[league]
        rows.append(
            {
                "league": league,
                "ledger_rows": coverage_row["ledger_rows"],
                "finished_result_rows": coverage_row["finished_result_rows"],
                "settled_fixtures": coverage_row["settled_fixtures"],
                "latest_pre_kickoff_fixtures": coverage_row["latest_pre_kickoff_fixtures"],
                "data_stage": coverage_row["data_stage"],
                "duplicate_prediction_rows": audit_row["duplicate_prediction_rows"],
                "duplicate_result_identities": audit_row["duplicate_result_identities"],
                "missing_event_ids": audit_row["missing_event_ids"],
                "unlinked_finished_results": audit_row["unlinked_finished_results"],
                "critical_failures": audit_row["critical_failures"],
            }
        )
    return rows


def main() -> None:
    rows = build_health_report()
    print("CANONICAL MULTI-LEAGUE HEALTH REPORT")
    print("Read-only. No readiness threshold is applied.")
    print()
    for row in rows:
        print(
            f"{row['league']}: "
            f"ledger={row['ledger_rows']}, "
            f"results={row['finished_result_rows']}, "
            f"settled={row['settled_fixtures']}, "
            f"latest_pre_kickoff={row['latest_pre_kickoff_fixtures']}, "
            f"critical={row['critical_failures']}, "
            f"unlinked_results={row['unlinked_finished_results']}, "
            f"stage={row['data_stage']}"
        )
    print()
    print("PASS: READ-ONLY MULTI-LEAGUE HEALTH REPORT COMPLETE")


if __name__ == "__main__":
    main()
