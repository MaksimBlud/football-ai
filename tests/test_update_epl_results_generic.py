import pandas as pd

import update_epl_results as updater


def sample_payload():
    return {
        "season": "2026/2027",
        "league": "EPL",
        "match_date": "2026-08-28",
        "match_time": "20:00",
        "home_team": "Crystal Palace",
        "away_team": "Manchester City",
        "home_goals": 1,
        "away_goals": 2,
        "result": "A",
    }


def test_build_generic_finished_results_contract():
    frame = (
        updater
        .build_generic_finished_results(
            [
                sample_payload()
            ]
        )
    )

    assert len(frame) == 1

    row = frame.iloc[0]

    assert row["league"] == "EPL"

    assert (
        row["season"]
        == "2026/2027"
    )

    assert (
        row["home_team"]
        == "Crystal Palace"
    )

    assert (
        row["away_team"]
        == "Manchester City"
    )

    assert row["home_goals"] == 1
    assert row["away_goals"] == 2
    assert row["result"] == "A"

    assert (
        row["source"]
        == "football-data.org"
    )

    assert (
        row["source_competition"]
        == "PL"
    )


def test_build_generic_finished_results_empty():
    frame = (
        updater
        .build_generic_finished_results(
            []
        )
    )

    assert isinstance(
        frame,
        pd.DataFrame,
    )

    assert frame.empty

    required = {
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    }

    assert required.issubset(
        frame.columns
    )


def test_generic_result_derived_result_contract():
    assert (
        updater.result_from_score(
            2,
            1,
        )
        == "H"
    )

    assert (
        updater.result_from_score(
            1,
            1,
        )
        == "D"
    )

    assert (
        updater.result_from_score(
            0,
            2,
        )
        == "A"
    )


def test_result_updater_uses_generic_persistence():
    source = open(
        "update_epl_results.py",
        encoding="utf-8",
    ).read()

    compact = "".join(
        source.split()
    )

    assert (
        "generic_persistence.persist_results("
        in compact
    )

    assert (
        "EPL_RUNTIME_CONFIG"
        in source
    )

    assert (
        'source"]="football-data.org"'
        in compact
    )
