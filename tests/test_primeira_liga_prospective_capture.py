from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from primeira_liga_prospective_capture import (
    FIELDNAMES,
    LEAGUE,
    PROTOCOL,
    TARGET_N,
    capture_market_only,
    validate_capture,
    validate_ledger,
)

FROZEN_NON_EPL_LEDGER_SHA256 = "97008bbb3bdb9172be8a617b24ca3dc126bcc834db1292cb791101fbe4d37d1d"
FROZEN_BUNDESLIGA_LEDGER_SHA256 = "11e65c6367ec494ba5be208aff16ca4603ea53631c94794dd05412422c72b24c"
FROZEN_LIGUE1_LEDGER_SHA256 = "82745c83224c9b6fb2ae32ddfc2180c896628d2091011ccc56f6389a7f772788"
FROZEN_TURKEY_LEDGER_SHA256 = "442a2e6884c9ab82494e276deaf4620247cd0b8c20b4fcd7d438e7ad2d7e1ea2"


def _row(**overrides):
    row = {
        "league": LEAGUE,
        "source_event_id": "event-portugal-001",
        "source_snapshot_time_utc": "2026-09-11T08:00:00+00:00",
        "home_team": "Benfica",
        "away_team": "Porto",
        "commence_time_utc": "2026-09-12T20:00:00+00:00",
        "captured_at_utc": "2026-09-11T10:00:00+00:00",
        "home_odds": 2.05,
        "draw_odds": 3.5,
        "away_odds": 3.4,
    }
    row.update(overrides)
    return row


def test_accepts_primeira_liga_market_only(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    result = capture_market_only(_row(), ledger)
    assert result.status == "INSERTED"
    assert result.league == LEAGUE == "PRIMEIRA_LIGA"
    assert result.protocol == PROTOCOL == "PRIMEIRA_LIGA_MARKET_ONLY_V1"
    assert result.observation_number == 1
    assert result.target_n == TARGET_N == 100
    assert validate_ledger(ledger) == 1
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    assert rows[0]["canonical_key"].endswith(f"|{PROTOCOL}")
    assert rows[0]["source_event_id"] == "event-portugal-001"


def test_empty_canonical_ledger_is_valid_capture_ready_state(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    ledger.write_text(",".join(FIELDNAMES) + "\n", encoding="utf-8")
    assert validate_ledger(ledger) == 0


def test_rejects_other_leagues():
    for league in (
        "EPL", "SERIE_A", "LA_LIGA", "BUNDESLIGA", "LIGUE_1",
        "EREDIVISIE", "TURKEY_SUPER_LIG", "PRIMEIRA",
    ):
        with pytest.raises(ValueError, match="unsupported league"):
            validate_capture(_row(league=league))


def test_rejects_post_kickoff_capture_and_snapshot():
    with pytest.raises(ValueError, match="strictly before kickoff"):
        validate_capture(_row(captured_at_utc="2026-09-12T20:00:00Z"))
    with pytest.raises(ValueError, match="source market snapshot must be strictly before kickoff"):
        validate_capture(_row(source_snapshot_time_utc="2026-09-12T20:00:00Z"))
    with pytest.raises(ValueError, match="cannot be later than captured_at_utc"):
        validate_capture(_row(source_snapshot_time_utc="2026-09-11T10:00:01Z"))


def test_requires_provenance_and_valid_market():
    with pytest.raises(ValueError, match="source_event_id"):
        validate_capture(_row(source_event_id=""))
    with pytest.raises(ValueError, match="source_snapshot_time_utc"):
        validate_capture(_row(source_snapshot_time_utc=""))
    with pytest.raises(ValueError, match="invalid decimal odds"):
        validate_capture(_row(home_odds=1.0))
    with pytest.raises(ValueError, match="invalid decimal odds"):
        validate_capture(_row(draw_odds=float("nan")))


def test_rejects_outcome_ai_and_structural_fields():
    with pytest.raises(ValueError, match="forbidden outcome"):
        validate_capture(_row(result="H"))
    with pytest.raises(ValueError, match="AI/Structural fields are forbidden"):
        validate_capture(_row(ai_home_probability=0.6))
    with pytest.raises(ValueError, match="AI/Structural fields are forbidden"):
        validate_capture(_row(structural_score=0.2))


def test_duplicate_is_idempotent_and_conflicting_rewrite_fails_closed(tmp_path: Path):
    ledger = tmp_path / "ledger.csv"
    first = capture_market_only(_row(), ledger)
    again = capture_market_only(_row(), ledger)
    assert first.observation_number == again.observation_number == 1
    assert again.unchanged is True
    with pytest.raises(ValueError, match="conflicting rewrite"):
        capture_market_only(_row(home_odds=2.10), ledger)
    with pytest.raises(ValueError, match="conflicting rewrite"):
        capture_market_only(_row(source_event_id="different-event"), ledger)


def test_sequence_and_schema_corruption_fail_closed(tmp_path: Path):
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

    malformed = tmp_path / "malformed-empty.csv"
    malformed.write_text("league,protocol\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ledger schema mismatch"):
        validate_ledger(malformed)


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
    kickoff = base + timedelta(days=TARGET_N + 1)
    with pytest.raises(ValueError, match="target already reached"):
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


def test_committed_primeira_ledger_is_valid_and_starts_at_zero():
    ledger = Path("experiments/primeira_liga_market_only_v1.csv")
    assert ledger.exists()
    assert validate_ledger(ledger) == 0


def test_existing_frozen_prospective_ledgers_are_untouched():
    expected = {
        Path("experiments/non_epl_market_only_v1.csv"): FROZEN_NON_EPL_LEDGER_SHA256,
        Path("experiments/bundesliga_market_only_v1.csv"): FROZEN_BUNDESLIGA_LEDGER_SHA256,
        Path("experiments/ligue1_market_only_v1.csv"): FROZEN_LIGUE1_LEDGER_SHA256,
        Path("experiments/turkey_super_lig_market_only_v1.csv"): FROZEN_TURKEY_LEDGER_SHA256,
    }
    for path, digest in expected.items():
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_no_production_live_database_or_provider_dependency():
    import inspect
    import primeira_liga_prospective_capture as module

    source = inspect.getsource(module).lower()
    assert ".pkl" not in source
    assert "football_model" not in source
    assert "supabase" not in source
    assert "odds_api" not in source
    assert "requests" not in source
