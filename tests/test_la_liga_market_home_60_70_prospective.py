import pandas as pd
import pytest

from la_liga_market_home_60_70_prospective import (
    IMPLEMENTATION_FREEZE_UTC,
    build_canonical_decisions,
    descriptive_evaluation,
)


def _ledger_row(event_id: str, snapshot: str, kickoff: str, home_prob: float, *, home="Home", away="Away"):
    draw = 0.25
    away_prob = 1.0 - home_prob - draw
    pick = "H" if home_prob >= max(draw, away_prob) else ("D" if draw >= away_prob else "A")
    return {
        "prediction_key": f"k-{event_id}-{snapshot}",
        "league": "LA_LIGA",
        "event_id": event_id,
        "home_team": home,
        "away_team": away,
        "kickoff_utc": kickoff,
        "snapshot_time_utc": snapshot,
        "market_home_prob": home_prob,
        "market_draw_prob": draw,
        "market_away_prob": away_prob,
        "market_pick": pick,
        "prediction_mode": "MARKET_ONLY",
    }


def _odds_row(source):
    return {
        "league": source["league"],
        "event_id": source["event_id"],
        "snapshot_time_utc": source["snapshot_time_utc"],
        "commence_time_utc": source["kickoff_utc"],
        "home_team": source["home_team"],
        "away_team": source["away_team"],
        "home_odds": 1.0 / source["market_home_prob"],
        "draw_odds": 1.0 / source["market_draw_prob"],
        "away_odds": 1.0 / source["market_away_prob"],
    }


def test_lower_bound_is_inclusive_and_upper_bound_exclusive():
    kickoff = "2026-09-12T18:00:00Z"
    rows = [
        _ledger_row("a", "2026-09-12T14:00:00Z", kickoff, 0.60, home="A", away="B"),
        _ledger_row("b", "2026-09-12T14:00:00Z", kickoff, 0.699999, home="C", away="D"),
        _ledger_row("c", "2026-09-12T14:00:00Z", kickoff, 0.70, home="E", away="F"),
    ]
    decisions, _ = build_canonical_decisions(pd.DataFrame(rows), pd.DataFrame([_odds_row(r) for r in rows]), now_utc="2026-09-12T15:00:00Z")
    by_event = decisions.set_index("event_id")["candidate_qualifies"].to_dict()
    assert by_event == {"a": True, "b": True, "c": False}


def test_latest_durable_pre_kickoff_row_is_canonical_decision():
    kickoff = "2026-09-12T18:00:00Z"
    early = _ledger_row("e1", "2026-09-12T10:00:00Z", kickoff, 0.61)
    late = _ledger_row("e1", "2026-09-12T16:00:00Z", kickoff, 0.58)
    decisions, _ = build_canonical_decisions(
        pd.DataFrame([early, late]),
        pd.DataFrame([_odds_row(early), _odds_row(late)]),
        now_utc="2026-09-12T17:00:00Z",
    )
    assert len(decisions) == 1
    row = decisions.iloc[0]
    assert row["snapshot_time_utc"] == pd.Timestamp("2026-09-12T16:00:00Z")
    assert bool(row["candidate_qualifies"]) is False


def test_pre_freeze_snapshots_are_not_part_of_prospective_sample():
    kickoff = "2026-09-05T18:00:00Z"
    row = _ledger_row("old", "2026-09-04T16:59:59Z", kickoff, 0.62)
    decisions, audit = build_canonical_decisions(pd.DataFrame([row]), pd.DataFrame([_odds_row(row)]), now_utc="2026-09-04T17:10:00Z")
    assert decisions.empty
    assert audit["eligible_events"] == 0
    assert IMPLEMENTATION_FREEZE_UTC == pd.Timestamp("2026-09-04T17:00:00Z")


def test_multiple_provider_events_for_same_fixture_pair_are_excluded_fail_closed():
    a = _ledger_row("rev-a", "2026-09-10T12:00:00Z", "2026-09-12T18:00:00Z", 0.62)
    b = _ledger_row("rev-b", "2026-09-11T12:00:00Z", "2026-09-13T18:00:00Z", 0.63)
    decisions, audit = build_canonical_decisions(
        pd.DataFrame([a, b]),
        pd.DataFrame([_odds_row(a), _odds_row(b)]),
        now_utc="2026-09-11T13:00:00Z",
    )
    assert decisions.empty
    assert set(audit["conflict_events"]) == {"rev-a", "rev-b"}


def test_raw_odds_must_match_ledger_no_vig_probabilities():
    row = _ledger_row("x", "2026-09-12T14:00:00Z", "2026-09-12T18:00:00Z", 0.62)
    raw = _odds_row(row)
    raw["home_odds"] = 9.0
    with pytest.raises(RuntimeError, match="do not match"):
        build_canonical_decisions(pd.DataFrame([row]), pd.DataFrame([raw]), now_utc="2026-09-12T15:00:00Z")


def test_descriptive_state_is_based_on_actual_minus_market_expected_only():
    settled = pd.DataFrame([
        {
            "kickoff_utc": "2027-01-01T18:00:00Z",
            "result": "H",
            "home_odds": 1.8,
            "market_home_prob": 0.62,
        },
        {
            "kickoff_utc": "2027-01-08T18:00:00Z",
            "result": "A",
            "home_odds": 1.7,
            "market_home_prob": 0.61,
        },
    ])
    summary, monthly, state = descriptive_evaluation(settled)
    assert summary.iloc[0]["count"] == 2
    assert not monthly.empty
    assert state == "DIRECTIONALLY_INCONSISTENT"
