import pytest

import predict_challenger as module


def fake_market(
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds,
):
    return {
        "home_team": home_team,
        "away_team": away_team,
        "prediction": "HOME",
        "home_probability": 0.50,
        "draw_probability": 0.30,
        "away_probability": 0.20,
        "bookmaker_margin": 0.05,
        "probability_source": "BOOKMAKER_NORMALIZED",
    }


def fake_ai(home_team, away_team):
    return {
        "home_team": home_team,
        "away_team": away_team,
        "prediction": "AWAY",
        "home_probability": 0.40,
        "draw_probability": 0.25,
        "away_probability": 0.35,
    }


def test_challenger_v0_equals_market(monkeypatch):
    monkeypatch.setattr(
        module,
        "predict_market",
        fake_market,
    )
    monkeypatch.setattr(
        module,
        "predict_match_no_odds",
        fake_ai,
    )
    monkeypatch.setattr(
        module,
        "normalize_team_name",
        lambda team: team,
    )

    result = module.predict_challenger(
        home_team="Home",
        away_team="Away",
        home_odds=2.0,
        draw_odds=3.0,
        away_odds=4.0,
    )

    challenger = result["challenger"]

    assert challenger["home_probability"] == pytest.approx(0.50)
    assert challenger["draw_probability"] == pytest.approx(0.30)
    assert challenger["away_probability"] == pytest.approx(0.20)

    assert challenger["prediction"] == "HOME"
    assert challenger["adjustment_weight"] == 0.0
    assert challenger["probability_source"] == "MARKET_PRIOR_V0"

    assert result["shadow_only"] is True


def test_delta_is_ai_minus_market(monkeypatch):
    monkeypatch.setattr(
        module,
        "predict_market",
        fake_market,
    )
    monkeypatch.setattr(
        module,
        "predict_match_no_odds",
        fake_ai,
    )
    monkeypatch.setattr(
        module,
        "normalize_team_name",
        lambda team: team,
    )

    result = module.predict_challenger(
        home_team="Home",
        away_team="Away",
        home_odds=2.0,
        draw_odds=3.0,
        away_odds=4.0,
    )

    assert result["delta"]["home"] == pytest.approx(-0.10)
    assert result["delta"]["draw"] == pytest.approx(-0.05)
    assert result["delta"]["away"] == pytest.approx(0.15)

    strongest = result["strongest_disagreement"]

    assert strongest["outcome"] == "AWAY"
    assert strongest["delta"] == pytest.approx(0.15)
    assert strongest["absolute_delta"] == pytest.approx(0.15)


def test_challenger_probabilities_sum_to_one(monkeypatch):
    monkeypatch.setattr(
        module,
        "predict_market",
        fake_market,
    )
    monkeypatch.setattr(
        module,
        "predict_match_no_odds",
        fake_ai,
    )
    monkeypatch.setattr(
        module,
        "normalize_team_name",
        lambda team: team,
    )

    result = module.predict_challenger(
        home_team="Home",
        away_team="Away",
        home_odds=2.0,
        draw_odds=3.0,
        away_odds=4.0,
    )

    challenger = result["challenger"]

    total = (
        challenger["home_probability"]
        + challenger["draw_probability"]
        + challenger["away_probability"]
    )

    assert total == pytest.approx(1.0)
