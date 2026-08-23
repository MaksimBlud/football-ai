"""Read-only Football AI V1 release audit.

This audit:
- performs no Odds API request;
- performs no Supabase write;
- performs no training or model promotion;
- does not stage, commit, reset, or modify git state;
- checks production artifacts, database health, research history,
  runtime files, and git safety.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

import project_cycle


ROOT = Path(__file__).resolve().parent

DEFAULT_REPORT = Path(
    "experiments/release_audit.json"
)


@dataclass
class AuditCheck:
    name: str
    passed: bool
    detail: str
    severity: str = "BLOCKER"


def git_status_lines() -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "status",
            "--short",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    return [
        line
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def staged_paths() -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    return [
        line
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def production_artifact_checks() -> list[AuditCheck]:
    hashes = project_cycle.production_hashes()

    expected = set(
        project_cycle.PRODUCTION_ARTIFACTS
    )

    present = set(
        hashes
    )

    missing = sorted(
        expected - present
    )

    checks = [
        AuditCheck(
            name="production_artifacts_present",
            passed=not missing,
            detail=(
                f"{len(present)}/{len(expected)} present"
                if not missing
                else f"missing={missing}"
            ),
        )
    ]

    staged = staged_paths()

    staged_pkl = [
        path
        for path in staged
        if path.endswith(".pkl")
    ]

    checks.append(
        AuditCheck(
            name="no_production_artifact_staged",
            passed=not staged_pkl,
            detail=(
                "no .pkl staged"
                if not staged_pkl
                else f"staged={staged_pkl}"
            ),
        )
    )

    return checks


def database_checks() -> list[AuditCheck]:
    try:
        state = (
            project_cycle.database_state()
        )

    except Exception as exc:
        return [
            AuditCheck(
                name="database_readable",
                passed=False,
                detail=(
                    f"{type(exc).__name__}: {exc}"
                ),
            )
        ]

    league_counts = state.get(
        "league_counts",
        {},
    )

    return [
        AuditCheck(
            name="database_readable",
            passed=True,
            detail=(
                f"rows={state['rows']}"
            ),
        ),
        AuditCheck(
            name="league_aware_database_unique",
            passed=(
                state[
                    "duplicate_snapshot_rows"
                ]
                == 0
            ),
            detail=(
                "la_liga_duplicate_rows="
                f"{state['duplicate_snapshot_rows']}"
            ),
        ),
        AuditCheck(
            name="epl_snapshots_present",
            passed=(
                league_counts.get(
                    "EPL",
                    0,
                )
                > 0
            ),
            detail=(
                f"EPL={league_counts.get('EPL', 0)}"
            ),
        ),
        AuditCheck(
            name="la_liga_snapshots_present",
            passed=(
                state[
                    "la_liga_rows"
                ]
                > 0
            ),
            detail=(
                "LA_LIGA="
                f"{state['la_liga_rows']}"
            ),
        ),
        AuditCheck(
            name="la_liga_temporal_depth",
            passed=(
                state[
                    "la_liga_snapshot_times"
                ]
                >= 3
            ),
            detail=(
                "snapshot_times="
                f"{state['la_liga_snapshot_times']}"
            ),
        ),
    ]


def research_history_checks() -> list[AuditCheck]:
    csvs = (
        project_cycle.csv_health()
    )

    checks = []

    history = csvs.get(
        "history"
    )

    if not isinstance(
        history,
        pd.DataFrame,
    ):
        checks.append(
            AuditCheck(
                name="la_liga_market_history",
                passed=False,
                detail="history unavailable",
            )
        )

    else:
        required = {
            "league",
            "event_id",
            "snapshot_time_utc",
        }

        schema_ok = required.issubset(
            history.columns
        )

        checks.append(
            AuditCheck(
                name="la_liga_market_history_schema",
                passed=schema_ok,
                detail=(
                    f"rows={len(history)}"
                ),
            )
        )

        if schema_ok:
            unique = (
                history[
                    [
                        "league",
                        "event_id",
                        "snapshot_time_utc",
                    ]
                ]
                .drop_duplicates()
            )

            duplicates = (
                len(history)
                - len(unique)
            )

            checks.append(
                AuditCheck(
                    name="la_liga_market_history_unique",
                    passed=(
                        duplicates == 0
                    ),
                    detail=(
                        f"rows={len(history)}, "
                        f"unique={len(unique)}, "
                        f"duplicates={duplicates}"
                    ),
                )
            )

    transitions = csvs.get(
        "transitions"
    )

    checks.append(
        AuditCheck(
            name="la_liga_transition_history",
            passed=(
                isinstance(
                    transitions,
                    pd.DataFrame,
                )
                and len(
                    transitions
                )
                > 0
            ),
            detail=(
                f"rows={len(transitions)}"
                if isinstance(
                    transitions,
                    pd.DataFrame,
                )
                else "unavailable"
            ),
        )
    )

    behavior_path = (
        ROOT
        / "experiments"
        / "la_liga_temporal_behavior.csv"
    )

    checks.append(
        AuditCheck(
            name="la_liga_temporal_behavior",
            passed=behavior_path.exists(),
            detail=str(
                behavior_path.relative_to(
                    ROOT
                )
            ),
        )
    )

    return checks


def runtime_checks() -> list[AuditCheck]:
    required = {
        "project_orchestrator":
            "project_cycle.py",

        "epl_prediction_runtime":
            "predict_upcoming_round.py",

        "challenger_runtime":
            "predict_challenger.py",

        "challenger_shadow_runtime":
            "generate_upcoming_challenger_shadow.py",

        "la_liga_collector":
            "save_la_liga_odds_snapshot.py",

        "la_liga_fixture_export":
            "export_la_liga_upcoming_matches.py",

        "la_liga_market_shadow":
            "generate_la_liga_market_shadow.py",

        "la_liga_movement_classifier":
            "classify_la_liga_market_movements.py",

        "la_liga_transition_tracker":
            "track_la_liga_market_transitions.py",

        "la_liga_temporal_behavior":
            "analyze_la_liga_temporal_behavior.py",
    }

    return [
        AuditCheck(
            name=name,
            passed=(
                ROOT / path
            ).exists(),
            detail=path,
        )
        for name, path
        in required.items()
    ]


def known_release_blockers() -> list[AuditCheck]:
    collection_ready, collection_status = (
        project_cycle
        ._la_liga_collection_status()
    )

    prediction_ready, prediction_status = (
        project_cycle
        ._la_liga_prediction_status()
    )

    return [
        AuditCheck(
            name="la_liga_automated_collection",
            passed=collection_ready,
            detail=collection_status,
            severity="V1_BLOCKER",
        ),
        AuditCheck(
            name="la_liga_prediction_runtime",
            passed=prediction_ready,
            detail=prediction_status,
            severity="V1_BLOCKER",
        ),
    ]


def working_tree_warnings() -> list[AuditCheck]:
    status = git_status_lines()

    modified_production = [
        line
        for line in status
        if any(
            artifact in line
            for artifact
            in project_cycle.PRODUCTION_ARTIFACTS
        )
    ]

    return [
        AuditCheck(
            name="production_worktree_clean",
            passed=(
                not modified_production
            ),
            detail=(
                "clean"
                if not modified_production
                else "; ".join(
                    modified_production
                )
            ),
            severity="WARNING",
        )
    ]


def build_audit() -> dict:
    checks = [
        *production_artifact_checks(),
        *database_checks(),
        *research_history_checks(),
        *runtime_checks(),
        *known_release_blockers(),
        *working_tree_warnings(),
    ]

    hard_failures = [
        check
        for check in checks
        if (
            not check.passed
            and check.severity
            == "BLOCKER"
        )
    ]

    v1_blockers = [
        check
        for check in checks
        if (
            not check.passed
            and check.severity
            == "V1_BLOCKER"
        )
    ]

    warnings = [
        check
        for check in checks
        if (
            not check.passed
            and check.severity
            == "WARNING"
        )
    ]

    return {
        "checks": [
            asdict(check)
            for check in checks
        ],
        "hard_failures": [
            check.name
            for check in hard_failures
        ],
        "v1_blockers": [
            check.name
            for check in v1_blockers
        ],
        "warnings": [
            check.name
            for check in warnings
        ],
        "audit_passed": (
            len(
                hard_failures
            )
            == 0
        ),
        "release_ready": (
            len(
                hard_failures
            )
            == 0
            and len(
                v1_blockers
            )
            == 0
        ),
    }


def write_report(
    audit: dict,
    path: Path,
) -> None:
    experiments = (
        ROOT / "experiments"
    ).resolve()

    resolved = (
        ROOT / path
    ).resolve()

    if experiments not in resolved.parents:
        raise ValueError(
            "Audit report must remain under experiments/"
        )

    resolved.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    resolved.write_text(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def print_audit(
    audit: dict,
) -> None:
    print()
    print("=" * 72)
    print("FOOTBALL AI V1 RELEASE AUDIT")
    print("=" * 72)

    for check in audit[
        "checks"
    ]:
        if check["passed"]:
            status = "PASS"
        elif (
            check["severity"]
            == "WARNING"
        ):
            status = "WARN"
        else:
            status = "BLOCKED"

        print(
            f'{check["name"]:38} '
            f'{status:8} '
            f'{check["detail"]}'
        )

    print()
    print(
        "AUDIT:",
        "PASS"
        if audit[
            "audit_passed"
        ]
        else "FAIL",
    )

    print(
        "RELEASE READY:",
        "YES"
        if audit[
            "release_ready"
        ]
        else "NO",
    )

    print(
        "V1 BLOCKERS:",
        audit[
            "v1_blockers"
        ]
        or "none",
    )

    print(
        "WARNINGS:",
        audit[
            "warnings"
        ]
        or "none",
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write-report",
        action="store_true",
        help=(
            "Write JSON report beneath experiments/."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT,
    )

    args = parser.parse_args()

    before = (
        project_cycle.production_hashes()
    )

    audit = build_audit()

    after = (
        project_cycle.production_hashes()
    )

    if before != after:
        audit[
            "audit_passed"
        ] = False

        audit[
            "release_ready"
        ] = False

        audit[
            "hard_failures"
        ].append(
            "production_hash_changed_during_audit"
        )

    print_audit(
        audit
    )

    if args.write_report:
        write_report(
            audit,
            args.output,
        )

        print(
            "\nreport:",
            args.output,
        )

    # Known V1 blockers do not make the audit itself fail.
    # The audit command fails only for integrity/safety failures.
    return (
        0
        if audit[
            "audit_passed"
        ]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
