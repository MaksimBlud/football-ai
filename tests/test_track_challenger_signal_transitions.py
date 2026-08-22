from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

import track_challenger_signal_transitions as module


ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

REPOSITORY_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        1
    ]
)

AI = (
    0.60,
    0.25,
    0.15,
)


def row(
    run,
    market,
    ai=AI,
    status="OK",
    home="Alpha",
):
    result = {
        "home_team":
            home,

        "away_team":
            "Beta",

        "commence_time_utc":
            "2026-08-24T18:00:00Z",

        "generated_at_utc":
            pd.Timestamp(
                run
            ),

        "shadow_status":
            status,

        "hours_before_kickoff":
            (
                pd.Timestamp(
                    "2026-08-24T18:00:00Z"
                )
                - pd.Timestamp(
                    run
                )
            ).total_seconds()
            / 3600,
    }

    for (
        outcome,
        market_value,
        ai_value,
    ) in zip(
        (
            "home",
            "draw",
            "away",
        ),
        market,
        ai,
    ):
        result[
            f"market_{outcome}_probability"
        ] = market_value

        result[
            f"ai_{outcome}_probability"
        ] = ai_value

    return result


def history(
    markets,
    statuses=None,
):
    times = pd.date_range(
        "2026-08-20T18:00:00Z",
        periods=len(
            markets
        ),
        freq="12h",
    )

    statuses = (
        statuses
        or [
            "OK"
        ]
        * len(
            markets
        )
    )

    return pd.DataFrame([
        row(
            time,
            market,
            status=status,
        )
        for (
            time,
            market,
            status,
        )
        in zip(
            times,
            markets,
            statuses,
        )
    ])


def hashes():
    return {
        name:
            sha256(
                (
                    REPOSITORY_ROOT
                    / name
                ).read_bytes()
            ).hexdigest()

        for name
        in ARTIFACTS

        if (
            REPOSITORY_ROOT
            / name
        ).exists()
    }


def test_hold_and_header_only_outputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    data = history([
        (
            0.45,
            0.35,
            0.20,
        )
    ])

    transitions = (
        module.build_signal_transitions(
            data
        )
    )

    summary = (
        module.build_fixture_state_summary(
            transitions
        )
    )

    module.print_report(
        data,
        transitions,
        summary,
    )

    assert (
        "HOLD"
        in capsys.readouterr().out
    )

    monkeypatch.chdir(
        tmp_path
    )

    module.write_outputs(
        transitions,
        summary,
        Path(
            "experiments/transitions.csv"
        ),
        Path(
            "experiments/summary.csv"
        ),
    )

    loaded_transitions = (
        pd.read_csv(
            "experiments/transitions.csv"
        )
    )

    loaded_summary = (
        pd.read_csv(
            "experiments/summary.csv"
        )
    )

    assert loaded_transitions.empty

    assert (
        list(
            loaded_transitions.columns
        )
        == module.TRANSITION_COLUMNS
    )

    assert loaded_summary.empty

    assert (
        list(
            loaded_summary.columns
        )
        == module.SUMMARY_COLUMNS
    )


def test_one_transition_from_two_observations():
    transitions = (
        module.build_signal_transitions(
            history([
                (
                    0.45,
                    0.35,
                    0.20,
                ),
                (
                    0.46,
                    0.34,
                    0.20,
                ),
            ])
        )
    )

    assert len(
        transitions
    ) == 1

    assert (
        transitions.iloc[
            0
        ][
            "transition_index"
        ]
        == 1
    )


def test_three_adjacent_transitions_are_chronologically_ordered():
    data = history([
        (
            0.45,
            0.35,
            0.20,
        ),
        (
            0.46,
            0.34,
            0.20,
        ),
        (
            0.47,
            0.33,
            0.20,
        ),
        (
            0.48,
            0.32,
            0.20,
        ),
    ]).iloc[
        [
            3,
            0,
            2,
            1,
        ]
    ]

    transitions = (
        module.build_signal_transitions(
            data
        )
    )

    assert len(
        transitions
    ) == 3

    assert (
        transitions[
            "transition_index"
        ].tolist()
        == [
            1,
            2,
            3,
        ]
    )

    assert (
        transitions[
            "from_generated_at_utc"
        ].is_monotonic_increasing
    )

    assert (
        transitions[
            "elapsed_hours"
        ]
        == 12
    ).all()


def test_no_market_odds_is_ignored_without_breaking_adjacency():
    data = history(
        [
            (
                0.45,
                0.35,
                0.20,
            ),
            (
                0.10,
                0.10,
                0.80,
            ),
            (
                0.47,
                0.33,
                0.20,
            ),
        ],
        [
            "OK",
            "NO_MARKET_ODDS",
            "OK",
        ],
    )

    transitions = (
        module.build_signal_transitions(
            data
        )
    )

    assert len(
        transitions
    ) == 1

    assert (
        transitions.iloc[
            0
        ][
            "market_home_movement"
        ]
        == pytest.approx(
            0.02
        )
    )


@pytest.mark.parametrize(
    "latest, expected",
    [
        (
            (
                0.47,
                0.33,
                0.20,
            ),
            "MARKET_TOWARD_AI",
        ),
        (
            (
                0.43,
                0.37,
                0.20,
            ),
            "MARKET_AWAY_FROM_AI",
        ),
        (
            (
                0.453,
                0.347,
                0.20,
            ),
            "INSUFFICIENT_MOVEMENT",
        ),
        (
            (
                0.45,
                0.36,
                0.19,
            ),
            "MIXED_MOVEMENT",
        ),
    ],
)
def test_fixed_classifier_semantics(
    latest,
    expected,
):
    transitions = (
        module.build_signal_transitions(
            history([
                (
                    0.45,
                    0.35,
                    0.20,
                ),
                latest,
            ])
        )
    )

    assert (
        transitions.iloc[
            0
        ][
            "transition_signal"
        ]
        == expected
    )


def test_sequences_streaks_changes_reversals_and_persistence():
    toward_then_away = (
        module.build_fixture_state_summary(
            module.build_signal_transitions(
                history([
                    (
                        0.40,
                        0.35,
                        0.25,
                    ),
                    (
                        0.42,
                        0.34,
                        0.24,
                    ),
                    (
                        0.44,
                        0.33,
                        0.23,
                    ),
                    (
                        0.41,
                        0.35,
                        0.24,
                    ),
                ])
            )
        )
        .iloc[
            0
        ]
    )

    assert (
        toward_then_away[
            "signal_sequence"
        ]
        ==
        (
            "MARKET_TOWARD_AI -> "
            "MARKET_TOWARD_AI -> "
            "MARKET_AWAY_FROM_AI"
        )
    )

    assert (
        toward_then_away[
            "latest_signal_streak"
        ]
        == 1
    )

    assert (
        toward_then_away[
            "maximum_same_signal_streak"
        ]
        == 2
    )

    assert (
        toward_then_away[
            "signal_changed_count"
        ]
        == 1
    )

    assert bool(
        toward_then_away[
            "toward_to_away_reversal"
        ]
    )

    assert bool(
        toward_then_away[
            "any_directional_reversal"
        ]
    )

    assert bool(
        toward_then_away[
            "persistent_toward_ai"
        ]
    )

    away_then_toward = (
        module.build_fixture_state_summary(
            module.build_signal_transitions(
                history([
                    (
                        0.50,
                        0.30,
                        0.20,
                    ),
                    (
                        0.48,
                        0.31,
                        0.21,
                    ),
                    (
                        0.46,
                        0.32,
                        0.22,
                    ),
                    (
                        0.48,
                        0.31,
                        0.21,
                    ),
                ])
            )
        )
        .iloc[
            0
        ]
    )

    assert bool(
        away_then_toward[
            "away_to_toward_reversal"
        ]
    )

    assert bool(
        away_then_toward[
            "persistent_away_from_ai"
        ]
    )


def test_output_is_restricted_and_artifacts_unchanged(
    tmp_path,
    monkeypatch,
):
    before = hashes()

    monkeypatch.chdir(
        tmp_path
    )

    empty_transitions = pd.DataFrame(
        columns=
            module.TRANSITION_COLUMNS
    )

    empty_summary = pd.DataFrame(
        columns=
            module.SUMMARY_COLUMNS
    )

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        module.write_outputs(
            empty_transitions,
            empty_summary,
            Path(
                "outside.csv"
            ),
            Path(
                "experiments/summary.csv"
            ),
        )

    assert not Path(
        "outside.csv"
    ).exists()

    assert (
        hashes()
        == before
    )
