from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

import analyze_challenger_shadow_history as analyzer
import classify_challenger_temporal_signals as module


ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)


def history_row(
    run,
    market,
    ai,
    home="Alpha",
    hours=24,
    status="OK",
):
    row = {
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
            hours,
    }

    for (
        outcome,
        market_value,
        ai_value,
    ) in zip(
        analyzer.OUTCOMES,
        market,
        ai,
    ):
        row[
            f"market_{outcome}_probability"
        ] = market_value

        row[
            f"ai_{outcome}_probability"
        ] = ai_value

    return row


def classify(
    first_market,
    latest_market,
    first_ai,
    latest_ai,
    home="Alpha",
):
    history = pd.DataFrame([
        history_row(
            "2026-08-22T06:00:00Z",
            first_market,
            first_ai,
            home,
            36,
        ),
        history_row(
            "2026-08-23T06:00:00Z",
            latest_market,
            latest_ai,
            home,
            12,
        ),
    ])

    return (
        module.build_temporal_signals(
            history
        )
        .iloc[
            0
        ]
    )


def artifact_hashes():
    return {
        path:
            sha256(
                Path(
                    path
                ).read_bytes()
            ).hexdigest()
        for path
        in ARTIFACTS
        if Path(
            path
        ).exists()
    }


def test_hold_empty_summary_and_readable_header_only_csv(
    tmp_path,
    monkeypatch,
    capsys,
):
    empty = (
        module.classify_movement_summary(
            analyzer.build_movement_summary(
                pd.DataFrame([
                    history_row(
                        "2026-08-22T06:00:00Z",
                        (
                            0.5,
                            0.3,
                            0.2,
                        ),
                        (
                            0.6,
                            0.2,
                            0.2,
                        ),
                    )
                ])
            )
        )
    )

    assert empty.empty

    assert (
        module.summary_report(
            empty
        )[
            "total_classified_fixtures"
        ]
        == 0
    )

    module.print_report(
        empty
    )

    assert (
        "HOLD"
        in capsys.readouterr().out
    )

    monkeypatch.chdir(
        tmp_path
    )

    output = Path(
        "experiments/empty.csv"
    )

    module.write_signals(
        empty,
        output,
    )

    loaded = pd.read_csv(
        output
    )

    assert loaded.empty

    assert (
        list(
            loaded.columns
        )
        == module.CLASSIFICATION_COLUMNS
    )


def test_toward_ai_strongest_selection_score_and_metadata():
    row = classify(
        (
            0.45,
            0.35,
            0.20,
        ),
        (
            0.47,
            0.34,
            0.19,
        ),
        (
            0.60,
            0.25,
            0.15,
        ),
        (
            0.58,
            0.25,
            0.17,
        ),
    )

    assert (
        row[
            "strongest_initial_disagreement_outcome"
        ]
        == "H"
    )

    assert (
        row[
            "strongest_initial_disagreement_signed_delta"
        ]
        == pytest.approx(
            0.15
        )
    )

    assert (
        row[
            "signed_toward_ai_score"
        ]
        == pytest.approx(
            0.02
        )
    )

    assert (
        row[
            "primary_signal"
        ]
        == "MARKET_TOWARD_AI"
    )

    assert (
        row[
            "ok_observations"
        ]
        == 2
    )

    assert (
        row[
            "first_hours_before_kickoff"
        ]
        == 36
    )

    assert (
        row[
            "latest_hours_before_kickoff"
        ]
        == 12
    )


def test_away_from_ai_and_negative_initial_delta_sign():
    row = classify(
        (
            0.60,
            0.25,
            0.15,
        ),
        (
            0.62,
            0.24,
            0.14,
        ),
        (
            0.40,
            0.35,
            0.25,
        ),
        (
            0.40,
            0.35,
            0.25,
        ),
    )

    assert (
        row[
            "strongest_initial_disagreement_outcome"
        ]
        == "H"
    )

    assert (
        row[
            "strongest_initial_disagreement_signed_delta"
        ]
        == pytest.approx(
            -0.20
        )
    )

    assert (
        row[
            "signed_toward_ai_score"
        ]
        == pytest.approx(
            -0.02
        )
    )

    assert (
        row[
            "primary_signal"
        ]
        == "MARKET_AWAY_FROM_AI"
    )


def test_insufficient_and_mixed_classifications():
    stable = classify(
        (
            0.50,
            0.30,
            0.20,
        ),
        (
            0.504,
            0.298,
            0.198,
        ),
        (
            0.60,
            0.20,
            0.20,
        ),
        (
            0.60,
            0.20,
            0.20,
        ),
    )

    mixed = classify(
        (
            0.50,
            0.30,
            0.20,
        ),
        (
            0.503,
            0.307,
            0.190,
        ),
        (
            0.60,
            0.20,
            0.20,
        ),
        (
            0.60,
            0.20,
            0.20,
        ),
    )

    assert (
        stable[
            "primary_signal"
        ]
        == "INSUFFICIENT_MOVEMENT"
    )

    assert (
        mixed[
            "primary_signal"
        ]
        == "MIXED_MOVEMENT"
    )


def test_disagreement_change_and_argmax_flags():
    increased = classify(
        (
            0.40,
            0.35,
            0.25,
        ),
        (
            0.30,
            0.32,
            0.38,
        ),
        (
            0.45,
            0.30,
            0.25,
        ),
        (
            0.20,
            0.50,
            0.30,
        ),
    )

    decreased = classify(
        (
            0.40,
            0.35,
            0.25,
        ),
        (
            0.44,
            0.31,
            0.25,
        ),
        (
            0.60,
            0.20,
            0.20,
        ),
        (
            0.50,
            0.30,
            0.20,
        ),
        "Gamma",
    )

    assert bool(
        increased[
            "disagreement_increased"
        ]
    )

    assert not bool(
        increased[
            "disagreement_decreased"
        ]
    )

    assert bool(
        increased[
            "latest_ai_market_argmax_disagreement"
        ]
    )

    assert bool(
        increased[
            "market_argmax_changed"
        ]
    )

    assert bool(
        increased[
            "ai_argmax_changed"
        ]
    )

    assert bool(
        decreased[
            "disagreement_decreased"
        ]
    )

    assert not bool(
        decreased[
            "disagreement_increased"
        ]
    )


def test_output_restricted_to_experiments(
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
        module.write_signals(
            pd.DataFrame(
                columns=
                    module.CLASSIFICATION_COLUMNS
            ),
            Path(
                "outside.csv"
            ),
        )


def test_production_artifact_hashes_unchanged(
    tmp_path,
    monkeypatch,
):
    before = (
        artifact_hashes()
    )

    monkeypatch.chdir(
        tmp_path
    )

    module.write_signals(
        pd.DataFrame(
            columns=
                module.CLASSIFICATION_COLUMNS
        )
    )

    monkeypatch.undo()

    assert (
        artifact_hashes()
        == before
    )
