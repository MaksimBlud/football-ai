from pathlib import Path

import pandas as pd
import pytest

import analyze_challenger_shadow_history as module


def row(
    run,
    home="Alpha",
    away="Beta",
    status="OK",
    market=(0.5, 0.3, 0.2),
    ai=(0.4, 0.3, 0.3),
    hours=24,
):
    return {
        "home_team":
            home,

        "away_team":
            away,

        "commence_time_utc":
            "2026-08-24T18:00:00Z",

        "generated_at_utc":
            run,

        "shadow_status":
            status,

        "hours_before_kickoff":
            hours,

        **{
            f"market_{name}_probability":
                value
            for (
                name,
                value,
            )
            in zip(
                module.OUTCOMES,
                market,
            )
        },

        **{
            f"ai_{name}_probability":
                value
            for (
                name,
                value,
            )
            in zip(
                module.OUTCOMES,
                ai,
            )
        },
    }


def loaded(
    tmp_path,
    rows,
):
    path = (
        tmp_path
        / "history.csv"
    )

    pd.DataFrame(
        rows
    ).to_csv(
        path,
        index=False,
    )

    return module.load_history(
        path
    )


def test_one_run_holds_but_validates(
    tmp_path,
):
    report, summary = (
        module.analyze_history(
            loaded(
                tmp_path,
                [
                    row(
                        "2026-08-22T06:00:00Z"
                    )
                ],
            )
        )
    )

    assert (
        report[
            "hold"
        ]
        is True
    )

    assert (
        report[
            "unique_shadow_runs"
        ]
        == 1
    )

    assert summary.empty


def test_schema_and_generated_timestamp_validation(
    tmp_path,
):
    bad = row(
        "not-a-time"
    )

    with pytest.raises(
        ValueError,
        match="generated_at_utc",
    ):
        loaded(
            tmp_path,
            [
                bad
            ],
        )

    del bad[
        "home_team"
    ]

    with pytest.raises(
        ValueError,
        match="home_team",
    ):
        loaded(
            tmp_path,
            [
                bad
            ],
        )


def test_multi_run_grouping_movement_argmax_and_no_market_ignored(
    tmp_path,
):
    rows = [
        row(
            "2026-08-22T06:00:00Z",
            market=(
                0.6,
                0.25,
                0.15,
            ),
            ai=(
                0.7,
                0.2,
                0.1,
            ),
            hours=30,
        ),
        row(
            "2026-08-22T12:00:00Z",
            status="NO_MARKET_ODDS",
            market=(
                0.01,
                0.98,
                0.01,
            ),
            ai=(
                0.01,
                0.98,
                0.01,
            ),
            hours=24,
        ),
        row(
            "2026-08-23T06:00:00Z",
            market=(
                0.3,
                0.25,
                0.45,
            ),
            ai=(
                0.2,
                0.6,
                0.2,
            ),
            hours=6,
        ),
        row(
            "2026-08-22T06:00:00Z",
            home="Gamma",
            away="Delta",
            market=(
                0.4,
                0.3,
                0.3,
            ),
            ai=(
                0.6,
                0.2,
                0.2,
            ),
        ),
        row(
            "2026-08-23T06:00:00Z",
            home="Gamma",
            away="Delta",
            market=(
                0.4,
                0.3,
                0.3,
            ),
            ai=(
                0.45,
                0.3,
                0.25,
            ),
        ),
    ]

    report, summary = (
        module.analyze_history(
            loaded(
                tmp_path,
                rows,
            )
        )
    )

    assert (
        report[
            "fixtures_observed"
        ]
        == 2
    )

    assert (
        report[
            "fixtures_with_at_least_2_observations"
        ]
        == 2
    )

    assert (
        report[
            "status_counts_by_run"
        ][
            pd.Timestamp(
                "2026-08-22T12:00:00Z"
            )
        ][
            "NO_MARKET_ODDS"
        ]
        == 1
    )

    alpha = (
        summary.loc[
            summary[
                "home_team"
            ].eq(
                "Alpha"
            )
        ]
        .iloc[
            0
        ]
    )

    assert (
        alpha[
            "ok_observations"
        ]
        == 2
    )

    assert (
        alpha[
            "market_home_movement"
        ]
        == pytest.approx(
            -0.3
        )
    )

    assert (
        alpha[
            "maximum_absolute_market_movement"
        ]
        == pytest.approx(
            0.3
        )
    )

    assert (
        alpha[
            "first_ai_minus_market_home"
        ]
        == pytest.approx(
            0.1
        )
    )

    assert (
        alpha[
            "latest_ai_minus_market_draw"
        ]
        == pytest.approx(
            0.35
        )
    )

    assert (
        alpha[
            "change_in_strongest_disagreement_absolute_delta"
        ]
        == pytest.approx(
            0.25
        )
    )

    assert (
        bool(
            alpha[
                "market_argmax_changed"
            ]
        )
    )

    assert (
        bool(
            alpha[
                "ai_argmax_changed"
            ]
        )
    )

    assert (
        bool(
            alpha[
                "market_ai_agreement_changed"
            ]
        )
    )

    assert (
        alpha[
            "first_hours_before_kickoff"
        ]
        == 30
    )

    assert (
        alpha[
            "latest_hours_before_kickoff"
        ]
        == 6
    )

    gamma = (
        summary.loc[
            summary[
                "home_team"
            ].eq(
                "Gamma"
            )
        ]
        .iloc[
            0
        ]
    )

    assert (
        gamma[
            "change_in_strongest_disagreement_absolute_delta"
        ]
        == pytest.approx(
            -0.15
        )
    )

    ranked = (
        module.ranked_summaries(
            summary
        )
    )

    assert (
        ranked[
            "largest_disagreement_increase"
        ][
            "home_team"
        ].tolist()
        == [
            "Alpha"
        ]
    )

    assert (
        ranked[
            "largest_disagreement_decrease"
        ][
            "home_team"
        ].tolist()
        == [
            "Gamma"
        ]
    )

    assert (
        ranked[
            "market_argmax_changed"
        ][
            "home_team"
        ].tolist()
        == [
            "Alpha"
        ]
    )

    assert (
        ranked[
            "latest_ai_market_disagreement"
        ][
            "home_team"
        ].tolist()
        == [
            "Alpha"
        ]
    )


def test_output_must_be_under_experiments(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    summary = pd.DataFrame([
        {
            "fixture":
                "example"
        }
    ])

    module.write_summary(
        summary,
        Path(
            "experiments/summary.csv"
        ),
    )

    assert (
        tmp_path
        / "experiments"
        / "summary.csv"
    ).is_file()

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        module.write_summary(
            summary,
            Path(
                "outside.csv"
            ),
        )


def test_empty_hold_summary_writes_readable_header_only_csv(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    history = pd.DataFrame([
        row("2026-08-22T06:00:00Z")
    ])

    history["generated_at_utc"] = pd.to_datetime(
        history["generated_at_utc"],
        utc=True,
    )

    report, summary = module.analyze_history(history)

    assert report["hold"] is True
    assert summary.empty
    assert list(summary.columns) == module.SUMMARY_COLUMNS

    output = Path(
        "experiments/empty_summary.csv"
    )

    module.write_summary(
        summary,
        output,
    )

    loaded = pd.read_csv(output)

    assert loaded.empty
    assert list(loaded.columns) == module.SUMMARY_COLUMNS
