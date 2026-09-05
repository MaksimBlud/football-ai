import numpy as np
import pandas as pd

import evaluate_turkey_portugal_structural_v2 as evaluation


def _row(season: str, target: int = 0) -> dict:
    return {
        "league": "TURKEY_SUPER_LIG",
        "season": season,
        "match_date": pd.Timestamp(f"{season[:4]}-08-01"),
        "home_team": "Home",
        "away_team": "Away",
        "result": ["H", "D", "A"][target],
        "target": target,
        "elo_difference": 10.0,
        "form_difference": 1.0,
        "venue_win_rate_difference": 0.1,
        "home_goals_scored_last5": 1.5,
        "home_goals_conceded_last5": 1.0,
        "away_goals_scored_last5": 1.0,
        "away_goals_conceded_last5": 1.4,
        "market_home_probability": 0.50,
        "market_draw_probability": 0.28,
        "market_away_probability": 0.22,
    }


def test_apply_candidate_preserves_market_argmax():
    market = np.array(
        [
            [0.40, 0.35, 0.25],
            [0.30, 0.45, 0.25],
            [0.30, 0.25, 0.45],
        ],
        dtype=float,
    )
    scores = np.array([2.0, 2.0, -2.0], dtype=float)
    corrected, enabled, _ = evaluation.apply_candidate(
        market,
        scores,
        alpha=0.25,
        threshold=0.25,
    )
    assert enabled.tolist() == [True, True, True]
    assert np.argmax(corrected, axis=1).tolist() == np.argmax(market, axis=1).tolist()
    assert np.allclose(corrected.sum(axis=1), 1.0)


def test_summarize_inner_folds_requires_sixty_percent_on_both_metrics():
    candidate = evaluation.Candidate(0.05, 0.75)
    folds = [
        {"rows": 100, "logloss_delta": -0.01, "brier_delta": -0.01},
        {"rows": 100, "logloss_delta": -0.01, "brier_delta": -0.01},
        {"rows": 100, "logloss_delta": -0.01, "brier_delta": -0.01},
        {"rows": 100, "logloss_delta": 0.001, "brier_delta": 0.001},
        {"rows": 100, "logloss_delta": 0.001, "brier_delta": 0.001},
    ]
    report = evaluation.summarize_inner_folds(candidate, folds, 0.6)
    assert report["required_improving_folds"] == 3
    assert report["robust"] is True

    folds[2] = {"rows": 100, "logloss_delta": -0.01, "brier_delta": 0.001}
    report = evaluation.summarize_inner_folds(candidate, folds, 0.6)
    assert report["brier_improving_folds"] == 2
    assert report["robust"] is False


def test_select_candidate_uses_frozen_tie_break_order(monkeypatch):
    training = pd.DataFrame(
        [_row("2016-2017"), _row("2017-2018"), _row("2018-2019")]
    )

    def fake_fold(inner_training, validation, candidate):
        return {
            "rows": len(validation),
            "logloss_delta": -0.01,
            "brier_delta": -0.01,
            "argmax_changes": 0,
        }

    monkeypatch.setattr(evaluation, "_evaluate_candidate_on_fold", fake_fold)
    selected, reports = evaluation.select_candidate(
        training,
        alphas=[0.05, 0.10],
        thresholds=[0.5, 1.0],
        min_fraction=0.6,
    )
    assert reports
    assert selected == evaluation.Candidate(alpha=0.05, threshold=1.0)


def test_select_candidate_returns_market_only_when_no_candidate_is_robust(monkeypatch):
    training = pd.DataFrame(
        [_row("2016-2017"), _row("2017-2018"), _row("2018-2019")]
    )

    def fake_fold(inner_training, validation, candidate):
        return {
            "rows": len(validation),
            "logloss_delta": 0.01,
            "brier_delta": 0.01,
            "argmax_changes": 0,
        }

    monkeypatch.setattr(evaluation, "_evaluate_candidate_on_fold", fake_fold)
    selected, reports = evaluation.select_candidate(
        training,
        alphas=[0.05],
        thresholds=[0.5],
        min_fraction=0.6,
    )
    assert selected is None
    assert reports[0]["robust"] is False


def test_outer_test_rows_are_not_passed_to_candidate_selector(monkeypatch):
    dataset = pd.DataFrame(
        [
            _row("2019-2020", target=0),
            _row("2020-2021", target=1),
            _row("2021-2022", target=2),
        ]
    )
    seen = {}

    def fake_selector(training, *, alphas, thresholds, min_fraction):
        seen["seasons"] = sorted(training["season"].unique().tolist())
        seen["targets"] = training["target"].tolist()
        return None, []

    monkeypatch.setattr(evaluation, "select_candidate", fake_selector)
    result = evaluation.evaluate_outer_fold(
        dataset,
        test_season="2021-2022",
        alphas=[0.05],
        thresholds=[0.5],
        min_fraction=0.6,
    )
    assert seen["seasons"] == ["2019-2020", "2020-2021"]
    assert seen["targets"] == [0, 1]
    assert result["selection_decision"] == "MARKET_ONLY"
    assert result["selected_candidate"] is None
    assert result["argmax_changes"] == 0


def test_preregistration_and_runtime_status_remain_research_only():
    prereg = evaluation.load_prereg()
    assert prereg["decision_contract"]["runtime_status_before_and_after_research"] == "CALIBRATION_REQUIRED"
    assert prereg["decision_contract"]["research_result_cannot_activate_structural_v2"] is True
    for config in evaluation.CONFIGS.values():
        assert config.structural_v2.calibration_status == "CALIBRATION_REQUIRED"


def test_candidate_grid_matches_frozen_preregistration():
    prereg = evaluation.load_prereg()
    grid = prereg["candidate_search_space"]
    assert grid["alphas"] == [0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.2, 0.25]
    assert grid["thresholds"] == [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
