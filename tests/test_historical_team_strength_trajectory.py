import pandas as pd

from historical_team_strength_trajectory import add_team_strength_trajectory


def _frame(results):
    dates = pd.date_range("2020-08-01", periods=len(results), freq="7D")
    rows = []
    for i, result in enumerate(results):
        rows.append(
            {
                "league": "EPL",
                "season": "2020-2021",
                "match_date": dates[i],
                "home_team": "A" if i % 2 == 0 else "B",
                "away_team": "B" if i % 2 == 0 else "A",
                "result": result,
            }
        )
    return pd.DataFrame(rows)


def test_trajectory_snapshot_is_pre_match():
    out = add_team_strength_trajectory(_frame(["H", "A"]))
    assert out.iloc[0].home_elo_level == 1500.0
    assert pd.isna(out.iloc[0].home_performance_residual_5)
    assert pd.notna(out.iloc[1].home_performance_residual_5)


def test_current_result_cannot_change_current_features():
    first = _frame(["H", "H"])
    second = first.copy()
    second.loc[1, "result"] = "A"
    a = add_team_strength_trajectory(first).iloc[1]
    b = add_team_strength_trajectory(second).iloc[1]
    columns = [
        "home_elo_level",
        "away_elo_level",
        "home_performance_residual_5",
        "away_performance_residual_5",
        "diff_elo_level",
        "diff_performance_residual_5",
    ]
    for column in columns:
        assert a[column] == b[column]


def test_five_match_rating_delta_uses_only_prior_matches():
    out = add_team_strength_trajectory(_frame(["H", "H", "H", "H", "H", "H"]))
    assert pd.isna(out.iloc[4].home_elo_delta_5)
    assert pd.notna(out.iloc[5].home_elo_delta_5)
