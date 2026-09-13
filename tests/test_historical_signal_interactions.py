import pandas as pd

from historical_signal_interactions import (
    FEATURE_SETS,
    INTERACTION_FEATURES,
    MAIN_EFFECTS,
    add_fixed_interactions,
)
from historical_team_strength_trajectory import add_team_strength_trajectory


def test_fixed_interaction_contract_excludes_closed_rest_family():
    assert INTERACTION_FEATURES == [
        "interaction_elo_delta_x_abs_sot_rate",
        "interaction_sot_rate_x_abs_performance_residual",
    ]
    assert all("rest" not in column.lower() for column in MAIN_EFFECTS + INTERACTION_FEATURES)
    assert FEATURE_SETS["CORNERS10_TRAJECTORY_SHOT_INTERACTIONS"][:-2] == FEATURE_SETS[
        "CORNERS10_TRAJECTORY_SHOT"
    ]
    assert FEATURE_SETS["MARKET_TRAJECTORY_SHOT_INTERACTIONS"][:-2] == FEATURE_SETS[
        "MARKET_TRAJECTORY_SHOT"
    ]


def test_fixed_interactions_preserve_direction_and_use_absolute_moderator():
    frame = pd.DataFrame(
        [
            {
                "diff_elo_delta_5": -4.0,
                "diff_performance_residual_5": -0.25,
                "diff_sot_rate_for_10": 0.5,
            }
        ]
    )
    out = add_fixed_interactions(frame).iloc[0]
    assert out.interaction_elo_delta_x_abs_sot_rate == -2.0
    assert out.interaction_sot_rate_x_abs_performance_residual == 0.125


def _history_frame(last_result: str) -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2020-08-01", periods=7, freq="7D")
    results = ["H", "D", "A", "H", "H", "D", last_result]
    for i, (date, result) in enumerate(zip(dates, results)):
        rows.append(
            {
                "league": "EPL",
                "season": "2020-2021",
                "match_date": date,
                "home_team": "A" if i % 2 == 0 else "B",
                "away_team": "B" if i % 2 == 0 else "A",
                "result": result,
                "diff_sot_rate_for_10": 0.10 + 0.01 * i,
            }
        )
    return pd.DataFrame(rows)


def test_current_match_result_cannot_change_current_interactions():
    first = add_fixed_interactions(add_team_strength_trajectory(_history_frame("H"))).iloc[-1]
    second = add_fixed_interactions(add_team_strength_trajectory(_history_frame("A"))).iloc[-1]
    for column in INTERACTION_FEATURES:
        left, right = first[column], second[column]
        assert (pd.isna(left) and pd.isna(right)) or left == right
