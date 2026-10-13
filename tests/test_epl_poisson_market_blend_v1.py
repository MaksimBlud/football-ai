"""Offline safety and arithmetic regressions for old-season Poisson/DC research."""
import math
from pathlib import Path

import pytest

import epl_poisson_market_blend_v1 as model


def row(mid, day, home="A", away="B", gh=2, ga=0, price=True):
    return {
        "id": mid, "match_date": day, "home_team": home, "away_team": away,
        "home_goals": gh, "away_goals": ga,
        "result": "H" if gh > ga else "D" if gh == ga else "A",
        "home_odds": 2.0 if price else None,
        "draw_odds": 3.5 if price else None,
        "away_odds": 4.2 if price else None,
    }


def test_market_normalized_and_dixon_coles_scores_form_simplex():
    p = model.no_vig_prices((2., 3.5, 4.2))
    assert len(p) == 3 and sum(p) == pytest.approx(1.0)
    assert p[0] == pytest.approx(.5 / (.5 + 1 / 3.5 + 1 / 4.2))
    a = model.poisson_score_probabilities(1.8, 1.0, 0.)
    b = model.poisson_score_probabilities(1.8, 1.0, -.08)
    assert sum(a) == pytest.approx(1.0)
    assert sum(b) == pytest.approx(1.0)
    assert all(0 < x < 1 for x in a + b)
    assert b[1] > a[1]  # Negative DC rho adds 0-0 and 1-1 mass
    assert model.CANDIDATE_COUNT == 36


@pytest.mark.parametrize("odds", [
    (1., 3., 4.), (2., 0., 4.), (2., 3., None),
    (2., 3.), (2., 3., 4., 5.), (float("nan"), 3., 4.),
    (float("inf"), 3., 4.), (True, 3., 4.),
])
def test_invalid_market_fails_closed(odds):
    with pytest.raises(ValueError):
        model.no_vig_prices(odds)


def test_no_same_day_result_or_same_match_goals_leak_into_predictions():
    one = row(1, "2019-08-10", "A", "B", 2, 0)
    two = row(2, "2019-08-10", "A", "C", 0, 1)
    three = row(3, "2019-08-11", "A", "D", 2, 0)
    first = model.historical_priced_examples([one, two, three])
    changed = model.historical_priced_examples([
        {**one, "home_goals": 0, "away_goals": 4, "result": "A"}, two, three
    ])
    assert first[0]["estimates"] == changed[0]["estimates"]
    assert first[1]["estimates"] == changed[1]["estimates"]
    assert first[2]["estimates"] != changed[2]["estimates"]
    assert first[1]["market"] == changed[1]["market"]
    assert first[1]["y"] == changed[1]["y"]


def test_pre_2019_unpriced_history_updates_prior_rates_without_synthetic_odds():
    earlier = row(1, "2017-08-10", gh=1, ga=3, price=False)
    following = row(2, "2019-08-10")
    with_history = model.historical_priced_examples([earlier, following])
    without_history = model.historical_priced_examples([following])
    assert len(with_history) == len(without_history) == 1
    assert with_history[0]["market"] == without_history[0]["market"]
    assert with_history[0]["estimates"] != without_history[0]["estimates"]


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(match_date="2022-08-01"),
    lambda r: r.update(result="UNKNOWN"),
    lambda r: r.update(home_team=""),
    lambda r: r.update(away_team="A"),
    lambda r: r.update(home_goals=-1),
    lambda r: r.update(away_goals=float("inf")),
    lambda r: r.update(home_odds=None),
])
def test_no_future_or_invalid_history_is_accepted(mutate):
    r = row(1, "2020-01-15")
    mutate(r)
    with pytest.raises((ValueError, TypeError)):
        model.historical_priced_examples([r])


def test_duplicate_id_fails_closed():
    r = row(1, "2019-08-10")
    with pytest.raises(ValueError, match="duplicate"):
        model.historical_priced_examples([r, r])


def _example(day, outcome=0, baseline=(.5, .25, .25), altered=(.8, .1, .1)):
    return {
        "date": day, "y": outcome, "market": baseline,
        "estimates": {(n, rho): altered
                      for n in model.SMOOTHING for rho in model.DC_RHO},
    }


def test_validation_only_hyperparameters_and_forward_failure(monkeypatch):
    validation = [_example("2019-08-10", outcome=0) for _ in range(380)]
    later = [_example("2020-08-10", outcome=2) for _ in range(760)]
    monkeypatch.setattr(model, "historical_priced_examples", lambda _: validation + later)
    r = model.evaluate([])
    assert r["cohort"]["validation_n"] == 380
    assert r["cohort"]["forward_n"] == 760
    assert r["candidate_grid_size"] == 36
    assert r["frozen_selection"]["poisson_blend_weight"] == .6
    assert r["research_status"] == "FAILED_FORWARD_HISTORICAL_EVAL"
    assert r["forward_candidate"]["log_loss"] > r["forward_market"]["log_loss"]
    assert r["market_fallback"] == r["forward_market"]
    assert r["market_fallback_is_ai"] is False
    assert r["production_model_changed"] is False
    assert r["read_frozen_prospective_outcomes"] is False
    assert r["is_pristine_untouched_evaluation"] is False
    assert r["provider_calls"] == 0 and r["bets"] == 0
    assert r["roi"] is None

    # Even completely different later outcomes never change the choice.
    other_later = [_example("2020-08-10", outcome=0) for _ in range(760)]
    monkeypatch.setattr(model, "historical_priced_examples", lambda _: validation + other_later)
    r2 = model.evaluate([])
    assert r2["frozen_selection"] == r["frozen_selection"]
    assert r2["forward_market"] != r["forward_market"]


def test_missing_full_historical_sample_cannot_claim_market_beating_result():
    with pytest.raises(ValueError, match="380/760"):
        model.evaluate([row(1, "2019-08-10")])


def test_read_only_data_boundary_and_no_automatic_model_promotion():
    src = Path("epl_poisson_market_blend_v1.py").read_text()
    assert 'HISTORY_END_EXCLUSIVE = "2022-08-01"' in src
    assert '.lt("match_date", HISTORY_END_EXCLUSIVE)' in src
    assert 'client.table("matches")' in src
    for banned in (".upsert(", ".insert(", ".update(", ".delete(",
                   "joblib.dump(", "pickle.dump(", ".pkl", "api.the-odds-api.com"):
        assert banned not in src
    assert "market_fallback_is_ai" in src
    assert "historic_odds_timestamp_qualified" in src
