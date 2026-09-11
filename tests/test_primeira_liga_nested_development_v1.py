from __future__ import annotations

import inspect

import numpy as np
import pandas as pd

import primeira_liga_nested_development_v1 as protocol
import primeira_liga_nested_support as support


def _predictions(ai=(0.7, 0.2, 0.1), market=(0.4, 0.35, 0.25)):
    rows = []
    for season in protocol.DEVELOPMENT_OOS_SEASONS:
        rows.append({
            "season": season,
            "target": 0,
            "ai_home_probability": ai[0],
            "ai_draw_probability": ai[1],
            "ai_away_probability": ai[2],
            "market_home_probability": market[0],
            "market_draw_probability": market[1],
            "market_away_probability": market[2],
        })
    return pd.DataFrame(rows)


def test_frozen_contract_constants():
    assert protocol.PROTOCOL == "primeira_liga_nested_development_v1"
    assert support.LEAGUE == "PRIMEIRA_LIGA"
    assert support.CURRENT_FORBIDDEN_SEASON == "2026-2027"
    assert support.ADMITTED_SEASONS == (
        "2016-2017", "2017-2018", "2018-2019", "2019-2020", "2020-2021",
        "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026",
    )
    assert protocol.DEVELOPMENT_OOS_SEASONS == (
        "2020-2021", "2021-2022", "2022-2023",
        "2023-2024", "2024-2025", "2025-2026",
    )
    assert protocol.OUTER_TEST_SEASONS == (
        "2022-2023", "2023-2024", "2024-2025", "2025-2026"
    )
    assert protocol.REQUIRED_OUTER_WINS == 3
    assert protocol.ALPHAS == (
        0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5
    )
    assert protocol.FEATURE_SET_ORDER == ("core", "core_elo", "full_no_odds")
    assert protocol.MODEL_ORDER == (
        "logistic_l2", "xgb_shallow", "xgb_base", "xgb_regularized"
    )


def test_first_outer_fold_has_two_earlier_oos_seasons():
    assert protocol.inner_seasons("2022-2023") == ("2020-2021", "2021-2022")
    assert protocol.inner_seasons("2025-2026") == (
        "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"
    )


def test_probability_roundoff_is_renormalized():
    probability = np.array([[0.50000003, 0.30000001, 0.20000002]])
    normalized = support.simplex(probability)
    assert normalized.shape == (1, 3)
    assert normalized.sum(axis=1)[0] == 1.0
    assert (normalized > 0).all()


def test_candidate_tie_break_is_deterministic():
    grid = {
        (feature_set, model_name): _predictions()
        for feature_set in protocol.FEATURE_SET_ORDER
        for model_name in protocol.MODEL_ORDER
    }
    winner, _ = protocol.select_candidate(
        grid, ("2020-2021", "2021-2022")
    )
    assert winner == ("core", "logistic_l2")


def test_alpha_selection_stays_inside_frozen_grid_when_ai_equals_market():
    predictions = _predictions(ai=(0.4, 0.35, 0.25), market=(0.4, 0.35, 0.25))
    alpha, score = protocol.select_alpha(
        predictions, protocol.DEVELOPMENT_OOS_SEASONS
    )
    assert alpha in protocol.ALPHAS
    y, ai, market = protocol.arrays(predictions)
    expected = protocol.metrics(y, market)
    assert score["accuracy"] == expected["accuracy"]
    assert abs(score["logloss"] - expected["logloss"]) < 1e-12
    assert abs(score["brier"] - expected["brier"]) < 1e-12


def test_gate_requires_all_frozen_conditions():
    winning = {
        "wins": {"accuracy": True, "logloss": True, "brier": True},
        "all_three_win": True,
    }
    losing = {
        "wins": {"accuracy": False, "logloss": False, "brier": False},
        "all_three_win": False,
    }
    gate = protocol.evaluate_gate(
        [winning, winning, winning, losing],
        {"accuracy": 0.50, "logloss": 1.0, "brier": 0.60},
        {"accuracy": 0.51, "logloss": 0.99, "brier": 0.59},
        True,
    )
    assert gate["passed"] is True
    assert gate["all_three_win_count"] == 3
    assert gate["outer_accuracy_wins_at_least_3_of_4"] is True
    assert gate["outer_logloss_wins_at_least_3_of_4"] is True
    assert gate["outer_brier_wins_at_least_3_of_4"] is True
    assert gate["outer_all_three_wins_at_least_3_of_4"] is True


def test_current_season_is_skipped_before_historical_fetch():
    source = inspect.getsource(support.build_history)
    assert source.index("if season == CURRENT_FORBIDDEN_SEASON") < source.index("_fetch(")


def test_every_admitted_season_must_pass_round_robin_validation():
    source = inspect.getsource(support._normalize)
    assert "validate_complete_double_round_robin" in source
    assert support.CURRENT_FORBIDDEN_SEASON not in support.ADMITTED_SEASONS


def test_runner_has_no_live_database_paid_api_or_model_write_surface():
    source = (inspect.getsource(protocol) + inspect.getsource(support)).lower()
    assert "from database import" not in source
    assert "import database" not in source
    assert ".table(" not in source
    assert "supabase" not in source
    assert "odds_api" not in source
    assert "joblib.dump" not in source
    assert "pickle.dump" not in source
    assert "--production" not in source
    assert "league_prediction_ledger" not in source
    assert "primeira_liga_market_only_v1.csv" not in source


def test_frozen_family_still_exists():
    protocol.assert_frozen_family()
