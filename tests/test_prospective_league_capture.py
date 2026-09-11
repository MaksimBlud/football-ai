from __future__ import annotations

import csv
from pathlib import Path

import pytest

from prospective_league_capture import PROTOCOL, TARGET_N, capture_market_only, validate_capture


def _row(**overrides):
    row = {
        "league": "SERIE_A",
        "home_team": "Inter",
        "away_team": "Juventus",
        "commence_time_utc": "2026-09-12T18:45:00+00:00",
        "captured_at_utc": "2026-09-11T22:00:00+00:00",
        "home_odds": 2.0,
        "draw_odds": 3.4,
        "away_odds": 3.8,
    }
    row.update(overrides)
    return row


def test_accepts_pre_match_market_only_for_both_leagues(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    first = capture_market_only(_row(), ledger)
    second = capture_market_only(
        _row(
            league="LA_LIGA",
            home_team="Real Sociedad",
            away_team="Villarreal",
            commence_time_utc="2026-09-13T16:30:00Z",
        ),
        ledger,
    )
    assert first.status == "INSERTED"
    assert second.status == "INSERTED"
    assert first.observation_number == 1
    assert second.observation_number == 1
    assert first.target_n == TARGET_N == 100
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    assert {r["league"] for r in rows} == {"SERIE_A", "LA_LIGA"}
    assert all(r["protocol"] == PROTOCOL for r in rows)


def test_rejects_post_kickoff_capture():
    with pytest.raises(ValueError, match="strictly before kickoff"):
        validate_capture(_row(captured_at_utc="2026-09-12T18:45:00Z"))


def test_rejects_outcome_fields_at_capture_time():
    with pytest.raises(ValueError, match="forbidden outcome"):
        validate_capture(_row(home_score=1, away_score=0))


def test_rejects_ai_fields_without_separate_eligibility_manifest():
    with pytest.raises(ValueError, match="AI fields are forbidden"):
        validate_capture(_row(ai_home_probability=0.52))


def test_does_not_accept_epl_or_other_leagues():
    with pytest.raises(ValueError, match="unsupported league"):
        validate_capture(_row(league="EPL"))


def test_duplicate_is_idempotent_and_conflict_fails_closed(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    first = capture_market_only(_row(), ledger)
    again = capture_market_only(_row(), ledger)
    assert first.observation_number == again.observation_number == 1
    assert again.unchanged is True
    with pytest.raises(ValueError, match="conflicting rewrite"):
        capture_market_only(_row(home_odds=1.95), ledger)


def test_no_production_model_dependency():
    import inspect
    import prospective_league_capture as module

    source = inspect.getsource(module)
    assert ".pkl" not in source
    assert "football_model" not in source
    assert "supabase" not in source.lower()
    assert "odds_api" not in source.lower()
