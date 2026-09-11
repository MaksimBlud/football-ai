from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from bundesliga_prospective_capture import (
    LEAGUE,
    PROTOCOL,
    TARGET_N,
    capture_market_only,
    validate_capture,
    validate_ledger,
)

FROZEN_NON_EPL_LEDGER_SHA256 = "97008bbb3bdb9172be8a617b24ca3dc126bcc834db1292cb791101fbe4d37d1d"


def _row(**overrides):
    row = {
        "league": LEAGUE,
        "source_event_id": "event-bundesliga-001",
        "source_snapshot_time_utc": "2026-09-11T08:00:00+00:00",
        "home_team": "Bayern Munich",
        "away_team": "Borussia Dortmund",
        "commence_time_utc": "2026-09-12T18:30:00+00:00",
        "captured_at_utc": "2026-09-11T10:00:00+00:00",
        "home_odds": 1.85,
        "draw_odds": 4.0,
        "away_odds": 4.2,
    }
    row.update(overrides)
    return row


def test_accepts_bundesliga_market_only(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    result = capture_market_only(_row(), ledger)
    assert result.status == "INSERTED"
    assert result.league == LEAGUE
    assert result.protocol == PROTOCOL
    assert result.observation_number == 1
    assert result.target_n == TARGET_N == 100
    assert validate_ledger(ledger) == 1
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    assert rows[0]["canonical_key"].endswith(f"|{PROTOCOL}")
    assert rows[0]["source_event_id"] == "event-bundesliga-001"


def test_rejects_other_leagues():
    for league in ("EPL", "SERIE_A", "LA_LIGA", "LIGUE_1"):
        with pytest.raises(ValueError, match="unsupported league"):
            validate_capture(_row(league=league))


def test_rejects_post_kickoff_capture_and_snapshot():
    with pytest.raises(ValueError, match="strictly before kickoff"):
        validate_capture(_row(captured_at_utc="2026-09-12T18:30:00Z"))
    with pytest.raises(ValueError, match="source market snapshot must be strictly before kickoff"):
        validate_capture(_row(source_snapshot_time_utc="2026-09-12T18:30:00Z"))
    with pytest.raises(ValueError, match="cannot be later than captured_at_utc"):
        validate_capture(_row(source_snapshot_time_utc="2026-09-11T10:00:01Z"))


def test_requires_provenance_and_valid_market():
    with pytest.raises(ValueError, match="source_event_id"):
        validate_capture(_row(source_event_id=""))
    with pytest.raises(ValueError, match="source_snapshot_time_utc"):
        validate_capture(_row(source_snapshot_time_utc=""))
    with pytest.raises(ValueError, match="invalid decimal odds"):
        validate_capture(_row(home_odds=1.0))


def test_rejects_outcome_and_ai_fields():
    with pytest.raises(ValueError, match="forbidden outcome"):
        validate_capture(_row(result="H"))
    with pytest.raises(ValueError, match="AI fields are forbidden"):
        validate_capture(_row(ai_home_probability=0.6))


def test_duplicate_is_idempotent_and_conflicting_rewrite_fails_closed(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    first = capture_market_only(_row(), ledger)
    again = capture_market_only(_row(), ledger)
    assert first.observation_number == again.observation_number == 1
    assert again.unchanged is True
    with pytest.raises(ValueError, match="conflicting rewrite"):
        capture_market_only(_row(home_odds=1.9), ledger)
    with pytest.raises(ValueError, match="conflicting rewrite"):
        capture_market_only(_row(source_event_id="different-event"), ledger)


def test_sequence_corruption_fails_closed(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    capture_market_only(_row(), ledger)
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    rows[0]["observation_number"] = "2"
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="not contiguous"):
        validate_ledger(ledger)


def test_target_overflow_fails_closed(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    base = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    for index in range(TARGET_N):
        kickoff = base + timedelta(days=index)
        capture_market_only(
            _row(
                source_event_id=f"event-{index}",
                source_snapshot_time_utc=(kickoff - timedelta(days=2)).isoformat(),
                captured_at_utc=(kickoff - timedelta(days=1)).isoformat(),
                commence_time_utc=kickoff.isoformat(),
                home_team=f"Home {index}",
                away_team=f"Away {index}",
            ),
            ledger,
        )
    assert validate_ledger(ledger) == TARGET_N
    with pytest.raises(ValueError, match="target already reached"):
        kickoff = base + timedelta(days=TARGET_N + 1)
        capture_market_only(
            _row(
                source_event_id="event-overflow",
                source_snapshot_time_utc=(kickoff - timedelta(days=2)).isoformat(),
                captured_at_utc=(kickoff - timedelta(days=1)).isoformat(),
                commence_time_utc=kickoff.isoformat(),
                home_team="Overflow Home",
                away_team="Overflow Away",
            ),
            ledger,
        )


def test_committed_bundesliga_ledger_is_valid_when_present():
    ledger = Path("experiments/bundesliga_market_only_v1.csv")
    if ledger.exists():
        count = validate_ledger(ledger)
        assert 0 < count <= TARGET_N


def test_existing_serie_a_la_liga_frozen_ledger_is_untouched():
    path = Path("experiments/non_epl_market_only_v1.csv")
    assert path.exists()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == FROZEN_NON_EPL_LEDGER_SHA256


def test_no_production_or_live_provider_dependency():
    import inspect
    import bundesliga_prospective_capture as module

    source = inspect.getsource(module).lower()
    assert ".pkl" not in source
    assert "football_model" not in source
    assert "supabase" not in source
    assert "odds_api" not in source
