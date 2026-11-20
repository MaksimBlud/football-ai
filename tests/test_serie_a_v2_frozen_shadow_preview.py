"""Real original V2 JSON weights; strict read-only preview and refusal tests."""
from datetime import datetime, timedelta, timezone
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

import market_anchor_1x2_v2_shadow as v2
import serie_a_v2_frozen_shadow_preview as v2_preview

NOW = datetime(2026, 10, 13, 15, 0, tzinfo=timezone.utc)
KICKOFF = "2026-10-19T19:00:00Z"
QUOTE = "2026-10-13T14:00:00+00:00"
CUTOFF = "2026-10-13T13:00:00Z"


def market(**overrides):
    row = {
        "league": "SERIE_A", "event_id": "event-serie-a-001",
        "home_team": "Inter", "away_team": "Napoli",
        "commence_time_utc": KICKOFF, "snapshot_time_utc": QUOTE,
        "home_odds": 2.4, "draw_odds": 3.2, "away_odds": 3.0,
    }
    row.update(overrides)
    return row


def features(**overrides):
    original = v2_preview.load_verified_original()
    row = {
        "event_id": "event-serie-a-001",
        "home_team": "Inter", "away_team": "Napoli",
        "commence_time_utc": KICKOFF,
        "feature_history_cutoff_utc": CUTOFF,
        "features": {k: (None if i % 6 == 0 else (i % 3 - 1) / 10)
                     for i, k in enumerate(original["features"])},
    }
    row.update(overrides)
    return row


def test_actual_sha_restored_candidate_is_used_and_shadow_is_not_active_market():
    original = v2_preview.load_verified_original()
    assert original["artifact_sha256"] == v2_preview.FROZEN_SHA
    assert original["training_rows"] == 3799
    assert original["active_lambda"] == 0
    report = v2_preview.shadow_preview([market()], [features()], as_of_utc=NOW)
    assert report["scored"] == 1
    assert report["mode"] == "READ_ONLY_DIAGNOSTIC_NOT_PROSPECTIVE"
    assert report["database_writes"] == report["paid_provider_calls"] == 0
    assert report["eligible_for_product_publication"] is False
    assert report["requires_independent_feature_provenance_and_incumbent_for_prospective_capture"]
    row = report["previews"][0]
    p, active, shadow = [row[k] for k in (
        "market_1x2", "active_market_fallback_1x2", "shadow_v2_residual_1x2",
    )]
    assert np.allclose(p, active, atol=1e-12, rtol=0)
    assert not np.allclose(p, shadow, atol=1e-6, rtol=0)
    # Frozen end-to-end reference vector: this pins the exact 19-feature order,
    # median imputation, scaler, original weights, market anchoring, and lambda=1.
    np.testing.assert_allclose(
        shadow,
        [0.3749396851899098, 0.3071031642078370, 0.3179571506022533],
        atol=1e-12,
        rtol=0,
    )
    assert sum(shadow) == pytest.approx(1)
    assert row["model_candidate_sha256"] == v2_preview.FROZEN_SHA
    assert row["eligible_for_frozen_prospective_cohort"] is False
    assert row["eligible_for_product_publication"] is False
    assert row["no_bet"] is True


def test_frozen_candidate_rejects_weight_tamper_with_stale_sha():
    original = v2_preview.load_verified_original()
    tampered = deepcopy(original)
    tampered["weights"][0][0] += 1e-12

    with pytest.raises(ValueError, match="candidate artifact sha256 mismatch"):
        v2.validate_candidate_artifact(tampered)


def test_absence_of_future_quotes_is_truthfully_empty():
    report = v2_preview.shadow_preview([], [], as_of_utc=NOW)
    assert report["scored"] == 0
    assert report["previews"] == []
    assert sum(report["blocked"].values()) == 0
    assert report["eligible_for_product_publication"] is False


@pytest.mark.parametrize("snapshot,status", [
    ("2026-10-10T14:00:00Z", "STALE_MARKET"),
    ("2026-10-13T16:00:00Z", "FUTURE_QUOTE"),
])
def test_bad_quote_age_is_not_published_or_scored(snapshot,status):
    report = v2_preview.shadow_preview(
        [market(snapshot_time_utc=snapshot)], [features()], as_of_utc=NOW
    )
    assert report["scored"] == 0
    assert report["blocked"][status] == 1


def test_missing_features_no_invented_probabilities():
    report = v2_preview.shadow_preview([market()], [], as_of_utc=NOW)
    assert report["scored"] == 0
    assert report["blocked"]["NO_FEATURES"] == 1


def test_feature_time_after_quote_is_ineligible():
    report = v2_preview.shadow_preview(
        [market()], [features(feature_history_cutoff_utc="2026-10-13T14:01:00Z")], as_of_utc=NOW
    )
    assert report["scored"] == 0
    assert report["blocked"]["INVALID_FEATURE_CUTOFF"] == 1


def test_actual_kickoff_must_be_future():
    report = v2_preview.shadow_preview(
        [market(commence_time_utc="2026-10-12T19:00:00Z",
                snapshot_time_utc="2026-10-12T12:00:00Z")], [], as_of_utc=NOW
    )
    assert report["scored"] == 0
    assert report["blocked"]["EXPIRED_FIXTURE"] == 1


@pytest.mark.parametrize("tamper", [
    {"league": "EPL"},
    {"snapshot_time_utc": KICKOFF},
    {"commence_time_utc": "2026-10-19T19:00:00"},
    {"home_odds": 1.0},
    {"home_odds": "NaN"},
    {"home_team": "Napoli", "away_team": "Napoli"},
    {"result": "H"},
])
def test_market_invalid_inputs_fail_or_are_blocked(tamper):
    if "home_odds" in tamper:
        report = v2_preview.shadow_preview([market(**tamper)], [features()], as_of_utc=NOW)
        assert report["scored"] == 0
        assert report["blocked"]["INVALID_MARKET"] == 1
    else:
        with pytest.raises(ValueError):
            v2_preview.shadow_preview([market(**tamper)], [features()], as_of_utc=NOW)


def test_feature_identity_and_frozen_feature_list_cannot_be_guessed():
    missing = features(features={"diff_points_5": 1.0})
    with pytest.raises(ValueError, match="19-feature original"):
        v2_preview.shadow_preview([market()], [missing], as_of_utc=NOW)
    fake = features()
    fake["features"]["result"] = "H"
    with pytest.raises(ValueError, match="result fields"):
        v2_preview.shadow_preview([market()], [fake], as_of_utc=NOW)
    with pytest.raises(ValueError, match="duplicate feature identity"):
        v2_preview.shadow_preview([market()], [features(), features()], as_of_utc=NOW)


def test_fallback_uses_latest_qualified_observation_only():
    earlier = market(snapshot_time_utc="2026-10-13T12:00:00Z",home_odds=3.0)
    report = v2_preview.shadow_preview([market(),earlier], [features()], as_of_utc=NOW)
    assert report["scored"] == 1
    assert report["previews"][0]["market_snapshot_time_utc"] == QUOTE.replace("+00:00", "+00:00")
    with pytest.raises(ValueError, match="duplicate exact market observation"):
        v2_preview.shadow_preview([market(),market()], [features()], as_of_utc=NOW)


def test_read_only_saved_supabase_query_does_not_call_provider():
    class Result:
        data = [market()]
    class Q:
        def __init__(self):
            self.calls = []
        def select(self, v): self.calls.append("select");return self
        def eq(self, k, v): self.calls.append("eq");assert (k,v)==("league","SERIE_A");return self
        def gt(self, k, v): self.calls.append("gt"); assert k=="commence_time_utc";return self
        def order(self, *a, **kw): self.calls.append("order");return self
        def limit(self, n): self.calls.append("limit");assert n==1000;return self
        def execute(self): self.calls.append("execute");return Result()
    class DB:
        def __init__(self): self.query=Q()
        def table(self, name):
            assert name=="odds_snapshots"
            return self.query
    db=DB()
    assert v2_preview.fetch_saved_upcoming_serie_a_quotes(db,now=NOW)==[market()]
    assert db.query.calls==["select","eq","gt","order","limit","execute"]


def test_research_no_promotion_or_outcome_read_source():
    src = Path("serie_a_v2_frozen_shadow_preview.py").read_text(encoding="utf-8")
    for forbidden in ("api.the-odds-api.com",".upsert(", ".insert(", ".update(", ".delete(",
                      "pickle.dump(", "joblib.dump(", "product_prediction_snapshots"):
        assert forbidden not in src
    assert '"eligible_for_frozen_prospective_cohort": False' in src
    assert '"eligible_for_product_publication": False' in src
    assert '"market_fallback_is_ai_model": False' in src



def test_entirely_imputed_inputs_are_not_treated_as_real_v2_forecasts():
    candidate = v2_preview.load_verified_original()
    missing = features(features={name: None for name in candidate["features"]})
    report = v2_preview.shadow_preview([market()], [missing], as_of_utc=NOW)
    assert report["scored"] == 0
    assert report["blocked"]["ALL_FEATURES_MEDIAN_IMPUTED"] == 1
    assert report["previews"] == []
    assert report["no_bet"] is True


def test_preserve_exact_frozen_predictions_with_explicit_imputation_diagnostics():
    report = v2_preview.shadow_preview([market()], [features()], as_of_utc=NOW)
    row = report["previews"][0]
    original = v2_preview.load_verified_original()
    assert row["observed_frozen_feature_count"] == 15
    assert row["median_imputed_frozen_feature_count"] == 4
    assert row["observed_frozen_feature_count"] + row["median_imputed_frozen_feature_count"] == len(original["features"])
    assert row["source_data_quality"] == "PARTIAL_MEDIAN_IMPUTATION"
    assert row["median_imputed_feature_names"] == [original["features"][i] for i in (0, 6, 12, 18)]
    assert row["historical_team_coverage"] is None
    assert row["market_1x2"] == pytest.approx(row["active_market_fallback_1x2"])
    assert row["no_bet"] is True


def test_odss_api_free_candidate_remains_held_outside_frozen_original_v2():
    audit_path = Path(
        "research/market_anchor_1x2_v2_odss_api_source_audit_20261120.json"
    )
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert audit["candidate_status"] == "HOLD_NO_INTEGRATION"
    assert audit["decision"]["integration_allowed_by_current_v2_contract"] is False
    assert audit["current_v2_contract"]["candidate_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert audit["current_v2_contract"]["frozen_feature_count"] == 19
    assert audit["current_v2_contract"]["active_lambda"] == 0.0
    assert audit["current_v2_contract"]["shadow_lambda"] == 1.0
    assert audit["rights"]["free_internal_model_analysis_listed_as_permitted"] is True
    assert audit["rights"]["free_tier_long_term_raw_retention_confirmed"] is False
    assert audit["free_plan"]["external_display_permitted"] is False
    assert audit["rights"]["historical_odds_endpoint_enabled"] is False
    assert audit["actions"]["api_key_created"] is False
    assert audit["actions"]["authenticated_odds_requests_made"] is False
    assert audit["actions"]["supabase_writes"] is False
    assert audit["actions"]["supabase_ddl"] is False
    assert audit["actions"]["paid_provider_calls"] is False
    assert audit["actions"]["model_code_changed"] is False


def test_api_football_free_stats_candidate_remains_held_outside_frozen_original_v2():
    audit_path = Path(
        "research/market_anchor_1x2_v2_api_football_free_stats_source_audit_20261120.json"
    )
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert audit["candidate_status"] == "HOLD_NO_INTEGRATION"
    assert audit["free_plan"]["price_usd_per_month"] == 0
    assert audit["free_plan"]["requests_per_day"] == 100
    assert audit["free_plan"]["statistics_endpoint_listed"] is True
    assert audit["technical_coverage"]["free_serie_a_2026_27_coverage_verified"] is False
    assert audit["technical_coverage"]["complete_original_19_feature_parity_verified"] is False
    assert audit["technical_coverage"]["per_stat_source_observation_timestamp_documented"] is False
    assert audit["rights"]["provider_publication_license_granted"] is False
    assert audit["rights"]["commercial_rights_on_competitions_granted"] is False
    assert audit["rights"]["internal_model_use_explicitly_cleared"] is False
    assert audit["current_v2_contract"]["new_source_integration_allowed"] is False
    assert audit["current_v2_contract"]["candidate_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert audit["current_v2_contract"]["frozen_feature_count"] == 19
    assert audit["current_v2_contract"]["active_lambda"] == 0
    assert audit["current_v2_contract"]["shadow_lambda"] == 1
    assert audit["actions"]["api_key_created"] is False
    assert audit["actions"]["authenticated_api_requests_made"] is False
    assert audit["actions"]["provider_api_calls"] == 0
    assert audit["actions"]["odds_endpoint_called"] is False
    assert audit["actions"]["supabase_writes"] is False
    assert audit["actions"]["supabase_ddl"] is False
    assert audit["actions"]["model_code_changed"] is False
    assert audit["actions"]["model_weights_changed"] is False
    assert audit["actions"]["production_pkl_changed"] is False
    assert audit["actions"]["protected_outcomes_read"] is False
