from pathlib import Path

import pytest

import website_btts_oos_readiness_v1
import website_goal_total_oos_readiness_v1
from website_goal_source_readiness import BLOCKED, evaluate_source_readiness


def test_current_repository_fails_closed_without_reading_outcomes_or_pickles():
    over = evaluate_source_readiness("OU25")
    btts = evaluate_source_readiness("BTTS")

    assert over["decision"] == BLOCKED
    assert btts["decision"] == BLOCKED
    assert over["no_bet"] is True
    assert btts["no_bet"] is True
    assert over["safety"]["reserved_2026_27_outcomes_read"] is False
    assert btts["safety"]["reserved_2026_27_outcomes_read"] is False
    assert over["safety"]["model_pickle_files_loaded"] is False
    assert btts["safety"]["model_pickle_files_loaded"] is False


def test_market_contracts_are_independent_and_not_pooled():
    over = evaluate_source_readiness("OU25")
    btts = evaluate_source_readiness("BTTS")

    assert over["hypothesis_family"] == "website_goal_total_oos_readiness_v1"
    assert btts["hypothesis_family"] == "website_btts_oos_readiness_v1"
    assert over["source_audit"]["required_market_price_fields"] == [
        "over_2_5_odds", "under_2_5_odds"
    ]
    assert btts["source_audit"]["required_market_price_fields"] == [
        "btts_yes_odds", "btts_no_odds"
    ]


def test_wrappers_route_to_their_own_market(monkeypatch: pytest.MonkeyPatch):
    calls = []

    def fake(market):
        calls.append(market)
        return {"market": market}

    monkeypatch.setattr(website_goal_total_oos_readiness_v1, "evaluate_source_readiness", fake)
    monkeypatch.setattr(website_btts_oos_readiness_v1, "evaluate_source_readiness", fake)
    assert website_goal_total_oos_readiness_v1.evaluate() == {"market": "OU25"}
    assert website_btts_oos_readiness_v1.evaluate() == {"market": "BTTS"}
    assert calls == ["OU25", "BTTS"]


def test_artifact_check_uses_presence_only(monkeypatch: pytest.MonkeyPatch):
    original = Path.open

    def guarded_open(self, *args, **kwargs):
        if self.suffix == ".pkl":
            raise AssertionError("production pickle must not be opened")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    report = evaluate_source_readiness("OU25")
    assert report["safety"]["model_pickle_files_loaded"] is False


def test_unknown_market_is_rejected():
    with pytest.raises(ValueError, match="unsupported goal market"):
        evaluate_source_readiness("1X2")
