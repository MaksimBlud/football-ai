"""Research-only tracking of Challenger temporal signals between shadow runs."""

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
from classify_challenger_temporal_signals import (
    SIGNALS,
    classify_movement_summary,
)


DEFAULT_TRANSITIONS_OUTPUT = Path(
    "experiments/challenger_signal_transitions.csv"
)

DEFAULT_SUMMARY_OUTPUT = Path(
    "experiments/challenger_signal_state_summary.csv"
)

DIRECTIONAL_SIGNALS = (
    "MARKET_TOWARD_AI",
    "MARKET_AWAY_FROM_AI",
)

TRANSITION_COLUMNS = [
    *FIXTURE_COLUMNS,
    "transition_index",
    "from_generated_at_utc",
    "to_generated_at_utc",
    "from_hours_before_kickoff",
    "to_hours_before_kickoff",
    "elapsed_hours",
]

for outcome in OUTCOMES:
    TRANSITION_COLUMNS.extend([
        f"from_market_{outcome}_probability",
        f"to_market_{outcome}_probability",
        f"from_ai_{outcome}_probability",
        f"to_ai_{outcome}_probability",
        f"market_{outcome}_movement",
        f"from_ai_minus_market_{outcome}",
        f"to_ai_minus_market_{outcome}",
    ])

TRANSITION_COLUMNS.extend([
    "strongest_initial_disagreement_outcome",
    "strongest_initial_disagreement_signed_delta",
    "strongest_initial_disagreement_absolute_delta",
    "market_movement_on_strongest_disagreement",
    "signed_toward_ai_score",
    "disagreement_change",
    "maximum_absolute_market_movement",
    "from_market_argmax",
    "to_market_argmax",
    "from_ai_argmax",
    "to_ai_argmax",
    "market_argmax_changed",
    "ai_argmax_changed",
    "from_market_ai_agree",
    "to_market_ai_agree",
    "transition_signal",
])

SUMMARY_COLUMNS = [
    *FIXTURE_COLUMNS,
    "valid_ok_observations",
    "transition_count",
    "first_signal",
    "latest_signal",
    "signal_sequence",
    "latest_signed_toward_ai_score",
    "latest_signal_streak",
    "maximum_same_signal_streak",
    "first_signal_generated_at_utc",
    "latest_signal_generated_at_utc",
    "first_signal_hours_before_kickoff",
    "latest_signal_hours_before_kickoff",
    "signal_changed_count",
    "ever_market_toward_ai",
    "ever_market_away_from_ai",
    "ever_mixed",
    "ever_insufficient",
    "toward_to_away_reversal",
    "away_to_toward_reversal",
    "any_directional_reversal",
    "persistent_toward_ai",
    "persistent_away_from_ai",
]


def _valid_observations(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Return only complete OK observations, preserving coverage elsewhere."""

    from fixture_identity import load_legacy_epl_history

    history = load_legacy_epl_history(
        history
    )

    probability_columns = [
        f"{prefix}_{outcome}_probability"
        for prefix in (
            "market",
            "ai",
        )
        for outcome in OUTCOMES
    ]

    valid = history.loc[
        history[
            "shadow_status"
        ].eq(
            "OK"
        )
    ].copy()

    valid[
        "generated_at_utc"
    ] = pd.to_datetime(
        valid[
            "generated_at_utc"
        ],
        utc=True,
        errors="raise",
    )

    valid[
        probability_columns
    ] = valid[
        probability_columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    valid[
        "hours_before_kickoff"
    ] = pd.to_numeric(
        valid[
            "hours_before_kickoff"
        ],
        errors="coerce",
    )

    return valid.dropna(
        subset=probability_columns
    )


def build_signal_transitions(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Classify every adjacent pair of valid observations for each fixture."""

    records: list[dict] = []

    valid = _valid_observations(
        history
    )

    for (
        fixture,
        observations,
    ) in valid.groupby(
        FIXTURE_COLUMNS,
        dropna=False,
        sort=False,
    ):
        observations = observations.sort_values(
            "generated_at_utc",
            kind="stable",
        )

        for index in range(
            len(observations) - 1
        ):
            pair = observations.iloc[
                [
                    index,
                    index + 1,
                ]
            ]

            movement = build_movement_summary(
                pair
            )

            classified = (
                classify_movement_summary(
                    movement
                )
                .iloc[
                    0
                ]
            )

            first = pair.iloc[
                0
            ]

            latest = pair.iloc[
                1
            ]

            record = dict(
                zip(
                    FIXTURE_COLUMNS,
                    fixture,
                )
            )

            record.update({
                "transition_index":
                    index + 1,

                "from_generated_at_utc":
                    first[
                        "generated_at_utc"
                    ],

                "to_generated_at_utc":
                    latest[
                        "generated_at_utc"
                    ],

                "from_hours_before_kickoff":
                    float(
                        first[
                            "hours_before_kickoff"
                        ]
                    ),

                "to_hours_before_kickoff":
                    float(
                        latest[
                            "hours_before_kickoff"
                        ]
                    ),

                "elapsed_hours":
                    (
                        latest[
                            "generated_at_utc"
                        ]
                        - first[
                            "generated_at_utc"
                        ]
                    ).total_seconds()
                    / 3600,
            })

            for outcome in OUTCOMES:
                record.update({
                    f"from_market_{outcome}_probability":
                        classified[
                            f"first_market_{outcome}_probability"
                        ],

                    f"to_market_{outcome}_probability":
                        classified[
                            f"latest_market_{outcome}_probability"
                        ],

                    f"from_ai_{outcome}_probability":
                        float(
                            first[
                                f"ai_{outcome}_probability"
                            ]
                        ),

                    f"to_ai_{outcome}_probability":
                        float(
                            latest[
                                f"ai_{outcome}_probability"
                            ]
                        ),

                    f"market_{outcome}_movement":
                        classified[
                            f"market_{outcome}_movement"
                        ],

                    f"from_ai_minus_market_{outcome}":
                        classified[
                            f"first_ai_minus_market_{outcome}"
                        ],

                    f"to_ai_minus_market_{outcome}":
                        classified[
                            f"latest_ai_minus_market_{outcome}"
                        ],
                })

            aliases = {
                "first_market_argmax":
                    "from_market_argmax",

                "latest_market_argmax":
                    "to_market_argmax",

                "first_ai_argmax":
                    "from_ai_argmax",

                "latest_ai_argmax":
                    "to_ai_argmax",

                "first_market_ai_agree":
                    "from_market_ai_agree",

                "latest_market_ai_agree":
                    "to_market_ai_agree",

                "primary_signal":
                    "transition_signal",
            }

            for column in TRANSITION_COLUMNS:
                if column in classified.index:
                    record[
                        column
                    ] = classified[
                        column
                    ]

            for (
                source,
                destination,
            ) in aliases.items():
                record[
                    destination
                ] = classified[
                    source
                ]

            records.append(
                record
            )

    return pd.DataFrame(
        records,
        columns=TRANSITION_COLUMNS,
    )


def _streaks(
    signals: list[str],
) -> list[tuple[str, int]]:
    streaks: list[
        tuple[
            str,
            int,
        ]
    ] = []

    for signal in signals:
        if (
            streaks
            and streaks[-1][0]
            == signal
        ):
            streaks[-1] = (
                signal,
                streaks[-1][1] + 1,
            )
        else:
            streaks.append(
                (
                    signal,
                    1,
                )
            )

    return streaks


def build_fixture_state_summary(
    transitions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Derive persistence, reversal,
    and latest-state facts per fixture.
    """

    records: list[dict] = []

    for (
        fixture,
        rows,
    ) in transitions.groupby(
        FIXTURE_COLUMNS,
        dropna=False,
        sort=False,
    ):
        rows = rows.sort_values(
            "transition_index",
            kind="stable",
        )

        signals = rows[
            "transition_signal"
        ].tolist()

        streaks = _streaks(
            signals
        )

        adjacent = list(
            zip(
                signals,
                signals[
                    1:
                ],
            )
        )

        toward_away = (
            (
                "MARKET_TOWARD_AI",
                "MARKET_AWAY_FROM_AI",
            )
            in adjacent
        )

        away_toward = (
            (
                "MARKET_AWAY_FROM_AI",
                "MARKET_TOWARD_AI",
            )
            in adjacent
        )

        record = dict(
            zip(
                FIXTURE_COLUMNS,
                fixture,
            )
        )

        record.update({
            "valid_ok_observations":
                len(
                    rows
                )
                + 1,

            "transition_count":
                len(
                    rows
                ),

            "first_signal":
                signals[
                    0
                ],

            "latest_signal":
                signals[
                    -1
                ],

            "signal_sequence":
                " -> ".join(
                    signals
                ),

            "latest_signed_toward_ai_score":
                rows.iloc[
                    -1
                ][
                    "signed_toward_ai_score"
                ],

            "latest_signal_streak":
                streaks[
                    -1
                ][
                    1
                ],

            "maximum_same_signal_streak":
                max(
                    length
                    for (
                        _,
                        length,
                    )
                    in streaks
                ),

            "first_signal_generated_at_utc":
                rows.iloc[
                    0
                ][
                    "to_generated_at_utc"
                ],

            "latest_signal_generated_at_utc":
                rows.iloc[
                    -1
                ][
                    "to_generated_at_utc"
                ],

            "first_signal_hours_before_kickoff":
                rows.iloc[
                    0
                ][
                    "to_hours_before_kickoff"
                ],

            "latest_signal_hours_before_kickoff":
                rows.iloc[
                    -1
                ][
                    "to_hours_before_kickoff"
                ],

            "signal_changed_count":
                sum(
                    left
                    != right
                    for (
                        left,
                        right,
                    )
                    in adjacent
                ),

            "ever_market_toward_ai":
                (
                    "MARKET_TOWARD_AI"
                    in signals
                ),

            "ever_market_away_from_ai":
                (
                    "MARKET_AWAY_FROM_AI"
                    in signals
                ),

            "ever_mixed":
                (
                    "MIXED_MOVEMENT"
                    in signals
                ),

            "ever_insufficient":
                (
                    "INSUFFICIENT_MOVEMENT"
                    in signals
                ),

            "toward_to_away_reversal":
                toward_away,

            "away_to_toward_reversal":
                away_toward,

            "any_directional_reversal":
                (
                    toward_away
                    or away_toward
                ),

            "persistent_toward_ai":
                any(
                    (
                        signal
                        == "MARKET_TOWARD_AI"
                    )
                    and length >= 2
                    for (
                        signal,
                        length,
                    )
                    in streaks
                ),

            "persistent_away_from_ai":
                any(
                    (
                        signal
                        == "MARKET_AWAY_FROM_AI"
                    )
                    and length >= 2
                    for (
                        signal,
                        length,
                    )
                    in streaks
                ),
        })

        records.append(
            record
        )

    return pd.DataFrame(
        records,
        columns=SUMMARY_COLUMNS,
    )


def _destination(
    path: Path,
) -> Path:
    root = Path.cwd().resolve()

    destination = (
        (
            root
            / path
        ).resolve()
        if not path.is_absolute()
        else path.resolve()
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

    return destination


def write_outputs(
    transitions: pd.DataFrame,
    summary: pd.DataFrame,
    transitions_output: Path = DEFAULT_TRANSITIONS_OUTPUT,
    summary_output: Path = DEFAULT_SUMMARY_OUTPUT,
) -> None:
    """
    Write both research CSVs,
    and nowhere outside experiments/.
    """

    destinations = [
        _destination(
            transitions_output
        ),
        _destination(
            summary_output
        ),
    ]

    for destination in destinations:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    transitions.reindex(
        columns=TRANSITION_COLUMNS
    ).to_csv(
        destinations[
            0
        ],
        index=False,
    )

    summary.reindex(
        columns=SUMMARY_COLUMNS
    ).to_csv(
        destinations[
            1
        ],
        index=False,
    )


def report_counts(
    history: pd.DataFrame,
    transitions: pd.DataFrame,
    summary: pd.DataFrame,
) -> dict:
    """Return coverage and behavioral counts used by the text report."""

    from fixture_identity import load_legacy_epl_history

    history = load_legacy_epl_history(
        history
    )

    valid = _valid_observations(
        history
    )

    valid_fixture_sizes = (
        valid.groupby(
            FIXTURE_COLUMNS,
            dropna=False,
        )
        .size()
    )

    return {
        "total_history_rows":
            len(
                history
            ),

        "unique_shadow_runs":
            history[
                "generated_at_utc"
            ].nunique(
                dropna=False
            ),

        "fixtures_observed":
            history.groupby(
                FIXTURE_COLUMNS,
                dropna=False,
            ).ngroups,

        "fixtures_with_at_least_2_valid_OK_observations":
            int(
                valid_fixture_sizes.ge(
                    2
                ).sum()
            ),

        "total_transitions":
            len(
                transitions
            ),

        "fixtures_with_transitions":
            len(
                summary
            ),

        "fixtures_with_signal_changes":
            (
                int(
                    summary[
                        "signal_changed_count"
                    ].gt(
                        0
                    ).sum()
                )
                if len(
                    summary
                )
                else 0
            ),

        "fixtures_with_directional_reversals":
            (
                int(
                    summary[
                        "any_directional_reversal"
                    ].sum()
                )
                if len(
                    summary
                )
                else 0
            ),

        "persistent_MARKET_TOWARD_AI_fixtures":
            (
                int(
                    summary[
                        "persistent_toward_ai"
                    ].sum()
                )
                if len(
                    summary
                )
                else 0
            ),

        "persistent_MARKET_AWAY_FROM_AI_fixtures":
            (
                int(
                    summary[
                        "persistent_away_from_ai"
                    ].sum()
                )
                if len(
                    summary
                )
                else 0
            ),
    }


def print_report(
    history: pd.DataFrame,
    transitions: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    if transitions.empty:
        print(
            "HOLD: no fixtures have at least "
            "two valid OK observations."
        )

    for (
        name,
        value,
    ) in report_counts(
        history,
        transitions,
        summary,
    ).items():
        print(
            f"{name}: {value}"
        )

    transition_counts = (
        transitions[
            "transition_signal"
        ].value_counts()
        if len(
            transitions
        )
        else {}
    )

    latest_counts = (
        summary[
            "latest_signal"
        ].value_counts()
        if len(
            summary
        )
        else {}
    )

    for signal in SIGNALS:
        print(
            f"transition_{signal}: "
            f"{int(transition_counts.get(signal, 0))}"
        )

        print(
            f"latest_{signal}: "
            f"{int(latest_counts.get(signal, 0))}"
        )

    rankings = {
        "strongest latest MARKET_TOWARD_AI":
            summary.loc[
                summary[
                    "latest_signal"
                ].eq(
                    "MARKET_TOWARD_AI"
                )
            ].sort_values(
                "latest_signed_toward_ai_score",
                ascending=False,
            ),

        "strongest latest MARKET_AWAY_FROM_AI":
            summary.loc[
                summary[
                    "latest_signal"
                ].eq(
                    "MARKET_AWAY_FROM_AI"
                )
            ].sort_values(
                "latest_signed_toward_ai_score"
            ),

        "most signal changes":
            summary.sort_values(
                "signal_changed_count",
                ascending=False,
            ),

        "directional reversals":
            summary.loc[
                summary[
                    "any_directional_reversal"
                ]
            ],

        "longest persistent directional streak":
            summary.loc[
                (
                    summary[
                        "persistent_toward_ai"
                    ]
                    |
                    summary[
                        "persistent_away_from_ai"
                    ]
                )
            ].sort_values(
                "maximum_same_signal_streak",
                ascending=False,
            ),
    }

    for (
        name,
        ranked,
    ) in rankings.items():
        print(
            f"{name}: "
            f"{len(ranked)} fixture(s)"
        )

        if len(
            ranked
        ):
            row = ranked.iloc[
                0
            ]

            print(
                "  "
                f"{row['home_team']} "
                "vs "
                f"{row['away_team']}"
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
        "--transitions-output",
        type=Path,
        default=DEFAULT_TRANSITIONS_OUTPUT,
    )

    parser.add_argument(
        "--summary-output",
        type=Path,
        default=DEFAULT_SUMMARY_OUTPUT,
    )

    args = parser.parse_args()

    history = load_history(
        args.input
    )

    transitions = build_signal_transitions(
        history
    )

    summary = build_fixture_state_summary(
        transitions
    )

    print_report(
        history,
        transitions,
        summary,
    )

    write_outputs(
        transitions,
        summary,
        args.transitions_output,
        args.summary_output,
    )


if __name__ == "__main__":
    main()
