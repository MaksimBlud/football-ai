import pandas as pd

from season_invariant_corners_v1 import classify_leagues, overall_portability


def _row(league, seasons=7, db=-0.01, dl=-0.02, bw=0.8, lw=0.8):
    return {
        "league": league,
        "candidate": "CORNERS10",
        "baseline": "GOALS10",
        "seasons": seasons,
        "mean_delta_brier": db,
        "mean_delta_log_loss": dl,
        "brier_win_rate": bw,
        "log_loss_win_rate": lw,
    }


def test_all_three_strong_is_portable_strong():
    frame = pd.DataFrame([_row("EPL"), _row("LA_LIGA"), _row("SERIE_A")])
    leagues = classify_leagues(frame)
    assert set(leagues.classification) == {"STRONG"}
    assert overall_portability(leagues) == "PORTABLE_STRONG"


def test_supportive_band_is_not_upgraded_to_strong():
    frame = pd.DataFrame([
        _row("EPL"),
        _row("LA_LIGA", bw=0.60, lw=0.60),
        _row("SERIE_A"),
    ])
    leagues = classify_leagues(frame)
    assert leagues.set_index("league").loc["LA_LIGA", "classification"] == "SUPPORTIVE"
    assert overall_portability(leagues) == "PORTABLE_SUPPORTIVE"


def test_positive_mean_delta_is_unstable_even_with_high_win_rate():
    frame = pd.DataFrame([
        _row("EPL"),
        _row("LA_LIGA", db=0.001, bw=0.9, lw=0.9),
        _row("SERIE_A"),
    ])
    leagues = classify_leagues(frame)
    assert leagues.set_index("league").loc["LA_LIGA", "classification"] == "UNSTABLE"
    assert overall_portability(leagues) == "NOT_PORTABLE"


def test_insufficient_seasons_is_fail_closed():
    frame = pd.DataFrame([
        _row("EPL"),
        _row("LA_LIGA", seasons=4),
        _row("SERIE_A"),
    ])
    leagues = classify_leagues(frame)
    assert leagues.set_index("league").loc["LA_LIGA", "classification"] == "UNSTABLE"
    assert overall_portability(leagues) == "NOT_PORTABLE"
