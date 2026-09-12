import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from all_leagues_market_only_v1_1_gate import (
    MIN_KICKOFF_MONTHS_PER_LEAGUE,
    MIN_UNIQUE_EVENTS_PER_LEAGUE,
    OUTCOME_DELAY_HOURS,
    V1_1_FREEZE_UTC,
    evaluate_gate,
    select_event_rows,
)


ROOT = Path(__file__).parents[1]
PROTOCOL = ROOT / "research" / "ALL_LEAGUES_PROSPECTIVE_CAPTURE_V1.md"
SUCCESSOR_PROTOCOL = ROOT / "research" / "ALL_LEAGUES_PROSPECTIVE_CAPTURE_V1_1.md"
SUCCESSOR_MANIFEST = ROOT / "research" / "ALL_LEAGUES_MARKET_ONLY_V1_1_MANIFEST.json"
EVALUATION_GATE = ROOT / "research" / "ALL_LEAGUES_MARKET_ONLY_V1_1_EVALUATION_GATE.json"

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


def _gate_contract() -> dict:
    return json.loads(EVALUATION_GATE.read_text(encoding="utf-8"))


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _row(league: str, event_id: str, kickoff: datetime, prediction_time: datetime | None = None) -> dict:
    prediction_time = prediction_time or kickoff - timedelta(days=1)
    return {
        "league": league,
        "event_id": event_id,
        "prediction_key": f"{league}:{event_id}",
        "kickoff_utc": kickoff.isoformat(),
        "prediction_time_utc": prediction_time.isoformat(),
        "snapshot_time_utc": (prediction_time - timedelta(minutes=1)).isoformat(),
        "prediction_mode": "MARKET_ONLY",
        "structural_applied": False,
        "market_home_prob": 0.4,
        "market_draw_prob": 0.3,
        "market_away_prob": 0.3,
    }


def _mature_rows() -> list[dict]:
    rows = []
    months = (9, 10, 11, 12)
    for league in LEAGUES:
        for month in months:
            kickoff = datetime(2026, month, 15, 12, 0, tzinfo=timezone.utc)
            for index in range(25):
                rows.append(_row(league, f"{month:02d}-{index:02d}", kickoff))
    return rows


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


def test_v1_1_evaluation_gate_freezes_existing_project_sample_conventions():
    gate = _gate_contract()

    assert gate["schema_version"] == "all_leagues_market_only_v1_1_evaluation_gate_v1"
    assert gate["experiment"] == "ALL_LEAGUES_MARKET_ONLY_V1_1"
    assert set(gate["scope"]["leagues"]) == set(LEAGUES)
    assert gate["sample_gate"]["minimum_unique_events_per_league"] == 100
    assert gate["sample_gate"]["minimum_kickoff_calendar_months_per_league"] == 4
    assert gate["outcome_embargo"]["minimum_delay_hours_after_latest_primary_prefix_kickoff"] == 24
    assert gate["outcome_embargo"]["scores_results_winners_settlements_forbidden_before_gate"] is True
    assert gate["outcome_embargo"]["common_gate_never_overrides_stricter_existing_gate"] is True
    assert gate["evaluation"]["primary_metrics"] == ["multiclass_log_loss", "multiclass_brier"]
    assert gate["evaluation"]["secondary_metrics"] == ["1x2_argmax_accuracy"]
    assert gate["evaluation"]["primary_interpretation"].startswith("descriptive frozen market baseline")

    assert MIN_UNIQUE_EVENTS_PER_LEAGUE == 100
    assert MIN_KICKOFF_MONTHS_PER_LEAGUE == 4
    assert OUTCOME_DELAY_HOURS == 24


def test_seed_key_precedence_allows_frozen_pre_freeze_seed_but_not_other_pre_freeze_rows():
    kickoff = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)
    seed = _row("EPL", "seed", kickoff, prediction_time=V1_1_FREEZE_UTC - timedelta(hours=1))
    old_nonseed = _row("EPL", "old", kickoff, prediction_time=V1_1_FREEZE_UTC - timedelta(hours=1))

    selected = select_event_rows([seed, old_nonseed], seed_keys=frozenset({seed["prediction_key"]}))

    assert [row["event_id"] for row in selected] == ["seed"]


def test_future_event_uses_earliest_qualifying_post_freeze_prediction():
    kickoff = datetime(2026, 9, 13, 14, 0, tzinfo=timezone.utc)
    early = _row("EPL", "future", kickoff, prediction_time=V1_1_FREEZE_UTC + timedelta(hours=1))
    late = dict(_row("EPL", "future", kickoff, prediction_time=V1_1_FREEZE_UTC + timedelta(hours=2)))
    late["prediction_key"] = "EPL:future-late"

    selected = select_event_rows([late, early], seed_keys=frozenset())

    assert len(selected) == 1
    assert selected[0]["prediction_key"] == early["prediction_key"]


def test_gate_remains_sample_closed_until_every_league_has_100_events_and_four_months():
    rows = [
        row
        for row in _mature_rows()
        if not (row["league"] == "TURKEY_SUPER_LIG" and row["event_id"] == "12-24")
    ]

    result = evaluate_gate(
        rows,
        now_utc=datetime(2027, 1, 1, tzinfo=timezone.utc),
        seed_keys=frozenset(),
        stricter_gate_clear=True,
    )

    assert result["status"] == "SAMPLE_CLOSED"
    assert result["outcome_read_allowed"] is False
    assert result["per_league"]["TURKEY_SUPER_LIG"]["selected_events"] == 99
    assert result["per_league"]["TURKEY_SUPER_LIG"]["sample_ready"] is False


def test_gate_requires_24_hours_after_latest_mature_prefix_kickoff():
    rows = _mature_rows()

    result = evaluate_gate(
        rows,
        now_utc=datetime(2026, 12, 15, 13, 0, tzinfo=timezone.utc),
        seed_keys=frozenset(),
        stricter_gate_clear=True,
    )

    assert result["status"] == "TIME_CLOSED"
    assert result["outcome_read_allowed"] is False
    assert result["latest_primary_prefix_kickoff_utc"] == "2026-12-15T12:00:00Z"
    assert result["outcome_read_not_before_utc"] == "2026-12-16T12:00:00Z"


def test_gate_fails_closed_when_an_applicable_stricter_contract_is_not_clear():
    result = evaluate_gate(
        _mature_rows(),
        now_utc=datetime(2026, 12, 17, 12, 0, tzinfo=timezone.utc),
        seed_keys=frozenset(),
        stricter_gate_clear=False,
    )

    assert result["status"] == "STRICTER_GATE_CLOSED"
    assert result["outcome_read_allowed"] is False


def test_gate_allows_outcome_read_only_after_sample_time_and_stricter_gates_clear():
    result = evaluate_gate(
        _mature_rows(),
        now_utc=datetime(2026, 12, 17, 12, 0, tzinfo=timezone.utc),
        seed_keys=frozenset(),
        stricter_gate_clear=True,
    )

    assert result["status"] == "OUTCOME_READ_ALLOWED"
    assert result["outcome_read_allowed"] is True
    assert all(entry["sample_ready"] for entry in result["per_league"].values())
    assert all(entry["primary_prefix_events"] == 100 for entry in result["per_league"].values())
