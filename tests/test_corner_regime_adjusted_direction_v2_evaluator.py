import inspect
import json
import zipfile

import pandas as pd
import pytest

import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2_evaluator as evaluator
import corner_regime_adjusted_direction_v2_lock as lock
import corner_regime_adjusted_direction_v2_metadata as metadata
import corner_regime_adjusted_direction_v2_odds_plan as odds_plan


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


def _lock_and_plan():
    rows = []
    fid = 30000
    for date in ("2026-09-20", "2026-09-27", "2026-10-04"):
        for league in v2.LEAGUE_ORDER:
            for _ in range(5):
                rows.append(_fixture(fid, league, date))
                fid += 1

    metadata_plan = v2.plan_future_cohort(rows, excluded_ids=set())
    assert metadata_plan["status"] == "COHORT_LOCKED"
    metadata_plan.update(
        {
            "metadata_live_experiment_id": metadata.EXPERIMENT_ID,
            "market_prices_opened": False,
            "total_prior_excluded_fixture_ids": 151,
        }
    )
    manifest = lock.build_lock_manifest(
        metadata_plan,
        rows,
        source_run_id="123",
        source_artifact_id="456",
        source_artifact_digest="d" * 64,
    )
    plan = odds_plan.build_acquisition_plan(manifest)
    return manifest, plan


def _raw_zip(tmp_path, fixture_ids, *, extra_ids=(), duplicate_id=None):
    path = tmp_path / "raw-odds.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for fixture_id in fixture_ids:
            zf.writestr(
                f"artifact/raw/odds/{fixture_id}.json",
                json.dumps({"success": 1, "data": [{"fixture_id": fixture_id}]}),
            )
        for fixture_id in extra_ids:
            zf.writestr(
                f"artifact/raw/odds/{fixture_id}.json",
                json.dumps({"success": 1, "data": []}),
            )
        if duplicate_id is not None:
            zf.writestr(
                f"second/raw/odds/{duplicate_id}.json",
                json.dumps({"success": 1, "data": []}),
            )
    return path


def _digest(path):
    return evaluator._file_sha256(path)


def test_incomplete_acquisition_stops_before_normalization_and_statistics(
    monkeypatch, tmp_path
):
    manifest, plan = _lock_and_plan()
    selected_ids = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected_ids[:-1])

    def forbidden(*args, **kwargs):
        raise AssertionError("normalization/statistics must not run on incomplete acquisition")

    monkeypatch.setattr(evaluator.replication, "normalize_corner_odds", forbidden)
    monkeypatch.setattr(evaluator.direction_v1, "evaluate_fresh_direction", forbidden)

    rows, report = evaluator.evaluate(
        manifest,
        plan,
        raw_zip,
        raw_workflow_run_id="1000",
        raw_artifact_id="2000",
        raw_artifact_digest=_digest(raw_zip),
    )

    assert rows.empty
    assert report["status"] == "ACQUISITION_INCOMPLETE"
    assert report["acquisition_complete"] is False
    assert report["statistical_evaluation_performed"] is False
    assert report["verdict"] is None
    assert report["captured_locked_raw_responses"] == len(selected_ids) - 1
    assert report["missing_locked_fixture_ids"] == [selected_ids[-1]]


def test_complete_acquisition_runs_frozen_orchestration(monkeypatch, tmp_path):
    manifest, plan = _lock_and_plan()
    selected_ids = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected_ids)

    calls = {"normalize": 0, "direction": 0}

    def fake_normalize(payload, fixture):
        calls["normalize"] += 1
        return {
            "fixture_id": fixture["fixture_id"],
            "league": fixture["league"],
            "kickoff_utc": fixture["kickoff_utc"],
        }

    def fake_holdout_row(row):
        idx = int(row["fixture_id"]) % 10
        return {
            "fixture_id": row["fixture_id"],
            "league": row["league"],
            "kickoff_utc": row["kickoff_utc"],
            "opening_lambda": 9.0 + idx / 100.0,
            "closing_lambda": 9.1 + idx / 100.0,
            "centre_delta": 0.1,
            "movement_magnitude": 0.1,
        }

    def fake_direction(frame):
        calls["direction"] += 1
        assert len(frame) == len(selected_ids)
        evaluated = frame.copy()
        return evaluated, {
            "experiment_id": "CORNER_REGIME_ADJUSTED_DIRECTION_V1",
            "verdict": "SAMPLE_TOO_SMALL",
            "direction_discrimination_confirmed": False,
            "eligible_rows": len(frame),
        }

    monkeypatch.setattr(evaluator.replication, "normalize_corner_odds", fake_normalize)
    monkeypatch.setattr(evaluator.replication, "_normalize_holdout_row", fake_holdout_row)
    monkeypatch.setattr(
        evaluator.direction_v1,
        "evaluate_fresh_direction",
        fake_direction,
    )

    rows, report = evaluator.evaluate(
        manifest,
        plan,
        raw_zip,
        raw_workflow_run_id="1001",
        raw_artifact_id="2001",
        raw_artifact_digest=_digest(raw_zip),
    )

    assert calls["normalize"] == len(selected_ids)
    assert calls["direction"] == 1
    assert len(rows) == len(selected_ids)
    assert report["status"] == "EVALUATED"
    assert report["acquisition_complete"] is True
    assert report["statistical_evaluation_performed"] is True
    assert report["eligible_normalized_rows"] == len(selected_ids)
    assert report["ineligible_selected_fixture_ids"] == []
    assert report["verdict"] == "SAMPLE_TOO_SMALL"
    assert report["source_selection_sha256"] == manifest["selection_sha256"]
    assert report["source_fixture_metadata_sha256"] == manifest[
        "fixture_metadata_sha256"
    ]


def test_complete_acquisition_keeps_selected_but_reports_ineligible(
    monkeypatch, tmp_path
):
    manifest, plan = _lock_and_plan()
    selected_ids = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected_ids)
    ineligible = selected_ids[0]

    def fake_normalize(payload, fixture):
        if fixture["fixture_id"] == ineligible:
            return None
        return fixture

    monkeypatch.setattr(evaluator.replication, "normalize_corner_odds", fake_normalize)
    monkeypatch.setattr(
        evaluator.replication,
        "_normalize_holdout_row",
        lambda fixture: {
            "fixture_id": fixture["fixture_id"],
            "league": fixture["league"],
            "kickoff_utc": fixture["kickoff_utc"],
            "opening_lambda": 9.0,
            "closing_lambda": 9.0,
            "centre_delta": 0.0,
            "movement_magnitude": 0.0,
        },
    )
    monkeypatch.setattr(
        evaluator.direction_v1,
        "evaluate_fresh_direction",
        lambda frame: (
            frame,
            {
                "verdict": "SAMPLE_TOO_SMALL",
                "direction_discrimination_confirmed": False,
            },
        ),
    )

    rows, report = evaluator.evaluate(
        manifest,
        plan,
        raw_zip,
        raw_workflow_run_id="1002",
        raw_artifact_id="2002",
        raw_artifact_digest=_digest(raw_zip),
    )

    assert len(rows) == len(selected_ids) - 1
    assert report["ineligible_selected_fixture_ids"] == [ineligible]
    assert report["locked_fixture_count"] == len(selected_ids)
    assert report["captured_locked_raw_responses"] == len(selected_ids)


def test_raw_artifact_rejects_nonlocked_and_duplicate_fixture(tmp_path):
    manifest, _ = _lock_and_plan()
    selected_ids = manifest["selected_fixture_ids"]

    extra_zip = _raw_zip(tmp_path, selected_ids, extra_ids=("999999",))
    with pytest.raises(RuntimeError, match="non-locked fixture"):
        evaluator.load_raw_odds(extra_zip, selected_ids=selected_ids)

    duplicate_zip = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate_zip, "w") as zf:
        fixture_id = selected_ids[0]
        zf.writestr(
            f"a/raw/odds/{fixture_id}.json",
            json.dumps({"success": 1, "data": []}),
        )
        zf.writestr(
            f"b/raw/odds/{fixture_id}.json",
            json.dumps({"success": 1, "data": []}),
        )
    with pytest.raises(RuntimeError, match="duplicate raw odds response"):
        evaluator.load_raw_odds(duplicate_zip, selected_ids=selected_ids)


def test_lock_and_acquisition_plan_mismatch_fails_closed(tmp_path):
    manifest, plan = _lock_and_plan()
    selected_ids = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected_ids)

    bad_plan = dict(plan)
    bad_plan["source_selection_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="source_selection_sha256"):
        evaluator.evaluate(
            manifest,
            bad_plan,
            raw_zip,
            raw_workflow_run_id="1003",
            raw_artifact_id="2003",
            raw_artifact_digest=_digest(raw_zip),
        )

    bad_manifest = dict(manifest)
    bad_manifest["fixture_metadata_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="fixture_metadata_sha256"):
        evaluator.evaluate(
            bad_manifest,
            plan,
            raw_zip,
            raw_workflow_run_id="1004",
            raw_artifact_id="2004",
            raw_artifact_digest=_digest(raw_zip),
        )


def test_raw_artifact_digest_mismatch_fails_closed(tmp_path):
    manifest, plan = _lock_and_plan()
    raw_zip = _raw_zip(tmp_path, manifest["selected_fixture_ids"])

    with pytest.raises(RuntimeError, match="artifact digest mismatch"):
        evaluator.evaluate(
            manifest,
            plan,
            raw_zip,
            raw_workflow_run_id="1005",
            raw_artifact_id="2005",
            raw_artifact_digest="0" * 64,
        )


def test_evaluator_module_has_no_network_or_live_transport():
    source = inspect.getsource(evaluator)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert "api.5dollarfootball.com" not in source
    assert "FIVE_DOLLAR_FOOTBALL_API_KEY" not in source
