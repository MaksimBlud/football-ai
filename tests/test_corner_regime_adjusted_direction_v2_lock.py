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
        "league_id": str(metadata.replication.LEAGUES[league]),
        "kickoff_utc": f"{date}T15:00:00Z",
        "home_team": f"H{fid}",
        "away_team": f"A{fid}",
        "status": "finished",
    }


def _locked_source():
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
    return plan, rows


def _manifest():
    plan, rows = _locked_source()
    return lock.build_lock_manifest(
        plan,
        rows,
        source_run_id="12345",
        source_artifact_id="67890",
        source_artifact_digest="a" * 64,
    )


def test_valid_locked_plan_builds_metadata_bound_immutable_manifest():
    plan, rows = _locked_source()
    manifest = lock.build_lock_manifest(
        plan,
        rows,
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
    assert [r["fixture_id"] for r in manifest["selected_fixture_metadata"]] == plan[
        "selected_fixture_ids"
    ]
    assert all(
        set(row)
        == {
            "fixture_id",
            "league",
            "league_id",
            "kickoff_utc",
            "home_team",
            "away_team",
        }
        for row in manifest["selected_fixture_metadata"]
    )
    assert manifest["metadata_potential_pairs"] == plan["metadata_potential_pairs"]
    assert manifest["selection_sha256"].startswith("sha256:")
    assert manifest["fixture_metadata_sha256"].startswith("sha256:")
    assert len(manifest["selection_sha256"]) == 71
    assert len(manifest["fixture_metadata_sha256"]) == 71
    assert manifest["source_artifact_digest"] == "sha256:" + "a" * 64


def test_selection_hash_is_stable_to_irrelevant_plan_key_order_and_extra_metadata():
    plan, rows = _locked_source()
    reordered = dict(reversed(list(plan.items())))
    extra = list(rows) + [
        _fixture("999999", "EPL", "2026-12-31")
    ]

    first = lock.build_lock_manifest(
        plan,
        rows,
        source_run_id="1",
        source_artifact_id="2",
        source_artifact_digest="b" * 64,
    )
    second = lock.build_lock_manifest(
        reordered,
        extra,
        source_run_id="1",
        source_artifact_id="2",
        source_artifact_digest="b" * 64,
    )
    assert first["selection_sha256"] == second["selection_sha256"]
    assert first["fixture_metadata_sha256"] == second["fixture_metadata_sha256"]


def test_wait_for_cohort_fails_closed():
    plan, rows = _locked_source()
    plan["status"] = "WAIT_FOR_COHORT"
    plan["locked"] = False

    with pytest.raises(RuntimeError, match="not COHORT_LOCKED"):
        lock.build_lock_manifest(
            plan,
            rows,
            source_run_id="1",
            source_artifact_id="2",
            source_artifact_digest="c" * 64,
        )


def test_tampered_selected_fixture_order_fails_closed():
    plan, _ = _locked_source()
    plan["selected_fixture_ids"] = list(reversed(plan["selected_fixture_ids"]))

    with pytest.raises(RuntimeError, match="deterministic earliest prefix"):
        lock.validate_locked_plan(plan)


def test_missing_or_changed_selected_fixture_metadata_fails_closed():
    plan, rows = _locked_source()
    selected = plan["selected_fixture_ids"][0]

    missing_rows = [row for row in rows if row["fixture_id"] != selected]
    with pytest.raises(RuntimeError, match="metadata missing"):
        lock.selected_fixture_metadata(plan, missing_rows)

    changed_rows = [dict(row) for row in rows]
    for row in changed_rows:
        if row["fixture_id"] == selected:
            row["home_team"] = ""
            break
    with pytest.raises(RuntimeError, match="missing home/away"):
        lock.selected_fixture_metadata(plan, changed_rows)


def test_fixture_metadata_must_match_block_and_league_mapping():
    plan, rows = _locked_source()
    selected = plan["selected_fixture_ids"][0]

    bad_league = [dict(row) for row in rows]
    for row in bad_league:
        if row["fixture_id"] == selected:
            row["league_id"] = "wrong"
            break
    with pytest.raises(RuntimeError, match="league_id mismatch"):
        lock.selected_fixture_metadata(plan, bad_league)

    bad_date = [dict(row) for row in rows]
    for row in bad_date:
        if row["fixture_id"] == selected:
            row["kickoff_utc"] = "2026-12-30T15:00:00Z"
            break
    with pytest.raises(RuntimeError, match="kickoff date"):
        lock.selected_fixture_metadata(plan, bad_date)


def test_changed_metadata_gate_fails_closed():
    plan, _ = _locked_source()
    plan["cohort_lock_gate"] = dict(plan["cohort_lock_gate"])
    plan["cohort_lock_gate"]["minimum_metadata_potential_pairs"] = 79

    with pytest.raises(RuntimeError, match="cohort-lock gate"):
        lock.validate_locked_plan(plan)


def test_duplicate_selected_fixture_fails_closed():
    plan, _ = _locked_source()
    duplicate = plan["selected_fixture_ids"][0]
    plan["selected_blocks"][0]["fixture_ids"][1] = duplicate
    plan["selected_blocks"][0]["fixture_count"] = len(
        plan["selected_blocks"][0]["fixture_ids"]
    )

    with pytest.raises(RuntimeError):
        lock.validate_locked_plan(plan)


def test_loader_requires_exactly_one_plan_and_metadata_file(tmp_path):
    plan, rows = _locked_source()

    duplicate_plan = tmp_path / "duplicate-plan.zip"
    with zipfile.ZipFile(duplicate_plan, "w") as zf:
        zf.writestr("a/cohort_plan.json", json.dumps(plan))
        zf.writestr("b/cohort_plan.json", json.dumps(plan))
        zf.writestr("a/future_fixture_metadata.json", json.dumps(rows))
    with pytest.raises(RuntimeError, match="exactly one cohort_plan"):
        lock.load_metadata_artifact(duplicate_plan)

    missing_metadata = tmp_path / "missing-metadata.zip"
    with zipfile.ZipFile(missing_metadata, "w") as zf:
        zf.writestr("a/cohort_plan.json", json.dumps(plan))
    with pytest.raises(RuntimeError, match="future_fixture_metadata"):
        lock.load_metadata_artifact(missing_metadata)


def test_lock_module_has_no_network_or_odds_transport():
    source = inspect.getsource(lock)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert '"/odds"' not in source
    assert "'/odds'" not in source
