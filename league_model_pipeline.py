"""League model research pipeline orchestrator.

Automates the repeatable research workflow:

historical data
-> normalization
-> temporal features
-> Elo
-> expanding-window OOS
-> diagnostics
-> quality gate
-> report

Safety:
- research only;
- no Supabase writes;
- no production promotion;
- no git mutation;
- no production .pkl modification;
- failed market gate never creates a candidate model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


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

REPORT_DIR = ROOT / "experiments" / "league_model_pipeline"


LEAGUES = {
    "LA_LIGA": {
        "steps": (
            (
                "historical_data",
                "build_la_liga_historical_dataset.py",
            ),
            (
                "normalization",
                "normalize_la_liga_history.py",
            ),
            (
                "temporal_features",
                "build_la_liga_temporal_features.py",
            ),
            (
                "elo",
                "add_la_liga_elo_features.py",
            ),
            (
                "oos",
                "evaluate_la_liga_oos_candidate.py",
            ),
        ),
        "metrics": (
            ROOT
            / "experiments"
            / "la_liga_oos_candidate_metrics.json"
        ),
        "predictions": (
            ROOT
            / "experiments"
            / "la_liga_oos_candidate_predictions.csv"
        ),
    },
}


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


def production_state() -> dict[str, str | None]:
    return {
        artifact: sha256(
            ROOT / artifact
        )
        for artifact in PRODUCTION_ARTIFACTS
    }


def run_step(
    label: str,
    script: str,
) -> dict:
    command = [
        sys.executable,
        script,
    ]

    print()
    print("=" * 72)
    print(label.upper())
    print("=" * 72)

    print(
        "$",
        " ".join(command),
    )

    started = datetime.now(
        timezone.utc
    )

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
    )

    finished = datetime.now(
        timezone.utc
    )

    result = {
        "label": label,
        "script": script,
        "returncode": completed.returncode,
        "passed": (
            completed.returncode
            == 0
        ),
        "started_at_utc":
            started.isoformat(),
        "finished_at_utc":
            finished.isoformat(),
    }

    print(
        f"{label} rc={completed.returncode}"
    )

    return result


def load_metrics(
    path: Path,
) -> dict:
    if not path.exists():
        raise RuntimeError(
            f"Metrics missing: {path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def evaluate_quality(
    metrics: dict,
) -> dict:
    ai_accuracy = float(
        metrics["ai_accuracy"]
    )

    market_accuracy = float(
        metrics["market_accuracy"]
    )

    home_accuracy = float(
        metrics["home_accuracy"]
    )

    ai_logloss = float(
        metrics["ai_logloss"]
    )

    market_logloss = float(
        metrics["market_logloss"]
    )

    ai_brier = float(
        metrics["ai_brier"]
    )

    market_brier = float(
        metrics["market_brier"]
    )

    beats_home = (
        ai_accuracy
        > home_accuracy
    )

    beats_market_accuracy = (
        ai_accuracy
        > market_accuracy
    )

    beats_market_logloss = (
        ai_logloss
        < market_logloss
    )

    beats_market_brier = (
        ai_brier
        < market_brier
    )

    # Promotion eligibility is deliberately strict.
    # Research success does NOT imply promotion.
    promotion_eligible = all([
        beats_market_accuracy,
        beats_market_logloss,
        beats_market_brier,
    ])

    return {
        "ai_beats_home_baseline":
            beats_home,

        "ai_beats_market_accuracy":
            beats_market_accuracy,

        "ai_beats_market_logloss":
            beats_market_logloss,

        "ai_beats_market_brier":
            beats_market_brier,

        "promotion_eligible":
            promotion_eligible,

        "accuracy_gap_vs_market":
            ai_accuracy
            - market_accuracy,

        "logloss_gap_vs_market":
            ai_logloss
            - market_logloss,

        "brier_gap_vs_market":
            ai_brier
            - market_brier,
    }


def write_report(
    league: str,
    report: dict,
) -> Path:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        REPORT_DIR
        / f"{league.lower()}_latest.json"
    )

    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return path


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        required=True,
        choices=sorted(
            LEAGUES
        ),
    )

    parser.add_argument(
        "--from-step",
        choices=(
            "historical_data",
            "normalization",
            "temporal_features",
            "elo",
            "oos",
        ),
        default="historical_data",
        help=(
            "Resume pipeline from a specific "
            "validated step."
        ),
    )

    parser.add_argument(
        "--skip-historical-download",
        action="store_true",
        help=(
            "Reuse existing historical source "
            "instead of running download step."
        ),
    )

    args = parser.parse_args()

    league = args.league
    config = LEAGUES[league]

    before = production_state()

    started_at = datetime.now(
        timezone.utc
    )

    print("=" * 72)
    print("LEAGUE MODEL RESEARCH PIPELINE")
    print("=" * 72)

    print(
        "league:",
        league,
    )

    print(
        "from step:",
        args.from_step,
    )

    print(
        "production promotion:",
        False,
    )

    print(
        "candidate .pkl creation:",
        False,
    )

    print()
    print("PRODUCTION HASHES BEFORE:")

    for artifact, digest in (
        before.items()
    ):
        print(
            artifact,
            digest or "MISSING",
        )

    step_names = [
        label
        for label, _
        in config["steps"]
    ]

    start_index = (
        step_names.index(
            args.from_step
        )
    )

    results = []

    for index, (
        label,
        script,
    ) in enumerate(
        config["steps"]
    ):
        if index < start_index:
            continue

        if (
            label
            == "historical_data"
            and args.skip_historical_download
        ):
            print()
            print(
                "SKIP historical_data: "
                "existing local dataset requested"
            )

            results.append({
                "label":
                    label,
                "script":
                    script,
                "returncode":
                    0,
                "passed":
                    True,
                "skipped":
                    True,
            })

            continue

        result = run_step(
            label,
            script,
        )

        results.append(
            result
        )

        if not result["passed"]:
            after = production_state()

            report = {
                "league":
                    league,

                "status":
                    "PIPELINE_FAILED",

                "failed_step":
                    label,

                "steps":
                    results,

                "production_before":
                    before,

                "production_after":
                    after,

                "production_unchanged":
                    before == after,
            }

            report_path = write_report(
                league,
                report,
            )

            print()
            print(
                "FAIL:",
                label,
            )

            print(
                "report:",
                report_path,
            )

            return 1

    metrics = load_metrics(
        config["metrics"]
    )

    quality = evaluate_quality(
        metrics
    )

    after = production_state()

    production_unchanged = (
        before == after
    )

    if not production_unchanged:
        status = (
            "PRODUCTION_SAFETY_FAILURE"
        )

    elif quality[
        "promotion_eligible"
    ]:
        status = (
            "RESEARCH_CANDIDATE_PASSED"
        )

    else:
        status = (
            "RESEARCH_CANDIDATE_REJECTED"
        )

    report = {
        "league":
            league,

        "pipeline_version":
            1,

        "started_at_utc":
            started_at.isoformat(),

        "finished_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "status":
            status,

        "steps":
            results,

        "metrics":
            metrics,

        "quality_gate":
            quality,

        "production_before":
            before,

        "production_after":
            after,

        "production_unchanged":
            production_unchanged,

        "promotion_performed":
            False,

        "candidate_model_saved":
            False,
    }

    report_path = write_report(
        league,
        report,
    )

    print()
    print("=" * 72)
    print("PIPELINE RESULT")
    print("=" * 72)

    print(
        "status:",
        status,
    )

    print(
        "OOS rows:",
        metrics.get(
            "oos_rows"
        ),
    )

    print(
        "AI accuracy:",
        f'{metrics["ai_accuracy"]:.4f}',
    )

    print(
        "Market accuracy:",
        f'{metrics["market_accuracy"]:.4f}',
    )

    print(
        "HOME baseline:",
        f'{metrics["home_accuracy"]:.4f}',
    )

    print(
        "AI logloss:",
        f'{metrics["ai_logloss"]:.4f}',
    )

    print(
        "Market logloss:",
        f'{metrics["market_logloss"]:.4f}',
    )

    print(
        "AI Brier:",
        f'{metrics["ai_brier"]:.4f}',
    )

    print(
        "Market Brier:",
        f'{metrics["market_brier"]:.4f}',
    )

    print()
    print("QUALITY GATE:")

    for key, value in (
        quality.items()
    ):
        print(
            f"{key:32}",
            value,
        )

    print()
    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "candidate model saved:",
        False,
    )

    print(
        "promotion performed:",
        False,
    )

    print(
        "report:",
        report_path,
    )

    if not production_unchanged:
        print()
        print(
            "FAIL: production artifact changed."
        )

        return 2

    print()

    if quality[
        "promotion_eligible"
    ]:
        print(
            "PASS: challenger cleared "
            "the strict research quality gate."
        )

        print(
            "NOTE: promotion still requires "
            "a separate explicit task."
        )

    else:
        print(
            "REJECTED: challenger did not "
            "beat market on all required metrics."
        )

        print(
            "Production remains unchanged."
        )

    # A rejected research candidate is still a
    # successfully completed experiment.
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
