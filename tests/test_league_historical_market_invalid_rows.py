import pandas as pd

from league_historical_market import MarketTriplet, normalize_market_frame
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


def test_normalize_market_frame_leaves_argmax_missing_for_invalid_market_rows():
    frame = pd.DataFrame(
        {
            "Date": ["01/08/2025", "02/08/2025"],
            "HomeTeam": ["Team A", "Team B"],
            "AwayTeam": ["Team B", "Team A"],
            "FTHG": [2, 1],
            "FTAG": [0, 1],
            "FTR": ["H", "D"],
            "B365H": [1.80, None],
            "B365D": [3.50, 3.20],
            "B365A": [4.50, 2.40],
        }
    )

    result = normalize_market_frame(
        frame,
        config=TURKEY_SUPER_LIG_RUNTIME_CONFIG,
        season="2025-2026",
        triplet=MarketTriplet("B365H", "B365D", "B365A", "BET365"),
    )

    valid = result[result["market_valid"]].iloc[0]
    invalid = result[~result["market_valid"]].iloc[0]

    assert valid["market_argmax"] == "H"
    assert abs(
        valid[
            [
                "market_home_probability",
                "market_draw_probability",
                "market_away_probability",
            ]
        ].sum()
        - 1.0
    ) < 1e-12

    assert pd.isna(invalid["market_argmax"])
    assert pd.isna(invalid["market_home_probability"])
    assert pd.isna(invalid["market_draw_probability"])
    assert pd.isna(invalid["market_away_probability"])
