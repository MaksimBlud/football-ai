import pandas as pd

import update_rpl_results as updater


def test_finished_frame_contract_contains_generic_result_columns():
    frame = updater.build_finished_frame([
        {
            "completed": True,
            "commence_time": "2030-08-28T15:00:00Z",
            "home_team": "Alpha",
            "away_team": "Beta",
            "scores": [
                {"name": "Alpha", "score": "1"},
                {"name": "Beta", "score": "1"},
            ],
        }
    ])
    assert list(frame.columns) == [
        "league",
        "season",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
        "source",
        "source_competition",
    ]
    assert frame.loc[0, "league"] == "RPL"
    assert frame.loc[0, "result"] == "D"
    assert frame.loc[0, "source"] == "the-odds-api"
    assert frame.loc[0, "source_competition"] == "soccer_russia_premier_league"


def test_empty_finished_frame_is_safe():
    frame = updater.build_finished_frame([])
    assert isinstance(frame, pd.DataFrame)
    assert frame.empty
