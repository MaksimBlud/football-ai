from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

import derive_challenger_decision_states as module


ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        1
    ]
)


def hashes():
    return {
        name:
            sha256(
                (
                    ROOT
                    / name
                ).read_bytes()
            ).hexdigest()

        for name in ARTIFACTS

        if (
            ROOT
            / name
        ).exists()
    }


def summary(
    sequence,
    **overrides,
):
    signals = (
        sequence.split(
            " -> "
        )
        if sequence
        else []
    )

    adjacent = list(
        zip(
            signals,
            signals[
                1:
            ],
        )
    )

    data = {
        "home_team":
            "Alpha",

        "away_team":
            "Beta",

        "commence_time_utc":
            "2026-08-24T18:00:00Z",

        "valid_ok_observations":
            len(signals) + 1,

        "transition_count":
            len(signals),

        "signal_sequence":
            sequence,

        "latest_signal":
            (
                signals[
                    -1
                ]
                if signals
                else pd.NA
            ),

        "latest_signed_toward_ai_score":
            0.0,

        "latest_signal_streak":
            1,

        "maximum_same_signal_streak":
            1,

        "signal_changed_count":
            sum(
                a != b
                for (
                    a,
                    b,
                )
                in adjacent
            ),

        "toward_to_away_reversal":
            (
                (
                    "MARKET_TOWARD_AI",
                    "MARKET_AWAY_FROM_AI",
                )
                in adjacent
            ),

        "away_to_toward_reversal":
            (
                (
                    "MARKET_AWAY_FROM_AI",
                    "MARKET_TOWARD_AI",
                )
                in adjacent
            ),

        "persistent_toward_ai":
            (
                "MARKET_TOWARD_AI -> MARKET_TOWARD_AI"
                in sequence
            ),

        "persistent_away_from_ai":
            (
                "MARKET_AWAY_FROM_AI -> MARKET_AWAY_FROM_AI"
                in sequence
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
    }

    data[
        "any_directional_reversal"
    ] = (
        data[
            "toward_to_away_reversal"
        ]
        or data[
            "away_to_toward_reversal"
        ]
    )

    data.update(
        overrides
    )

    return pd.DataFrame([
        data
    ])


def state(
    sequence,
    **overrides,
):
    return (
        module.derive_decision_states(
            summary(
                sequence,
                **overrides,
            )
        )
        .iloc[
            0
        ]
    )


def test_hold_and_header_only_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    states = (
        module.derive_decision_states(
            pd.DataFrame()
        )
    )

    module.print_report(
        states
    )

    assert (
        "HOLD"
        in capsys.readouterr().out
    )

    monkeypatch.chdir(
        tmp_path
    )

    module.write_decision_states(
        states
    )

    loaded = pd.read_csv(
        module.DEFAULT_OUTPUT
    )

    assert loaded.empty

    assert (
        list(
            loaded.columns
        )
        == module.OUTPUT_COLUMNS
    )


@pytest.mark.parametrize(
    "sequence, expected",
    [
        (
            "INSUFFICIENT_MOVEMENT",
            "STABLE_NO_EDGE",
        ),
        (
            "MARKET_TOWARD_AI",
            "EARLY_CONFIRMATION",
        ),
        (
            "MARKET_AWAY_FROM_AI",
            "EARLY_REJECTION",
        ),
        (
            "MARKET_TOWARD_AI -> INSUFFICIENT_MOVEMENT",
            "FADED_CONFIRMATION",
        ),
        (
            "MARKET_AWAY_FROM_AI -> INSUFFICIENT_MOVEMENT",
            "FADED_REJECTION",
        ),
        (
            "MARKET_TOWARD_AI -> MARKET_AWAY_FROM_AI",
            "REVERSAL_AWAY_FROM_AI",
        ),
        (
            "MARKET_AWAY_FROM_AI -> MARKET_TOWARD_AI",
            "REVERSAL_TO_AI",
        ),
        (
            "MIXED_MOVEMENT",
            "MIXED_WATCH",
        ),
    ],
)
def test_required_state_scenarios(
    sequence,
    expected,
):
    assert (
        state(
            sequence
        )[
            "decision_state"
        ]
        == expected
    )


def test_reversal_has_deterministic_priority_over_persistence():
    result = state(
        "MARKET_TOWARD_AI -> "
        "MARKET_TOWARD_AI -> "
        "MARKET_AWAY_FROM_AI"
    )

    assert (
        result[
            "decision_state"
        ]
        == "REVERSAL_AWAY_FROM_AI"
    )


@pytest.mark.parametrize(
    "sequence, bias",
    [
        (
            "MARKET_TOWARD_AI",
            "TOWARD_AI",
        ),
        (
            "MARKET_AWAY_FROM_AI",
            "AWAY_FROM_AI",
        ),
        (
            "MIXED_MOVEMENT",
            "NONE",
        ),
    ],
)
def test_directional_bias(
    sequence,
    bias,
):
    assert (
        state(
            sequence
        )[
            "directional_bias"
        ]
        == bias
    )


def test_state_strength_counts_consecutive_supporting_transitions():
    active = state(
        "MARKET_TOWARD_AI -> "
        "MARKET_TOWARD_AI"
    )

    faded = state(
        "MARKET_AWAY_FROM_AI -> "
        "INSUFFICIENT_MOVEMENT"
    )

    assert (
        active[
            "state_strength"
        ]
        == 2
    )

    assert (
        faded[
            "state_strength"
        ]
        == 1
    )


def test_output_is_restricted_to_experiments(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        module.write_decision_states(
            module.derive_decision_states(
                pd.DataFrame()
            ),
            Path(
                "outside.csv"
            ),
        )


def test_production_hashes_unchanged(
    tmp_path,
    monkeypatch,
):
    before = hashes()

    monkeypatch.chdir(
        tmp_path
    )

    module.write_decision_states(
        module.derive_decision_states(
            summary(
                "MARKET_TOWARD_AI"
            )
        )
    )

    assert (
        hashes()
        == before
    )
