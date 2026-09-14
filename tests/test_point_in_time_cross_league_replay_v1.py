from pathlib import Path

import numpy as np
import pandas as pd

import point_in_time_cross_league_replay_v1 as replay


def _history_row(date, time, home, away, result="H"):
    return {
        "match_date": pd.Timestamp(date),
        "match_time": time,
        "home_team": home,
        "away_team": away,
        "home_goals": 2.0,
        "away_goals": 1.0,
        "result": result,
        "home_shots": 10.0,
        "away_shots": 8.0,
        "home_shots_target": 4.0,
        "away_shots_target": 3.0,
    }


def test_current_season_parser_skips_post_cutoff_before_result_validation():
    payload = (
        "Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HS,AS,HST,AST\n"
        "10/09/2026,20:00,Alpha,Beta,2,1,H,10,8,4,3\n"
        "11/09/2026,18:00,Gamma,Delta,999,999,NOT_A_RESULT,999,999,999,999\n"
    ).encode()
    frame = replay.parse_football_data_csv_outcome_blind(
        "BUNDESLIGA", payload, current_season=True
    )
    assert len(frame) == 1
    assert frame.iloc[0]["home_team"] == "Alpha"
    assert frame.iloc[0]["result"] == "H"


def test_history_as_of_snapshot_uses_four_hour_result_buffer():
    history = pd.DataFrame(
        [
            _history_row("2026-09-10", "12:00", "Alpha", "Beta"),
            _history_row("2026-09-11", "12:00", "Gamma", "Delta"),
        ],
        columns=replay.HISTORY_COLUMNS,
    )
    safe = replay.history_as_of_snapshot(
        history,
        pd.Timestamp("2026-09-11T15:00:00Z"),
        "Europe/Berlin",
    )
    assert list(safe["home_team"]) == ["Alpha"]


def test_cold_start_matches_production_neutral_defaults():
    history = pd.DataFrame(
        [_history_row("2026-09-01", "12:00", "Known A", "Known B")],
        columns=replay.HISTORY_COLUMNS,
    )
    features, home_known, away_known = replay.build_feature_frame_allow_cold_start(
        history,
        home_team="New Home",
        away_team="New Away",
        home_odds=2.0,
        draw_odds=3.0,
        away_odds=4.0,
    )
    assert home_known is False
    assert away_known is False
    row = features.iloc[0]
    assert row["home_last5_points"] == 0
    assert row["away_last5_points"] == 0
    assert row["home_elo"] == replay.INITIAL_ELO
    assert row["away_elo"] == replay.INITIAL_ELO
    assert row["elo_difference"] == replay.HOME_ADVANTAGE


def test_source_aliases_cover_known_market_identity_mismatches():
    assert replay.normalize_source_team("BUNDESLIGA", "Schalke 04") == "FC Schalke 04"
    assert replay.normalize_source_team("BUNDESLIGA", "FC Koln") == "1. FC Köln"
    assert replay.normalize_source_team("EREDIVISIE", "Twente") == "FC Twente Enschede"
    assert replay.normalize_source_team("EREDIVISIE", "PSV") == "PSV Eindhoven"
    assert replay.normalize_source_team("LA_LIGA", "Santander") == "Real Racing Club de Santander"
    assert replay.normalize_source_team("LIGUE_1", "Paris SG") == "Paris Saint Germain"
    assert replay.normalize_source_team("SERIE_A", "Milan") == "AC Milan"


def test_market_probabilities_are_devigged_and_normalized():
    probs = replay.normalized_market_probabilities(2.0, 3.0, 4.0)
    assert np.isclose(probs.sum(), 1.0)
    assert np.all(probs > 0)


def test_protocol_is_fixed_to_47_non_epl_events():
    assert replay.EXPECTED_COUNTS == {
        "BUNDESLIGA": 9,
        "EREDIVISIE": 9,
        "LA_LIGA": 10,
        "LIGUE_1": 9,
        "SERIE_A": 10,
    }
    assert sum(replay.EXPECTED_COUNTS.values()) == 47
    assert replay.EVIDENCE_CLASS == "RETROSPECTIVE_POINT_IN_TIME_REPLAY"
    assert replay.FROZEN_MODEL_SHA256 == (
        "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
    )


def test_replay_source_contains_no_settlement_table_dependency():
    source = Path(replay.__file__).read_text(encoding="utf-8")
    forbidden = (
        "league_finished_results",
        "la_liga_finished_results",
        "league_multi_market_settlements",
    )
    lowered = source.lower()
    for token in forbidden:
        assert token not in lowered
