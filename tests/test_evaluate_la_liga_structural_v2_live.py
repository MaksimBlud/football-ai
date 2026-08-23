import pandas as pd

import evaluate_la_liga_structural_v2_live as live


def history_rows():
    return pd.DataFrame([
        {
            "event_id": "x",
            "commence_time_utc":
                "2030-01-02T12:00:00+00:00",
            "recorded_at_utc":
                "2030-01-01T10:00:00+00:00",
            "snapshot_time_utc":
                "2030-01-01T09:00:00+00:00",
            "pre_kickoff_valid": True,
            "home_team": "A",
            "away_team": "B",
            "correction_enabled": True,
            "market_home_probability": 0.50,
            "market_draw_probability": 0.30,
            "market_away_probability": 0.20,
            "shadow_home_probability": 0.52,
            "shadow_draw_probability": 0.29,
            "shadow_away_probability": 0.19,
        },
        {
            "event_id": "x",
            "commence_time_utc":
                "2030-01-02T12:00:00+00:00",
            "recorded_at_utc":
                "2030-01-02T10:00:00+00:00",
            "snapshot_time_utc":
                "2030-01-02T09:00:00+00:00",
            "pre_kickoff_valid": True,
            "home_team": "A",
            "away_team": "B",
            "correction_enabled": True,
            "market_home_probability": 0.51,
            "market_draw_probability": 0.29,
            "market_away_probability": 0.20,
            "shadow_home_probability": 0.53,
            "shadow_draw_probability": 0.28,
            "shadow_away_probability": 0.19,
        },
    ])


def test_latest_pre_kickoff_is_selected():
    result = (
        live.latest_pre_kickoff(
            history_rows()
        )
    )

    assert len(result) == 1

    assert (
        result.iloc[0][
            "recorded_at_utc"
        ].hour
        == 10
    )

    assert (
        result.iloc[0][
            "market_home_probability"
        ]
        == 0.51
    )


def test_result_matching():
    observations = (
        live.latest_pre_kickoff(
            history_rows()
        )
    )

    results = pd.DataFrame([
        {
            "match_date":
                "2030-01-02",
            "match_time":
                "12:00",
            "home_team":
                "A",
            "away_team":
                "B",
            "home_goals":
                2,
            "away_goals":
                1,
            "result":
                "H",
        }
    ])

    settled = live.match_results(
        observations,
        results,
    )

    assert len(settled) == 1
    assert (
        settled.iloc[0][
            "target"
        ]
        == 0
    )


def test_empty_evaluation_waits():
    result = live.evaluate(
        pd.DataFrame()
    )

    assert (
        result["status"]
        == "NO_SETTLED_MATCHES"
    )


def test_live_metrics_compare_market_and_v2():
    settled = (
        live.latest_pre_kickoff(
            history_rows()
        )
    )

    settled["target"] = 0

    report = live.evaluate(
        settled
    )

    assert (
        report["status"]
        == "EVALUATED"
    )

    assert (
        report["settled_matches"]
        == 1
    )

    assert (
        "logloss_gap"
        in report[
            "all_matches"
        ]
    )
