import inspect
import json
import zipfile

import pytest

import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2_lock as lock
import corner_regime_adjusted_direction_v2_metadata as metadata


def _fixture(fid, league, date):
    return {
        "fixture_id": str(fid),
        "league": league,
        "kickoff_utc": f"{date}T15:00:00Z",
        "status": "finished",
    }


def _locked_plan():
    rows = []
    fid = 10000
    for date in ("2026-09-20", "2026-09-27", "2026-10-04"):
        for league in v2.LEAGUE_ORDER:
            for _ in range(5):
                rows.append(_fixture(fid, league, date))
                fid += 1

    plan = v2.plan_future_cohort(rows, excluded_ids=set())
    assert plan["status"] == "COHORT_LOCKED"
    plan.update(
        {
            "metadata_live_experiment_id": metadata.EXPERIMENT_ID,
            "market_prices_opened": False,
            "total_prior_excluded_fixture_ids": 151,
        }
    )
    return plan


def test_valid_locked_plan_builds_immutable_manifest():
    plan = _locked_plan()
    manifest = lock.build_lock_manifest(
        plan,
        source_run_id="12345",
        source_artifact_id="67890",
        source_artifact_digest="a" * 64,
    )

    assert manifest["lock_experiment_id"] == lock.LOCK_EXPERIMENT_ID
    assert manifest["lock_status"] == "IMMUTABLE_COHORT_LOCKED"
    assert manifest["immutable"] is True
    assert manifest["offline_only"] is True
    assert manifest["odds_acquisition_authorized"] is False
    assert manifest["betting_enabled"] is False
    assert manifest["production_promotion_authorized"] is False
    assert manifest["selected_fixture_ids"] == plan["selected_fixture_ids"]
    assert manifest["selected_blocks"] == plan["selected_blocks"]
    assert manifest["metadata_potential_pairs"] == plan["metadata_potential_pairs"]
    assert manifest["selection_sha256"].startswith("sha256:")
    assert len(manifest["selection_sha256"]) == 71
    assert manifest["source_artifact_digest"] == "sha256:" + "a" * 64


def test_selection_hash_is_stable_to_irrelevant_plan_key_order():
    plan = _locked_plan()
    reordered = dict(reversed(list(plan.items())))

    first = lock.build_lock_manifest(
        plan,
        source_run_id="1",
        source_artifact_id="2",
        source_artifact_digest="b" * 64,
    )
    second = lock.build_lock_manifest(
        reordered,
        source_run_id="1",
        source_artifact_id="2",
        source_artifact_digest="b" * 64,
    )
    assert first["selection_sha256"] == second["selection_sha256"]


def test_wait_for_cohort_fails_closed():
    plan = _locked_plan()
    plan["status"] = "WAIT_FOR_COHORT"
    plan["locked"] = False

    with pytest.raises(RuntimeError, match="not COHORT_LOCKED"):
        lock.build_lock_manifest(
            plan,
            source_run_id="1",
            source_artifact_id="2",
            source_artifact_digest="c" * 64,
        )


def test_tampered_selected_fixture_order_fails_closed():
    plan = _locked_plan()
    plan["selected_fixture_ids"] = list(reversed(plan["selected_fixture_ids"]))

    with pytest.raises(RuntimeError, match="deterministic earliest prefix"):
        lock.validate_locked_plan(plan)


def test_changed_metadata_gate_fails_closed():
    plan = _locked_plan()
    plan["cohort_lock_gate"] = dict(plan["cohort_lock_gate"])
    plan["cohort_lock_gate"]["minimum_metadata_potential_pairs"] = 79

    with pytest.raises(RuntimeError, match="cohort-lock gate"):
        lock.validate_locked_plan(plan)


def test_duplicate_selected_fixture_fails_closed():
    plan = _locked_plan()
    duplicate = plan["selected_fixture_ids"][0]
    plan["selected_blocks"][0]["fixture_ids"][1] = duplicate
    plan["selected_blocks"][0]["fixture_count"] = len(
        plan["selected_blocks"][0]["fixture_ids"]
    )

    with pytest.raises(RuntimeError):
        lock.validate_locked_plan(plan)


def test_loader_requires_exactly_one_plan(tmp_path):
    path = tmp_path / "metadata.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("a/cohort_plan.json", json.dumps(_locked_plan()))
        zf.writestr("b/cohort_plan.json", json.dumps(_locked_plan()))

    with pytest.raises(RuntimeError, match="exactly one"):
        lock.load_cohort_plan(path)


def test_lock_module_has_no_network_or_odds_transport():
    source = inspect.getsource(lock)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert '"/odds"' not in source
    assert "'/odds'" not in source
