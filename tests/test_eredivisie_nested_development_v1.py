from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

import eredivisie_nested_development_v1 as protocol


def _prediction_grid(*, ai=(0.90, 0.05, 0.05), market=(0.35, 0.40, 0.25)) -> pd.DataFrame:
    rows = []
    for feature_set in protocol.FEATURE_SET_ORDER:
        for model_name in protocol.MODEL_ORDER:
            candidate = protocol.candidate_key(feature_set, model_name)
            for season in protocol.DEVELOPMENT_OOS_SEASONS:
                rows.append(
                    {
                        "candidate": candidate,
                        "feature_set": feature_set,
                        "model": model_name,
                        "season": season,
                        "target": 0,
                        "ai_home": ai[0],
                        "ai_draw": ai[1],
                        "ai_away": ai[2],
                        "market_home": market[0],
                        "market_draw": market[1],
                        "market_away": market[2],
                    }
                )
    return pd.DataFrame(rows)


def _source_from_pairs(pairs: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["01/01/2020"] * len(pairs),
            "HomeTeam": [home for home, _ in pairs],
            "AwayTeam": [away for _, away in pairs],
            "FTHG": [1] * len(pairs),
            "FTAG": [0] * len(pairs),
            "FTR": ["H"] * len(pairs),
            "B365H": [2.0] * len(pairs),
            "B365D": [3.2] * len(pairs),
            "B365A": [4.0] * len(pairs),
        }
    )


def test_contract_constants_are_frozen():
    assert protocol.LEAGUE == "EREDIVISIE"
    assert protocol.CURRENT_FORBIDDEN_SEASON == "2026-2027"
    assert protocol.STRUCTURALLY_EXCLUDED_SEASONS == ("2019-2020",)
    assert "2019-2020" not in protocol.ADMITTED_HISTORICAL_SEASONS
    assert "2026-2027" not in protocol.ADMITTED_HISTORICAL_SEASONS
    assert protocol.DEVELOPMENT_OOS_SEASONS == (
        "2020-2021", "2021-2022", "2022-2023",
        "2023-2024", "2024-2025", "2025-2026",
    )
    assert protocol.OUTER_TEST_SEASONS == (
        "2022-2023", "2023-2024", "2024-2025", "2025-2026",
    )
    assert protocol.REQUIRED_OUTER_SEASON_WINS == 3
    assert protocol.ALPHAS == (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5)
    assert protocol.FEATURE_SET_ORDER == ("core", "core_elo", "full_no_odds")
    assert protocol.MODEL_ORDER == ("logistic_l2", "xgb_shallow", "xgb_base", "xgb_regularized")


def test_current_or_later_historical_season_fails_closed():
    frame = pd.DataFrame(
        {
            "league": ["EREDIVISIE"] * (len(protocol.ADMITTED_HISTORICAL_SEASONS) + 1),
            "season": list(protocol.ADMITTED_HISTORICAL_SEASONS) + ["2026-2027"],
        }
    )
    with pytest.raises(ValueError, match="current/later-than-2025-2026"):
        protocol.assert_historical_boundary(frame)


def test_structurally_excluded_season_cannot_enter_model_frame():
    frame = pd.DataFrame(
        {
            "league": ["EREDIVISIE"] * (len(protocol.ADMITTED_HISTORICAL_SEASONS) + 1),
            "season": list(protocol.ADMITTED_HISTORICAL_SEASONS) + ["2019-2020"],
        }
    )
    with pytest.raises(ValueError, match="Structurally excluded"):
        protocol.assert_historical_boundary(frame)


def test_non_eredivisie_data_fails_closed():
    frame = pd.DataFrame(
        {
            "league": ["LIGUE_1"] * len(protocol.ADMITTED_HISTORICAL_SEASONS),
            "season": list(protocol.ADMITTED_HISTORICAL_SEASONS),
        }
    )
    with pytest.raises(ValueError, match="pure EREDIVISIE"):
        protocol.assert_historical_boundary(frame)


def test_missing_admitted_historical_season_fails_closed():
    frame = pd.DataFrame(
        {
            "league": ["EREDIVISIE"] * (len(protocol.ADMITTED_HISTORICAL_SEASONS) - 1),
            "season": list(protocol.ADMITTED_HISTORICAL_SEASONS[:-1]),
        }
    )
    with pytest.raises(ValueError, match="Missing required admitted historical seasons"):
        protocol.assert_historical_boundary(frame)


def test_terminated_2019_2020_source_must_be_incomplete_18_team_shape():
    teams = [f"Team {index:02d}" for index in range(18)]
    all_pairs = [(home, away) for home in teams for away in teams if home != away]
    terminated = _source_from_pairs(all_pairs[:232])
    protocol.validate_structurally_excluded_source(terminated, season="2019-2020")

    complete = _source_from_pairs(all_pairs)
    with pytest.raises(ValueError, match="must contain fewer than"):
        protocol.validate_structurally_excluded_source(complete, season="2019-2020")


def test_candidate_tie_break_is_deterministic_and_uses_fixed_order():
    winner, _ = protocol.select_candidate(_prediction_grid())
    assert winner == "core::logistic_l2"


def test_alpha_tie_break_prefers_lower_alpha():
    predictions = _prediction_grid(ai=(0.35, 0.40, 0.25), market=(0.35, 0.40, 0.25))
    winner = predictions[predictions["candidate"] == "core::logistic_l2"]
    alpha, _ = protocol.select_alpha(winner)
    assert alpha == 0.05


def test_probability_roundoff_is_renormalized_before_scoring():
    probabilities = np.array([[0.50000003, 0.30000001, 0.20000002]], dtype=float)
    normalized = protocol._renormalize(probabilities)
    assert normalized.shape == (1, 3)
    assert normalized.sum(axis=1)[0] == pytest.approx(1.0, abs=1e-15)
    assert (normalized >= 0.0).all()


def test_nested_pass_only_recommends_future_freeze_not_ai_readiness():
    report = protocol.evaluate_nested(_prediction_grid())
    assert report["status"] == "ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE"
    assert report["prospective_ai_ready"] is False
    assert report["model_ready"] is False
    assert report["artifact_created"] is False
    assert report["untouched_holdout_claimed"] is False
    assert report["all_admitted_historical_data_is_development_only"] is True
    assert report["outer_aggregate"]["all_three_win_count"] == 4
    assert all(report["gate"].values())


def test_nested_rejects_when_market_is_better():
    predictions = _prediction_grid(ai=(0.20, 0.55, 0.25), market=(0.80, 0.10, 0.10))
    report = protocol.evaluate_nested(predictions)
    assert report["status"] == "REJECTED_NO_FREEZE_RECOMMENDATION"
    assert not all(report["gate"].values())


def test_runner_has_no_live_database_paid_api_or_model_write_surface():
    source = inspect.getsource(protocol).lower()
    assert "from database import" not in source
    assert "import database" not in source
    assert ".table(" not in source
    assert "supabase" not in source
    assert "odds_api" not in source
    assert "joblib.dump" not in source
    assert "pickle.dump" not in source
    assert "--production" not in source
    assert "league_prediction_ledger" not in source
    assert "structural_v2_observations" not in source


def test_current_2026_2027_source_is_skipped_before_download():
    source = inspect.getsource(protocol.build_historical_frame)
    skip_pos = source.index("if season == CURRENT_FORBIDDEN_SEASON")
    download_pos = source.index("download_source")
    assert skip_pos < download_pos


def test_frozen_family_matches_preexisting_sweep():
    protocol.assert_frozen_family()
