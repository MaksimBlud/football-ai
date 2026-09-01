import json
from pathlib import Path


SPEC = Path("research/la_liga_market_home_60_70_v1.json")


def test_frozen_candidate_spec_is_research_only_and_exact():
    payload = json.loads(SPEC.read_text(encoding="utf-8"))
    assert payload["candidate_id"] == "LA_LIGA_MARKET_HOME_60_70_V1"
    assert payload["status"] == "FROZEN_RESEARCH_ONLY"
    assert payload["league"] == "LA_LIGA"
    assert payload["market"] == "1X2"
    assert payload["selection"] == "HOME"
    assert payload["lower_bound_inclusive"] == 0.60
    assert payload["upper_bound_exclusive"] == 0.70
    assert payload["decision_time"] == "pre-kickoff"
    assert payload["production_use"] is False
    assert payload["activation"] == "NONE"
    assert payload["structural_alpha_change"] is False
    assert payload["model_promotion"] is False


def test_prospective_rules_forbid_post_result_reselection():
    payload = json.loads(SPEC.read_text(encoding="utf-8"))
    rules = payload["prospective_rules"]
    assert rules["tag_every_qualifying_fixture_before_kickoff"] is True
    assert rules["do_not_reselect_thresholds"] is True
    assert rules["do_not_exclude_teams_after_results"] is True
    assert rules["do_not_exclude_seasons_or_months_after_results"] is True
    assert rules["preserve_market_snapshot_and_odds_used_for_tagging"] is True
    assert rules["evaluate_all_tagged_fixtures"] is True
