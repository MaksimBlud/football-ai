import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "source_rights" / "lega_serie_a_reports.json"
CANDIDATE = ROOT / "research" / "models" / "market_anchor_v2_serie_a_frozen_candidate.json"


def test_lega_report_source_remains_hold_without_written_permission():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    permissions = manifest["permissions"]
    assert manifest["decision"] == "HOLD"
    assert permissions["written_permission_obtained"] is False
    for key in (
        "extraction_or_use_without_written_permission",
        "automated_capture_without_written_permission",
        "manual_extraction_without_written_permission",
        "internal_ml_training_authorized",
        "internal_inference_authorized",
        "private_raw_storage_authorized",
        "commercial_use_authorized",
        "redistribution_authorized",
    ):
        assert permissions[key] is False
    assert manifest["provenance"]["source_before_quote_proven"] is False
    assert manifest["controls"]["provider_api_requests"] == 0
    assert manifest["controls"]["source_downloads"] == 0
    assert manifest["controls"]["protected_outcomes_read"] == 0


def test_audit_is_bound_to_unchanged_original_v2_candidate():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert manifest["candidate_id"] == "MARKET_ANCHOR_1X2_V2"
    assert manifest["candidate_sha256"] == candidate["artifact_sha256"]
    assert candidate["artifact_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0.0
    assert candidate["shadow_residual_lambda"] == 1.0
    assert candidate["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is False
