import math
import pytest

from multi_market_oos_evaluator import (
    EvaluationContractError,
    evaluate,
    select_latest_event_snapshots,
    select_settlement_revisions,
    settlement_target,
)


def card(prob=0.6):
    return {
        "schema_version": "MULTI_MARKET_V1",
        "research_only": True,
        "handicap": {"home_probability": prob},
        "total_goals": {"over_probability": prob},
        "total_corners": {"over_probability": prob},
        "team_corners": {
            "home": {"over_probability": prob},
            "away": {"over_probability": prob},
        },
    }


def snapshot(event_id="e1", snapshot_key="s1", snapshot_time="2026-09-05T10:00:00+00:00", prob=0.6):
    return {
        "snapshot_key": snapshot_key,
        "league": "LA_LIGA",
        "event_id": event_id,
        "home_team": "Home",
        "away_team": "Away",
        "kickoff_utc": "2026-09-05T12:00:00+00:00",
        "snapshot_time_utc": snapshot_time,
        "payload": {
            "schema_version": "MULTI_MARKET_V1",
            "research_only": True,
            "card": card(prob),
        },
    }


def settlement(snapshot_row, completeness="GOALS_AND_CORNERS", statuses=None):
    statuses = statuses or {
        "handicap": "WIN",
        "total_goals": "HALF_WIN",
        "total_corners": "PUSH",
        "home_team_corners": "HALF_LOSS",
        "away_team_corners": "LOSS",
    }
    settled = {
        "schema_version": "MULTI_MARKET_SETTLEMENT_V2",
        "research_only": True,
        "handicap": {"home": {"status": statuses["handicap"]}},
        "total_goals": {"over": {"status": statuses["total_goals"]}},
        "total_corners": {"over": {"status": statuses["total_corners"]}},
        "team_corners": {
            "home": {"over": {"status": statuses["home_team_corners"]}},
            "away": {"over": {"status": statuses["away_team_corners"]}},
        },
    }
    return {
        "settlement_key": "k-" + snapshot_row["snapshot_key"] + "-" + completeness,
        "snapshot_key": snapshot_row["snapshot_key"],
        "league": snapshot_row["league"],
        "event_id": snapshot_row["event_id"],
        "home_team": snapshot_row["home_team"],
        "away_team": snapshot_row["away_team"],
        "kickoff_utc": snapshot_row["kickoff_utc"],
        "snapshot_time_utc": snapshot_row["snapshot_time_utc"],
        "outcome_completeness": completeness,
        "payload": {
            "schema_version": "MULTI_MARKET_SETTLEMENT_V2",
            "research_only": True,
            "settlement": settled,
        },
    }


def test_soft_target_mapping_is_frozen():
    assert settlement_target("WIN") == 1.0
    assert settlement_target("HALF_WIN") == 0.75
    assert settlement_target("PUSH") == 0.5
    assert settlement_target("HALF_LOSS") == 0.25
    assert settlement_target("LOSS") == 0.0
    assert settlement_target("INVALID") is None


def test_latest_pre_kickoff_snapshot_selected_once():
    old = snapshot(snapshot_key="old", snapshot_time="2026-09-05T08:00:00+00:00")
    new = snapshot(snapshot_key="new", snapshot_time="2026-09-05T11:59:00+00:00")
    selected = select_latest_event_snapshots([old, new])
    assert selected[("LA_LIGA", "e1")]["snapshot_key"] == "new"


def test_post_kickoff_snapshot_fails_closed():
    bad = snapshot(snapshot_time="2026-09-05T12:00:00+00:00")
    with pytest.raises(EvaluationContractError, match="strictly before"):
        select_latest_event_snapshots([bad])


def test_more_complete_settlement_revision_is_preferred():
    s = snapshot()
    goals = settlement(s, "GOALS_ONLY")
    full = settlement(s, "GOALS_AND_CORNERS")
    selected = select_settlement_revisions([goals, full])
    assert selected[s["snapshot_key"]]["outcome_completeness"] == "GOALS_AND_CORNERS"


def test_same_completeness_revision_is_ambiguous():
    s = snapshot()
    a = settlement(s)
    b = dict(a)
    b["settlement_key"] = "different"
    with pytest.raises(EvaluationContractError, match="ambiguous"):
        select_settlement_revisions([a, b])


def test_one_canonical_side_per_market_and_soft_losses():
    s = snapshot(prob=0.6)
    result = evaluate([s], [settlement(s)])
    assert result["selected_events"] == 1
    assert result["usable_observations"] == 5
    assert {row["market"] for row in result["observations"]} == {
        "handicap_home",
        "total_goals_over",
        "total_corners_over",
        "home_team_corners_over",
        "away_team_corners_over",
    }
    targets = {row["market"]: row["target"] for row in result["observations"]}
    assert targets["handicap_home"] == 1.0
    assert targets["total_goals_over"] == 0.75
    assert targets["total_corners_over"] == 0.5
    assert targets["home_team_corners_over"] == 0.25
    assert targets["away_team_corners_over"] == 0.0
    expected = (0.6 - 1.0) ** 2
    assert next(row for row in result["observations"] if row["market"] == "handicap_home")["brier"] == pytest.approx(expected)


def test_unsettled_and_invalid_probability_are_counted_not_silently_coerced():
    s = snapshot(prob=0.6)
    s["payload"]["card"]["total_goals"]["over_probability"] = 1.0
    statuses = {
        "handicap": "UNSETTLED_MISSING_OUTCOME",
        "total_goals": "WIN",
        "total_corners": "NOT_OFFERED",
        "home_team_corners": "INVALID",
        "away_team_corners": "LOSS",
    }
    result = evaluate([s], [settlement(s, statuses=statuses)])
    assert result["usable_observations"] == 1
    assert result["exclusions"]["UNSETTLED_MISSING_OUTCOME"] == 1
    assert result["exclusions"]["INVALID_OR_MISSING_PROBABILITY"] == 1
    assert result["exclusions"]["NOT_OFFERED"] == 1
    assert result["exclusions"]["INVALID"] == 1


def test_snapshot_settlement_identity_mismatch_fails_closed():
    s = snapshot()
    settled = settlement(s)
    settled["event_id"] = "wrong"
    with pytest.raises(EvaluationContractError, match="identity mismatch"):
        evaluate([s], [settled])


def test_missing_settlement_counts_all_preregistered_markets():
    result = evaluate([snapshot()], [])
    assert result["usable_observations"] == 0
    assert result["exclusions"] == {"MISSING_SETTLEMENT": 5}


def test_readiness_floor_is_thirty_unique_events():
    snapshots = []
    settlements = []
    for i in range(30):
        event_id = f"e{i}"
        key = f"s{i}"
        s = snapshot(event_id=event_id, snapshot_key=key)
        snapshots.append(s)
        settlements.append(settlement(s))
    result = evaluate(snapshots, settlements)
    assert len(result["per_league_market"]) == 5
    assert all(cell["sample_status"] == "READY" for cell in result["per_league_market"])
    assert result["macro_ready_cells"]["cells"] == 5
    assert math.isfinite(result["micro"]["mean_logloss"])
