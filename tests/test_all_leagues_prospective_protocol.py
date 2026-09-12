from pathlib import Path


PROTOCOL = (
    Path(__file__).parents[1]
    / "research"
    / "ALL_LEAGUES_PROSPECTIVE_CAPTURE_V1.md"
)

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


def _text() -> str:
    return PROTOCOL.read_text(encoding="utf-8")


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
