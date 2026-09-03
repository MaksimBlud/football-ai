import pandas as pd
import pytest

from prospective_availability_evaluation import (
    CUTOFF_HOURS_BEFORE_KICKOFF,
    readiness,
    run_preregistered_evaluation,
    select_frozen_market_rows,
)


def test_market_selection_uses_one_latest_row_at_or_before_six_hour_cutoff():
    rows = []
    for stamp in ("2026-09-10T10:00:00Z", "2026-09-10T11:00:00Z", "2026-09-10T12:30:00Z"):
        rows.append(
            {
                "league": "EPL",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "commence_time_utc": "2026-09-10T18:00:00Z",
                "snapshot_time_utc": stamp,
                "market_home_probability": 0.5,
                "market_draw_probability": 0.25,
                "market_away_probability": 0.25,
            }
        )
    selected = select_frozen_market_rows(pd.DataFrame(rows))
    assert CUTOFF_HOURS_BEFORE_KICKOFF == 6
    assert len(selected) == 1
    assert selected.iloc[0]["snapshot_time_utc"] == pd.Timestamp("2026-09-10T11:00:00Z")


def test_readiness_requires_all_frozen_time_and_sample_gates():
    rows = []
    months = ("2026-09", "2026-10", "2026-11", "2026-12")
    for league in ("EPL", "LA_LIGA", "SERIE_A"):
        for month_index, month in enumerate(months):
            for i in range(30):
                rows.append(
                    {
                        "league": league,
                        "commence_time_utc": f"{month}-{(i % 20) + 1:02d}T12:00:00Z",
                        "result": ("H", "D", "A")[i % 3],
                        "availability_covered": True,
                    }
                )
    state = readiness(pd.DataFrame(rows))
    assert state["ready"].all()
    assert (state["eligible_evaluation_blocks"] >= 2).all()


def test_evaluation_refuses_to_score_early_sample():
    frame = pd.DataFrame(
        [
            {
                "league": "EPL",
                "commence_time_utc": "2026-09-10T18:00:00Z",
                "result": "H",
                "availability_covered": True,
            }
        ]
    )
    with pytest.raises(RuntimeError, match="PROSPECTIVE_SAMPLE_NOT_READY"):
        run_preregistered_evaluation(frame)
