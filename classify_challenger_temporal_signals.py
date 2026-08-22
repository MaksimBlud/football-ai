"""Research-only temporal signal classification for Challenger shadow history."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from analyze_challenger_shadow_history import (
    DEFAULT_INPUT,
    FIXTURE_COLUMNS,
    OUTCOMES,
    build_movement_summary,
    load_history,
)


DEFAULT_OUTPUT = Path(
    "experiments/challenger_temporal_signals.csv"
)

STABLE_MARKET_THRESHOLD = 0.005
TOWARD_AWAY_THRESHOLD = 0.005

OUTCOME_LABELS = dict(
    zip(
        OUTCOMES,
        ("H", "D", "A"),
    )
)

SIGNALS = (
    "MARKET_TOWARD_AI",
    "MARKET_AWAY_FROM_AI",
    "INSUFFICIENT_MOVEMENT",
    "MIXED_MOVEMENT",
)

CLASSIFICATION_COLUMNS = [
    *FIXTURE_COLUMNS,
    "first_generated_at_utc",
    "latest_generated_at_utc",
    "first_hours_before_kickoff",
    "latest_hours_before_kickoff",
    "ok_observations",
]

for outcome in OUTCOMES:
    CLASSIFICATION_COLUMNS.extend([
        f"first_market_{outcome}_probability",
        f"latest_market_{outcome}_probability",
        f"market_{outcome}_movement",
        f"first_ai_minus_market_{outcome}",
        f"latest_ai_minus_market_{outcome}",
    ])

CLASSIFICATION_COLUMNS.extend([
    "strongest_initial_disagreement_outcome",
    "strongest_initial_disagreement_signed_delta",
    "strongest_initial_disagreement_absolute_delta",
    "market_movement_on_strongest_disagreement",
    "signed_toward_ai_score",
    "disagreement_change",
    "maximum_absolute_market_movement",
    "first_market_argmax",
    "latest_market_argmax",
    "first_ai_argmax",
    "latest_ai_argmax",
    "market_argmax_changed",
    "ai_argmax_changed",
    "first_market_ai_agree",
    "latest_market_ai_agree",
    "latest_ai_market_argmax_disagreement",
    "disagreement_increased",
    "disagreement_decreased",
    "primary_signal",
])


def classify_movement_summary(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Classify pre-match movement-summary rows
    without using match results.
    """

    records = []

    for _, row in summary.iterrows():
        strongest = max(
            OUTCOMES,
            key=lambda outcome: abs(
                row[
                    f"first_ai_minus_market_{outcome}"
                ]
            ),
        )

        initial_delta = float(
            row[
                f"first_ai_minus_market_{strongest}"
            ]
        )

        movement = float(
            row[
                f"market_{strongest}_movement"
            ]
        )

        # Positive initial AI delta:
        # market increase = movement toward AI.
        #
        # Negative initial AI delta:
        # market decrease = movement toward AI.
        if initial_delta > 0:
            sign = 1.0
        elif initial_delta < 0:
            sign = -1.0
        else:
            sign = 0.0

        score = (
            sign
            * movement
        )

        maximum_movement = float(
            row[
                "maximum_absolute_market_movement"
            ]
        )

        disagreement_change = float(
            row[
                "change_in_strongest_disagreement_absolute_delta"
            ]
        )

        if (
            maximum_movement
            < STABLE_MARKET_THRESHOLD
        ):
            signal = (
                "INSUFFICIENT_MOVEMENT"
            )

        elif (
            score
            >= TOWARD_AWAY_THRESHOLD
        ):
            signal = (
                "MARKET_TOWARD_AI"
            )

        elif (
            score
            <= -TOWARD_AWAY_THRESHOLD
        ):
            signal = (
                "MARKET_AWAY_FROM_AI"
            )

        else:
            signal = (
                "MIXED_MOVEMENT"
            )

        record = {
            column: row[column]
            for column
            in CLASSIFICATION_COLUMNS
            if column in row.index
        }

        record.update({
            "strongest_initial_disagreement_outcome":
                OUTCOME_LABELS[
                    strongest
                ],

            "strongest_initial_disagreement_signed_delta":
                initial_delta,

            "strongest_initial_disagreement_absolute_delta":
                abs(
                    initial_delta
                ),

            "market_movement_on_strongest_disagreement":
                movement,

            "signed_toward_ai_score":
                score,

            "disagreement_change":
                disagreement_change,

            "latest_ai_market_argmax_disagreement":
                not bool(
                    row[
                        "latest_market_ai_agree"
                    ]
                ),

            "disagreement_increased":
                disagreement_change > 0,

            "disagreement_decreased":
                disagreement_change < 0,

            "primary_signal":
                signal,
        })

        records.append(
            record
        )

    return pd.DataFrame(
        records,
        columns=CLASSIFICATION_COLUMNS,
    )


def build_temporal_signals(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reuse canonical first/latest movement summary,
    then classify it.
    """

    return classify_movement_summary(
        build_movement_summary(
            history
        )
    )


def summary_report(
    classified: pd.DataFrame,
) -> dict[str, int]:
    """Return aggregate signal and flag counts."""

    counts = (
        classified[
            "primary_signal"
        ].value_counts()
        if not classified.empty
        else {}
    )

    return {
        "total_classified_fixtures":
            len(
                classified
            ),

        **{
            signal:
                int(
                    counts.get(
                        signal,
                        0,
                    )
                )
            for signal
            in SIGNALS
        },

        "latest_ai_market_argmax_disagreements":
            (
                int(
                    classified[
                        "latest_ai_market_argmax_disagreement"
                    ].sum()
                )
                if not classified.empty
                else 0
            ),

        "market_argmax_changes":
            (
                int(
                    classified[
                        "market_argmax_changed"
                    ].sum()
                )
                if not classified.empty
                else 0
            ),

        "ai_argmax_changes":
            (
                int(
                    classified[
                        "ai_argmax_changed"
                    ].sum()
                )
                if not classified.empty
                else 0
            ),
    }


def ranked_examples(
    classified: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Return strongest examples for research views."""

    names = (
        "strongest_MARKET_TOWARD_AI",
        "strongest_MARKET_AWAY_FROM_AI",
        "largest_disagreement_increase",
        "largest_disagreement_decrease",
    )

    if classified.empty:
        return {
            name:
                classified.copy()
            for name
            in names
        }

    return {
        "strongest_MARKET_TOWARD_AI":
            classified.loc[
                classified[
                    "primary_signal"
                ].eq(
                    "MARKET_TOWARD_AI"
                )
            ].sort_values(
                "signed_toward_ai_score",
                ascending=False,
            ),

        "strongest_MARKET_AWAY_FROM_AI":
            classified.loc[
                classified[
                    "primary_signal"
                ].eq(
                    "MARKET_AWAY_FROM_AI"
                )
            ].sort_values(
                "signed_toward_ai_score"
            ),

        "largest_disagreement_increase":
            classified.sort_values(
                "disagreement_change",
                ascending=False,
            ),

        "largest_disagreement_decrease":
            classified.sort_values(
                "disagreement_change"
            ),
    }


def write_signals(
    classified: pd.DataFrame,
    output_path: Path = DEFAULT_OUTPUT,
) -> None:
    """
    Write research CSV only beneath experiments/.
    """

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
            "Research output must be written "
            "under experiments/"
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    classified.reindex(
        columns=CLASSIFICATION_COLUMNS
    ).to_csv(
        destination,
        index=False,
    )


def print_report(
    classified: pd.DataFrame,
) -> None:
    """
    Print HOLD, aggregate counts,
    and ranked examples.
    """

    report = summary_report(
        classified
    )

    if classified.empty:
        print(
            "HOLD: no fixtures have at least "
            "two valid OK observations."
        )

    for (
        name,
        count,
    ) in report.items():
        print(
            f"{name}: {count}"
        )

    for (
        name,
        ranked,
    ) in ranked_examples(
        classified
    ).items():
        print(
            f"{name}: "
            f"{len(ranked)} fixture(s)"
        )

        if not ranked.empty:
            example = ranked.iloc[
                0
            ]

            print(
                "  "
                f"{example['home_team']} "
                "vs "
                f"{example['away_team']}"
            )


def main() -> None:
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
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    classified = (
        build_temporal_signals(
            load_history(
                args.input
            )
        )
    )

    print_report(
        classified
    )

    write_signals(
        classified,
        args.output,
    )


if __name__ == "__main__":
    main()
