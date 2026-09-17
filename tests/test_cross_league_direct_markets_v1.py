import numpy as np

from cross_league_direct_markets_v1 import (
    AH_FEATURES,
    OU_FEATURES,
    _binary_devig,
    _binary_scores,
    _is_half_step_line,
    _settle_ah_home,
)


def test_binary_devig_is_symmetric_and_favors_shorter_price():
    assert np.isclose(_binary_devig(1.9, 1.9), 0.5)
    assert _binary_devig(1.7, 2.2) > 0.5


def test_ah_v1_accepts_only_integer_or_half_goal_lines():
    assert _is_half_step_line(0.0)
    assert _is_half_step_line(-0.5)
    assert _is_half_step_line(1.5)
    assert not _is_half_step_line(-0.25)
    assert not _is_half_step_line(0.75)


def test_ah_home_settlement_excludes_pushes():
    assert _settle_ah_home(2, 1, -0.5) == 1
    assert _settle_ah_home(1, 1, -0.5) == 0
    assert _settle_ah_home(1, 1, 0.5) == 1
    assert _settle_ah_home(1, 1, 0.0) is None


def test_binary_scores_reward_perfect_probabilities():
    y = np.array([0, 1, 0, 1])
    strong = _binary_scores(y, np.array([0.01, 0.99, 0.02, 0.98]))
    weak = _binary_scores(y, np.array([0.5, 0.5, 0.5, 0.5]))
    assert strong["brier"] < weak["brier"]
    assert strong["log_loss"] < weak["log_loss"]


def test_candidate_features_cannot_include_same_match_outcomes():
    forbidden = {
        "FTHG",
        "FTAG",
        "FTR",
        "HC",
        "AC",
        "HY",
        "AY",
        "HR",
        "AR",
        "result",
        "target",
    }
    assert forbidden.isdisjoint(OU_FEATURES)
    assert forbidden.isdisjoint(AH_FEATURES)
    assert OU_FEATURES[0] == "market_logit"
    assert AH_FEATURES[:2] == ["market_logit", "ah_line"]
