"""Offline guarantees for the EPL market-floor research (no production changes)."""
from datetime import date, timedelta
import math
from pathlib import Path

import pytest

import epl_market_floor_v1 as research


def fixture(n, *, day, result="H", home="A", away="B", odds=(2.0, 3.5, 4.0)):
    return {
        "id": n, "match_date": day, "match_time": "12:00",
        "home_team": home, "away_team": away, "result": result,
        "home_goals": 2 if result == "H" else 0,
        "away_goals": 2 if result == "A" else 0,
        "home_shots_target": 5, "away_shots_target": 2,
        "home_odds": odds[0], "draw_odds": odds[1], "away_odds": odds[2],
    }


def dataset():
    rows = []
    groups = [
        (date(2020, 1, 1), 120, "H"),
        (date(2022, 8, 5), 120, "H"),
        (date(2023, 8, 5), 120, "A"),
    ]
    for start, count, result in groups:
        for i in range(count):
            rows.append(fixture(len(rows) + 1, day=(start + timedelta(days=i)).isoformat(), result=result))
    return rows


def test_market_no_vig_exact_normalization_and_fair_score():
    p = research.no_vig_market((2.0, 3.5, 4.0))
    assert len(p) == 3 and sum(p) == pytest.approx(1.0, abs=1e-15)
    assert p[0] == pytest.approx(.5 / (.5 + 1 / 3.5 + .25))
    assert max(range(3), key=lambda i: p[i]) == 0
    assert research.metrics([{"y": 0, "p": p}])["accuracy"] == 1.0
    assert research.metrics([{"y": 2, "p": p}])["accuracy"] == 0.0


@pytest.mark.parametrize("odds", [
    (1, 3, 2), (0, 3, 2), (None, 3, 2),
    (float("nan"), 3, 2), (float("inf"), 3, 2),
    (2, 3), (2, 3, 4, 5), (True, 3, 2),
])
def test_market_floor_rejects_missing_ambiguous_or_invalid_prices(odds):
    with pytest.raises(ValueError):
        research.no_vig_market(odds)


def test_future_match_outcomes_do_not_enter_its_own_features():
    previous = fixture(1, day="2019-08-09", result="H")
    test_match = fixture(2, day="2019-08-10", result="H")
    last = fixture(3, day="2019-08-11", result="A")
    a = research.historical_examples([previous, test_match, last])
    changed = research.historical_examples([previous, {**test_match, "result": "A"}, last])
    assert a[1]["f"] == changed[1]["f"]       # no same-match result leakage
    assert a[2]["f"] != changed[2]["f"]       # prior result legitimately affects next match
    assert a[1]["p"] == changed[1]["p"]
    assert a[1]["y"] != changed[1]["y"]


def test_rejects_protected_future_outcomes_and_duplicates():
    rows = [fixture(1, day="2025-08-01", result="H")]
    with pytest.raises(ValueError, match="protected newer result"):
        research.historical_examples(rows)
    item = fixture(1, day="2020-08-01", result="H")
    with pytest.raises(ValueError, match="duplicate"):
        research.historical_examples([item, item])
    with pytest.raises(ValueError, match="invalid historical teams"):
        research.historical_examples([{**item, "away_team": "A"}])


def test_selection_is_strictly_prior_validation_and_falls_back_to_market(monkeypatch):
    # An unchanged residual score cannot qualify as genuine AI improvement.
    def unchanged(rows, dim, l2, **kwargs):
        return tuple(tuple(0.0 for _ in range(dim)) for _ in range(3))
    monkeypatch.setattr(research, "fit_market_residual", unchanged)
    output = research.evaluate_historical_market_floor(dataset())
    assert output["samples"] == {"training": 120, "validation": 120, "heldout": 120}
    assert output["candidates_considered_on_validation"] == 64
    assert output["candidate_accepted_on_validation"] is False
    assert output["selected_candidate"] is None
    assert output["selected_or_floor_heldout"] == output["market_heldout"]
    assert output["conclusion"] == "MARKET_FLOOR_ONLY_NO_AI_UPLIFT"
    assert output["not_worse_than_market_on_heldout"] is True
    assert output["market_only_is_not_ai_model"] is True
    assert output["automatic_promotion"] is False
    assert output["production_artifact_written"] is False
    assert output["no_bet"] is True and output["roi"] is None
    assert output["provider_calls"] == 0
    assert "fixture_ids" not in output and "individual_predictions" not in output


def test_heldout_failure_cannot_be_hidden_by_selecting_after_results(monkeypatch):
    # An artificial candidate truly improves VALIDATION (HOME every match),
    # but is worse on HELDOUT (AWAY every match). No post-hoc retuning or PASS.
    def misleading(rows, dimension, l2, **kwargs):
        return tuple(
            tuple((2.0 if j == 0 and k == 0 else 0.0) for k in range(dimension))
            for j in range(3)
        )
    monkeypatch.setattr(research, "fit_market_residual", misleading)
    output = research.evaluate_historical_market_floor(dataset())
    assert output["candidate_accepted_on_validation"] is True
    assert output["selected_candidate"] is not None
    assert output["not_worse_than_market_on_heldout"] is False
    assert output["conclusion"] == "RESEARCH_CANDIDATE_FAILED_HELDOUT"
    assert output["selected_or_floor_heldout"]["log_loss"] > output["market_heldout"]["log_loss"]
    assert output["automatic_promotion"] is False


def test_split_preserves_chronological_out_of_sample_boundary():
    rows = research.historical_examples(dataset())
    train, valid, test = research.split_examples(rows)
    assert len(train) == len(valid) == len(test) == 120
    assert max(r["date"] for r in train) < min(r["date"] for r in valid)
    assert max(r["date"] for r in valid) < min(r["date"] for r in test)
    assert research.TRAIN_END == "2022-08-01"
    assert research.VALID_END == "2023-08-01"
    assert research.HISTORY_END_EXCLUSIVE == "2025-08-01"


def test_read_boundary_is_fixed_and_no_provider_or_writes_in_module():
    code = Path("epl_market_floor_v1.py").read_text(encoding="utf-8")
    assert "HISTORY_END_EXCLUSIVE = \"2025-08-01\"" in code
    assert '.lt("match_date", HISTORY_END_EXCLUSIVE)' in code
    assert 'client.table("matches").select(' in code
    for disallowed in ["api.the-odds-api.com", ".upsert(", ".insert(", ".delete(",
                       ".update(", "joblib.dump(", "pickle.dump(", "football_model_xgboost_elo.pkl"]:
        assert disallowed not in code
    assert "market_only_is_not_ai_model" in code
    assert "historical_odds_timestamp_qualified" in code
