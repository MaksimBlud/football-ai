import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "research" / "prospective_corners10_incremental_v1.json"


def load_protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_protocol_is_fail_closed_and_research_only():
    p = load_protocol()
    assert p["research_block"] == "PROSPECTIVE_CORNERS10_INCREMENTAL_V1"
    assert p["status"] == "PREREGISTERED_EXTERNALLY_GATED_RESEARCH_ONLY"
    assert p["leagues"] == ["EPL", "LA_LIGA", "SERIE_A"]
    assert p["activation_gates"] == {
        "provider_corner_capability_must_be_separately_approved": True,
        "prospective_collection_only": True,
        "automatic_activation": False,
        "automatic_promotion": False,
    }
    assert p["execution"]["evaluation_requires_explicit_manual_action"] is True
    assert p["execution"]["scheduled_outcome_scoring"] is False
    assert p["execution"]["supabase_writes"] is False
    assert p["execution"]["live_provider_calls"] is False
    assert p["execution"]["production_artifact_changes"] is False


def test_protocol_freezes_sample_and_information_boundary():
    p = load_protocol()
    sample = p["sample_contract"]
    assert sample["post_activation_kickoffs_only"] is True
    assert sample["current_fixture_outcome_forbidden_from_features"] is True
    assert sample["future_outcomes_forbidden_before_evaluation_gate"] is True
    assert sample["canonical_fixture_identity_required"] is True
    assert sample["minimum_settled_eligible_fixtures_per_league"] == 100
    assert sample["minimum_calendar_months_per_league"] == 4
    assert sample["minimum_valid_monthly_test_blocks_per_league"] == 2
    assert sample["minimum_prior_training_fixtures_per_block"] == 60
    assert sample["minimum_test_fixtures_per_block"] == 20
    assert sample["scores_forbidden_before_all_leagues_ready"] is True


def test_protocol_freezes_corners10_and_paired_market_comparison():
    p = load_protocol()
    feature = p["feature_contract"]
    comparison = p["comparison"]
    evaluation = p["evaluation"]
    assert feature["signal"] == "CORNERS10"
    assert feature["rolling_window_matches"] == 10
    assert feature["rolling_state_must_use_only_prior_finished_matches"] is True
    assert feature["feature_definition_must_match_closed_historical_signal_family"] is True
    assert feature["no_post_freeze_feature_selection"] is True
    assert feature["no_post_outcome_parameter_search"] is True
    assert comparison["baseline"] == "MARKET_MODEL"
    assert comparison["challenger"] == "MARKET_CORNERS10"
    assert comparison["same_rows_required"] is True
    assert comparison["same_walk_forward_splits_required"] is True
    assert comparison["split"] == "expanding_monthly_walk_forward"
    assert evaluation["primary_metrics"] == ["multiclass_brier", "log_loss"]
    assert evaluation["paired_deltas"] == "MARKET_CORNERS10 minus MARKET_MODEL"
    assert evaluation["no_threshold_search"] is True
    assert evaluation["no_feature_selection_after_results"] is True
    assert evaluation["no_league_weighting_after_results"] is True


def test_protocol_freezes_decision_rule_without_promotion():
    p = load_protocol()
    rule = p["decision_rule"]
    assert set(rule) == {"PASS", "FAIL", "INCONCLUSIVE", "production_promotion_from_result"}
    assert "every league" in rule["PASS"]
    assert "pooled micro" in rule["PASS"]
    assert "at least two leagues" in rule["FAIL"]
    assert rule["production_promotion_from_result"] is False
