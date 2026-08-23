"""Evaluate frozen Structural Edge V2 on genuine live observations.

Research-only.

Evaluation contract:
- history is append-only;
- only observations actually recorded before kickoff qualify;
- one observation per fixture is scored:
  the latest valid pre-kickoff observation;
- finished results are never used to create/rewrite predictions;
- compares MARKET vs STRUCTURAL V2;
- reports all fixtures and correction-only subset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from la_liga_structural_v2_shadow import (
    CURRENT_RESULTS_PATH,
    normalize_finished_matches,
)


ROOT = Path(__file__).resolve().parent

HISTORY_PATH = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_shadow_history.csv"
)

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "la_liga_structural_v2_live_evaluation"
)

TARGET = {
    "H": 0,
    "D": 1,
    "A": 2,
}


def multiclass_metrics(
    frame: pd.DataFrame,
    prefix: str,
) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        log_loss,
    )

    y = (
        frame["target"]
        .astype(int)
        .to_numpy()
    )

    probability = frame[
        [
            f"{prefix}_home_probability",
            f"{prefix}_draw_probability",
            f"{prefix}_away_probability",
        ]
    ].astype(float).to_numpy()

    prediction = np.argmax(
        probability,
        axis=1,
    )

    one_hot = np.eye(3)[y]

    return {
        "rows":
            len(frame),

        "accuracy":
            float(
                accuracy_score(
                    y,
                    prediction,
                )
            ),

        "logloss":
            float(
                log_loss(
                    y,
                    probability,
                    labels=[0, 1, 2],
                )
            ),

        "brier":
            float(
                np.mean(
                    np.sum(
                        (
                            probability
                            - one_hot
                        ) ** 2,
                        axis=1,
                    )
                )
            ),
    }


def latest_pre_kickoff(
    history: pd.DataFrame,
) -> pd.DataFrame:
    if history.empty:
        return history.copy()

    required = {
        "event_id",
        "commence_time_utc",
        "recorded_at_utc",
        "pre_kickoff_valid",
    }

    missing = (
        required
        - set(history.columns)
    )

    if missing:
        raise ValueError(
            "History missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    frame = history.copy()

    frame[
        "commence_time_utc"
    ] = pd.to_datetime(
        frame[
            "commence_time_utc"
        ],
        utc=True,
        errors="raise",
    )

    frame[
        "recorded_at_utc"
    ] = pd.to_datetime(
        frame[
            "recorded_at_utc"
        ],
        utc=True,
        errors="raise",
    )

    valid = frame[
        frame[
            "pre_kickoff_valid"
        ].astype(bool)
        & (
            frame[
                "recorded_at_utc"
            ]
            < frame[
                "commence_time_utc"
            ]
        )
    ].copy()

    valid = (
        valid
        .sort_values(
            [
                "event_id",
                "recorded_at_utc",
                "snapshot_time_utc",
            ]
        )
        .groupby(
            "event_id",
            as_index=False,
            sort=False,
        )
        .tail(1)
        .reset_index(drop=True)
    )

    return valid


def match_results(
    observations: pd.DataFrame,
    results: pd.DataFrame,
) -> pd.DataFrame:
    if (
        observations.empty
        or results.empty
    ):
        return pd.DataFrame()

    obs = observations.copy()

    finished = (
        normalize_finished_matches(
            results
        )
    )

    obs[
        "kickoff_date"
    ] = pd.to_datetime(
        obs[
            "commence_time_utc"
        ],
        utc=True,
        errors="raise",
    ).dt.date

    finished[
        "result_date"
    ] = pd.to_datetime(
        finished[
            "match_date"
        ],
        errors="raise",
    ).dt.date

    candidates = obs.merge(
        finished[
            [
                "match_date",
                "result_date",
                "home_team",
                "away_team",
                "home_goals",
                "away_goals",
                "result",
            ]
        ],
        on=[
            "home_team",
            "away_team",
        ],
        how="inner",
    )

    if candidates.empty:
        return candidates

    candidates[
        "date_distance_days"
    ] = (
        pd.to_datetime(
            candidates[
                "result_date"
            ]
        )
        - pd.to_datetime(
            candidates[
                "kickoff_date"
            ]
        )
    ).abs().dt.days

    candidates = candidates[
        candidates[
            "date_distance_days"
        ]
        <= 1
    ].copy()

    if candidates.empty:
        return candidates

    candidates = (
        candidates
        .sort_values(
            [
                "event_id",
                "date_distance_days",
            ]
        )
        .groupby(
            "event_id",
            as_index=False,
            sort=False,
        )
        .head(1)
        .reset_index(drop=True)
    )

    candidates[
        "target"
    ] = (
        candidates[
            "result"
        ]
        .map(TARGET)
    )

    candidates = candidates.dropna(
        subset=[
            "target",
        ]
    ).copy()

    candidates[
        "target"
    ] = (
        candidates[
            "target"
        ].astype(int)
    )

    return candidates


def evaluate(
    settled: pd.DataFrame,
) -> dict:
    if settled.empty:
        return {
            "settled_matches": 0,
            "status": "NO_SETTLED_MATCHES",
        }

    market = multiclass_metrics(
        settled,
        "market",
    )

    shadow = multiclass_metrics(
        settled.rename(
            columns={
                "shadow_home_probability":
                    "v2_home_probability",
                "shadow_draw_probability":
                    "v2_draw_probability",
                "shadow_away_probability":
                    "v2_away_probability",
            }
        ),
        "v2",
    )

    corrected = settled[
        settled[
            "correction_enabled"
        ].astype(bool)
    ].copy()

    correction_report = None

    if not corrected.empty:
        correction_market = (
            multiclass_metrics(
                corrected,
                "market",
            )
        )

        correction_v2 = (
            multiclass_metrics(
                corrected.rename(
                    columns={
                        "shadow_home_probability":
                            "v2_home_probability",
                        "shadow_draw_probability":
                            "v2_draw_probability",
                        "shadow_away_probability":
                            "v2_away_probability",
                    }
                ),
                "v2",
            )
        )

        correction_report = {
            "market":
                correction_market,

            "v2":
                correction_v2,

            "logloss_gap":
                (
                    correction_v2[
                        "logloss"
                    ]
                    - correction_market[
                        "logloss"
                    ]
                ),

            "brier_gap":
                (
                    correction_v2[
                        "brier"
                    ]
                    - correction_market[
                        "brier"
                    ]
                ),
        }

    return {
        "settled_matches":
            len(settled),

        "corrected_matches":
            len(corrected),

        "status":
            "EVALUATED",

        "all_matches": {
            "market":
                market,

            "v2":
                shadow,

            "accuracy_gap":
                (
                    shadow[
                        "accuracy"
                    ]
                    - market[
                        "accuracy"
                    ]
                ),

            "logloss_gap":
                (
                    shadow[
                        "logloss"
                    ]
                    - market[
                        "logloss"
                    ]
                ),

            "brier_gap":
                (
                    shadow[
                        "brier"
                    ]
                    - market[
                        "brier"
                    ]
                ),
        },

        "correction_only":
            correction_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--history",
        type=Path,
        default=HISTORY_PATH,
    )

    parser.add_argument(
        "--results",
        type=Path,
        default=CURRENT_RESULTS_PATH,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
    )

    args = parser.parse_args()

    if not args.history.exists():
        print(
            "No Structural V2 live history yet."
        )
        return 0

    history = pd.read_csv(
        args.history
    )

    observations = (
        latest_pre_kickoff(
            history
        )
    )

    if (
        not args.results.exists()
        or args.results.stat().st_size
        == 0
    ):
        settled = pd.DataFrame()
    else:
        results = pd.read_csv(
            args.results
        )

        settled = match_results(
            observations,
            results,
        )

    report = evaluate(
        settled
    )

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        args.output_dir
        / "la_liga_report.json"
    )

    settled_path = (
        args.output_dir
        / "la_liga_settled_matches.csv"
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    settled.to_csv(
        settled_path,
        index=False,
    )

    print("=" * 72)
    print("LA LIGA STRUCTURAL V2 LIVE EVALUATION")
    print("=" * 72)

    print(
        "history observations:",
        len(history),
    )

    print(
        "canonical pre-kickoff fixtures:",
        len(observations),
    )

    print(
        "settled matches:",
        report[
            "settled_matches"
        ],
    )

    print(
        "status:",
        report["status"],
    )

    if (
        report["status"]
        == "EVALUATED"
    ):
        print()

        print(
            "ALL MATCHES:"
        )

        print(
            json.dumps(
                report[
                    "all_matches"
                ],
                indent=2,
            )
        )

        print()

        print(
            "CORRECTION ONLY:"
        )

        print(
            json.dumps(
                report[
                    "correction_only"
                ],
                indent=2,
            )
        )

    else:
        print(
            "Waiting for genuine 2026/27 "
            "settled fixtures."
        )

    print()
    print(
        "report:",
        report_path,
    )

    print(
        "settled:",
        settled_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
