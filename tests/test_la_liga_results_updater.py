from pathlib import Path

import pandas as pd
import pytest

import la_liga_results_updater as updater


def source_frame():
    return pd.DataFrame([
        {
            "Div": "SP1",
            "Date": "15/08/2026",
            "Time": "20:00",
            "HomeTeam": "Ath Madrid",
            "AwayTeam": "Betis",
            "FTHG": 2,
            "FTAG": 1,
            "FTR": "H",
        },
        {
            "Div": "SP1",
            "Date": "16/08/2026",
            "Time": "18:00",
            "HomeTeam": "Osasuna",
            "AwayTeam": "Barcelona",
            "FTHG": None,
            "FTAG": None,
            "FTR": None,
        },
    ])


def test_finished_only_and_aliases():
    result = updater.normalize_source(
        source_frame(),
        updated_at_utc=(
            "2026-08-16T00:00:00+00:00"
        ),
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row["home_team"]
        == "Atlético Madrid"
    )

    assert (
        row["away_team"]
        == "Real Betis"
    )

    assert (
        row["result"]
        == "H"
    )

    assert (
        row["season"]
        == "2026-2027"
    )

    assert (
        row["league"]
        == "LA_LIGA"
    )


def test_result_derived_from_goals():
    assert (
        updater.result_from_goals(
            3,
            1,
        )
        == "H"
    )

    assert (
        updater.result_from_goals(
            1,
            1,
        )
        == "D"
    )

    assert (
        updater.result_from_goals(
            0,
            1,
        )
        == "A"
    )


def test_conflicting_ftr_rejected():
    frame = source_frame().iloc[
        [0]
    ].copy()

    frame.loc[
        frame.index[0],
        "FTR",
    ] = "A"

    with pytest.raises(
        updater.ResultsSourceError
    ):
        updater.normalize_source(
            frame
        )


def test_unknown_team_rejected():
    frame = source_frame().iloc[
        [0]
    ].copy()

    frame.loc[
        frame.index[0],
        "HomeTeam",
    ] = "Imaginary FC"

    with pytest.raises(
        updater.UnknownTeamError
    ):
        updater.normalize_source(
            frame
        )


def test_duplicate_source_deduplicated():
    frame = pd.concat(
        [
            source_frame().iloc[
                [0]
            ],
            source_frame().iloc[
                [0]
            ],
        ],
        ignore_index=True,
    )

    result = updater.normalize_source(
        frame
    )

    assert len(result) == 1


def test_conflicting_source_duplicate_rejected():
    first = source_frame().iloc[
        [0]
    ].copy()

    second = first.copy()

    second["FTHG"] = 0
    second["FTAG"] = 1
    second["FTR"] = "A"

    frame = pd.concat(
        [
            first,
            second,
        ],
        ignore_index=True,
    )

    with pytest.raises(
        updater.ResultsConflictError
    ):
        updater.normalize_source(
            frame
        )


def test_idempotent_update(tmp_path):
    path = (
        tmp_path
        / "results.csv"
    )

    first = updater.update_results(
        output_path=path,
        source_frame=source_frame(),
    )

    before = path.read_bytes()

    second = updater.update_results(
        output_path=path,
        source_frame=source_frame(),
    )

    after = path.read_bytes()

    assert first[
        "new_rows"
    ] == 1

    assert second[
        "new_rows"
    ] == 0

    assert second[
        "unchanged_rows"
    ] == 1

    assert before == after


def test_existing_conflict_rejected(
    tmp_path,
):
    path = (
        tmp_path
        / "results.csv"
    )

    updater.update_results(
        output_path=path,
        source_frame=source_frame(),
    )

    conflict = source_frame().iloc[
        [0]
    ].copy()

    conflict["FTHG"] = 0
    conflict["FTAG"] = 2
    conflict["FTR"] = "A"

    with pytest.raises(
        updater.ResultsConflictError
    ):
        updater.update_results(
            output_path=path,
            source_frame=conflict,
        )


def test_no_finished_matches_is_wait(
    tmp_path,
):
    frame = source_frame().iloc[
        [1]
    ].copy()

    report = updater.update_results(
        output_path=(
            tmp_path
            / "results.csv"
        ),
        source_frame=frame,
    )

    assert (
        report["status"]
        == "WAIT"
    )

    assert (
        report["detail"]
        == "NO_FINISHED_MATCHES"
    )

def test_current_football_data_deportivo_alias():
    frame = pd.DataFrame([
        {
            "Div": "SP1",
            "Date": "20/08/2026",
            "Time": "20:00",
            "HomeTeam": "Dep. A Coruna",
            "AwayTeam": "Valencia",
            "FTHG": 1,
            "FTAG": 0,
            "FTR": "H",
        }
    ])

    result = updater.normalize_source(
        frame
    )

    assert len(result) == 1

    assert (
        result.iloc[0]["home_team"]
        == "Deportivo La Coruña"
    )


def test_current_football_data_atletico_alias():
    allowed = updater.canonical_team_set()

    assert (
        updater.normalize_team(
            "Atl. Madrid",
            allowed,
        )
        == "Atlético Madrid"
    )


def test_current_football_data_rayo_alias():
    allowed = updater.canonical_team_set()

    assert (
        updater.normalize_team(
            "Rayo Vallecano",
            allowed,
        )
        == "Vallecano"
    )
