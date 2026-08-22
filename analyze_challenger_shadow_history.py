"""Research-only analysis of accumulated Challenger shadow observations."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from fixture_identity import load_legacy_epl_history


DEFAULT_INPUT = Path(
    "experiments/upcoming_challenger_shadow_history.csv"
)

FIXTURE_COLUMNS = [
    "league",
    "home_team",
    "away_team",
    "commence_time_utc",
]

OUTCOMES = (
    "home",
    "draw",
    "away",
)

REQUIRED_COLUMNS = {
    *FIXTURE_COLUMNS,
    "generated_at_utc",
    "shadow_status",
    "hours_before_kickoff",
    *(
        f"market_{outcome}_probability"
        for outcome in OUTCOMES
    ),
    *(
        f"ai_{outcome}_probability"
        for outcome in OUTCOMES
    ),
}

SUMMARY_COLUMNS = [
    *FIXTURE_COLUMNS,
    "ok_observations",
    "first_generated_at_utc",
    "latest_generated_at_utc",
]

for outcome in OUTCOMES:
    SUMMARY_COLUMNS.extend([
        f"first_market_{outcome}_probability",
        f"latest_market_{outcome}_probability",
        f"market_{outcome}_movement",
        f"first_ai_{outcome}_probability",
        f"latest_ai_{outcome}_probability",
        f"first_ai_minus_market_{outcome}",
        f"latest_ai_minus_market_{outcome}",
    ])

SUMMARY_COLUMNS.extend([
    "maximum_absolute_market_movement",
    "first_strongest_disagreement_absolute_delta",
    "latest_strongest_disagreement_absolute_delta",
    "change_in_strongest_disagreement_absolute_delta",
    "first_hours_before_kickoff",
    "latest_hours_before_kickoff",
    "first_market_argmax",
    "latest_market_argmax",
    "first_ai_argmax",
    "latest_ai_argmax",
    "market_argmax_changed",
    "ai_argmax_changed",
    "first_market_ai_agree",
    "latest_market_ai_agree",
    "market_ai_agreement_changed",
])


def load_history(
    path: Path = DEFAULT_INPUT,
) -> pd.DataFrame:
    """Load history and validate its schema and run timestamps."""

    frame = pd.read_csv(
        path
    )
    frame = load_legacy_epl_history(
        frame
    )

    missing = sorted(
        REQUIRED_COLUMNS.difference(
            frame.columns
        )
    )

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                missing
            )
        )

    generated = pd.to_datetime(
        frame["generated_at_utc"],
        utc=True,
        errors="coerce",
    )

    if generated.isna().any():
        rows = (
            generated[
                generated.isna()
            ]
            .index
            .tolist()
        )

        raise ValueError(
            "Invalid generated_at_utc "
            f"timestamps at rows: {rows}"
        )

    frame = frame.copy()

    frame[
        "generated_at_utc"
    ] = generated

    return frame


def _prediction(
    row: pd.Series,
    prefix: str,
) -> str:
    values = [
        row[
            f"{prefix}_{outcome}_probability"
        ]
        for outcome in OUTCOMES
    ]

    return (
        "H",
        "D",
        "A",
    )[
        max(
            range(3),
            key=values.__getitem__,
        )
    ]


def build_movement_summary(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize first/latest valid market observation per fixture.
    """

    history = load_legacy_epl_history(
        history
    )

    ok = history.loc[
        history[
            "shadow_status"
        ].eq(
            "OK"
        )
    ].copy()

    probability_columns = [
        f"{prefix}_{outcome}_probability"
        for prefix in (
            "market",
            "ai",
        )
        for outcome in OUTCOMES
    ]

    numeric_columns = (
        probability_columns
        + [
            "hours_before_kickoff"
        ]
    )

    ok[
        numeric_columns
    ] = ok[
        numeric_columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    ok = ok.dropna(
        subset=probability_columns
    )

    records = []

    for (
        fixture,
        observations,
    ) in ok.groupby(
        FIXTURE_COLUMNS,
        dropna=False,
        sort=False,
    ):
        observations = (
            observations
            .sort_values(
                "generated_at_utc",
                kind="stable",
            )
        )

        if len(
            observations
        ) < 2:
            continue

        first = observations.iloc[
            0
        ]

        latest = observations.iloc[
            -1
        ]

        record = dict(
            zip(
                FIXTURE_COLUMNS,
                fixture,
            )
        )

        record[
            "ok_observations"
        ] = len(
            observations
        )

        record[
            "first_generated_at_utc"
        ] = first[
            "generated_at_utc"
        ]

        record[
            "latest_generated_at_utc"
        ] = latest[
            "generated_at_utc"
        ]

        first_deltas = []
        latest_deltas = []
        movements = []

        for outcome in OUTCOMES:
            market = (
                f"market_{outcome}_probability"
            )

            ai = (
                f"ai_{outcome}_probability"
            )

            first_delta = float(
                first[ai]
                - first[market]
            )

            latest_delta = float(
                latest[ai]
                - latest[market]
            )

            movement = float(
                latest[market]
                - first[market]
            )

            record[
                f"first_market_{outcome}_probability"
            ] = float(
                first[market]
            )

            record[
                f"latest_market_{outcome}_probability"
            ] = float(
                latest[market]
            )

            record[
                f"market_{outcome}_movement"
            ] = movement

            record[
                f"first_ai_{outcome}_probability"
            ] = float(
                first[ai]
            )

            record[
                f"latest_ai_{outcome}_probability"
            ] = float(
                latest[ai]
            )

            record[
                f"first_ai_minus_market_{outcome}"
            ] = first_delta

            record[
                f"latest_ai_minus_market_{outcome}"
            ] = latest_delta

            first_deltas.append(
                first_delta
            )

            latest_deltas.append(
                latest_delta
            )

            movements.append(
                movement
            )

        first_disagreement = max(
            map(
                abs,
                first_deltas,
            )
        )

        latest_disagreement = max(
            map(
                abs,
                latest_deltas,
            )
        )

        first_market = _prediction(
            first,
            "market",
        )

        latest_market = _prediction(
            latest,
            "market",
        )

        first_ai = _prediction(
            first,
            "ai",
        )

        latest_ai = _prediction(
            latest,
            "ai",
        )

        record.update({
            "maximum_absolute_market_movement":
                max(
                    map(
                        abs,
                        movements,
                    )
                ),

            "first_strongest_disagreement_absolute_delta":
                first_disagreement,

            "latest_strongest_disagreement_absolute_delta":
                latest_disagreement,

            "change_in_strongest_disagreement_absolute_delta":
                (
                    latest_disagreement
                    - first_disagreement
                ),

            "first_hours_before_kickoff":
                float(
                    first[
                        "hours_before_kickoff"
                    ]
                ),

            "latest_hours_before_kickoff":
                float(
                    latest[
                        "hours_before_kickoff"
                    ]
                ),

            "first_market_argmax":
                first_market,

            "latest_market_argmax":
                latest_market,

            "first_ai_argmax":
                first_ai,

            "latest_ai_argmax":
                latest_ai,

            "market_argmax_changed":
                (
                    first_market
                    != latest_market
                ),

            "ai_argmax_changed":
                (
                    first_ai
                    != latest_ai
                ),

            "first_market_ai_agree":
                (
                    first_market
                    == first_ai
                ),

            "latest_market_ai_agree":
                (
                    latest_market
                    == latest_ai
                ),

            "market_ai_agreement_changed":
                (
                    (
                        first_market
                        == first_ai
                    )
                    !=
                    (
                        latest_market
                        == latest_ai
                    )
                ),
        })

        records.append(
            record
        )

    return pd.DataFrame(
        records,
        columns=SUMMARY_COLUMNS,
    )


def analyze_history(
    history: pd.DataFrame,
):
    """Return run coverage/status counts and movement diagnostics."""

    history = load_legacy_epl_history(
        history
    )

    grouped = (
        history.groupby(
            FIXTURE_COLUMNS,
            dropna=False,
        )
        .size()
    )

    by_run = (
        history.groupby(
            [
                "generated_at_utc",
                "shadow_status",
            ],
            dropna=False,
        )
        .size()
        .unstack(
            fill_value=0
        )
    )

    coverage = (
        history.groupby(
            "generated_at_utc",
            dropna=False,
        )
        .size()
    )

    runs = sorted(
        history[
            "generated_at_utc"
        ].unique()
    )

    report = {
        "total_history_rows":
            len(
                history
            ),

        "unique_shadow_runs":
            len(
                runs
            ),

        "fixtures_observed":
            len(
                grouped
            ),

        "fixtures_with_at_least_2_observations":
            int(
                grouped.ge(
                    2
                ).sum()
            ),

        "coverage_by_run":
            coverage.to_dict(),

        "status_counts_by_run": {
            run: {
                "OK":
                    int(
                        by_run.loc[
                            run
                        ].get(
                            "OK",
                            0,
                        )
                    ),

                "NO_MARKET_ODDS":
                    int(
                        by_run.loc[
                            run
                        ].get(
                            "NO_MARKET_ODDS",
                            0,
                        )
                    ),
            }
            for run
            in by_run.index
        },

        "hold":
            len(
                runs
            ) < 2,
    }

    return (
        report,
        build_movement_summary(
            history
        ),
    )


def ranked_summaries(
    summary: pd.DataFrame,
):
    """Build ranked and filtered research views."""

    names = (
        "largest_market_movement",
        "largest_disagreement_increase",
        "largest_disagreement_decrease",
        "market_argmax_changed",
        "latest_ai_market_disagreement",
    )

    if summary.empty:
        return {
            name:
                summary.copy()
            for name
            in names
        }

    change = (
        "change_in_strongest_disagreement_absolute_delta"
    )

    return {
        "largest_market_movement":
            summary.sort_values(
                "maximum_absolute_market_movement",
                ascending=False,
            ),

        "largest_disagreement_increase":
            summary.loc[
                summary[
                    change
                ] > 0
            ].sort_values(
                change,
                ascending=False,
            ),

        "largest_disagreement_decrease":
            summary.loc[
                summary[
                    change
                ] < 0
            ].sort_values(
                change
            ),

        "market_argmax_changed":
            summary.loc[
                summary[
                    "market_argmax_changed"
                ]
            ].sort_values(
                "maximum_absolute_market_movement",
                ascending=False,
            ),

        "latest_ai_market_disagreement":
            summary.loc[
                ~summary[
                    "latest_market_ai_agree"
                ]
            ].sort_values(
                "latest_strongest_disagreement_absolute_delta",
                ascending=False,
            ),
    }


def write_summary(
    summary: pd.DataFrame,
    output_path: Path,
) -> None:
    """Write research output only under experiments/."""

    root = Path.cwd().resolve()

    destination = (
        (
            root
            / output_path
        ).resolve()
        if not output_path.is_absolute()
        else output_path.resolve()
    )

    experiments = (
        root
        / "experiments"
    ).resolve()

    if (
        destination
        != experiments
        and experiments
        not in destination.parents
    ):
        raise ValueError(
            "Research output must be written under experiments/"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        destination,
        index=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
    )

    args = parser.parse_args()

    report, summary = analyze_history(
        load_history(
            args.input
        )
    )

    for (
        key,
        value,
    ) in report.items():
        if key not in {
            "coverage_by_run",
            "status_counts_by_run",
            "hold",
        }:
            print(
                f"{key}: {value}"
            )

    print(
        "coverage_by_run:"
    )

    for (
        run,
        count,
    ) in report[
        "coverage_by_run"
    ].items():
        statuses = report[
            "status_counts_by_run"
        ][run]

        print(
            f"  {run}: "
            f"rows={count}, "
            f"OK={statuses['OK']}, "
            "NO_MARKET_ODDS="
            f"{statuses['NO_MARKET_ODDS']}"
        )

    if report[
        "hold"
    ]:
        print(
            "HOLD: insufficient temporal history "
            "(fewer than 2 unique shadow runs)."
        )
    else:
        for (
            name,
            ranked,
        ) in ranked_summaries(
            summary
        ).items():
            print(
                f"{name}: "
                f"{len(ranked)} fixture(s)"
            )

    if args.output is not None:
        write_summary(
            summary,
            args.output,
        )


if __name__ == "__main__":
    main()
