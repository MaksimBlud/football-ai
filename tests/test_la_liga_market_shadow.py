from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

import generate_la_liga_market_shadow as market


def upcoming():
    return pd.DataFrame([
        {
            "league":
                "LA_LIGA",

            "event_id":
                "event-1",

            "home_team":
                "Barcelona",

            "away_team":
                "Real Madrid",

            "commence_time_utc":
                pd.Timestamp(
                    "2030-01-02T20:00:00Z"
                ),
        }
    ])


def snapshots(
    home=2.0,
    draw=4.0,
    away=4.0,
):
    return pd.DataFrame([
        {
            "league":
                "LA_LIGA",

            "event_id":
                "event-1",

            "snapshot_time_utc":
                "2030-01-01T20:00:00Z",

            "commence_time_utc":
                "2030-01-02T20:00:00Z",

            "home_team":
                "Barcelona",

            "away_team":
                "Real Madrid",

            "home_odds":
                home,

            "draw_odds":
                draw,

            "away_odds":
                away,
        }
    ])


def test_probabilities_are_devigged():
    home, draw, away = (
        market.normalized_market_probabilities(
            2.0,
            4.0,
            4.0,
        )
    )

    assert home == pytest.approx(
        0.5
    )

    assert draw == pytest.approx(
        0.25
    )

    assert away == pytest.approx(
        0.25
    )

    assert (
        home + draw + away
    ) == pytest.approx(
        1.0
    )


def test_market_shadow_uses_no_ai_fields():
    result = market.build_market_shadow(
        upcoming(),
        snapshots(),
        generated_at_utc=datetime(
            2030,
            1,
            1,
            21,
            tzinfo=timezone.utc,
        ),
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row[
            "market_shadow_status"
        ]
        == "OK"
    )

    assert bool(
        row["market_only"]
    ) is True

    assert (
        row[
            "market_argmax"
        ]
        == "H"
    )

    assert not any(
        column.startswith("ai_")
        for column in result.columns
    )


def test_second_run_calculates_market_movement():
    first_snapshots = snapshots(
        2.0,
        4.0,
        4.0,
    )

    first = market.build_market_shadow(
        upcoming(),
        first_snapshots,
        generated_at_utc=datetime(
            2030,
            1,
            1,
            20,
            tzinfo=timezone.utc,
        ),
    )

    second_snapshots = snapshots(
        1.8,
        4.2,
        4.4,
    )

    second_snapshots[
        "snapshot_time_utc"
    ] = "2030-01-01T20:30:00Z"

    second = market.build_market_shadow(
        upcoming(),
        second_snapshots,
        previous_history=first,
        generated_at_utc=datetime(
            2030,
            1,
            1,
            21,
            tzinfo=timezone.utc,
        ),
    )

    row = second.iloc[0]

    assert pd.notna(
        row[
            "maximum_absolute_market_movement"
        ]
    )

    assert (
        row[
            "maximum_absolute_market_movement"
        ]
        > 0
    )

def test_non_la_liga_snapshot_rejected():
    frame = snapshots()
    frame.loc[
        0,
        "league",
    ] = "EPL"

    with pytest.raises(
        ValueError
    ):
        market.prepare_snapshots(
            frame
        )


def test_post_kickoff_snapshot_is_excluded():
    frame = snapshots()

    frame.loc[
        0,
        "snapshot_time_utc",
    ] = "2030-01-03T20:00:00Z"

    prepared = (
        market.prepare_snapshots(
            frame
        )
    )

    assert prepared.empty


def test_output_is_restricted_to_experiments(
    tmp_path,
):
    result = market.build_market_shadow(
        upcoming(),
        snapshots(),
    )

    with pytest.raises(
        ValueError
    ):
        market.write_outputs(
            result,
            latest_path=(
                tmp_path
                / "outside.csv"
            ),
            history_path=(
                tmp_path
                / "outside_history.csv"
            ),
        )


def test_history_append_only(
    tmp_path,
    monkeypatch,
):
    experiments = (
        tmp_path
        / "experiments"
    )

    experiments.mkdir()

    monkeypatch.chdir(
        tmp_path
    )

    first_snapshots = snapshots()

    first = market.build_market_shadow(
        upcoming(),
        first_snapshots,
        generated_at_utc=datetime(
            2030,
            1,
            1,
            20,
            tzinfo=timezone.utc,
        ),
    )

    second_snapshots = snapshots()

    second_snapshots[
        "snapshot_time_utc"
    ] = "2030-01-01T20:30:00Z"

    second = market.build_market_shadow(
        upcoming(),
        second_snapshots,
        previous_history=first,
        generated_at_utc=datetime(
            2030,
            1,
            1,
            21,
            tzinfo=timezone.utc,
        ),
    )

    latest_path = Path(
        "experiments/latest.csv"
    )

    history_path = Path(
        "experiments/history.csv"
    )

    market.write_outputs(
        first,
        latest_path=latest_path,
        history_path=history_path,
    )

    combined = market.write_outputs(
        second,
        latest_path=latest_path,
        history_path=history_path,
    )

    assert len(combined) == 2

    assert (
        combined[
            "snapshot_time_utc"
        ].nunique()
        == 2
    )

def test_same_market_snapshot_does_not_create_movement():
    first = market.build_market_shadow(
        upcoming(),
        snapshots(),
        generated_at_utc=datetime(
            2030,
            1,
            1,
            20,
            tzinfo=timezone.utc,
        ),
    )

    second = market.build_market_shadow(
        upcoming(),
        snapshots(),
        previous_history=first,
        generated_at_utc=datetime(
            2030,
            1,
            1,
            21,
            tzinfo=timezone.utc,
        ),
    )

    row = second.iloc[0]

    assert pd.isna(
        row[
            "maximum_absolute_market_movement"
        ]
    )


def test_floating_point_noise_is_zeroed():
    previous = market.build_market_shadow(
        upcoming(),
        snapshots(),
        generated_at_utc=datetime(
            2030,
            1,
            1,
            19,
            tzinfo=timezone.utc,
        ),
    )

    current_snapshots = snapshots()
    current_snapshots.loc[
        0,
        "snapshot_time_utc",
    ] = "2030-01-01T21:00:00Z"

    current = market.build_market_shadow(
        upcoming(),
        current_snapshots,
        previous_history=previous,
        generated_at_utc=datetime(
            2030,
            1,
            1,
            22,
            tzinfo=timezone.utc,
        ),
    )

    row = current.iloc[0]

    assert (
        row[
            "market_home_movement"
        ]
        == 0.0
    )

    assert (
        row[
            "market_draw_movement"
        ]
        == 0.0
    )

    assert (
        row[
            "market_away_movement"
        ]
        == 0.0
    )

    assert (
        row[
            "maximum_absolute_market_movement"
        ]
        == 0.0
    )


def test_repeated_shadow_write_does_not_duplicate_observation(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    Path(
        "experiments"
    ).mkdir()

    run = market.build_market_shadow(
        upcoming(),
        snapshots(),
        generated_at_utc=datetime(
            2030,
            1,
            1,
            20,
            tzinfo=timezone.utc,
        ),
    )

    latest_path = Path(
        "experiments/latest.csv"
    )

    history_path = Path(
        "experiments/history.csv"
    )

    market.write_outputs(
        run,
        latest_path=latest_path,
        history_path=history_path,
    )

    combined = market.write_outputs(
        run,
        latest_path=latest_path,
        history_path=history_path,
    )

    assert len(combined) == 1
