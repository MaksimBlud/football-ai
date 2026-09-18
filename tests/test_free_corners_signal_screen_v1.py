import math

import numpy as np
import pandas as pd

import free_corners_signal_screen_v1 as s


def test_frozen_free_contract_constants():
    assert s.EXPERIMENT_ID == "FREE_CORNERS_SIGNAL_SCREEN_V1"
    assert set(s.LEAGUES) == {"EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1"}
    assert s.FIXTURES_PER_LEAGUE == 11
    assert s.LIST_PER_PAGE == 50
    assert s.MAX_PROVIDER_REQUESTS == 60
    assert s.REQUEST_INTERVAL_SECONDS >= 3.0
    assert s.MIN_PRIOR_MATCHES == 10
    assert s.MIN_POOLED_ROWS == 40
    assert s.BLEND_WEIGHT_FOOTBALL == 0.25
    assert s.BOOTSTRAP_SEED == 20260917


def test_canonical_team_explicit_aliases_only():
    assert s.canonical_team("Manchester United") == s.canonical_team("Man Utd")
    assert s.canonical_team("CD Alaves") == s.canonical_team("Alaves")
    assert s.canonical_team("Inter Milan") == s.canonical_team("Inter")
    assert s.canonical_team("Borussia Monchengladbach") == s.canonical_team("M'gladbach")
    assert s.canonical_team("Paris Saint-Germain") == s.canonical_team("Paris SG")
    assert s.canonical_team("Completely Different Club") == "completelydifferentclub"


def test_fixture_row_requires_finished_identity_score_and_corners():
    raw = {
        "id": 123,
        "kickoff_utc": "2026-09-10T18:00:00+00:00",
        "status": "finished",
        "teams": {"home": {"name": "Manchester United"}, "away": {"name": "Man City"}},
        "goals": {"home": 2, "away": 1},
        "corners": {"home": 6, "away": 4},
        "cards": {"home": {"yellow": 1, "red": 0}, "away": {"yellow": 2, "red": 0}},
    }
    row = s._fixture_row(raw, "EPL")
    assert row["fixture_id"] == "123"
    assert row["HomeTeam"] == "manunited"
    assert row["AwayTeam"] == "mancity"
    assert row["FTR"] == "H"
    assert row["HC"] + row["AC"] == 10
    assert s._fixture_row({**raw, "status": "scheduled"}, "EPL") is None
    assert s._fixture_row({**raw, "corners": None}, "EPL") is None


def test_opening_parser_uses_bet365_and_requires_both_prices():
    fixture = {"fixture_id": "1", "league": "EPL", "kickoff_utc": "2026-09-01T12:00:00+00:00", "provider_home_team": "A", "provider_away_team": "B"}
    payload = {
        "success": 1,
        "data": {"bookmakers": [
            {"slug": "other", "odds": {"corner_line": {"opening": {"line": 8.5, "over": 1.8, "under": 2.0}}}},
            {"slug": "bet365", "odds": {"corner_line": {"opening": {"line": 9.5, "over": 1.9, "under": 1.9}}}},
        ]},
    }
    row = s._opening_from_odds_payload(payload, fixture)
    assert row["opening_line"] == 9.5
    assert row["opening_over"] == 1.9
    bad = {"success": 1, "data": {"bookmakers": [{"slug": "bet365", "odds": {"corner_line": {"opening": {"line": 9.5, "over": 1.9}}}}]}}
    assert s._opening_from_odds_payload(bad, fixture) is None


def test_market_devig_and_supported_lines():
    assert math.isclose(s._market_probability(1.9, 1.9), 0.5)
    assert s._line_kind(9.0) == "integer"
    assert s._line_kind(9.5) == "half"
    assert s._line_kind(9.25) is None
    assert s._line_kind(9.75) is None


def test_football_probability_half_and_integer_are_valid():
    half = s._football_probability(10.0, 9.5)
    integer = s._football_probability(10.0, 10.0)
    assert 0 < half < 1
    assert 0 < integer < 1
    # Symmetry around an integer Poisson mean after conditioning away the push.
    assert abs(integer - 0.5) < 0.1


def test_scores_reward_better_probabilities():
    y = np.array([1.0, 0.0, 1.0, 0.0])
    good = s._scores(y, np.array([0.8, 0.2, 0.7, 0.3]))
    bad = s._scores(y, np.array([0.2, 0.8, 0.3, 0.7]))
    assert good["brier"] < bad["brier"]
    assert good["log_loss"] < bad["log_loss"]


def test_bootstrap_alignment_is_deterministic():
    terms = np.array([0.1, 0.2, -0.05, 0.15, 0.1])
    a = s._bootstrap_alignment(terms)
    b = s._bootstrap_alignment(terms)
    assert a == b
    assert a[0] < a[1]


def test_cache_loader_uses_fixture_id(tmp_path):
    p = tmp_path / "cache.jsonl"
    p.write_text('{"fixture_id":"123","opening_line":9.5,"opening_over":1.9,"opening_under":1.9}\n')
    cache = s.load_market_cache(p)
    assert set(cache) == {"123"}
    assert cache["123"]["opening_line"] == 9.5


def test_load_history_dir_reads_frozen_local_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(s, "LEAGUES", {"EPL": {"competition_code": "E0"}})
    monkeypatch.setattr(s, "TRAIN_SEASONS", (("1617", "2016-17"),))
    d = tmp_path / "EPL"
    d.mkdir()
    pd.DataFrame([{
        "Date": "13/08/2016", "HomeTeam": "Man Utd", "AwayTeam": "Man City",
        "HC": 5, "AC": 4, "FTHG": 1, "FTAG": 0, "FTR": "H"
    }]).to_csv(d / "1617.csv", index=False)
    out = s._load_history_dir(tmp_path)
    assert list(out) == ["EPL"]
    assert out["EPL"].iloc[0]["season"] == "2016-17"
    assert out["EPL"].iloc[0]["HomeTeam"] == s.canonical_team("Man Utd")


def test_load_replay_inputs_requires_exact_selected_market_ids(monkeypatch, tmp_path):
    monkeypatch.setattr(s, "LEAGUES", {"EPL": {"competition_code": "E0"}})
    monkeypatch.setattr(s, "FIXTURES_PER_LEAGUE", 1)
    (tmp_path / "raw" / "fixtures").mkdir(parents=True)
    (tmp_path / "normalized").mkdir(parents=True)
    raw = {
        "id": 123,
        "kickoff_utc": "2026-09-10T18:00:00+00:00",
        "status": "finished",
        "teams": {"home": {"name": "Man Utd"}, "away": {"name": "Man City"}},
        "goals": {"home": 1, "away": 0},
        "corners": {"home": 5, "away": 4},
        "cards": {"home": {"yellow": 1, "red": 0}, "away": {"yellow": 1, "red": 0}},
    }
    (tmp_path / "raw" / "fixtures" / "EPL.json").write_text(
        __import__("json").dumps({"success": 1, "data": [raw]})
    )
    selected = {"EPL": [{
        "fixture_id": "123", "league": "EPL", "kickoff_utc": raw["kickoff_utc"],
        "provider_home_team": "Man Utd", "provider_away_team": "Man City",
    }]}
    (tmp_path / "selected_fixtures.json").write_text(__import__("json").dumps(selected))
    (tmp_path / "normalized" / "opening_corner_markets.jsonl").write_text(
        '{"fixture_id":"123","league":"EPL","opening_line":9.5,"opening_over":1.9,"opening_under":1.9}\n'
    )
    got_selected, current_rows, markets = s._load_replay_inputs(tmp_path)
    assert got_selected["EPL"][0]["fixture_id"] == "123"
    assert current_rows[0]["fixture_id"] == "123"
    assert markets[0]["fixture_id"] == "123"
