import pandas as pd

from historical_rest_congestion import add_league_schedule_rest


def _frame():
    return pd.DataFrame(
        [
            {"league":"EPL","season":"2020-2021","match_date":pd.Timestamp("2020-09-01"),"home_team":"A","away_team":"B","result":"H"},
            {"league":"EPL","season":"2020-2021","match_date":pd.Timestamp("2020-09-04"),"home_team":"C","away_team":"A","result":"D"},
            {"league":"EPL","season":"2020-2021","match_date":pd.Timestamp("2020-09-08"),"home_team":"A","away_team":"B","result":"A"},
        ]
    )


def test_rest_and_counts_use_only_prior_league_matches():
    out = add_league_schedule_rest(_frame())
    assert pd.isna(out.iloc[0].home_league_rest_days)
    assert out.iloc[1].away_league_rest_days == 3.0
    assert out.iloc[2].home_league_rest_days == 4.0
    assert out.iloc[2].home_league_matches_7d == 2.0
    assert out.iloc[2].home_league_matches_14d == 2.0


def test_current_result_does_not_affect_rest_features():
    first = _frame()
    second = first.copy()
    second.loc[2, "result"] = "H"
    a = add_league_schedule_rest(first).iloc[2]
    b = add_league_schedule_rest(second).iloc[2]
    for column in [
        "home_league_rest_days",
        "away_league_rest_days",
        "diff_league_rest_days",
        "diff_league_matches_7d",
        "diff_league_matches_14d",
    ]:
        left, right = a[column], b[column]
        assert (pd.isna(left) and pd.isna(right)) or left == right


def test_histories_reset_at_season_boundary():
    frame = _frame().iloc[:1].copy()
    second = frame.copy()
    second["season"] = "2021-2022"
    second["match_date"] = pd.Timestamp("2021-08-01")
    both = pd.concat([frame, second], ignore_index=True)
    out = add_league_schedule_rest(both)
    assert pd.isna(out.iloc[1].home_league_rest_days)
    assert out.iloc[1].home_league_matches_14d == 0.0
