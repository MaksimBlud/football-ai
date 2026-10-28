"""Offline tests for the gated original MARKET_ANCHOR_1X2_V2 evaluator."""
from __future__ import annotations

from datetime import date, timedelta
import json
import math
from pathlib import Path

import pytest

import market_anchor_1x2_v2_prospective_evaluator as evaluator
from market_anchor_1x2_v2_prospective_evaluator import (
    EXPERIMENT_ID,
    FROZEN_CANDIDATE_SHA256,
    MIN_COMPLETED_ELIGIBLE_FORECASTS,
    COHORT_PREREGISTRATION_COMMIT_SHA,
    COHORT_FROZEN_AT_UTC,
    PRIMARY_SEASON_START,
    PRIMARY_SEASON_END,
    evaluate_after_gate,
)


def make_forecasts(n=30):
    rows = []
    start = date(2026, 10, 20)
    for i in range(n):
        match_date = (start + timedelta(days=i)).isoformat()
        rows.append({
            "experiment_id": EXPERIMENT_ID,
            "evidence_class": "PROSPECTIVE_SHADOW",
            "league": "SERIE_A",
            "event_id": f"provider-event-{i}",
            "match_date": match_date,
            "home_team": f"Home {i}",
            "away_team": f"Away {i}",
            "candidate_sha256": FROZEN_CANDIDATE_SHA256,
            "active_lambda": 0.0,
            "shadow_residual_lambda": 1.0,
            "no_bet": True,
            "eligible_for_current_form_forward_shadow": True,
            "eligible_for_product_publication": False,
            "shadow_evidence_status": "SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE",
            "source_artifact_id": 123456,
            "source_archive_sha256": "a" * 64,
            "source_observed_at_utc": "2026-10-18T08:30:00Z",
            "source_archive_created_at_utc": "2026-10-18T08:35:00Z",
            "source_parent_run_id": 654321,
            "source_parent_run_sha": "b" * 40,
            "source_parent_run_completed_at_utc": "2026-10-18T08:40:00Z",
            "quote_time_utc": "2026-10-18T09:00:00Z",
            "forecast_captured_at_utc": "2026-10-18T09:01:00Z",
            "kickoff_utc": f"{match_date}T18:00:00Z",
            "market_1x2": [0.50, 0.30, 0.20],
            "active_market_fallback_1x2": [0.50, 0.30, 0.20],
            "incumbent_1x2": [0.55, 0.25, 0.20],
            "incumbent_evidence": {
                "league": "SERIE_A",
                "match_date": match_date,
                "home_team": f"Home {i}",
                "away_team": f"Away {i}",
                "kickoff_utc": f"{match_date}T18:00:00Z",
                "model_version": "frozen-incumbent-test-v1",
                "artifact_sha256": "c" * 64,
                "source_record_id": f"incumbent-snapshot-{i}",
                "generated_at_utc": "2026-10-18T08:55:00Z",
                "history_cutoff_utc": "2026-10-18T08:30:00Z",
            },
            "shadow_v2_residual_1x2": [0.70, 0.20, 0.10],
        })
    return rows


def identities(rows):
    return {(row["match_date"], row["home_team"], row["away_team"]) for row in rows}


def make_completed_gate_attestation(completed, *, captured_at_utc="2026-11-19T00:00:00Z"):
    normalized = {tuple(item) for item in completed}
    captured = evaluator._utc(captured_at_utc, "test captured_at_utc")
    return {
        "schema_version": evaluator.COMPLETED_FIXTURE_GATE_SCHEMA,
        "source_table": evaluator.COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
        "selected_columns": list(evaluator.COMPLETED_FIXTURE_GATE_COLUMNS),
        "league": evaluator.PRIMARY_LEAGUE,
        "season": "2026-2027",
        "query_contract_id": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID,
        "query_contract_sha256": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
        "captured_at_utc": captured.isoformat().replace("+00:00", "Z"),
        "cutoff_date_exclusive_utc": captured.date().isoformat(),
        "completed_fixture_identity_count": len(normalized),
        "completed_fixture_identity_sha256": evaluator._sha_fixture_set(normalized),
        "outcome_columns_selected": False,
        "target_outcomes_read": False,
    }


def evaluate_with_gate_attestation(rows, completed, outcome_loader, *, attestation=None):
    completed_set = set(completed)
    evidence = (
        make_completed_gate_attestation(completed_set)
        if attestation is None else attestation
    )
    return evaluate_after_gate(
        rows,
        completed_set,
        outcome_loader,
        completed_fixture_gate_attestation=evidence,
    )


TEST_INCUMBENT_REFERENCE = {
    "model_version": "frozen-incumbent-test-v1",
    "artifact_sha256": "c" * 64,
}


def pin_test_incumbent(monkeypatch):
    monkeypatch.setattr(evaluator, "FROZEN_INCUMBENT_REFERENCE", dict(TEST_INCUMBENT_REFERENCE))


def test_missing_completed_fixture_gate_attestation_fails_before_outcome_read():
    rows = make_forecasts(30)
    called = []
    with pytest.raises(ValueError, match="explicit metadata-only attestation"):
        evaluate_after_gate(
            rows,
            identities(rows),
            lambda keys: called.append(keys) or {key: "H" for key in keys},
        )
    assert called == []


def test_completed_fixture_gate_attestation_rejects_future_fixture_identities():
    rows = make_forecasts(30)
    completed = identities(rows)
    attestation = make_completed_gate_attestation(
        completed, captured_at_utc="2026-10-28T03:00:00Z"
    )
    called = []
    with pytest.raises(ValueError, match="not completed before the metadata cutoff"):
        evaluate_after_gate(
            rows,
            completed,
            lambda keys: called.append(keys) or {key: "H" for key in keys},
            completed_fixture_gate_attestation=attestation,
        )
    assert called == []


def test_completed_fixture_gate_attestation_digest_and_query_contract_are_enforced():
    rows = make_forecasts(30)
    completed = identities(rows)
    called = []
    attestation = make_completed_gate_attestation(completed)
    attestation["completed_fixture_identity_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest does not match"):
        evaluate_after_gate(
            rows,
            completed,
            lambda keys: called.append(keys) or {key: "H" for key in keys},
            completed_fixture_gate_attestation=attestation,
        )
    assert called == []
    attestation = make_completed_gate_attestation(completed)
    attestation["selected_columns"] = ["match_date", "home_team", "away_team", "result"]
    with pytest.raises(ValueError, match="frozen identity-only query contract"):
        evaluate_after_gate(
            rows,
            completed,
            lambda keys: called.append(keys) or {key: "H" for key in keys},
            completed_fixture_gate_attestation=attestation,
        )
    assert called == []


def test_completed_fixture_query_contract_sha_is_pinned():
    assert evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256 == "181d76b75c092d46b57535591abbb4e625c3e54e9b0f876402c9a3e0ed2457fb"
    assert evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT == (
        "SELECT match_date, home_team, away_team FROM public.league_finished_results "
        "WHERE league = 'SERIE_A' AND season = '2026-2027' "
        "AND match_date >= DATE '2026-07-01' AND match_date < :cutoff_date_exclusive"
    )


def test_29_completed_primary_forecasts_do_not_call_outcome_loader():
    rows = make_forecasts(30)
    called = []
    report = evaluate_with_gate_attestation(
        rows,
        identities(rows[:29]),
        lambda keys: called.append(keys) or {key: "H" for key in keys},
    )
    assert report["status"] == "OUTCOME_READ_GATE_CLOSED"
    assert report["eligible_completed_forecasts"] == 29
    assert report["outcome_read_gate_open"] is False
    assert report["target_outcomes_read"] is False
    assert report["metrics"] is None
    assert called == []


def test_exact_30_gate_scores_all_three_frozen_comparators_after_lazy_read(monkeypatch):
    pin_test_incumbent(monkeypatch)
    rows = make_forecasts(30)
    called = []

    def loader(keys):
        called.append(keys)
        return {key: "H" for key in keys}

    report = evaluate_with_gate_attestation(rows, identities(rows), loader)
    assert len(called) == 1
    assert called[0] == frozenset(identities(rows))
    assert report["status"] == "EVALUATED_RESEARCH_ONLY"
    assert report["eligible_completed_forecasts"] == 30
    assert report["scored_forecasts"] == 30
    assert report["target_outcomes_read"] is True
    assert report["metrics"]["market"]["brier"] == pytest.approx(0.38)
    assert report["metrics"]["market"]["log_loss"] == pytest.approx(-math.log(0.50))
    assert report["metrics"]["incumbent"]["brier"] == pytest.approx(0.305)
    assert report["metrics"]["shadow"]["brier"] == pytest.approx(0.14)
    assert report["metrics"]["shadow"]["log_loss"] == pytest.approx(-math.log(0.70))
    assert report["review_signal"] is True
    assert report["no_bet"] is True
    assert report["automatic_promotion"] is False
    assert '"H"' not in json.dumps(report)


def test_future_forecasts_do_not_count_toward_completed_gate():
    rows = make_forecasts(30)
    called = []
    report = evaluate_with_gate_attestation(
        rows,
        identities(rows[:20]),
        lambda keys: called.append(keys) or {key: "H" for key in keys},
    )
    assert report["eligible_completed_forecasts"] == 20
    assert report["outcome_read_gate_open"] is False
    assert called == []


@pytest.mark.parametrize("field,value", [
    ("candidate_sha256", "0" * 64),
    ("active_lambda", 1.0),
    ("shadow_residual_lambda", 0.0),
    ("no_bet", False),
    ("eligible_for_product_publication", True),
    ("shadow_evidence_status", "UNVERIFIED_SOURCE"),
    ("source_archive_sha256", "bad"),
])
def test_contract_or_source_provenance_drift_fails_before_outcome_read(field, value):
    rows = make_forecasts(30)
    rows[0][field] = value
    called = []
    with pytest.raises(ValueError):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_source_after_quote_fails_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["source_archive_created_at_utc"] = "2026-10-18T09:00:00Z"
    called = []
    with pytest.raises(ValueError, match="ordering"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_offsetless_clock_fails_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["quote_time_utc"] = "2026-09-02T01:00:00"
    called = []
    with pytest.raises(ValueError, match="UTC offset"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_precontract_quote_is_rejected_before_outcome_read():
    rows = make_forecasts(30)
    row = rows[0]
    row["source_observed_at_utc"] = "2026-10-18T07:30:00Z"
    row["source_archive_created_at_utc"] = "2026-10-18T07:35:00Z"
    row["source_parent_run_completed_at_utc"] = "2026-10-18T07:40:00Z"
    row["quote_time_utc"] = "2026-10-18T08:00:00Z"
    row["forecast_captured_at_utc"] = "2026-10-18T08:01:00Z"
    row["incumbent_evidence"]["history_cutoff_utc"] = "2026-10-18T07:25:00Z"
    row["incumbent_evidence"]["generated_at_utc"] = "2026-10-18T07:50:00Z"
    called = []
    with pytest.raises(ValueError, match="preregistration time"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_forecast_outside_frozen_2026_27_season_is_rejected_before_outcome_read():
    rows = make_forecasts(30)
    original_completed = identities(rows)
    rows[0]["match_date"] = "2027-07-01"
    rows[0]["kickoff_utc"] = "2027-07-01T18:00:00Z"
    called = []
    with pytest.raises(ValueError, match="outside the frozen 2026/27 primary season"):
        evaluate_after_gate(
            rows,
            original_completed,
            lambda keys: called.append(keys) or {},
            completed_fixture_gate_attestation=make_completed_gate_attestation(original_completed),
        )
    assert called == []


def test_preregistration_cutoff_and_season_are_explicitly_pinned():
    assert COHORT_PREREGISTRATION_COMMIT_SHA == "9df6f63db10e0128aff89c38fb8c6d88703ef8b8"
    assert COHORT_FROZEN_AT_UTC.isoformat() == "2026-10-18T08:15:32+00:00"
    assert PRIMARY_SEASON_START.isoformat() == "2026-07-01"
    assert PRIMARY_SEASON_END.isoformat() == "2027-06-30"


def test_kickoff_utc_date_must_match_fixture_identity_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["kickoff_utc"] = "2026-10-02T18:00:00Z"
    called = []
    with pytest.raises(ValueError, match="kickoff UTC date"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_stale_source_or_quote_fails_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["source_observed_at_utc"] = "2026-08-31T00:00:00Z"
    rows[0]["incumbent_evidence"]["history_cutoff_utc"] = "2026-08-30T00:00:00Z"
    called = []
    with pytest.raises(ValueError, match="24-hour"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_forecast_payload_with_outcome_fields_is_rejected_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["result"] = "H"
    called = []
    with pytest.raises(ValueError, match="outcome/score field"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


@pytest.mark.parametrize("key", [
    "home_goal", "away_goal", "goals_home", "goals_away",
    "home_ft_goals", "away_ft_goals",
    "full_time_home_goals", "full_time_away_goals",
    "final_home_goals", "final_away_goals",
    "winner", "winning_team", "match_winner",
    "home_win", "away_win", "is_draw", "draw",
])
def test_common_target_outcome_aliases_are_rejected_before_outcome_read(key):
    rows = make_forecasts(30)
    rows[0][key] = 1
    called = []
    with pytest.raises(ValueError, match="outcome/score field"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_duplicate_event_or_fixture_identity_fails_closed():
    rows = make_forecasts(30)
    rows[1]["event_id"] = rows[0]["event_id"]
    called = []
    with pytest.raises(ValueError, match="duplicate provider event_id"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []

    rows = make_forecasts(30)
    rows[1]["match_date"] = rows[0]["match_date"]
    rows[1]["home_team"] = rows[0]["home_team"]
    rows[1]["away_team"] = rows[0]["away_team"]
    rows[1]["kickoff_utc"] = rows[0]["kickoff_utc"]
    rows[1]["incumbent_evidence"]["league"] = rows[1]["league"]
    rows[1]["incumbent_evidence"]["match_date"] = rows[1]["match_date"]
    rows[1]["incumbent_evidence"]["home_team"] = rows[1]["home_team"]
    rows[1]["incumbent_evidence"]["away_team"] = rows[1]["away_team"]
    rows[1]["incumbent_evidence"]["kickoff_utc"] = rows[1]["kickoff_utc"]
    with pytest.raises(ValueError, match="duplicate canonical fixture"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_missing_incumbent_vector_is_not_silently_replaced_by_market():
    rows = make_forecasts(30)
    del rows[0]["incumbent_1x2"]
    called = []
    with pytest.raises(ValueError, match="missing required fields"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_market_fallback_must_equal_market_at_frozen_lambda_zero():
    rows = make_forecasts(30)
    rows[0]["active_market_fallback_1x2"] = [0.51, 0.29, 0.20]
    called = []
    with pytest.raises(ValueError, match="exactly the de-vigged market"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_review_signal_requires_shadow_to_beat_both_comparators_on_both_metrics(monkeypatch):
    pin_test_incumbent(monkeypatch)
    rows = make_forecasts(30)
    for row in rows:
        row["incumbent_1x2"] = [0.80, 0.10, 0.10]
    report = evaluate_with_gate_attestation(rows, identities(rows), lambda keys: {key: "H" for key in keys})
    assert report["shadow_beats_market_on_both_metrics"] is True
    assert report["shadow_beats_incumbent_on_both_metrics"] is False
    assert report["review_signal"] is False


def test_outcome_loader_must_return_exactly_the_gated_fixture_set(monkeypatch):
    pin_test_incumbent(monkeypatch)
    rows = make_forecasts(30)
    called = []
    def incomplete_loader(keys):
        called.append(keys)
        return {next(iter(keys)): "H"}
    with pytest.raises(ValueError, match="exactly one outcome"):
        evaluate_with_gate_attestation(rows, identities(rows), incomplete_loader)
    assert len(called) == 1


def test_30_completed_forecasts_do_not_read_outcomes_without_pinned_incumbent(monkeypatch):
    monkeypatch.setattr(evaluator, "FROZEN_INCUMBENT_REFERENCE", None)
    rows = make_forecasts(30)
    called = []
    report = evaluate_with_gate_attestation(
        rows,
        identities(rows),
        lambda keys: called.append(keys) or {key: "H" for key in keys},
    )
    assert report["status"] == "EVALUATION_BLOCKED_UNPINNED_INCUMBENT"
    assert report["eligible_completed_forecasts"] == 30
    assert report["frozen_incumbent_reference_pinned"] is False
    assert report["outcome_read_gate_open"] is False
    assert report["target_outcomes_read"] is False
    assert report["metrics"] is None
    assert called == []


def test_incumbent_evidence_must_match_frozen_reference_before_outcome_read(monkeypatch):
    pin_test_incumbent(monkeypatch)
    rows = make_forecasts(30)
    rows[0]["incumbent_evidence"]["artifact_sha256"] = "d" * 64
    called = []
    with pytest.raises(ValueError, match="does not match the frozen incumbent reference"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_legacy_xgboost_incumbent_evidence_is_rejected_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["incumbent_evidence"]["model_version"] = "legacy-xgboost-production"
    called = []
    with pytest.raises(ValueError, match="legacy XGBoost incumbent evidence is forbidden"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_duplicate_incumbent_source_record_id_fails_closed(monkeypatch):
    pin_test_incumbent(monkeypatch)
    rows = make_forecasts(30)
    rows[1]["incumbent_evidence"]["source_record_id"] = rows[0]["incumbent_evidence"]["source_record_id"]
    called = []
    with pytest.raises(ValueError, match="duplicate incumbent source record ID"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_incumbent_prediction_must_not_follow_quote(monkeypatch):
    pin_test_incumbent(monkeypatch)
    rows = make_forecasts(30)
    rows[0]["incumbent_evidence"]["generated_at_utc"] = "2026-10-18T09:01:00Z"
    called = []
    with pytest.raises(ValueError, match="must not follow the quote"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_incumbent_history_cutoff_must_not_exceed_v2_source_observation():
    rows = make_forecasts(30)
    # This comparator was generated before the market quote, but its declared
    # history cutoff is later than the source observation used by V2.
    # It therefore has an information-time advantage and must fail closed.
    rows[0]["incumbent_evidence"]["history_cutoff_utc"] = "2026-10-18T08:31:00Z"
    called = []
    with pytest.raises(ValueError, match="same-information-time comparison"):
        evaluate_with_gate_attestation(rows, identities(rows), lambda keys: called.append(keys) or {})
    assert called == []


def test_current_form_policy_matches_evaluator_frozen_constants():
    root = Path(__file__).resolve().parents[1]
    policy = json.loads((root / "experiments/market_anchor_1x2_v2_current_form_policy.json").read_text())
    assert policy["experiment_id"] == EXPERIMENT_ID
    assert policy["frozen_original_candidate"]["artifact_sha256"] == FROZEN_CANDIDATE_SHA256
    assert policy["frozen_original_candidate"]["active_lambda"] == 0.0
    assert policy["frozen_original_candidate"]["shadow_residual_lambda"] == 1.0
    assert policy["target_outcome_evaluation_gate"]["minimum_completed_eligible_prospective_forecasts"] == MIN_COMPLETED_ELIGIBLE_FORECASTS
    assert evaluator.FROZEN_INCUMBENT_REFERENCE is None
    assert "frozen_incumbent_reference" not in policy["target_outcome_evaluation_gate"]
    assert set(policy["target_outcome_evaluation_gate"]["required_comparison"]) == {
        "DE_VIGGED_MARKET", "FROZEN_PRODUCTION_INCUMBENT", "INACTIVE_LAMBDA_1_RESIDUAL_SHADOW"
    }


@pytest.mark.parametrize("key", ["home_winner_flag", "home_won", "match_decision", "winner_code"])
def test_unknown_top_level_fields_fail_closed_before_outcome_read(key):
    rows = make_forecasts(30)
    rows[0][key] = True
    called = []
    with pytest.raises(ValueError, match="unapproved fields"):
        evaluate_with_gate_attestation(
            rows,
            identities(rows),
            lambda keys: called.append(keys) or {item: "H" for item in keys},
        )
    assert called == []


def test_unknown_nested_incumbent_evidence_fields_fail_closed_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["incumbent_evidence"]["home_winner_flag"] = True
    called = []
    with pytest.raises(ValueError, match="incumbent evidence contains unapproved fields"):
        evaluate_with_gate_attestation(
            rows,
            identities(rows),
            lambda keys: called.append(keys) or {item: "H" for item in keys},
        )
    assert called == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("league", "EPL"),
        ("match_date", "2026-10-25"),
        ("home_team", "Different Home"),
        ("away_team", "Different Away"),
    ],
)
def test_incumbent_evidence_must_match_same_canonical_fixture_before_outcome_read(field, value):
    rows = make_forecasts(30)
    rows[0]["incumbent_evidence"][field] = value
    called = []
    with pytest.raises(ValueError, match="incumbent evidence event identity does not match forecast"):
        evaluate_with_gate_attestation(
            rows,
            identities(rows),
            lambda keys: called.append(keys) or {item: "H" for item in keys},
        )
    assert called == []


def test_incumbent_evidence_kickoff_must_match_exact_forecast_event_before_outcome_read():
    rows = make_forecasts(30)
    rows[0]["incumbent_evidence"]["kickoff_utc"] = "2026-10-20T19:00:00Z"
    called = []
    with pytest.raises(ValueError, match="incumbent evidence event identity does not match forecast"):
        evaluate_with_gate_attestation(
            rows,
            identities(rows),
            lambda keys: called.append(keys) or {item: "H" for item in keys},
        )
    assert called == []


def test_incumbent_evidence_requires_explicit_fixture_identity_fields():
    rows = make_forecasts(30)
    del rows[0]["incumbent_evidence"]["home_team"]
    called = []
    with pytest.raises(ValueError, match="incumbent evidence missing fields"):
        evaluate_with_gate_attestation(
            rows,
            identities(rows),
            lambda keys: called.append(keys) or {item: "H" for item in keys},
        )
    assert called == []
