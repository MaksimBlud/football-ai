import pandas as pd
import pytest

from league_offline_history import (
    expected_double_round_robin_matches,
    normalize_football_data_frame,
)
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


def _complete_round_robin(team_count: int) -> pd.DataFrame:
    teams = [f"Team {i:02d}" for i in range(team_count)]
    rows = []
    for home in teams:
        for away in teams:
            if home == away:
                continue
            rows.append(
                {
                    "Date": "01/08/2025",
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FTHG": 1,
                    "FTAG": 0,
                    "FTR": "H",
                }
            )
    return pd.DataFrame(rows)


@pytest.mark.parametrize(
    ("team_count", "expected_matches"),
    [(20, 380), (18, 306), (16, 240)],
)
def test_complete_match_count_is_inferred_from_observed_league_size(
    team_count,
    expected_matches,
):
    frame = _complete_round_robin(team_count)
    assert expected_double_round_robin_matches(frame) == expected_matches
    normalized = normalize_football_data_frame(
        frame,
        config=TURKEY_SUPER_LIG_RUNTIME_CONFIG,
        season="2025-2026",
        require_complete=True,
    )
    assert len(normalized) == expected_matches


def test_incomplete_round_robin_is_rejected_without_assuming_380_rows():
    frame = _complete_round_robin(18).iloc[:-1].copy()
    with pytest.raises(ValueError, match="305 rows; expected 306"):
        normalize_football_data_frame(
            frame,
            config=TURKEY_SUPER_LIG_RUNTIME_CONFIG,
            season="2025-2026",
            require_complete=True,
        )
