import json
from pathlib import Path


def test_odss_api_candidate_stays_outside_frozen_original_v2():
    root = Path(__file__).resolve().parents[1]
    audit = json.loads(
        (root / "research/market_anchor_1x2_v2_odss_api_source_audit_20261120.json")
        .read_text(encoding="utf-8")
    )

    assert audit["candidate_status"] == "HOLD_NO_INTEGRATION"
    assert audit["decision"]["status"] == "HOLD_NO_INTEGRATION"
    assert audit["decision"]["integration_allowed_by_current_v2_contract"] is False
    assert audit["current_v2_contract"]["new_provider_would_change_quote_source_contract"] is True
    assert audit["current_v2_contract"]["candidate_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert audit["current_v2_contract"]["frozen_feature_count"] == 19
    assert audit["current_v2_contract"]["active_lambda"] == 0.0
    assert audit["current_v2_contract"]["shadow_lambda"] == 1.0

    assert audit["rights"]["free_internal_model_analysis_listed_as_permitted"] is True
    assert audit["rights"]["free_tier_long_term_raw_retention_confirmed"] is False
    assert audit["rights"]["external_display_permitted"] is False
    assert audit["rights"]["historical_odds_endpoint_enabled"] is False

    assert audit["actions"]["api_key_created"] is False
    assert audit["actions"]["authenticated_odds_requests_made"] is False
    assert audit["actions"]["synthetic_mock_odds_requested"] is False
    assert audit["actions"]["supabase_writes"] is False
    assert audit["actions"]["supabase_ddl"] is False
    assert audit["actions"]["paid_provider_calls"] is False
    assert audit["actions"]["model_code_changed"] is False
