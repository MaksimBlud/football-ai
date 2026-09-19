import inspect

import pytest

import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2_lock as lock
import corner_regime_adjusted_direction_v2_metadata as metadata
import corner_regime_adjusted_direction_v2_odds_plan as plan


def _fixture(fid, league, date):
    return {
        "fixture_id": str(fid),
        "league": league,
        "league_id": str(metadata.replication.LEAGUES[league]),
        "kickoff_utc": f"{date}T15:00:00Z",
        "home_team": f"H{fid}",
        "away_team": f"A{fid}",
        "status": "finished",
    }


def _lock_manifest():
    rows = []
    fid = 20000
    for date in ("2026-09-20", "2026-09-27", "2026-10-04"):
        for league in v2.LEAGUE_ORDER:
            for _ in range(5):
                rows.append(_fixture(fid, league, date))
                fid += 1

    metadata_plan = v2.plan_future_cohort(rows, excluded_ids=set())
    metadata_plan.update(
        {
            "metadata_live_experiment_id": metadata.EXPERIMENT_ID,
            "market_prices_opened": False,
            "total_prior_excluded_fixture_ids": 151,
        }
    )
    return lock.build_lock_manifest(
        metadata_plan,
        rows,
        source_run_id="123",
        source_artifact_id="456",
        source_artifact_digest="d" * 64,
    )


def test_valid_lock_builds_deterministic_metadata_bound_batched_plan():
    manifest = _lock_manifest()
    result = plan.build_acquisition_plan(manifest)

    assert result["plan_experiment_id"] == plan.PLAN_EXPERIMENT_ID
    assert result["offline_only"] is True
    assert result["live_odds_acquisition_authorized"] is False
    assert result["requires_explicit_live_authorization"] is True
    assert result["fixture_reselection_allowed"] is False
    assert result["betting_enabled"] is False
    assert result["production_promotion_authorized"] is False
    assert result["selected_fixture_ids"] == manifest["selected_fixture_ids"]
    assert result["selected_fixture_metadata"] == manifest["selected_fixture_metadata"]
    assert result["source_fixture_metadata_sha256"] == manifest[
        "fixture_metadata_sha256"
    ]
    assert result["total_planned_odds_requests"] == result["selected_fixture_count"]
    assert result["max_odds_requests_per_run"] == 30

    flattened_ids = [
        fixture_id
        for batch in result["batches"]
        for fixture_id in batch["fixture_ids"]
    ]
    flattened_metadata = [
        row
        for batch in result["batches"]
        for row in batch["fixture_metadata"]
    ]
    assert flattened_ids == manifest["selected_fixture_ids"]
    assert flattened_metadata == manifest["selected_fixture_metadata"]
    assert all(batch["planned_requests"] <= 30 for batch in result["batches"])
    assert all(
        batch["batch_index"] == index
        for index, batch in enumerate(result["batches"], start=1)
    )


def test_tampered_selection_hash_fails_closed():
    manifest = _lock_manifest()
    manifest["selection_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(RuntimeError, match="selection_sha256 mismatch"):
        plan.validate_lock_manifest(manifest)


def test_tampered_fixture_metadata_hash_or_order_fails_closed():
    manifest = _lock_manifest()
    manifest["fixture_metadata_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="fixture_metadata_sha256 mismatch"):
        plan.validate_lock_manifest(manifest)

    manifest = _lock_manifest()
    manifest["selected_fixture_metadata"] = list(
        reversed(manifest["selected_fixture_metadata"])
    )
    with pytest.raises(RuntimeError, match="metadata does not match"):
        plan.validate_lock_manifest(manifest)


def test_source_cannot_pre_authorize_odds():
    manifest = _lock_manifest()
    manifest["odds_acquisition_authorized"] = True

    with pytest.raises(RuntimeError, match="odds_acquisition_authorized"):
        plan.validate_lock_manifest(manifest)


def test_reordered_or_duplicate_fixture_membership_fails_closed():
    manifest = _lock_manifest()
    manifest["selected_fixture_ids"] = list(reversed(manifest["selected_fixture_ids"]))

    with pytest.raises(RuntimeError, match="whole-block"):
        plan.validate_lock_manifest(manifest)

    manifest = _lock_manifest()
    manifest["selected_fixture_ids"][1] = manifest["selected_fixture_ids"][0]
    with pytest.raises(RuntimeError):
        plan.validate_lock_manifest(manifest)


def test_batched_plan_is_stable_for_same_lock():
    manifest = _lock_manifest()
    first = plan.build_acquisition_plan(manifest)
    second = plan.build_acquisition_plan(dict(manifest))
    assert first == second


def test_plan_module_has_no_network_or_odds_transport():
    source = inspect.getsource(plan)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert '"/odds"' not in source
    assert "'/odds'" not in source
