import json
from pathlib import Path

import pytest

from multi_market_provider_capability_attestation import (
    ATTESTATION_SCHEMA,
    PROBE_SCHEMA,
    load_attestation,
    validate_attestation,
)


def approved_payload():
    return {
        "schema_version": ATTESTATION_SCHEMA,
        "review_status": "APPROVED",
        "review_decision": "ACCEPT_PROVIDER_CAPABILITY_ONLY",
        "research_only": True,
        "production_promotion": False,
        "prospective_oos_evaluation_active": False,
        "source_probe_writes_performed": False,
        "provider": "the_odds_api",
        "probe_schema_version": PROBE_SCHEMA,
        "probe_status": "CAPABILITY_CONFIRMED",
        "workflow_run_id": 34000000000,
        "artifact_id": 9980000000,
        "artifact_sha256": "a" * 64,
        "probe_head_sha": "b" * 40,
        "reviewed_at_utc": "2026-09-06T05:30:00+00:00",
        "target": {
            "league": "LIGUE_1",
            "event_id": "event-1",
            "home_team": "Troyes",
            "away_team": "Strasbourg",
            "commence_time_utc": "2026-09-06T13:00:00+00:00",
        },
        "corner_market_keys": [
            "alternate_totals_corners",
            "alternate_team_totals_corners",
        ],
        "corner_bookmaker_count": 2,
    }


def test_missing_attestation_is_fail_closed_and_read_only(tmp_path):
    result = load_attestation(tmp_path / "missing.json")
    assert result["read_only"] is True
    assert result["present"] is False
    assert result["valid"] is False
    assert result["capability_ready"] is False
    assert result["error"] is None


def test_approved_attestation_loads_as_capability_ready(tmp_path):
    path = tmp_path / "attestation.json"
    path.write_text(json.dumps(approved_payload()), encoding="utf-8")
    result = load_attestation(path)
    assert result["present"] is True
    assert result["valid"] is True
    assert result["capability_ready"] is True
    assert result["workflow_run_id"] == 34000000000
    assert result["artifact_id"] == 9980000000
    assert result["league"] == "LIGUE_1"
    assert result["corner_market_keys"] == [
        "alternate_team_totals_corners",
        "alternate_totals_corners",
    ]
    assert result["corner_bookmaker_count"] == 2


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("review_status", "DRAFT", "review_status"),
        ("review_decision", "AUTO_PROMOTE", "capability-only"),
        ("production_promotion", True, "production promotion"),
        ("prospective_oos_evaluation_active", True, "OOS evaluation"),
        ("source_probe_writes_performed", True, "write-free"),
        ("probe_status", "CAPABILITY_MISS", "did not confirm"),
        ("artifact_sha256", "bad", "64 lowercase hex"),
        ("probe_head_sha", "bad", "40 lowercase hex"),
        ("corner_market_keys", ["h2h"], "unrecognized corner market"),
        ("corner_bookmaker_count", 0, "positive integer"),
    ],
)
def test_invalid_or_nonreviewed_attestations_fail_closed(field, value, message):
    payload = approved_payload()
    payload[field] = value
    with pytest.raises(ValueError, match=message):
        validate_attestation(payload)


def test_noncanonical_league_cannot_be_attested():
    payload = approved_payload()
    payload["target"]["league"] = "RPL"
    with pytest.raises(ValueError, match="corner-source-ready"):
        validate_attestation(payload)


def test_invalid_present_file_never_becomes_ready(tmp_path):
    path = tmp_path / "attestation.json"
    payload = approved_payload()
    payload["review_status"] = "DRAFT"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = load_attestation(path)
    assert result["present"] is True
    assert result["valid"] is False
    assert result["capability_ready"] is False
    assert "review_status" in result["error"]


def test_contract_does_not_create_attestation_as_side_effect(tmp_path):
    path = tmp_path / "attestation.json"
    load_attestation(path)
    assert not path.exists()
