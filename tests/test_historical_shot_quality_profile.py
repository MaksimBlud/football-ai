import pandas as pd
import pytest

from historical_shot_quality_profile import (
    build_point_in_time_shot_quality,
    source_capability,
)


def _row(date, home, away, hs, ass, hst, ast):
    return {
        "Date": date,
        "HomeTeam": home,
        "AwayTeam": away,
        "HS": hs,
        "AS": ass,
        "HST": hst,
        "AST": ast,
    }


def test_shot_quality_uses_only_prior_matches():
    df = pd.DataFrame(
        [
            _row("01/08/2020", "A", "B", 20, 4, 10, 1),
            _row("08/08/2020", "B", "A", 8, 12, 2, 6),
        ]
    )
    out = build_point_in_time_shot_quality(df, "EPL")
    assert pd.isna(out.iloc[0].home_shots_for_10)
    assert out.iloc[1].away_shots_for_10 == 20.0
    assert out.iloc[1].away_sot_for_10 == 10.0
    assert out.iloc[1].away_sot_rate_for_10 == 0.5


def test_current_match_shots_cannot_change_current_features():
    first = pd.DataFrame(
        [
            _row("01/08/2020", "A", "B", 10, 6, 5, 2),
            _row("08/08/2020", "A", "B", 2, 30, 1, 20),
        ]
    )
    second = first.copy()
    second.loc[1, ["HS", "AS", "HST", "AST"]] = [30, 2, 20, 1]
    a = build_point_in_time_shot_quality(first, "EPL").iloc[1]
    b = build_point_in_time_shot_quality(second, "EPL").iloc[1]
    for column in [
        "home_shots_for_10",
        "away_shots_for_10",
        "home_sot_for_10",
        "away_sot_for_10",
        "diff_shots_for_10",
        "diff_sot_rate_for_10",
    ]:
        left, right = a[column], b[column]
        assert (pd.isna(left) and pd.isna(right)) or left == right


def test_source_capability_does_not_invent_true_xg():
    frame = pd.DataFrame([_row("01/08/2020", "A", "B", 10, 6, 5, 2)])
    capability = source_capability(frame)
    assert capability["shots_complete"] is True
    assert capability["true_xg_pair_detected"] is False
    frame["HxG"] = 1.2
    frame["AxG"] = 0.7
    capability = source_capability(frame)
    assert capability["true_xg_pair_detected"] is True
    assert capability["true_xg_columns"] == ("HxG", "AxG")


def test_missing_shot_columns_fail_closed():
    frame = pd.DataFrame(
        [{"Date": "01/08/2020", "HomeTeam": "A", "AwayTeam": "B", "HS": 10}]
    )
    capability = source_capability(frame)
    assert capability["shots_complete"] is False
    with pytest.raises(ValueError, match="Missing required shot-quality columns"):
        build_point_in_time_shot_quality(frame, "EPL")
