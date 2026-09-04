import pandas as pd

from schedule_load_signal_lab import (
    REST_DAY_CAP,
    SCHEDULE_FEATURES,
    build_schedule_features,
    paired_incremental,
    run_schedule_lab,
)


def _rows():
    return pd.DataFrame(
        [
            {"Date": "01/08/2023", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "_season": "2023/24", "B365H": 2.0, "B365D": 3.2, "B365A": 4.0},
            {"Date": "05/08/2023", "HomeTeam": "C", "AwayTeam": "A", "FTR": "D", "_season": "2023/24", "B365H": 2.4, "B365D": 3.1, "B365A": 3.0},
            {"Date": "10/08/2023", "HomeTeam": "A", "AwayTeam": "D", "FTR": "A", "_season": "2023/24", "B365H": 2.1, "B365D": 3.3, "B365A": 3.7},
            {"Date": "20/09/2023", "HomeTeam": "B", "AwayTeam": "A", "FTR": "H", "_season": "2023/24", "B365H": 2.8, "B365D": 3.0, "B365A": 2.6},
        ]
    )


def test_schedule_features_use_only_prior_matches_and_cap_long_rest():
    features = build_schedule_features(_rows(), "EPL")
    first = features.iloc[0]
    assert pd.isna(first.home_rest_days_capped)
    assert first.home_matches_7d == 0
    second = features.iloc[1]
    assert second.away_team == "A"
    assert second.away_rest_days_capped == 4
    assert second.away_matches_7d == 1
    third = features.iloc[2]
    assert third.home_rest_days_capped == 5
    assert third.home_matches_7d == 1
    assert third.home_matches_14d == 2
    fourth = features.iloc[3]
    assert fourth.away_rest_days_capped == REST_DAY_CAP


def test_future_rows_cannot_change_earlier_schedule_snapshots():
    base = _rows().iloc[:3].copy()
    extended = _rows().copy()
    before = build_schedule_features(base, "EPL")
    after = build_schedule_features(extended, "EPL").iloc[:3].reset_index(drop=True)
    pd.testing.assert_frame_equal(before.reset_index(drop=True), after)


def test_feature_family_is_exactly_frozen_v1():
    assert SCHEDULE_FEATURES == [
        "home_rest_days_capped",
        "away_rest_days_capped",
        "diff_rest_days_capped",
        "home_matches_7d",
        "away_matches_7d",
        "diff_matches_7d",
        "home_matches_14d",
        "away_matches_14d",
        "diff_matches_14d",
    ]


def test_walk_forward_and_paired_market_comparison_are_complete():
    rows = []
    for season_index in range(5):
        season = f"20{20+season_index}/{str(21+season_index).zfill(2)}"
        for match_index in range(30):
            home = f"T{match_index % 6}"
            away = f"T{(match_index + 1) % 6}"
            rows.append(
                {
                    "league": "EPL",
                    "season": season,
                    "match_date": pd.Timestamp(2020 + season_index, 8, 1) + pd.Timedelta(days=match_index),
                    "home_team": home,
                    "away_team": away,
                    "result": ["H", "D", "A"][match_index % 3],
                    "market_home": 0.45,
                    "market_draw": 0.28,
                    "market_away": 0.27,
                    "home_rest_days_capped": float(3 + match_index % 5),
                    "away_rest_days_capped": float(3 + (match_index + 2) % 5),
                    "diff_rest_days_capped": float((match_index % 5) - ((match_index + 2) % 5)),
                    "home_matches_7d": float(match_index % 3),
                    "away_matches_7d": float((match_index + 1) % 3),
                    "diff_matches_7d": float((match_index % 3) - ((match_index + 1) % 3)),
                    "home_matches_14d": float(match_index % 4),
                    "away_matches_14d": float((match_index + 1) % 4),
                    "diff_matches_14d": float((match_index % 4) - ((match_index + 1) % 4)),
                }
            )
    results = run_schedule_lab(pd.DataFrame(rows), min_train_seasons=3)
    assert set(results.feature_set) == {"MARKET_RAW", "SCHEDULE_ONLY", "MARKET_MODEL", "MARKET_SCHEDULE"}
    paired = paired_incremental(results)
    assert len(paired) == 2
    assert set(paired.test_season) == {"2023/24", "2024/25"}
