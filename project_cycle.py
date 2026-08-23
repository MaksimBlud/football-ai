"""Safe orchestration commands for football-ai research workflows.

Examples:

    python3 project_cycle.py verify
    python3 project_cycle.py la-liga
    python3 project_cycle.py la-liga --live-snapshot
    python3 project_cycle.py full

Safety guarantees:
- no model training;
- no model promotion;
- no Odds API request without --live-snapshot;
- no Supabase write without --live-snapshot;
- no git staging/commit/push;
- production artifact hashes checked before/after.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent

PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

LA_LIGA_STEPS = (
    (
        "fixture export",
        ["python3", "export_la_liga_upcoming_matches.py"],
    ),
    (
        "market shadow",
        ["python3", "generate_la_liga_market_shadow.py"],
    ),
    (
        "movement classifier",
        ["python3", "classify_la_liga_market_movements.py"],
    ),
    (
        "transition tracker",
        ["python3", "track_la_liga_market_transitions.py"],
    ),
    (
        "temporal behavior",
        ["python3", "analyze_la_liga_temporal_behavior.py"],
    ),
)

TEST_FILES = (
    "tests/test_analyze_la_liga_temporal_behavior.py",
    "tests/test_track_la_liga_market_transitions.py",
    "tests/test_classify_la_liga_market_movements.py",
    "tests/test_la_liga_market_shadow.py",
    "tests/test_la_liga_fixture_exporter.py",
    "tests/test_la_liga_manual_collector.py",
    "tests/test_odds_snapshot_league_runtime.py",
    "tests/test_league_aware_challenger.py",
    "tests/test_generate_upcoming_challenger_shadow.py",
    "tests/test_analyze_challenger_shadow_history.py",
    "tests/test_classify_challenger_temporal_signals.py",
    "tests/test_track_challenger_signal_transitions.py",
    "tests/test_derive_challenger_decision_states.py",
    "tests/test_shadow_automation.py",
    "tests/test_predict_challenger.py",
    "tests/test_artifact_lifecycle.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def production_hashes() -> dict[str, str]:
    result = {}

    for name in PRODUCTION_ARTIFACTS:
        path = ROOT / name

        if path.exists():
            result[name] = sha256(path)

    return result


def run_step(
    label: str,
    command: list[str],
) -> bool:
    print()
    print("=" * 72)
    print(label.upper())
    print("=" * 72)
    print("$", " ".join(command))

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
    )

    print(
        f"{label} rc={completed.returncode}"
    )

    if completed.returncode != 0:
        print(
            f"FAIL: {label}"
        )
        return False

    print(
        f"PASS: {label}"
    )
    return True


def run_tests() -> bool:
    existing = [
        path
        for path in TEST_FILES
        if (ROOT / path).exists()
    ]

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *existing,
    ]

    return run_step(
        "research regression",
        command,
    )


def database_state() -> dict:
    from database import supabase

    response = (
        supabase
        .table("odds_snapshots")
        .select(
            "league,event_id,snapshot_time_utc",
            count="exact",
        )
        .limit(10000)
        .execute()
    )

    frame = pd.DataFrame(
        response.data or []
    )

    result = {
        "rows":
            int(response.count or 0),

        "league_counts":
            {},

        "la_liga_rows":
            0,

        "la_liga_snapshot_times":
            0,

        "la_liga_fixtures":
            0,

        "duplicate_snapshot_rows":
            0,
    }

    if frame.empty:
        return result

    result[
        "league_counts"
    ] = (
        frame["league"]
        .value_counts(
            dropna=False
        )
        .to_dict()
    )

    la_liga = frame[
        frame["league"]
        == "LA_LIGA"
    ].copy()

    result[
        "la_liga_rows"
    ] = len(la_liga)

    if not la_liga.empty:
        result[
            "la_liga_snapshot_times"
        ] = (
            la_liga[
                "snapshot_time_utc"
            ]
            .nunique()
        )

        result[
            "la_liga_fixtures"
        ] = (
            la_liga[
                "event_id"
            ]
            .nunique()
        )

        result[
            "duplicate_snapshot_rows"
        ] = int(
            la_liga.duplicated(
                subset=[
                    "league",
                    "event_id",
                    "snapshot_time_utc",
                ],
                keep=False,
            ).sum()
        )

    return result


def csv_health() -> dict:
    result = {}

    files = {
        "shadow":
            ROOT
            / "experiments"
            / "la_liga_market_shadow.csv",

        "history":
            ROOT
            / "experiments"
            / "la_liga_market_shadow_history.csv",

        "states":
            ROOT
            / "experiments"
            / "la_liga_market_movement_states.csv",

        "transitions":
            ROOT
            / "experiments"
            / "la_liga_market_transitions.csv",
    }

    for key, path in files.items():
        if path.exists():
            try:
                result[key] = pd.read_csv(
                    path
                )
            except Exception as exc:
                result[key] = exc
        else:
            result[key] = None

    return result


def git_status() -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "status",
            "--short",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    return [
        line
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def print_dashboard(
    *,
    hashes_before: dict[str, str],
    hashes_after: dict[str, str],
    db: dict | None,
) -> bool:
    print()
    print("=" * 72)
    print("FOOTBALL-AI HEALTH")
    print("=" * 72)

    artifacts_safe = (
        hashes_before
        == hashes_after
    )

    print(
        "Production hashes:",
        "PASS"
        if artifacts_safe
        else "FAIL",
    )

    print(
        "Production artifacts:",
        len(hashes_after),
    )

    if db is not None:
        print(
            "DB rows:",
            db["rows"],
        )

        print(
            "League counts:",
            db["league_counts"],
        )

        print(
            "La Liga rows:",
            db["la_liga_rows"],
        )

        print(
            "La Liga snapshot times:",
            db[
                "la_liga_snapshot_times"
            ],
        )

        print(
            "La Liga fixtures:",
            db[
                "la_liga_fixtures"
            ],
        )

        print(
            "La Liga DB duplicates:",
            db[
                "duplicate_snapshot_rows"
            ],
        )

    csvs = csv_health()

    history = csvs.get(
        "history"
    )

    if isinstance(
        history,
        pd.DataFrame,
    ):
        print(
            "Market observations:",
            len(history),
        )

        if {
            "league",
            "event_id",
            "snapshot_time_utc",
        }.issubset(
            history.columns
        ):
            observations = (
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
                - len(observations)
            )

            print(
                "Observation duplicates:",
                duplicates,
            )

    states = csvs.get(
        "states"
    )

    if isinstance(
        states,
        pd.DataFrame,
    ):
        print(
            "Movement states:",
            len(states),
        )

        if (
            "movement_state"
            in states.columns
        ):
            print(
                "Latest state counts:",
                states[
                    "movement_state"
                ]
                .value_counts()
                .to_dict(),
            )

    transitions = csvs.get(
        "transitions"
    )

    if isinstance(
        transitions,
        pd.DataFrame,
    ):
        print(
            "Transition rows:",
            len(transitions),
        )

        if (
            "transition"
            in transitions.columns
        ):
            print(
                "Transition types:",
                transitions[
                    "transition"
                ]
                .value_counts()
                .to_dict(),
            )

    print()
    print("GIT STATUS:")

    status = git_status()

    if not status:
        print("clean")
    else:
        for line in status:
            print(line)

    protected_staged = [
        line
        for line in status
        if any(
            artifact
            in line
            for artifact
            in PRODUCTION_ARTIFACTS
        )
        and not line.startswith(
            " M "
        )
    ]

    if protected_staged:
        print(
            "WARNING: protected artifact "
            "may be staged."
        )

    return (
        artifacts_safe
        and (
            db is None
            or db[
                "duplicate_snapshot_rows"
            ]
            == 0
        )
    )


def run_la_liga(
    *,
    live_snapshot: bool,
    tests: bool,
) -> bool:
    hashes_before = (
        production_hashes()
    )

    print()
    print(
        "Production artifacts before:",
        len(hashes_before),
    )

    if live_snapshot:
        ok = run_step(
            "LIVE La Liga snapshot",
            [
                sys.executable,
                "save_la_liga_odds_snapshot.py",
            ],
        )

        if not ok:
            print(
                "STOP: live collection failed. "
                "Downstream steps skipped."
            )
            return False
    else:
        print()
        print(
            "LIVE SNAPSHOT: SKIPPED "
            "(use --live-snapshot to enable)"
        )

    for label, command in (
        LA_LIGA_STEPS
    ):
        if not run_step(
            label,
            command,
        ):
            print(
                "STOP: downstream pipeline "
                "skipped after failure."
            )
            return False

    if tests:
        if not run_tests():
            return False

    hashes_after = (
        production_hashes()
    )

    try:
        db = database_state()
    except Exception as exc:
        print()
        print(
            "DB HEALTH CHECK FAILED:",
            type(exc).__name__,
            exc,
        )
        db = None

    return print_dashboard(
        hashes_before=hashes_before,
        hashes_after=hashes_after,
        db=db,
    )


def run_verify(
    *,
    tests: bool,
) -> bool:
    hashes_before = (
        production_hashes()
    )

    if tests:
        if not run_tests():
            return False

    hashes_after = (
        production_hashes()
    )

    try:
        db = database_state()
    except Exception as exc:
        print(
            "DB health unavailable:",
            type(exc).__name__,
            exc,
        )
        db = None

    return print_dashboard(
        hashes_before=hashes_before,
        hashes_after=hashes_after,
        db=db,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safe football-ai workflow runner"
        )
    )

    parser.add_argument(
        "mode",
        choices=[
            "verify",
            "la-liga",
            "full",
            "release-audit",
        ],
    )

    parser.add_argument(
        "--live-snapshot",
        action="store_true",
        help=(
            "Explicitly permit one live "
            "La Liga Odds API snapshot/write."
        ),
    )

    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help=(
            "Skip regression tests."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    tests = not args.skip_tests

    if (
        args.live_snapshot
        and args.mode in {
            "verify",
            "release-audit",
        }
    ):
        print(
            "ERROR: --live-snapshot is not "
            "valid with this mode."
        )
        return 2

    if args.mode == "verify":
        ok = run_verify(
            tests=tests,
        )

    elif args.mode == "release-audit":
        ok = run_step(
            "V1 release audit",
            [
                sys.executable,
                "release_audit.py",
            ],
        )

    elif args.mode in {
        "la-liga",
        "full",
    }:
        # 'full' currently means the complete
        # safe research cycle. It intentionally
        # does not run training or promotion.
        ok = run_la_liga(
            live_snapshot=(
                args.live_snapshot
            ),
            tests=tests,
        )

    else:
        raise AssertionError(
            args.mode
        )

    print()
    print(
        "FINAL RESULT:",
        "PASS"
        if ok
        else "FAIL",
    )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )


def _file_present(path: str) -> bool:
    return (ROOT / path).exists()


def _la_liga_collection_status() -> tuple[bool, str]:
    try:
        from league_config import LA_LIGA

        enabled = bool(
            getattr(
                LA_LIGA,
                "collection_enabled",
                False,
            )
        )

        ready = bool(
            getattr(
                LA_LIGA,
                "collection_ready",
                False,
            )
        )

        if enabled and ready:
            return True, "READY"

        return False, "MANUAL_ONLY"

    except Exception:
        return False, "UNKNOWN"


def _la_liga_prediction_status() -> tuple[bool, str]:
    # V1 requires an explicit La Liga prediction path,
    # not reuse of the EPL production model by accident.
    candidates = (
        "predict_la_liga.py",
        "predict_la_liga_round.py",
        "la_liga_predictor.py",
    )

    present = any(
        _file_present(path)
        for path in candidates
    )

    return (
        present,
        "READY"
        if present
        else "NOT_READY",
    )


def v1_readiness() -> dict:
    """Return release-oriented V1 readiness state."""

    db = database_state()
    csvs = csv_health()

    history = csvs.get(
        "history"
    )

    transitions = csvs.get(
        "transitions"
    )

    collection_ready, collection_status = (
        _la_liga_collection_status()
    )

    prediction_ready, prediction_status = (
        _la_liga_prediction_status()
    )

    checks = {
        "production_artifacts_present":
            len(
                production_hashes()
            )
            == len(
                PRODUCTION_ARTIFACTS
            ),

        "league_aware_database":
            db[
                "duplicate_snapshot_rows"
            ]
            == 0,

        "epl_data_present":
            db[
                "league_counts"
            ].get(
                "EPL",
                0,
            )
            > 0,

        "epl_runtime_present":
            _file_present(
                "predict_upcoming_round.py"
            )
            and _file_present(
                "generate_upcoming_challenger_shadow.py"
            ),

        "challenger_runtime_present":
            _file_present(
                "predict_challenger.py"
            )
            and _file_present(
                "analyze_challenger_shadow_history.py"
            ),

        "la_liga_data_present":
            db[
                "la_liga_rows"
            ]
            > 0,

        "la_liga_three_snapshots":
            db[
                "la_liga_snapshot_times"
            ]
            >= 3,

        "la_liga_observation_history":
            isinstance(
                history,
                pd.DataFrame,
            )
            and len(history) > 0,

        "la_liga_transition_history":
            isinstance(
                transitions,
                pd.DataFrame,
            )
            and len(transitions) > 0,

        "la_liga_automated_collection":
            collection_ready,

        "la_liga_prediction_runtime":
            prediction_ready,

        "project_orchestrator":
            _file_present(
                "project_cycle.py"
            ),

        "release_audit_script":
            _file_present(
                "release_audit.py"
            ),
    }

    passed = sum(
        bool(value)
        for value in checks.values()
    )

    total = len(checks)

    percent = round(
        100 * passed / total
    )

    blockers = [
        key
        for key, value
        in checks.items()
        if not value
    ]

    return {
        "checks":
            checks,

        "passed":
            passed,

        "total":
            total,

        "percent":
            percent,

        "blockers":
            blockers,

        "details": {
            "la_liga_collection":
                collection_status,

            "la_liga_prediction":
                prediction_status,
        },
    }


def print_v1_readiness() -> None:
    readiness = v1_readiness()

    print()
    print("=" * 72)
    print("V1 RELEASE READINESS")
    print("=" * 72)

    for key, value in (
        readiness[
            "checks"
        ].items()
    ):
        print(
            f"{key:36}",
            "PASS"
            if value
            else "BLOCKED",
        )

    print()
    print("DETAILS:")

    for key, value in (
        readiness[
            "details"
        ].items()
    ):
        print(
            f"{key:36}",
            value,
        )

    print()
    print(
        "READINESS:",
        f'{readiness["percent"]}%',
    )

    print(
        "PASSED:",
        f'{readiness["passed"]}/{readiness["total"]}',
    )

    print(
        "BLOCKERS:",
        readiness["blockers"]
        or "none",
    )
