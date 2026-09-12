import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROTOCOL = ROOT / "research" / "ALL_LEAGUES_PROSPECTIVE_CAPTURE_V1.md"
SUCCESSOR_PROTOCOL = ROOT / "research" / "ALL_LEAGUES_PROSPECTIVE_CAPTURE_V1_1.md"
SUCCESSOR_MANIFEST = ROOT / "research" / "ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json"

LEAGUES = (
    "EPL",
    "LA_LIGA",
    "SERIE_A",
    "BUNDESLIGA",
    "LIGUE_1",
    "EREDIVISIE",
    "TURKEY_SUPER_LIG",
    "PRIMEIRA_LIGA",
)

SUCCESSOR_COUNTS = {
    "BUNDESLIGA": 17,
    "EPL": 20,
    "EREDIVISIE": 18,
    "LA_LIGA": 19,
    "LIGUE_1": 17,
    "PRIMEIRA_LIGA": 9,
    "SERIE_A": 19,
    "TURKEY_SUPER_LIG": 8,
}


def _text() -> str:
    return PROTOCOL.read_text(encoding="utf-8")


def _successor_text() -> str:
    return SUCCESSOR_PROTOCOL.read_text(encoding="utf-8")


def _manifest() -> dict:
    return json.loads(SUCCESSOR_MANIFEST.read_text(encoding="utf-8"))


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_protocol_freezes_exactly_all_eight_operational_leagues():
    text = _text()

    for league in LEAGUES:
        assert f"`{league}`" in text

    assert "Scope: 8 leagues" in text
    assert "ALL_LEAGUES_MARKET_ONLY_V1" in text


def test_protocol_t0_is_atomic_and_not_backdated():
    text = _text()

    assert "T0_COMMIT" in text
    assert "T0_UTC" in text
    assert "merge commit that first introduces this file into `main`" in text
    assert "begins strictly after `T0_UTC`" in text
    assert "not retroactively admitted" in text
    assert "133 fresh 2026-09-11 market events" in text


def test_protocol_is_pre_kickoff_market_only_and_no_peek():
    text = _text()

    assert "`MARKET_ONLY` only" in text
    assert "`structural_applied` must be false" in text
    assert "`prediction_time_utc < kickoff_utc`" in text
    assert "`snapshot_time_utc < kickoff_utc`" in text
    assert "Outcome, score, winner, settlement" in text
    assert "No result/outcome source may be queried" in text
    assert "production `.pkl`" in text
    assert "model promotion is outside scope" in text


def test_completeness_expected_side_cannot_be_derived_from_captured_rows():
    text = _text()

    assert "`all_leagues_capture_gate.py`" in text
    assert "`expected_event_ids` must be frozen before" in text
    assert "independent of the rows later read back from `odds_snapshots`" in text
    assert "forbidden to construct `expected_event_ids`" in text
    assert "completeness check circular" in text
    assert "`MISSING`" in text
    assert "`UNEXPECTED`" in text


def test_evaluation_metrics_and_stricter_existing_contracts_are_frozen():
    text = _text()

    assert "multiclass log loss" in text
    assert "multiclass Brier score" in text
    assert "1X2 argmax accuracy" in text
    assert "reported per league and pooled" in text
    assert "the stricter gate wins" in text
    assert "grants no paid API permission" in text


def test_successor_manifest_freezes_exactly_127_unique_prediction_keys():
    manifest = _manifest()

    assert manifest["schema_version"] == "all_leagues_market_only_v1_1_manifest_v1"
    assert manifest["experiment"] == "ALL_LEAGUES_MARKET_ONLY_V1_1"
    assert manifest["original_t0_utc"] == "2026-09-12T01:51:19Z"
    assert manifest["freeze_utc"] == "2026-09-12T02:04:34Z"
    assert manifest["event_count"] == 127
    assert set(manifest["leagues"]) == set(LEAGUES)

    keys = []
    for league, expected_count in SUCCESSOR_COUNTS.items():
        entry = manifest["leagues"][league]
        assert entry["event_count"] == expected_count
        assert len(entry["prediction_keys"]) == expected_count
        assert entry["prediction_keys"] == sorted(entry["prediction_keys"])
        assert all(key.startswith(f"{league}:") for key in entry["prediction_keys"])
        keys.extend(entry["prediction_keys"])

    assert len(keys) == 127
    assert len(set(keys)) == 127


def test_successor_seed_was_frozen_before_every_seed_league_first_kickoff():
    manifest = _manifest()
    freeze = _utc(manifest["freeze_utc"])
    original_t0 = _utc(manifest["original_t0_utc"])

    assert original_t0 < freeze
    for entry in manifest["leagues"].values():
        assert freeze < _utc(entry["first_kickoff_utc"])
        assert _utc(entry["first_kickoff_utc"]) <= _utc(entry["last_kickoff_utc"])


def test_successor_is_separate_from_v1_and_excludes_already_started_matches():
    text = _successor_text()

    assert "V1 remains frozen and is not edited or reinterpreted" in text
    assert "separate successor cohort rather than weakening V1 retroactively" in text
    assert "six 2026-09-11 matches" in text
    assert "explicitly excluded" in text
    assert "must never be backfilled into V1.1" in text
    assert "exact frozen 127-key seed manifest" in text
    assert "plus\n2. future qualifying MARKET_ONLY captures" in text


def test_successor_preserves_no_peek_paid_and_production_boundaries():
    text = _successor_text()

    assert "no result, score, winner, settlement or other outcome source was read" in text
    assert "No prospective outcome may be used" in text
    assert "does not open any result table" in text
    assert "grants no paid API permission" in text
    assert "Production `.pkl` artifacts remain outside this research capture path" in text
    assert "A stricter existing league-specific gate wins" in text
