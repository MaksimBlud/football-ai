from pathlib import Path

import pytest

from bootstrap_product_predictions_from_pair_ledger import (
    build_bootstrap_rows,
    snapshot_from_pair_row,
)
from product_snapshot_store import PREDICTION_COLUMNS


ROOT = Path(__file__).resolve().parents[1]


def pair_row(**overrides):
    row = {
        "experiment_id": "EPL_AI_MARKET_PAIR_V1",
        "league": "EPL",
        "event_id": "event-live-1",
        "provider_home_team": "Liverpool",
        "provider_away_team": "Fulham",
        "model_home_team": "Liverpool",
        "model_away_team": "Fulham",
        "kickoff_utc": "2026-09-12T14:00:00+00:00",
        "model_generated_at_utc": "2026-09-12T04:49:14+00:00",
        "model_home_prob": 0.675,
        "model_draw_prob": 0.157,
        "model_away_prob": 0.168,
        "model_artifact_sha256": "a" * 64,
        "code_commit_sha": "b" * 40,
    }
    row.update(overrides)
    return row


def test_pair_ledger_bootstrap_preserves_real_model_provenance_and_london_kickoff():
    row = snapshot_from_pair_row(pair_row(), run_id="pair-ledger-bootstrap:test")

    assert row["event_id"] == "event-live-1"
    assert row["match_date"] == "2026-09-12"
    assert row["match_time"] == "15:00"  # BST = UTC+1 in September
    assert row["prediction"] == "HOME"
    assert row["model_1x2_version"] == "EPL_AI_MARKET_PAIR_V1"
    assert row["model_1x2_sha256"] == "a" * 64
    assert row["publisher_version"] == "product-publisher.pair-ledger-bootstrap.v1"
    assert row["expected_total_goals"] is None


def test_bootstrap_keeps_latest_generation_per_event():
    older = pair_row(model_generated_at_utc="2026-09-11T04:00:00+00:00", model_home_prob=0.60, model_draw_prob=0.20, model_away_prob=0.20)
    newer = pair_row(model_generated_at_utc="2026-09-12T04:49:14+00:00")

    run_id, rows = build_bootstrap_rows([older, newer])

    assert run_id == "pair-ledger-bootstrap:20260912T044914Z"
    assert len(rows) == 1
    assert rows[0]["home_probability"] == pytest.approx(0.675)


def test_bootstrap_rejects_invalid_probability_vector():
    with pytest.raises(ValueError, match="sum to 1"):
        snapshot_from_pair_row(
            pair_row(model_home_prob=0.70, model_draw_prob=0.20, model_away_prob=0.20),
            run_id="pair-ledger-bootstrap:test",
        )


def test_public_prediction_select_excludes_internal_model_provenance():
    assert "model_1x2_sha256" not in PREDICTION_COLUMNS
    assert "model_goals_sha256" not in PREDICTION_COLUMNS
    assert "publisher_version" not in PREDICTION_COLUMNS
    assert "event_id" in PREDICTION_COLUMNS
    assert "commence_time_utc" in PREDICTION_COLUMNS


def test_public_product_migration_is_read_only_and_time_bounded():
    sql = (
        ROOT
        / "supabase/migrations/20260912091500_public_product_read_window.sql"
    ).read_text(encoding="utf-8").lower()

    assert "revoke all privileges" in sql
    assert "from anon" in sql
    assert "grant select (" in sql
    assert "to anon" in sql
    assert 'create policy "anon reads upcoming product prediction snapshots"' in sql
    assert 'create policy "anon reads upcoming product odds"' in sql
    assert "commence_time_utc >= now() - interval '2 hours'" in sql
    assert "commence_time_utc < now() + interval '15 days'" in sql
    assert "grant insert" not in sql
    assert "grant update" not in sql
    assert "grant delete" not in sql


def test_web_detail_route_uses_stable_string_id_and_publishable_key():
    source = (ROOT / "web_app.py").read_text(encoding="utf-8")

    assert "def product_market_match(match_id: str)" in source
    assert 'get("product_match_id") == match_id' in source
    assert "SUPABASE_PUBLISHABLE_KEY" in source
    assert "match_id < 0" not in source
