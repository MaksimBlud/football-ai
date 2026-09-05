import json
from pathlib import Path

from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


CONTRACT = Path("research/turkey_portugal_structural_v2_calibration_v1.json")


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_preregistration_freezes_independent_league_research():
    contract = load_contract()
    assert contract["status"] == "PREREGISTERED_NOT_EVALUATED"
    assert contract["research_only"] is True
    assert contract["governance"]["copy_final_parameters_from_other_leagues"] is False
    assert contract["dataset_contract"]["cross_league_pooling"] is False
    assert contract["governance"]["outcome_dependent_changes_after_freeze"] is False


def test_current_season_excluded_and_completed_seasons_frozen():
    contract = load_contract()
    expected = [f"{year}-{year + 1}" for year in range(2016, 2026)]
    assert contract["dataset_contract"]["current_season_2026_2027_excluded"] is True
    for league in ("TURKEY_SUPER_LIG", "PRIMEIRA_LIGA"):
        assert contract["leagues"][league]["completed_seasons"] == expected
        assert "2026-2027" not in contract["leagues"][league]["completed_seasons"]


def test_outcome_blind_market_source_is_frozen_from_live_proof():
    contract = load_contract()
    turkey = contract["leagues"]["TURKEY_SUPER_LIG"]
    portugal = contract["leagues"]["PRIMEIRA_LIGA"]
    for league in (turkey, portugal):
        assert league["market_source"] == "BET365"
        assert league["market_columns"] == ["B365H", "B365D", "B365A"]
        assert league["outcome_blind_market_coverage_proof"]["workflow_run"] == 33955853472
    assert turkey["outcome_blind_market_coverage_proof"]["valid_rows"] == 3352
    assert portugal["outcome_blind_market_coverage_proof"]["valid_rows"] == 3058


def test_nested_oos_protocol_and_search_space_are_frozen():
    contract = load_contract()
    assert contract["candidate_search_space"]["alphas"] == [
        0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.2, 0.25
    ]
    assert contract["candidate_search_space"]["thresholds"] == [
        0.25, 0.5, 0.75, 1.0, 1.25, 1.5
    ]
    nested = contract["nested_walk_forward"]
    assert nested["outer_test_seasons"] == [
        "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"
    ]
    assert nested["candidate_selection_must_not_read_outer_test_outcomes"] is True
    assert nested["minimum_positive_fraction_per_metric"] == 0.6
    assert nested["no_robust_candidate_action"] == "MARKET_ONLY"


def test_runtime_configs_remain_uncalibrated():
    for config in (TURKEY_SUPER_LIG_RUNTIME_CONFIG, PRIMEIRA_LIGA_RUNTIME_CONFIG):
        structural = config.structural_v2
        assert structural.calibration_status == "CALIBRATION_REQUIRED"
        assert structural.structural_alpha is None
        assert structural.edge_threshold is None
        assert structural.prediction_source == "STRUCTURAL_EDGE_V2_SHADOW"
        config.validate()


def test_research_result_cannot_activate_runtime():
    contract = load_contract()
    decision = contract["decision_contract"]
    assert decision["runtime_status_before_and_after_research"] == "CALIBRATION_REQUIRED"
    assert decision["research_result_cannot_activate_structural_v2"] is True
    assert decision["any_future_runtime_calibration_requires_separate_explicit_review_and_PR"] is True
