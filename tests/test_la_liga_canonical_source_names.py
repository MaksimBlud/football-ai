import pandas as pd

from football_data_current_results import build_finished_frame
from la_liga_canonical_names import normalize_team
from league_runtime_config import LA_LIGA_RUNTIME_CONFIG
from multi_market_corner_results import normalize_corner_source_frame


def test_market_canonical_alias_direction_matches_live_identity_contract():
    expected = {
        "Alaves": "Alavés",
        "Alavés": "Alavés",
        "Espanol": "Espanyol",
        "Espanyol": "Espanyol",
        "Vallecano": "Rayo Vallecano",
        "Rayo Vallecano": "Rayo Vallecano",
        "Ath Madrid": "Atlético Madrid",
        "Atl. Madrid": "Atlético Madrid",
        "Santander": "Real Racing Club de Santander",
    }
    assert {name: normalize_team(name) for name in expected} == expected


def test_current_results_normalization_uses_market_canonical_la_liga_names():
    raw = pd.DataFrame(
        {
            "Date": ["05/09/2026", "06/09/2026", "07/09/2026"],
            "HomeTeam": ["Alaves", "Espanol", "Rayo Vallecano"],
            "AwayTeam": ["Vallecano", "Real Madrid", "Santander"],
            "FTHG": [1, 2, 0],
            "FTAG": [0, 1, 0],
            "FTR": ["H", "H", "D"],
        }
    )

    rows = build_finished_frame(raw, LA_LIGA_RUNTIME_CONFIG)

    assert rows[["home_team", "away_team"]].to_dict(orient="records") == [
        {"home_team": "Alavés", "away_team": "Rayo Vallecano"},
        {"home_team": "Espanyol", "away_team": "Real Madrid"},
        {"home_team": "Rayo Vallecano", "away_team": "Real Racing Club de Santander"},
    ]


def test_corner_normalization_uses_same_market_canonical_names():
    raw = pd.DataFrame(
        {
            "Date": ["05/09/2026"],
            "HomeTeam": ["Alaves"],
            "AwayTeam": ["Vallecano"],
            "FTHG": [1],
            "FTAG": [0],
            "FTR": ["H"],
            "HC": [6],
            "AC": [3],
        }
    )

    rows = normalize_corner_source_frame(
        LA_LIGA_RUNTIME_CONFIG,
        raw,
        source_url="https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
        fetched_at_utc="2026-09-05T20:00:00+00:00",
    )

    assert rows.iloc[0]["home_team"] == "Alavés"
    assert rows.iloc[0]["away_team"] == "Rayo Vallecano"
