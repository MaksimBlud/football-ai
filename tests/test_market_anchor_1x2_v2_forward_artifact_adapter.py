from __future__ import annotations

from copy import deepcopy

import pytest

import market_anchor_1x2_v2_prospective_evaluator as evaluator
from market_anchor_1x2_v2_forward_artifact_adapter import (
    FORWARD_WORKFLOW_NAME, FORWARD_WORKFLOW_PATH, SOURCE_WORKFLOW_PATH,
    load_selection_policy, normalize_forward_report, select_first_eligible_forecasts,
)


def _fixture():
    source_sha, parent_sha = "b" * 64, "a" * 40
    source = {
        "artifact_id": 123, "artifact_sha256": source_sha,
        "source_archive_created_at_utc": "2026-10-18T06:30:00+00:00",
        "latest_source_observed_at_utc": "2026-10-18T06:25:00+00:00",
        "parent_run": {
            "run_id": 456, "run_head_sha": parent_sha, "workflow_path": SOURCE_WORKFLOW_PATH,
            "run_created_at_utc": "2026-10-18T06:00:00+00:00",
            "run_completed_at_utc": "2026-10-18T06:32:00+00:00",
        },
        "historical_match_rows": 3800, "current_season_history_rows": 90,
    }
    preview = {
        "league": "SERIE_A", "event_id": "event-1", "home_team": "Atalanta", "away_team": "Torino",
        "market_snapshot_time_utc": "2026-10-19T05:30:00+00:00",
        "kickoff_utc": "2026-10-19T18:00:00+00:00",
        "model_candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
        "shadow_evidence_status": "SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE",
        "eligible_for_current_form_forward_shadow": True,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False, "no_bet": True,
        "market_1x2": [0.50, 0.28, 0.22],
        "active_market_fallback_1x2": [0.50, 0.28, 0.22],
        "shadow_v2_residual_1x2": [0.51, 0.27, 0.22],
    }
    row = {
        "status": "CURRENT_FORM_V2_SHADOW_CAPTURED_PREKICKOFF",
        "event_id": "event-1", "home_team": "Atalanta", "away_team": "Torino",
        "quote_time_utc": "2026-10-19T05:30:00+00:00", "kickoff_utc": "2026-10-19T18:00:00+00:00",
        "source_artifact_id": 123, "source_artifact_sha256": source_sha,
        "source_archive_created_at_utc": "2026-10-18T06:30:00+00:00",
        "source_observed_at_utc": "2026-10-18T06:25:00+00:00",
        "source_age_at_quote_seconds": 83100, "v2_preview": preview,
    }
    report = {
        "schema_version": "SERIE_A_V2_CURRENT_FORM_FORWARD_CAPTURE_V1",
        "experiment_id": evaluator.EXPERIMENT_ID, "mode": "READ_ONLY_PREKICKOFF_SHADOW_NO_BET",
        "as_of_utc": "2026-10-19T05:31:00+00:00",
        "candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
        "active_lambda": 0.0, "shadow_residual_lambda": 1.0,
        "active_model_is_exact_de_vigged_market": True,
        "target_outcomes_read": False, "target_outcomes_scored": False,
        "target_outcome_evaluation_gate_open": False, "model_refit_or_selection": False,
        "production_or_supabase_writes": 0, "paid_provider_calls": 0,
        "eligible_for_frozen_original_cohort": False,
        "eligible_for_current_form_forward_shadow": True,
        "eligible_for_product_publication": False, "no_bet": True,
        "v2_current_form_shadow_captured": 1, "rows": [row], "source_artifacts_used": [source],
    }
    run = {
        "run_id": 789, "head_sha": "c" * 40, "head_branch": "main",
        "path": FORWARD_WORKFLOW_PATH, "name": FORWARD_WORKFLOW_NAME,
        "status": "completed", "conclusion": "success", "event": "schedule",
        "run_created_at_utc": "2026-10-19T05:20:00+00:00",
        "run_completed_at_utc": "2026-10-19T05:32:00+00:00",
        "artifact_created_at_utc": "2026-10-19T05:31:30+00:00",
    }
    return report, run


def test_actual_forward_report_maps_to_exact_frozen_evaluator_schema():
    report, run = _fixture()
    candidates = normalize_forward_report(report, forward_artifact_id=999, forward_run=run)
    assert len(candidates) == 1
    row = candidates[0]["row"]
    assert row["match_date"] == "2026-10-19"
    assert row["source_parent_run_id"] == 456
    assert row["source_parent_run_sha"] == "a" * 40
    assert row["source_archive_sha256"] == "b" * 64
    assert row["forecast_captured_at_utc"] == report["as_of_utc"]
    assert row["active_lambda"] == 0 and row["shadow_residual_lambda"] == 1
    assert "incumbent_1x2" not in row and "incumbent_evidence" not in row


def test_source_sha_must_match_forward_row_and_source_manifest():
    report, run = _fixture()
    report["rows"][0]["source_artifact_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="source SHA"):
        normalize_forward_report(report, forward_artifact_id=999, forward_run=run)


def test_source_parent_must_be_exact_current_form_source_workflow():
    report, run = _fixture()
    report["source_artifacts_used"][0]["parent_run"]["workflow_path"] = ".github/workflows/other.yml"
    with pytest.raises(ValueError, match="workflow path"):
        normalize_forward_report(report, forward_artifact_id=999, forward_run=run)


def test_push_triggered_forward_artifact_is_rejected_even_on_manual_evaluation():
    report, run = _fixture()
    run["event"] = "push"
    with pytest.raises(ValueError, match="successful allowed main"):
        normalize_forward_report(report, forward_artifact_id=999, forward_run=run)


def test_non_main_forward_run_is_rejected():
    report, run = _fixture()
    run["head_branch"] = "feature/untrusted"
    with pytest.raises(ValueError, match="successful allowed main"):
        normalize_forward_report(report, forward_artifact_id=999, forward_run=run)


def test_report_claiming_outcome_access_is_rejected():
    report, run = _fixture()
    report["target_outcomes_read"] = True
    with pytest.raises(ValueError, match="research-only contract"):
        normalize_forward_report(report, forward_artifact_id=999, forward_run=run)


def test_preview_quote_time_must_match_forward_row():
    report, run = _fixture()
    report["rows"][0]["v2_preview"]["market_snapshot_time_utc"] = "2026-10-19T05:29:00+00:00"
    with pytest.raises(ValueError, match="market snapshot time"):
        normalize_forward_report(report, forward_artifact_id=999, forward_run=run)


def test_first_eligible_forecast_per_fixture_is_selected():
    report, run = _fixture()
    first = normalize_forward_report(report, forward_artifact_id=999, forward_run=run)[0]
    second = deepcopy(first)
    second["row"]["forecast_captured_at_utc"] = "2026-10-19T05:45:00+00:00"
    second["provenance"]["forward_artifact_id"] = 1000
    selected, summary = select_first_eligible_forecasts([second, first])
    assert len(selected) == 1
    assert selected[0]["row"]["forecast_captured_at_utc"] == "2026-10-19T05:31:00+00:00"
    assert summary["duplicate_forecast_rows_not_selected"] == 1
    assert summary["outcome_dependent_selection"] is False


def test_equal_capture_time_for_same_fixture_fails_closed():
    report, run = _fixture()
    first = normalize_forward_report(report, forward_artifact_id=999, forward_run=run)[0]
    second = deepcopy(first)
    second["provenance"]["forward_artifact_id"] = 1000
    with pytest.raises(ValueError, match="same capture timestamp"):
        select_first_eligible_forecasts([first, second])


def test_provider_event_id_cannot_map_to_multiple_fixtures():
    report, run = _fixture()
    first = normalize_forward_report(report, forward_artifact_id=999, forward_run=run)[0]
    second = deepcopy(first)
    second["row"].update({
        "home_team": "Inter", "away_team": "Roma", "match_date": "2026-10-20",
        "kickoff_utc": "2026-10-20T18:00:00+00:00",
        "quote_time_utc": "2026-10-20T05:30:00+00:00",
        "forecast_captured_at_utc": "2026-10-20T05:31:00+00:00",
        "source_observed_at_utc": "2026-10-19T06:25:00+00:00",
        "source_archive_created_at_utc": "2026-10-19T06:30:00+00:00",
        "source_parent_run_completed_at_utc": "2026-10-19T06:32:00+00:00",
    })
    second["provenance"]["forward_artifact_id"] = 1000
    with pytest.raises(ValueError, match="maps to multiple"):
        select_first_eligible_forecasts([first, second])


def test_selection_policy_sha_and_30_event_gate_are_unchanged():
    policy, digest = load_selection_policy()
    assert digest == "9fabe72f5aae341e758b1ce4c3fec1fa60e3ea7c8d2122f48e00f9040914842d"
    assert policy["minimum_completed_eligible_forecasts"] == 30
    assert policy["scope"]["active_lambda"] == 0
    assert policy["scope"]["shadow_residual_lambda"] == 1
    assert policy["scope"]["automatic_promotion"] is False
