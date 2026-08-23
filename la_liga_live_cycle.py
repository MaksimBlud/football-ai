"""One-command La Liga Structural V2 live operating cycle.

Research-only.

Cycle:
1. optional odds collection
2. fixture export / reuse
3. market shadow
4. Structural V2 shadow
5. append-only V2 history
6. result-source check
7. live evaluation
8. compact structured summary

No training.
No promotion.
No production artifact modification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

import export_la_liga_upcoming_matches as fixtures
import generate_la_liga_market_shadow as market_shadow
import la_liga_structural_v2_shadow as structural_shadow
import la_liga_structural_v2_shadow_history as shadow_history
import evaluate_la_liga_structural_v2_live as live_eval


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

UPCOMING_PATH = (
    ROOT
    / "data"
    / "upcoming_matches_la_liga.csv"
)

MARKET_PATH = (
    ROOT
    / "experiments"
    / "la_liga_market_shadow.csv"
)

STRUCTURAL_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_shadow.csv"
)

HISTORY_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_shadow_history.csv"
)

RESULTS_PATH = (
    ROOT
    / "data"
    / "la_liga_2026_2027_results.csv"
)

EVAL_REPORT_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_live_evaluation"
    / "la_liga_report.json"
)


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def production_state() -> dict:
    return {
        name: sha256(
            ROOT / name
        )
        for name in PRODUCTION_ARTIFACTS
    }


def step(
    status: str,
    detail: str = "",
) -> dict:
    return {
        "status": status,
        "detail": detail,
    }


def call_legacy_main(
    main_func,
) -> None:
    """Run a legacy CLI main without leaking parent argv."""

    original_argv = sys.argv[:]

    try:
        sys.argv = [
            getattr(
                main_func,
                "__module__",
                "league_step",
            )
        ]

        try:
            result = main_func()
        except SystemExit as exc:
            code = exc.code

            if code not in (
                None,
                0,
            ):
                raise RuntimeError(
                    "legacy main exited "
                    f"with code {code}"
                ) from exc

            return

        if (
            isinstance(
                result,
                int,
            )
            and result != 0
        ):
            raise RuntimeError(
                "legacy main returned "
                f"code {result}"
            )

    finally:
        sys.argv = original_argv


def run_cycle(
    *,
    skip_collection: bool = False,
) -> dict:
    before = production_state()

    result = {
        "status": "PASS",
        "steps": {},
        "metrics": {},
        "production_unchanged":
            False,
    }

    # --------------------------------------------------
    # 1. collection
    # --------------------------------------------------
    if skip_collection:
        result["steps"][
            "collection"
        ] = step(
            "SKIP",
            "existing odds data reused",
        )
    else:
        try:
            import la_liga_collection_runner as collector

            call_legacy_main(collector.main)

            result["steps"][
                "collection"
            ] = step(
                "PASS"
            )

        except Exception as exc:
            result["steps"][
                "collection"
            ] = step(
                "FAIL",
                str(exc),
            )

            result["status"] = "FAIL"

            after = production_state()

            result[
                "production_unchanged"
            ] = (
                before == after
            )

            return result

    # --------------------------------------------------
    # 2. fixtures
    # --------------------------------------------------
    try:
        if (
            skip_collection
            and UPCOMING_PATH.exists()
        ):
            result["steps"][
                "fixtures"
            ] = step(
                "PASS",
                "existing fixture export reused",
            )

        else:
            call_legacy_main(fixtures.main)

            result["steps"][
                "fixtures"
            ] = step(
                "PASS"
            )

    except Exception as exc:
        result["steps"][
            "fixtures"
        ] = step(
            "FAIL",
            str(exc),
        )

        result["status"] = "FAIL"

        after = production_state()

        result[
            "production_unchanged"
        ] = (
            before == after
        )

        return result

    # --------------------------------------------------
    # 3. market shadow
    # --------------------------------------------------
    try:
        call_legacy_main(market_shadow.main)

        result["steps"][
            "market_shadow"
        ] = step(
            "PASS"
        )

    except Exception as exc:
        result["steps"][
            "market_shadow"
        ] = step(
            "FAIL",
            str(exc),
        )

        result["status"] = "FAIL"

        after = production_state()

        result[
            "production_unchanged"
        ] = (
            before == after
        )

        return result

    # --------------------------------------------------
    # 4. Structural V2 shadow
    # --------------------------------------------------
    try:
        call_legacy_main(structural_shadow.main)

        structural = pd.read_csv(
            STRUCTURAL_PATH
        )

        argmax_changes = int(
            (
                structural[
                    "market_argmax"
                ]
                != structural[
                    "shadow_argmax"
                ]
            ).sum()
        )

        if argmax_changes:
            raise RuntimeError(
                "Structural V2 changed market argmax: "
                f"{argmax_changes}"
            )

        result["steps"][
            "structural_v2_shadow"
        ] = step(
            "PASS"
        )

    except Exception as exc:
        result["steps"][
            "structural_v2_shadow"
        ] = step(
            "FAIL",
            str(exc),
        )

        result["status"] = "FAIL"

        after = production_state()

        result[
            "production_unchanged"
        ] = (
            before == after
        )

        return result

    # --------------------------------------------------
    # 5. append-only live history
    # --------------------------------------------------
    try:
        call_legacy_main(shadow_history.main)

        result["steps"][
            "live_history"
        ] = step(
            "PASS"
        )

    except Exception as exc:
        result["steps"][
            "live_history"
        ] = step(
            "FAIL",
            str(exc),
        )

        result["status"] = "FAIL"

        after = production_state()

        result[
            "production_unchanged"
        ] = (
            before == after
        )

        return result

    # --------------------------------------------------
    # 6. results
    # --------------------------------------------------
    if (
        not RESULTS_PATH.exists()
        or RESULTS_PATH.stat().st_size
        == 0
    ):
        result["steps"][
            "results"
        ] = step(
            "WAIT",
            "WAITING_FOR_RESULTS_SOURCE",
        )

    else:
        try:
            raw_results = pd.read_csv(
                RESULTS_PATH
            )

            normalized = (
                structural_shadow
                .normalize_finished_matches(
                    raw_results
                )
            )

            result["steps"][
                "results"
            ] = step(
                "PASS",
                f"rows={len(normalized)}",
            )

        except Exception as exc:
            result["steps"][
                "results"
            ] = step(
                "FAIL",
                str(exc),
            )

            result["status"] = "FAIL"

            after = production_state()

            result[
                "production_unchanged"
            ] = (
                before == after
            )

            return result

    # --------------------------------------------------
    # 7. evaluation
    # --------------------------------------------------
    try:
        call_legacy_main(live_eval.main)

        if EVAL_REPORT_PATH.exists():
            report = json.loads(
                EVAL_REPORT_PATH.read_text(
                    encoding="utf-8"
                )
            )
        else:
            report = {
                "status":
                    "NO_SETTLED_MATCHES",
                "settled_matches":
                    0,
            }

        if (
            report.get(
                "status"
            )
            == "NO_SETTLED_MATCHES"
        ):
            result["steps"][
                "evaluation"
            ] = step(
                "WAIT",
                "NO_SETTLED_MATCHES",
            )

        else:
            result["steps"][
                "evaluation"
            ] = step(
                "PASS"
            )

            result["metrics"][
                "evaluation"
            ] = report

    except Exception as exc:
        result["steps"][
            "evaluation"
        ] = step(
            "FAIL",
            str(exc),
        )

        result["status"] = "FAIL"

        after = production_state()

        result[
            "production_unchanged"
        ] = (
            before == after
        )

        return result

    # --------------------------------------------------
    # metrics
    # --------------------------------------------------
    if UPCOMING_PATH.exists():
        upcoming = pd.read_csv(
            UPCOMING_PATH
        )

        result["metrics"][
            "upcoming_fixtures"
        ] = len(upcoming)

    if MARKET_PATH.exists():
        market = pd.read_csv(
            MARKET_PATH
        )

        result["metrics"][
            "market_observations"
        ] = len(market)

    if STRUCTURAL_PATH.exists():
        structural = pd.read_csv(
            STRUCTURAL_PATH
        )

        result["metrics"][
            "structural_ready"
        ] = int(
            structural[
                "structural_ready"
            ]
            .astype(bool)
            .sum()
        )

        result["metrics"][
            "corrections_enabled"
        ] = int(
            structural[
                "correction_enabled"
            ]
            .astype(bool)
            .sum()
        )

    if HISTORY_PATH.exists():
        history = pd.read_csv(
            HISTORY_PATH
        )

        result["metrics"][
            "v2_history_observations"
        ] = len(history)

        result["metrics"][
            "canonical_live_fixtures"
        ] = history[
            "event_id"
        ].nunique()

    after = production_state()

    result[
        "production_unchanged"
    ] = (
        before == after
    )

    if not result[
        "production_unchanged"
    ]:
        result["status"] = "FAIL"

        result["steps"][
            "production_safety"
        ] = step(
            "FAIL",
            "production artifact changed",
        )

    return result


def print_summary(
    result: dict,
) -> None:
    print()
    print("=" * 72)
    print(
        "LA LIGA STRUCTURAL V2 LIVE CYCLE"
    )
    print("=" * 72)

    ordered = (
        "collection",
        "fixtures",
        "market_shadow",
        "structural_v2_shadow",
        "live_history",
        "results",
        "evaluation",
    )

    for name in ordered:
        entry = (
            result[
                "steps"
            ].get(
                name
            )
        )

        if not entry:
            continue

        print(
            f"{name:28}"
            f"{entry['status']}"
        )

        if entry.get(
            "detail"
        ):
            print(
                " "
                + entry[
                    "detail"
                ]
            )

    metrics = result[
        "metrics"
    ]

    print()

    labels = {
        "upcoming_fixtures":
            "Upcoming fixtures",
        "market_observations":
            "Market observations",
        "structural_ready":
            "Structural-ready",
        "corrections_enabled":
            "Corrections enabled",
        "v2_history_observations":
            "V2 history observations",
        "canonical_live_fixtures":
            "Canonical live fixtures",
    }

    for key, label in (
        labels.items()
    ):
        if key in metrics:
            print(
                f"{label}: "
                f"{metrics[key]}"
            )

    evaluation = (
        metrics.get(
            "evaluation"
        )
    )

    if (
        evaluation
        and evaluation.get(
            "status"
        )
        == "EVALUATED"
    ):
        all_matches = (
            evaluation[
                "all_matches"
            ]
        )

        market = (
            all_matches[
                "market"
            ]
        )

        v2_metrics = (
            all_matches[
                "v2"
            ]
        )

        print()
        print(
            "Settled matches:",
            evaluation[
                "settled_matches"
            ],
        )

        print(
            "Corrected settled matches:",
            evaluation[
                "corrected_matches"
            ],
        )

        print()
        print(
            "Market LogLoss:",
            market[
                "logloss"
            ],
        )

        print(
            "V2 LogLoss:",
            v2_metrics[
                "logloss"
            ],
        )

        print(
            "Delta LogLoss:",
            all_matches[
                "logloss_gap"
            ],
        )

        print()
        print(
            "Market Brier:",
            market[
                "brier"
            ],
        )

        print(
            "V2 Brier:",
            v2_metrics[
                "brier"
            ],
        )

        print(
            "Delta Brier:",
            all_matches[
                "brier_gap"
            ],
        )

    print()
    print(
        "Production unchanged:",
        (
            "PASS"
            if result[
                "production_unchanged"
            ]
            else "FAIL"
        ),
    )

    print(
        "Cycle status:",
        result[
            "status"
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--skip-collection",
        action="store_true",
    )

    args = parser.parse_args()

    result = run_cycle(
        skip_collection=(
            args.skip_collection
        )
    )

    print_summary(
        result
    )

    return (
        0
        if result[
            "status"
        ]
        != "FAIL"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
