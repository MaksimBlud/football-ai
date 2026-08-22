"""Derive research-only Challenger decision states from temporal signals."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from track_challenger_signal_transitions import (
    DEFAULT_SUMMARY_OUTPUT,
    DIRECTIONAL_SIGNALS,
)


DEFAULT_OUTPUT = Path(
    "experiments/challenger_decision_states.csv"
)

DECISION_STATES = (
    "EARLY_CONFIRMATION",
    "EARLY_REJECTION",
    "FADED_CONFIRMATION",
    "FADED_REJECTION",
    "REVERSAL_TO_AI",
    "REVERSAL_AWAY_FROM_AI",
    "MIXED_WATCH",
    "STABLE_NO_EDGE",
    "WATCH",
)

OUTPUT_COLUMNS = [
    "league",
    "home_team",
    "away_team",
    "commence_time_utc",
    "valid_ok_observations",
    "transition_count",
    "signal_sequence",
    "latest_signal",
    "latest_signed_toward_ai_score",
    "latest_signal_streak",
    "maximum_same_signal_streak",
    "signal_changed_count",
    "any_directional_reversal",
    "toward_to_away_reversal",
    "away_to_toward_reversal",
    "persistent_toward_ai",
    "persistent_away_from_ai",
    "ever_market_toward_ai",
    "ever_market_away_from_ai",
    "ever_mixed",
    "ever_insufficient",
    "decision_state",
    "directional_bias",
    "state_strength",
    "state_reason",
]

BOOLEAN_COLUMNS = [
    "any_directional_reversal",
    "toward_to_away_reversal",
    "away_to_toward_reversal",
    "persistent_toward_ai",
    "persistent_away_from_ai",
    "ever_market_toward_ai",
    "ever_market_away_from_ai",
    "ever_mixed",
    "ever_insufficient",
]


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
        }

    return (
        bool(value)
        if not pd.isna(value)
        else False
    )


def _signals(row: pd.Series) -> list[str]:
    sequence = row.get(
        "signal_sequence",
        "",
    )

    if pd.isna(sequence):
        return []

    return [
        part.strip()
        for part in str(sequence).split("->")
        if part.strip()
    ]


def _latest_directional(
    signals: list[str],
) -> str | None:
    return next(
        (
            signal
            for signal in reversed(signals)
            if signal in DIRECTIONAL_SIGNALS
        ),
        None,
    )


def _directional_streak(
    signals: list[str],
    direction: str,
) -> int:
    """Count the run ending at the most recent occurrence of direction."""

    try:
        end = (
            len(signals)
            - 1
            - signals[::-1].index(direction)
        )
    except ValueError:
        return 0

    count = 0

    for signal in reversed(
        signals[: end + 1]
    ):
        if signal != direction:
            break

        count += 1

    return count


def classify_decision_state(
    row: pd.Series,
) -> tuple[str, str, int, str]:
    """Apply deterministic decision-state precedence to one fixture."""

    signals = _signals(row)

    latest = str(
        row.get(
            "latest_signal",
            "",
        )
    )

    latest_directional = (
        _latest_directional(
            signals
        )
    )

    flags = {
        column:
            _as_bool(
                row.get(
                    column,
                    False,
                )
            )
        for column in BOOLEAN_COLUMNS
    }

    if (
        flags[
            "away_to_toward_reversal"
        ]
        and latest_directional
        == "MARKET_TOWARD_AI"
    ):
        return (
            "REVERSAL_TO_AI",
            "TOWARD_AI",
            _directional_streak(
                signals,
                "MARKET_TOWARD_AI",
            ),
            "away_to_toward_reversal_latest_direction_toward_ai",
        )

    if (
        flags[
            "toward_to_away_reversal"
        ]
        and latest_directional
        == "MARKET_AWAY_FROM_AI"
    ):
        return (
            "REVERSAL_AWAY_FROM_AI",
            "AWAY_FROM_AI",
            _directional_streak(
                signals,
                "MARKET_AWAY_FROM_AI",
            ),
            "toward_to_away_reversal_latest_direction_away_from_ai",
        )

    if (
        flags[
            "persistent_toward_ai"
        ]
        or (
            latest
            == "MARKET_TOWARD_AI"
            and not flags[
                "toward_to_away_reversal"
            ]
        )
    ):
        reason = (
            "persistent_toward_ai"
            if flags[
                "persistent_toward_ai"
            ]
            else "latest_toward_ai_no_reversal"
        )

        return (
            "EARLY_CONFIRMATION",
            "TOWARD_AI",
            _directional_streak(
                signals,
                "MARKET_TOWARD_AI",
            ),
            reason,
        )

    if (
        flags[
            "persistent_away_from_ai"
        ]
        or (
            latest
            == "MARKET_AWAY_FROM_AI"
            and not flags[
                "away_to_toward_reversal"
            ]
        )
    ):
        reason = (
            "persistent_away_from_ai"
            if flags[
                "persistent_away_from_ai"
            ]
            else "latest_away_from_ai_no_reversal"
        )

        return (
            "EARLY_REJECTION",
            "AWAY_FROM_AI",
            _directional_streak(
                signals,
                "MARKET_AWAY_FROM_AI",
            ),
            reason,
        )

    if (
        latest
        == "INSUFFICIENT_MOVEMENT"
        and flags[
            "ever_market_toward_ai"
        ]
        and not flags[
            "toward_to_away_reversal"
        ]
    ):
        return (
            "FADED_CONFIRMATION",
            "TOWARD_AI",
            _directional_streak(
                signals,
                "MARKET_TOWARD_AI",
            ),
            "toward_ai_faded_without_away_reversal",
        )

    if (
        latest
        == "INSUFFICIENT_MOVEMENT"
        and flags[
            "ever_market_away_from_ai"
        ]
        and not flags[
            "away_to_toward_reversal"
        ]
    ):
        return (
            "FADED_REJECTION",
            "AWAY_FROM_AI",
            _directional_streak(
                signals,
                "MARKET_AWAY_FROM_AI",
            ),
            "away_from_ai_faded_without_toward_reversal",
        )

    if flags[
        "ever_mixed"
    ]:
        return (
            "MIXED_WATCH",
            "NONE",
            0,
            "mixed_movement_without_stronger_state",
        )

    if (
        signals
        and all(
            signal
            == "INSUFFICIENT_MOVEMENT"
            for signal in signals
        )
    ):
        return (
            "STABLE_NO_EDGE",
            "NONE",
            0,
            "only_insufficient_movement_observed",
        )

    return (
        "WATCH",
        "NONE",
        0,
        "unusual_or_incomplete_signal_combination",
    )


def derive_decision_states(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    from fixture_identity import load_legacy_epl_history

    summary = load_legacy_epl_history(
        summary
    )

    records: list[dict] = []

    for _, row in summary.iterrows():
        (
            state,
            bias,
            strength,
            reason,
        ) = classify_decision_state(
            row
        )

        record = {
            column:
                row.get(
                    column,
                    pd.NA,
                )
            for column
            in OUTPUT_COLUMNS[:-4]
        }

        record.update(
            decision_state=state,
            directional_bias=bias,
            state_strength=strength,
            state_reason=reason,
        )

        records.append(
            record
        )

    return pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
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
            "Research output must be written under experiments/"
        )

    return destination


def write_decision_states(
    states: pd.DataFrame,
    output_path: Path = DEFAULT_OUTPUT,
) -> None:
    destination = _destination(
        output_path
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    states.reindex(
        columns=OUTPUT_COLUMNS
    ).to_csv(
        destination,
        index=False,
    )


def report_counts(
    states: pd.DataFrame,
) -> dict[str, object]:
    state_counts = (
        states[
            "decision_state"
        ].value_counts().to_dict()
        if not states.empty
        else {}
    )

    bias_counts = (
        states[
            "directional_bias"
        ].value_counts().to_dict()
        if not states.empty
        else {}
    )

    return {
        "total_fixtures":
            len(states),

        "decision_state_counts":
            state_counts,

        "directional_bias_counts":
            bias_counts,

        "reversal_count":
            int(
                states[
                    "decision_state"
                ].isin([
                    "REVERSAL_TO_AI",
                    "REVERSAL_AWAY_FROM_AI",
                ]).sum()
            )
            if not states.empty
            else 0,

        "faded_confirmation_count":
            int(
                state_counts.get(
                    "FADED_CONFIRMATION",
                    0,
                )
            ),

        "faded_rejection_count":
            int(
                state_counts.get(
                    "FADED_REJECTION",
                    0,
                )
            ),

        "active_confirmation_count":
            int(
                state_counts.get(
                    "EARLY_CONFIRMATION",
                    0,
                )
            ),

        "active_rejection_count":
            int(
                state_counts.get(
                    "EARLY_REJECTION",
                    0,
                )
            ),
    }


def ranked_examples(
    states: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    groups = {
        "strongest_EARLY_CONFIRMATION":
            [
                "EARLY_CONFIRMATION"
            ],

        "strongest_EARLY_REJECTION":
            [
                "EARLY_REJECTION"
            ],

        "strongest_FADED_CONFIRMATION":
            [
                "FADED_CONFIRMATION"
            ],

        "strongest_FADED_REJECTION":
            [
                "FADED_REJECTION"
            ],

        "reversals":
            [
                "REVERSAL_TO_AI",
                "REVERSAL_AWAY_FROM_AI",
            ],
    }

    return {
        name:
            states.loc[
                states[
                    "decision_state"
                ].isin(
                    state_names
                )
            ].sort_values(
                [
                    "state_strength",
                    "latest_signed_toward_ai_score",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            if not states.empty
            else states.copy()

        for (
            name,
            state_names,
        )
        in groups.items()
    }


def print_report(
    states: pd.DataFrame,
) -> None:
    if states.empty:
        print(
            "HOLD: no fixture has transitions."
        )

    for (
        name,
        count,
    ) in report_counts(
        states
    ).items():
        print(
            f"{name}: {count}"
        )

    for (
        name,
        rows,
    ) in ranked_examples(
        states
    ).items():
        print(
            f"{name}: "
            f"{len(rows)} fixture(s)"
        )

        if not rows.empty:
            first = rows.iloc[
                0
            ]

            print(
                "  "
                f"{first['home_team']} "
                "vs "
                f"{first['away_team']}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_SUMMARY_OUTPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    summary = pd.read_csv(
        args.input
    )

    states = derive_decision_states(
        summary
    )

    print_report(
        states
    )

    write_decision_states(
        states,
        args.output,
    )


if __name__ == "__main__":
    main()
