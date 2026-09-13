from datetime import datetime, timezone

import pytest

from advance_product_lifecycle import _fetch_all
from product_operational_automation import (
    CYCLE_ACTION_REQUIRED,
    CYCLE_HEALTHY_NOOP,
    CYCLE_READY_TO_APPLY,
    FROZEN_EPL_MODEL_SHA256,
    OPERATIONAL_PUBLISHER_VERSION,
    SOURCE_COVERED,
    SOURCE_READY_TO_INGEST,
    SOURCE_WAITING,
    build_incremental_product_rows,
    build_operational_report,
    source_coverage,
    validate_private_supabase_credentials,
)


NOW = datetime(2026, 9, 13, 5, 0, tzinfo=timezone.utc)
KICKOFF = "2026-09-14T19:00:00+00:00"
GENERATION_1 = "2026-09-13T04:00:00+00:00"
GENERATION_2 = "2026-09-13T04:30:00+00:00"


def pair_row(**overrides):
    row = {
        "pair_key": "pair-1",
        "experiment_id": "EPL_AI_MARKET_PAIR_V1",
        "league": "EPL",
        "event_id": "event-1",
        "provider_home_team": "Arsenal",
        "provider_away_team": "Chelsea",
        "model_home_team": "Arsenal",
        "model_away_team": "Chelsea",
        "kickoff_utc": KICKOFF,
        "model_generated_at_utc": GENERATION_1,
        "model_home_prob": 0.55,
        "model_draw_prob": 0.25,
        "model_away_prob": 0.20,
        "model_artifact_sha256": FROZEN_EPL_MODEL_SHA256,
        "code_commit_sha": "abc123",
    }
    row.update(overrides)
    return row


def product_row(**overrides):
    row = {
        "league": "EPL",
        "event_id": "event-1",
        "commence_time_utc": KICKOFF,
        "generated_at_utc": GENERATION_1,
    }
    row.update(overrides)
    return row


def odds_row(**overrides):
    row = {
        "league": "EPL",
        "event_id": "event-1",
        "commence_time_utc": KICKOFF,
    }
    row.update(overrides)
    return row


def test_existing_product_event_is_idempotent_noop():
    pending = build_incremental_product_rows(
        [pair_row()], [product_row()], now_utc=NOW
    )
    assert pending == []


def test_newer_pair_generation_is_held_for_already_published_fixture():
    pending = build_incremental_product_rows(
        [pair_row(model_generated_at_utc=GENERATION_2)],
        [product_row()],
        now_utc=NOW,
    )
    coverage = source_coverage(
        [odds_row()],
        [product_row()],
        [pair_row(model_generated_at_utc=GENERATION_2)],
        now_utc=NOW,
    )

    assert pending == []
    assert coverage["state"] == SOURCE_COVERED
    assert coverage["revision_candidates_held"] == 1


def test_first_pair_for_new_event_creates_one_product_snapshot():
    pending = build_incremental_product_rows([pair_row()], [], now_utc=NOW)

    assert len(pending) == 1
    snapshot = pending[0]
    assert snapshot["event_id"] == "event-1"
    assert snapshot["generated_at_utc"] == GENERATION_1
    assert snapshot["publisher_version"] == OPERATIONAL_PUBLISHER_VERSION
    assert snapshot["run_id"].startswith("pair-ledger-operational:")


def test_pair_bridge_fails_closed_on_post_kickoff_model_generation():
    with pytest.raises(ValueError, match="not pre-kickoff"):
        build_incremental_product_rows(
            [pair_row(model_generated_at_utc="2026-09-14T19:00:00+00:00")],
            [],
            now_utc=NOW,
        )


def test_pair_bridge_fails_closed_on_unapproved_model_sha():
    with pytest.raises(ValueError, match="unexpected EPL model artifact SHA"):
        build_incremental_product_rows(
            [pair_row(model_artifact_sha256="bad-sha")], [], now_utc=NOW
        )


def test_known_odds_event_with_product_prediction_is_covered():
    coverage = source_coverage(
        [odds_row()], [product_row()], [pair_row()], now_utc=NOW
    )
    assert coverage["state"] == SOURCE_COVERED
    assert coverage["known_future_odds_events"] == 1
    assert coverage["covered_product_events"] == 1
    assert coverage["waiting_for_prediction_source"] == 0
    assert coverage["revision_candidates_held"] == 0


def test_missing_product_with_valid_pair_is_ready_to_ingest_not_fabricated():
    coverage = source_coverage([odds_row()], [], [pair_row()], now_utc=NOW)
    pending = build_incremental_product_rows([pair_row()], [], now_utc=NOW)

    assert coverage["state"] == SOURCE_READY_TO_INGEST
    assert coverage["ready_from_pair_ledger"] == 1
    assert len(pending) == 1


def test_missing_product_and_pair_waits_for_prediction_source():
    coverage = source_coverage([odds_row()], [], [], now_utc=NOW)

    assert coverage["state"] == SOURCE_WAITING
    assert coverage["waiting_for_prediction_source"] == 1
    assert coverage["waiting_event_ids"] == ["event-1"]


def test_source_monitor_uses_same_pair_validation_as_bridge():
    with pytest.raises(ValueError, match="unexpected EPL model artifact SHA"):
        source_coverage(
            [odds_row()],
            [],
            [pair_row(model_artifact_sha256="bad-sha")],
            now_utc=NOW,
        )


def test_private_credential_contract_rejects_public_or_missing_key():
    with pytest.raises(RuntimeError, match="SUPABASE_KEY is required"):
        validate_private_supabase_credentials(
            supabase_url="https://example.supabase.co", supabase_key=None
        )
    with pytest.raises(RuntimeError, match="publishable credentials"):
        validate_private_supabase_credentials(
            supabase_url="https://example.supabase.co",
            supabase_key="sb_publishable_public",
        )

    validate_private_supabase_credentials(
        supabase_url="https://example.supabase.co", supabase_key="private-service-key"
    )


def test_cycle_status_distinguishes_noop_apply_and_action_required():
    base_counts = {
        "registered": 0,
        "market_observed": 0,
        "settled": 0,
        "skipped_non_pre_kickoff": 0,
    }
    covered = {
        "state": SOURCE_COVERED,
        "known_future_odds_events": 1,
        "covered_product_events": 1,
        "ready_from_pair_ledger": 0,
        "waiting_for_prediction_source": 0,
        "waiting_event_ids": [],
        "revision_candidates_held": 0,
        "coverage_ratio": 1.0,
    }
    noop = build_operational_report(
        coverage=covered,
        pending_prediction_count=0,
        lifecycle_counts=base_counts,
        lifecycle_pending_count=0,
    )
    apply = build_operational_report(
        coverage=covered,
        pending_prediction_count=0,
        lifecycle_counts={**base_counts, "market_observed": 1},
        lifecycle_pending_count=1,
    )
    action = build_operational_report(
        coverage={**covered, "state": SOURCE_WAITING},
        pending_prediction_count=0,
        lifecycle_counts=base_counts,
        lifecycle_pending_count=0,
    )

    assert noop["status"] == CYCLE_HEALTHY_NOOP
    assert apply["status"] == CYCLE_READY_TO_APPLY
    assert action["status"] == CYCLE_ACTION_REQUIRED
    assert noop["safety"]["paid_provider_calls"] is False
    assert noop["safety"]["model_inference"] is False
    assert noop["safety"]["automatic_forecast_revisions"] is False
    assert noop["safety"]["betting_actions"] is False


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.start = 0
        self.end = len(rows) - 1

    def select(self, _columns):
        return self

    def order(self, _column):
        return self

    def range(self, start, end):
        self.start = start
        self.end = end
        return self

    def execute(self):
        return FakeResponse(self.rows[self.start : self.end + 1])


class FakeClient:
    def __init__(self, rows):
        self.rows = rows

    def table(self, _name):
        return FakeQuery(self.rows)


def test_lifecycle_loader_paginates_beyond_old_5000_row_cap():
    rows = [{"id": index} for index in range(6001)]
    loaded = _fetch_all(FakeClient(rows), "odds_snapshots", order="id", page_size=1000)

    assert len(loaded) == 6001
    assert loaded[0]["id"] == 0
    assert loaded[-1]["id"] == 6000
