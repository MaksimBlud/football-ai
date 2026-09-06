from multi_market_activation_status import build_status
from test_multi_market_activation_status import Client, NON_CORNER_ROW, quota


def approved_attestation():
    return {
        "schema_version": "MULTI_MARKET_PROVIDER_CORNER_CAPABILITY_ATTESTATION_V1",
        "read_only": True,
        "present": True,
        "valid": True,
        "capability_ready": True,
        "error": None,
        "workflow_run_id": 34000000000,
        "artifact_id": 9980000000,
        "artifact_sha256": "a" * 64,
        "probe_head_sha": "b" * 40,
        "league": "LIGUE_1",
        "corner_market_keys": ["alternate_totals_corners"],
        "corner_bookmaker_count": 1,
    }


def test_reviewed_attestation_breaks_probe_collection_deadlock_without_db_write():
    status = build_status(
        Client(snapshot_rows=[NON_CORNER_ROW, NON_CORNER_ROW]),
        lambda: quota(193),
        approved_attestation,
    )
    assert status["infrastructure_collection_ready"] is True
    assert status["provider_corner_capability"]["corner_evidence_rows"] == 0
    assert status["provider_corner_capability_sources"] == {
        "stored_snapshot_evidence": False,
        "reviewed_attestation": True,
    }
    assert status["provider_corner_capability_attestation"]["valid"] is True
    assert status["provider_corner_capability_ready"] is True
    assert status["collection_ready"] is True
    assert status["activation_ready"] is True
    assert status["status"] == "READY_AWAITING_MANUAL_ACTIVATION"
    assert status["blockers"] == []
    assert status["manual_collection_activation_required"] is True
    assert status["scheduled_collection_enabled"] is False
    assert status["prospective_oos_evaluation_active"] is False
    assert status["writes_performed"] is False
    assert status["paid_provider_requests"] == 0
    assert status["paid_provider_credits"] == 0


def test_present_but_invalid_attestation_cannot_unlock_collection():
    invalid = approved_attestation()
    invalid["valid"] = False
    invalid["capability_ready"] = False
    invalid["error"] = "ValueError: review_status is not APPROVED"
    status = build_status(
        Client(snapshot_rows=[NON_CORNER_ROW]),
        lambda: quota(193),
        lambda: invalid,
    )
    assert status["provider_corner_capability_sources"] == {
        "stored_snapshot_evidence": False,
        "reviewed_attestation": False,
    }
    assert status["provider_corner_capability_ready"] is False
    assert status["collection_ready"] is False
    assert status["blockers"] == ["PROVIDER_CORNER_CAPABILITY_UNPROVEN"]


def test_attestation_loader_failure_is_fail_closed():
    def fail():
        raise RuntimeError("attestation read failed")

    status = build_status(
        Client(snapshot_rows=[NON_CORNER_ROW]),
        lambda: quota(193),
        fail,
    )
    attestation = status["provider_corner_capability_attestation"]
    assert attestation["valid"] is False
    assert attestation["capability_ready"] is False
    assert "attestation read failed" in attestation["error"]
    assert status["collection_ready"] is False


def test_stored_corner_snapshot_evidence_remains_sufficient_without_attestation():
    status = build_status(Client(), lambda: quota(193), lambda: {"capability_ready": False})
    assert status["provider_corner_capability_sources"] == {
        "stored_snapshot_evidence": True,
        "reviewed_attestation": False,
    }
    assert status["provider_corner_capability_ready"] is True
    assert status["collection_ready"] is True
