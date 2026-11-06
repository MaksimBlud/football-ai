from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib

import pytest

import market_anchor_1x2_v2_original_market_only_evaluator as evaluator


def _run(run_id, path, name, created, completed, event="schedule"):
    return {
        "id": run_id,
        "path": path,
        "name": name,
        "head_branch": "main",
        "head_sha": f"{run_id:040x}"[-40:],
        "event": event,
        "status": "completed",
        "conclusion": "success",
        "created_at_utc": created,
        "completed_at_utc": completed,
    }


def _artifact(artifact_id, name, path, workflow_name, created, run_created, run_completed, event="schedule"):
    run_id = artifact_id + 1000
    return {
        "artifact_id": artifact_id,
        "name": name,
        "sha256": hashlib.sha256(str(artifact_id).encode()).hexdigest(),
        "created_at_utc": created,
        "zip_sha256_verified": True,
        "run_metadata_verified": True,
        "code_contract_verified": True,
        "parent_run_id": run_id,
        "parent_run": _run(run_id, path, workflow_name, run_created, run_completed, event),
    }


def _valid_report():
    quote = "2026-09-20T11:00:00Z"
    capture = "2026-09-20T11:05:00Z"
    kickoff = "2026-09-20T13:00:00Z"
    source_created = "2026-09-20T10:00:00Z"
    source_run_created = "2026-09-20T09:00:00Z"
    source_run_completed = "2026-09-20T10:01:00Z"
    forward_run_created = "2026-09-20T11:04:00Z"
    forward_artifact_created = "2026-09-20T11:07:00Z"
    forward_run_completed = "2026-09-20T11:08:00Z"
    source = _artifact(
        123, evaluator.SOURCE_ARTIFACT_NAME, evaluator.SOURCE_WORKFLOW_PATH,
        evaluator.SOURCE_WORKFLOW_NAME, source_created, source_run_created, source_run_completed,
    )
    forward = _artifact(
        456, evaluator.FORWARD_ARTIFACT_NAME, evaluator.FORWARD_WORKFLOW_PATH,
        evaluator.FORWARD_WORKFLOW_NAME, forward_artifact_created, forward_run_created, forward_run_completed,
    )
    source_sha = source["sha256"]
    report = {
        "schema_version": "SERIE_A_ORIGINAL_V2_FORWARD_SOURCE_BEFORE_QUOTE_V1",
        "mode": "RESTORED_ORIGINAL_V2_RESEARCH_ONLY_NO_BET",
        "captured_at_utc": capture,
        "quotes_seen": 1,
        "future_quotes_checked": 1,
        "v2_diagnostic_previews_captured": 1,
        "archived_sources_used": {"123": source_sha},
        "source_workflow_run_attestation_required": True,
        "rows": [{
            "event_id": "event-123",
            "quote_time_utc": quote,
            "kickoff_utc": kickoff,
            "status": "SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY",
            "source_artifact_id": 123,
            "source_artifact_sha256": source_sha,
            "verified_source_workflow_run": {
                "run_id": source["parent_run"]["id"],
                "run_head_sha": source["parent_run"]["head_sha"],
                "workflow_path": evaluator.SOURCE_WORKFLOW_PATH,
                "run_completed_at_utc": source_run_completed,
                "source_loader_blob_sha1": evaluator.SOURCE_LOADER_BLOB_SHA1,
                "source_rights_helper_blob_sha1": evaluator.SOURCE_RIGHTS_HELPER_BLOB_SHA1,
                "source_rights_manifest_blob_sha1": evaluator.SOURCE_RIGHTS_MANIFEST_BLOB_SHA1,
            },
            "no_bet": True,
            "v2_preview": {
                "event_id": "event-123",
                "home_team": "Juventus",
                "away_team": "Atalanta BC",
                "kickoff_utc": kickoff,
                "market_snapshot_time_utc": quote,
                "feature_history_cutoff_utc": "2026-09-19T23:59:00Z",
                "market_1x2": [0.50, 0.25, 0.25],
                "active_market_fallback_1x2": [0.50, 0.25, 0.25],
                "shadow_v2_residual_1x2": [0.55, 0.20, 0.25],
                "model_candidate_sha256": evaluator.CANDIDATE_SHA256,
                "shadow_evidence_status": "UNVERIFIED_EXTERNAL_FEATURE_PROVENANCE",
                "eligible_for_frozen_prospective_cohort": False,
                "eligible_for_product_publication": False,
                "no_bet": True,
            },
        }],
        "uses_original_frozen_v2": True,
        "independent_incumbent_asof_verified": False,
        "uses_2026_27_results": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
        "training_or_promotion": False,
    }
    return report, forward, {123: source}


def _identities(n=30):
    days = [datetime(2026, 8, 1, tzinfo=timezone.utc).date() + timedelta(days=i) for i in range(n)]
    return {(day.isoformat(), f"Home {i}", f"Away {i}") for i, day in enumerate(days)}


def _gate(identities):
    return {
        "schema_version": "MARKET_ANCHOR_1X2_V2_COMPLETED_FIXTURE_IDENTITY_GATE_V1",
        "source_table": evaluator.COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
        "selected_columns": list(evaluator.COMPLETED_FIXTURE_GATE_COLUMNS),
        "league": evaluator.PRIMARY_LEAGUE,
        "season": evaluator.PRIMARY_SEASON,
        "query_contract_id": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID,
        "query_contract_sha256": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
        "captured_at_utc": "2026-11-06T02:30:00Z",
        "cutoff_date_exclusive_utc": "2026-11-06",
        "completed_fixture_identity_count": len(identities),
        "completed_fixture_identity_sha256": evaluator._sha_fixture_set(identities),
        "outcome_columns_selected": False,
        "target_outcomes_read": False,
    }


def _forecasts(identities):
    rows = []
    for index, identity in enumerate(sorted(identities)):
        match_day = identity[0]
        rows.append({
            "fixture_identity": identity,
            "event_id": f"event-{index}",
            "quote_time_utc": f"{match_day}T09:00:00Z",
            "capture_time_utc": f"{match_day}T11:05:00Z",
            "kickoff_utc": f"{match_day}T13:00:00Z",
            "feature_history_cutoff_utc": f"{match_day}T08:30:00Z",
            "source_artifact_id": 1000 + index,
            "source_artifact_sha256": hashlib.sha256(f"source-{index}".encode()).hexdigest(),
            "source_artifact_created_at_utc": f"{match_day}T08:00:00Z",
            "source_parent_run_id": 2000 + index,
            "source_parent_run_head_sha": f"{2000 + index:040x}",
            "source_parent_run_created_at_utc": f"{match_day}T07:00:00Z",
            "source_parent_run_completed_at_utc": f"{match_day}T08:01:00Z",
            "source_parent_run_path": evaluator.SOURCE_WORKFLOW_PATH,
            "source_parent_run_name": evaluator.SOURCE_WORKFLOW_NAME,
            "source_parent_run_branch": "main",
            "source_parent_run_event": "schedule",
            "source_parent_run_status": "completed",
            "source_parent_run_conclusion": "success",
            "source_loader_blob_sha1": evaluator.SOURCE_LOADER_BLOB_SHA1,
            "source_rights_helper_blob_sha1": evaluator.SOURCE_RIGHTS_HELPER_BLOB_SHA1,
            "source_rights_manifest_blob_sha1": evaluator.SOURCE_RIGHTS_MANIFEST_BLOB_SHA1,
            "source_artifact_metadata_verified": True,
            "source_code_contract_verified": True,
            "forward_artifact_id": 3000 + index,
            "forward_artifact_sha256": hashlib.sha256(f"forward-{index}".encode()).hexdigest(),
            "forward_artifact_created_at_utc": f"{match_day}T11:07:00Z",
            "forward_parent_run_id": 4000 + index,
            "forward_parent_run_head_sha": f"{4000 + index:040x}",
            "forward_parent_run_created_at_utc": f"{match_day}T11:04:00Z",
            "forward_parent_run_completed_at_utc": f"{match_day}T11:08:00Z",
            "forward_parent_run_path": evaluator.FORWARD_WORKFLOW_PATH,
            "forward_parent_run_name": evaluator.FORWARD_WORKFLOW_NAME,
            "forward_parent_run_branch": "main",
            "forward_parent_run_event": "schedule",
            "forward_parent_run_status": "completed",
            "forward_parent_run_conclusion": "success",
            "forward_artifact_metadata_verified": True,
            "source_before_quote_provenance_verified": True,
            "candidate_sha256": evaluator.CANDIDATE_SHA256,
            "market_1x2": (0.50, 0.25, 0.25),
            "active_market_fallback_1x2": (0.50, 0.25, 0.25),
            "shadow_v2_residual_1x2": (0.55, 0.20, 0.25),
            "original_frozen_cohort_eligible": False,
            "secondary_market_only_eligible": True,
            "no_bet": True,
        })
    return rows


def test_original_forward_report_is_admitted_only_to_secondary_market_only_lane():
    report, forward, sources = _valid_report()
    rows = evaluator.normalize_original_forward_report(
        report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["candidate_sha256"] == evaluator.CANDIDATE_SHA256
    assert row["secondary_market_only_eligible"] is True
    assert row["original_frozen_cohort_eligible"] is False
    assert row["market_1x2"] == row["active_market_fallback_1x2"]
    assert row["shadow_v2_residual_1x2"] != row["market_1x2"]
    assert row["fixture_identity"] == ("2026-09-20", "Juventus", "Atalanta")
    assert row["source_before_quote_provenance_verified"] is True
    assert row["source_parent_run_completed_at_utc"] < row["quote_time_utc"]


def test_source_created_after_quote_is_rejected():
    report, forward, sources = _valid_report()
    sources[123]["created_at_utc"] = "2026-09-20T11:01:00Z"
    sources[123]["parent_run"]["completed_at_utc"] = "2026-09-20T11:02:00Z"
    with pytest.raises(ValueError, match="created before the quote"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_source_loader_sha_must_match_frozen_source_pin():
    report, forward, sources = _valid_report()
    report["rows"][0]["verified_source_workflow_run"]["source_loader_blob_sha1"] = "0" * 40
    with pytest.raises(ValueError, match="source run attestation"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_active_lambda_zero_must_equal_market_exactly():
    report, forward, sources = _valid_report()
    report["rows"][0]["v2_preview"]["active_market_fallback_1x2"] = [0.51, 0.24, 0.25]
    with pytest.raises(ValueError, match="active_lambda=0"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_forward_capture_after_kickoff_is_rejected():
    report, forward, sources = _valid_report()
    report["captured_at_utc"] = "2026-09-20T13:01:00Z"
    forward["created_at_utc"] = "2026-09-20T13:02:00Z"
    forward["parent_run"]["completed_at_utc"] = "2026-09-20T13:02:00Z"
    with pytest.raises(ValueError, match="between quote and kickoff"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_target_outcome_fields_are_rejected_from_forward_artifacts():
    report, forward, sources = _valid_report()
    report["rows"][0]["v2_preview"]["result"] = "H"
    with pytest.raises(ValueError, match="target outcome/score field"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_wrong_source_artifact_digest_is_rejected():
    report, forward, sources = _valid_report()
    sources[123]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="ID/SHA"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_completed_gate_requires_identity_only_fields_and_matching_sha():
    identities = _identities()
    gate = _gate(identities)
    assert len(evaluator._validate_completed_gate(identities, gate)) == 30
    gate["selected_columns"] = ["match_date", "home_team", "away_team", "home_goals"]
    with pytest.raises(ValueError, match="identity metadata only"):
        evaluator._validate_completed_gate(identities, gate)


def test_no_outcomes_are_loaded_when_completed_primary_gate_is_closed():
    identities = _identities(29)
    forecasts = _forecasts(identities)
    called = []
    result = evaluator.evaluate_market_only_secondary_cohort(
        forecasts,
        completed_fixture_identities=identities,
        completed_gate_attestation=_gate(identities),
        load_outcomes=lambda keys: called.append(keys) or {},
    )
    assert result["status"] == "COMPLETED_PRIMARY_IDENTITY_PREFLIGHT_CLOSED_NO_OUTCOME_READ"
    assert result["target_outcomes_read"] is False
    assert called == []


def test_no_outcomes_are_loaded_when_fewer_than_30_eligible_completed_forecasts():
    identities = _identities()
    forecasts = _forecasts(identities)[:29]
    called = []
    result = evaluator.evaluate_market_only_secondary_cohort(
        forecasts,
        completed_fixture_identities=identities,
        completed_gate_attestation=_gate(identities),
        load_outcomes=lambda keys: called.append(keys) or {},
    )
    assert result["status"] == "PROTECTED_30_PRIMARY_COMPLETED_FORECAST_GATE_CLOSED_NO_OUTCOME_READ"
    assert result["target_outcomes_read"] is False
    assert called == []


def test_market_only_metrics_and_paired_bootstrap_run_only_after_both_gates():
    identities = _identities()
    forecasts = _forecasts(identities)
    called = []

    def load_outcomes(keys):
        called.append(keys)
        return {key: {"result": "H", "persisted_at_utc": f"{key[0]}T14:00:00Z"} for key in keys}

    result = evaluator.evaluate_market_only_secondary_cohort(
        forecasts,
        completed_fixture_identities=identities,
        completed_gate_attestation=_gate(identities),
        load_outcomes=load_outcomes,
    )
    assert len(called) == 1
    assert len(called[0]) == 30
    assert result["status"] == "EVALUATED_SECONDARY_MARKET_ONLY"
    assert result["target_outcomes_read"] is True
    assert result["post_kickoff_persistence_verified"] is True
    assert result["sample_size"] == 30
    assert result["market"]["brier_score"] > result["shadow_lambda_1"]["brier_score"]
    assert result["market"]["log_loss"] > result["shadow_lambda_1"]["log_loss"]
    assert result["paired_bootstrap"]["replicates"] == 10_000
    assert result["superiority_claim_permitted"] is False
    assert result["original_frozen_cohort_eligible"] is False
    assert result["incumbent_used"] is False


def test_first_capture_per_fixture_is_selected_without_outcome_or_price_logic():
    identity = next(iter(_identities(1)))
    base = _forecasts({identity})[0]
    later = dict(base, capture_time_utc="2026-08-01T11:06:00Z", event_id="event-later")
    selected = evaluator.select_first_eligible_forecast_per_fixture([later, base])
    assert len(selected) == 1
    assert selected[0]["capture_time_utc"] == base["capture_time_utc"]


def test_equal_capture_time_for_same_fixture_fails_closed():
    identity = next(iter(_identities(1)))
    base = _forecasts({identity})[0]
    duplicate = dict(base, event_id="event-duplicate")
    with pytest.raises(ValueError, match="equal capture timestamps"):
        evaluator.select_first_eligible_forecast_per_fixture([base, duplicate])


def test_one_event_id_cannot_map_to_two_fixture_identities():
    identities = _identities(2)
    first, second = _forecasts(identities)
    second["event_id"] = first["event_id"]
    with pytest.raises(ValueError, match="maps to multiple fixtures"):
        evaluator.select_first_eligible_forecast_per_fixture([first, second])


def test_post_gate_outcome_persistence_must_be_strictly_after_kickoff():
    identities = _identities()
    forecasts = _forecasts(identities)

    def load_outcomes(keys):
        return {
            key: {
                "result": "H",
                "persisted_at_utc": f"{key[0]}T13:00:00Z",
            }
            for key in keys
        }

    with pytest.raises(ValueError, match="strictly after kickoff"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=load_outcomes,
        )



def test_post_gate_outcome_persistence_cannot_be_later_than_evaluation_observation_time():
    identities = _identities()
    forecasts = _forecasts(identities)

    def load_outcomes(keys):
        return {
            key: {
                "result": "H",
                "persisted_at_utc": "2026-12-01T14:00:00Z",
            }
            for key in keys
        }

    with pytest.raises(ValueError, match="cannot be later than evaluation observation time"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=load_outcomes,
        )


def test_forward_workflow_run_from_paid_snapshot_is_not_admitted():
    report, forward, sources = _valid_report()
    forward["parent_run"]["event"] = "workflow_run"
    with pytest.raises(ValueError, match="event is not allowed"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )

def test_secondary_evaluator_rejects_rows_without_normalized_source_provenance():
    identities = _identities()
    forecasts = _forecasts(identities)
    del forecasts[0]["source_artifact_sha256"]
    with pytest.raises(ValueError, match="lacks normalized source-before-quote provenance"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=lambda keys: {},
        )


def test_secondary_evaluator_rechecks_source_parent_completion_before_quote():
    identities = _identities()
    forecasts = _forecasts(identities)
    forecasts[0]["source_parent_run_completed_at_utc"] = forecasts[0]["quote_time_utc"]
    with pytest.raises(ValueError, match="source archive and successful source workflow must both precede the quote"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=lambda keys: {},
        )


def test_secondary_evaluator_rejects_forward_capture_outside_parent_run():
    identities = _identities()
    forecasts = _forecasts(identities)
    forecasts[0]["forward_parent_run_completed_at_utc"] = "2026-08-01T11:04:00Z"
    with pytest.raises(ValueError, match="forward artifact is outside its successful parent workflow interval"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=lambda keys: {},
        )



def test_forward_forecast_artifact_must_be_persisted_before_kickoff():
    report, forward, sources = _valid_report()
    forward["created_at_utc"] = "2026-09-20T13:01:00Z"
    forward["parent_run"]["completed_at_utc"] = "2026-09-20T13:02:00Z"
    with pytest.raises(ValueError, match="forward forecast artifact was not persisted after capture and before kickoff"):
        evaluator.normalize_original_forward_report(
            report, forward_artifact_metadata=forward, source_artifacts_by_id=sources
        )


def test_secondary_evaluator_rejects_forward_artifact_persisted_after_kickoff():
    identities = _identities()
    forecasts = _forecasts(identities)
    forecasts[0]["forward_artifact_created_at_utc"] = "2026-08-01T13:01:00Z"
    forecasts[0]["forward_parent_run_completed_at_utc"] = "2026-08-01T13:02:00Z"
    with pytest.raises(ValueError, match="forward forecast artifact was not persisted after capture and before kickoff"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=lambda keys: {},
        )



@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_parent_run_path", ".github/workflows/unrelated.yml"),
        ("source_parent_run_branch", "feature"),
        ("source_parent_run_event", "workflow_run"),
        ("source_parent_run_status", "in_progress"),
        ("source_parent_run_conclusion", "failure"),
        ("source_rights_manifest_blob_sha1", "0" * 40),
        ("source_artifact_metadata_verified", False),
        ("source_code_contract_verified", False),
    ],
)
def test_secondary_evaluator_rejects_invalid_source_parent_attestation(field, value):
    identities = _identities()
    forecasts = _forecasts(identities)
    forecasts[0][field] = value
    with pytest.raises(ValueError, match="source parent/workflow/code attestation"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=lambda keys: {},
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("forward_parent_run_path", ".github/workflows/unrelated.yml"),
        ("forward_parent_run_branch", "feature"),
        ("forward_parent_run_event", "workflow_run"),
        ("forward_parent_run_status", "in_progress"),
        ("forward_parent_run_conclusion", "failure"),
        ("forward_artifact_metadata_verified", False),
    ],
)
def test_secondary_evaluator_rejects_invalid_forward_parent_attestation(field, value):
    identities = _identities()
    forecasts = _forecasts(identities)
    forecasts[0][field] = value
    with pytest.raises(ValueError, match="forward parent/workflow attestation"):
        evaluator.evaluate_market_only_secondary_cohort(
            forecasts,
            completed_fixture_identities=identities,
            completed_gate_attestation=_gate(identities),
            load_outcomes=lambda keys: {},
        )
