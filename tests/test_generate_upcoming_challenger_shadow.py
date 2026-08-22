from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import generate_upcoming_challenger_shadow as module


KICKOFF = "2026-08-23T14:00:00Z"


def upcoming(
    home="Arsenal",
    away="Chelsea",
):
    return pd.DataFrame([
        {
            "match_date":
                "2026-08-23",

            "match_time":
                "15:00",

            "match_datetime_uk":
                KICKOFF,

            "home_team":
                home,

            "away_team":
                away,
        }
    ])


def snapshot(
    home="Arsenal",
    away="Chelsea",
    time="2026-08-23T12:00:00Z",
):
    return {
        "snapshot_time_utc":
            time,

        "commence_time_utc":
            KICKOFF,

        "home_team":
            home,

        "away_team":
            away,

        "home_odds":
            2.0,

        "draw_odds":
            3.0,

        "away_odds":
            4.0,
    }


def fake_predictor(**kwargs):
    market = {
        "prediction":
            "HOME",

        "home_probability":
            0.5,

        "draw_probability":
            0.3,

        "away_probability":
            0.2,
    }

    ai = {
        "prediction":
            "AWAY",

        "home_probability":
            0.4,

        "draw_probability":
            0.25,

        "away_probability":
            0.35,
    }

    return {
        "market":
            market,

        "ai":
            ai,

        "delta": {
            "home":
                -0.1,

            "draw":
                -0.05,

            "away":
                0.15,
        },

        "strongest_disagreement": {
            "outcome":
                "AWAY",

            "delta":
                0.15,

            "absolute_delta":
                0.15,
        },

        "challenger": {
            "prediction":
                "HOME",

            "home_probability":
                0.5,

            "draw_probability":
                0.3,

            "away_probability":
                0.2,

            "adjustment_weight":
                0.0,

            "probability_source":
                "MARKET_PRIOR_V0",
        },

        "shadow_only":
            True,
    }


def test_exact_team_and_kickoff_match():
    matched = (
        module.match_odds_to_upcoming(
            upcoming(),
            pd.DataFrame([
                snapshot()
            ]),
        )
    )

    assert (
        matched.loc[
            0,
            "home_odds",
        ]
        == 2.0
    )


def test_team_name_normalization_match():
    matched = (
        module.match_odds_to_upcoming(
            upcoming(
                "Manchester City",
                "Tottenham Hotspur",
            ),
            pd.DataFrame([
                snapshot(
                    "Man City",
                    "Tottenham",
                )
            ]),
        )
    )

    assert (
        matched.loc[
            0,
            "away_odds",
        ]
        == 4.0
    )


def test_latest_eligible_pre_kickoff_snapshot_is_selected():
    records = [
        snapshot(
            time=(
                "2026-08-23"
                "T10:00:00Z"
            )
        ),
        {
            **snapshot(
                time=(
                    "2026-08-23"
                    "T13:59:00Z"
                )
            ),
            "home_odds":
                1.8,
        },
    ]

    matched = (
        module.match_odds_to_upcoming(
            upcoming(),
            pd.DataFrame(
                records
            ),
        )
    )

    assert (
        matched.loc[
            0,
            "home_odds",
        ]
        == 1.8
    )

    assert (
        matched.loc[
            0,
            "snapshot_time_utc",
        ]
        == pd.Timestamp(
            "2026-08-23T13:59:00Z"
        )
    )


@pytest.mark.parametrize(
    "time",
    [
        KICKOFF,
        "2026-08-23T14:01:00Z",
    ],
)
def test_at_or_post_kickoff_snapshot_is_rejected(
    time,
):
    matched = (
        module.match_odds_to_upcoming(
            upcoming(),
            pd.DataFrame([
                snapshot(
                    time=time
                )
            ]),
        )
    )

    assert pd.isna(
        matched.loc[
            0,
            "snapshot_time_utc",
        ]
    )


def test_missing_odds_remains_with_no_market_status():
    results = (
        module.build_shadow_results(
            upcoming(),
            pd.DataFrame(
                columns=module.ODDS_COLUMNS
            ),
            fake_predictor,
        )
    )

    assert len(
        results
    ) == 1

    assert (
        results.loc[
            0,
            "shadow_status",
        ]
        == "NO_MARKET_ODDS"
    )


def test_successful_challenger_v0_row():
    results = (
        module.build_shadow_results(
            upcoming(),
            pd.DataFrame([
                snapshot()
            ]),
            fake_predictor,
        )
    )

    row = results.iloc[
        0
    ]

    assert (
        row["shadow_status"]
        == "OK"
    )

    market = row[
        [
            f"market_{x}_probability"
            for x in (
                "home",
                "draw",
                "away",
            )
        ]
    ].to_numpy(
        float
    )

    challenger = row[
        [
            f"challenger_{x}_probability"
            for x in (
                "home",
                "draw",
                "away",
            )
        ]
    ].to_numpy(
        float
    )

    assert np.isfinite(
        challenger
    ).all()

    assert (
        challenger.sum()
        == pytest.approx(
            1.0
        )
    )

    assert (
        challenger
        == pytest.approx(
            market
        )
    )

    assert (
        row[
            "challenger_probability_source"
        ]
        == "MARKET_PRIOR_V0"
    )

    assert (
        row[
            "challenger_adjustment_weight"
        ]
        == 0.0
    )


def test_invalid_odds_are_rejected():
    bad = snapshot()

    bad[
        "home_odds"
    ] = 1.0

    matched = (
        module.match_odds_to_upcoming(
            upcoming(),
            pd.DataFrame([
                bad
            ]),
        )
    )

    assert pd.isna(
        matched.loc[
            0,
            "snapshot_time_utc",
        ]
    )


def test_output_is_written_only_under_experiments(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    results = pd.DataFrame([
        {
            "shadow_status":
                "NO_MARKET_ODDS"
        }
    ])

    module.write_shadow_results(
        results,
        Path(
            "experiments/shadow.csv"
        ),
    )

    assert (
        tmp_path
        / "experiments"
        / "shadow.csv"
    ).exists()

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        module.write_shadow_results(
            results,
            Path(
                "elsewhere/shadow.csv"
            ),
        )


def test_production_artifact_hashes_remain_unchanged(
    tmp_path,
):
    artifact = (
        tmp_path
        / module.PRODUCTION_ARTIFACTS[0]
    )

    artifact.write_bytes(
        b"production"
    )

    before = (
        module.hash_production_artifacts(
            tmp_path
        )
    )

    module.build_shadow_results(
        upcoming(),
        pd.DataFrame([
            snapshot()
        ]),
        fake_predictor,
    )

    after = (
        module.hash_production_artifacts(
            tmp_path
        )
    )

    assert (
        after
        == before
    )


def test_past_matches_are_excluded_from_upcoming_shadow():
    frame = pd.DataFrame([
        {
            "match_date": "2026-08-21",
            "match_time": "20:00",
            "match_datetime_uk": "2026-08-21T19:00:00Z",
            "home_team": "Arsenal",
            "away_team": "Coventry City",
        },
        {
            "match_date": "2026-08-23",
            "match_time": "14:00",
            "match_datetime_uk": "2026-08-23T13:00:00Z",
            "home_team": "Manchester City",
            "away_team": "AFC Bournemouth",
        },
    ])

    prepared = module.prepare_upcoming_matches(
        frame,
        now="2026-08-22T06:00:00Z",
    )

    assert len(prepared) == 1
    assert prepared.iloc[0]["home_team"] == "Manchester City"


def test_generated_at_utc_is_attached_to_every_shadow_row():
    results = module.build_shadow_results(
        upcoming(),
        pd.DataFrame([
            snapshot()
        ]),
        fake_predictor,
        generated_at_utc="2026-08-22T06:30:00Z",
    )

    assert len(results) == 1

    assert (
        results.loc[
            0,
            "generated_at_utc",
        ]
        == "2026-08-22T06:30:00+00:00"
    )


def test_shadow_history_appends_rows(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    first = pd.DataFrame([
        {
            "shadow_status": "OK",
            "generated_at_utc": "2026-08-22T06:00:00+00:00",
        }
    ])

    second = pd.DataFrame([
        {
            "shadow_status": "NO_MARKET_ODDS",
            "generated_at_utc": "2026-08-22T07:00:00+00:00",
        }
    ])

    history = Path(
        "experiments/shadow_history.csv"
    )

    module.append_shadow_history(
        first,
        history,
    )

    module.append_shadow_history(
        second,
        history,
    )

    saved = pd.read_csv(
        history
    )

    assert len(saved) == 2

    assert saved[
        "generated_at_utc"
    ].tolist() == [
        "2026-08-22T06:00:00+00:00",
        "2026-08-22T07:00:00+00:00",
    ]


def test_shadow_history_is_experiments_only(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    results = pd.DataFrame([
        {
            "shadow_status": "OK",
            "generated_at_utc": "2026-08-22T06:00:00+00:00",
        }
    ])

    with pytest.raises(
        ValueError,
        match="experiments",
    ):
        module.append_shadow_history(
            results,
            Path("elsewhere/history.csv"),
        )
