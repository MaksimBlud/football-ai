import pandas as pd
import pytest

from league_offline_history import validate_complete_double_round_robin


def make_round_robin(team_count: int) -> pd.DataFrame:
    teams = [f"Team {index:02d}" for index in range(team_count)]
    rows = [
        {"HomeTeam": home_team, "AwayTeam": away_team}
        for home_team in teams
        for away_team in teams
        if home_team != away_team
    ]
    return pd.DataFrame(rows)


@pytest.mark.parametrize(
    ("team_count", "expected_matches"),
    [(20, 380), (18, 306), (16, 240)],
)
def test_complete_double_round_robin_accepts_league_size_changes(
    team_count,
    expected_matches,
):
    frame = make_round_robin(team_count)
    assert len(frame) == expected_matches

    validate_complete_double_round_robin(frame, season="2026-2027")


def test_complete_double_round_robin_rejects_missing_fixture():
    frame = make_round_robin(18).iloc[:-1].copy()

    with pytest.raises(ValueError, match="Incomplete season"):
        validate_complete_double_round_robin(frame, season="2026-2027")


def test_complete_double_round_robin_rejects_duplicate_pairing_even_at_full_row_count():
    frame = make_round_robin(18)
    frame.loc[len(frame) - 1, ["HomeTeam", "AwayTeam"]] = frame.loc[
        0, ["HomeTeam", "AwayTeam"]
    ]

    with pytest.raises(ValueError, match="duplicate home/away pairing"):
        validate_complete_double_round_robin(frame, season="2026-2027")
