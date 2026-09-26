import inspect
import json
import zipfile
from pathlib import Path

import pytest

import corner_regime_adjusted_direction_v2b as v2b
import corner_regime_adjusted_direction_v2b_acquisition as acquisition
import corner_regime_adjusted_direction_v2b_lock as lock
import corner_regime_adjusted_direction_v2b_odds_plan as odds_plan
import corner_repricing_direction_replication_v1 as replication


BLOCK_SIZES = [
    ("EPL", "2026-09-19", 5),
    ("LA_LIGA", "2026-09-19", 4),
    ("SERIE_A", "2026-09-19", 4),
    ("BUNDESLIGA", "2026-09-19", 5),
    ("LIGUE_1", "2026-09-19", 5),
    ("EPL", "2026-09-20", 4),
    ("LA_LIGA", "2026-09-20", 5),
    ("SERIE_A", "2026-09-20", 5),
    ("BUNDESLIGA", "2026-09-20", 3),
    ("LIGUE_1", "2026-09-20", 3),
]


def _manifest_and_plan(monkeypatch):
    blocks = []
    rows = []
    next_id = 700000

    for league, date, size in BLOCK_SIZES:
        ids = []
        for idx in range(size):
            fixture_id = str(next_id)
            next_id += 1
            ids.append(fixture_id)
            rows.append(
                {
                    "fixture_id": fixture_id,
                    "league": league,
                    "league_id": str(replication.LEAGUES[league]),
                    "kickoff_utc": f"{date}T{12+idx:02d}:00:00+00:00",
                    "home_team": f"H_{fixture_id}",
                    "away_team": f"A_{fixture_id}",
                    "status": "finished",
                }
            )
        blocks.append(
            {
                "regime_block": f"{league}|{date}",
                "league": league,
                "kickoff_date_utc": date,
                "fixture_count": size,
                "potential_pairs": size * (size - 1) // 2,
                "fixture_ids": ids,
            }
        )

    source = {
        "experiment_id": v2b.SOURCE_EXPERIMENT_ID,
        "metadata_live_experiment_id": v2b.SOURCE_METADATA_EXPERIMENT_ID,
        "research_only": True,
        "metadata_only": True,
        "odds_endpoint_used": False,
        "market_prices_opened": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "paid_subscription_used": False,
        "future_cutoff_utc": v2b.FUTURE_CUTOFF_UTC,
        "total_prior_excluded_fixture_ids": 151,
        "status": "WAIT_FOR_COHORT",
        "candidate_blocks": blocks,
        "statistical_gate_unchanged_from_v1": {
            "minimum_total_rows": v2b.MIN_TOTAL_ROWS,
            "minimum_leagues_with_pairs": v2b.MIN_LEAGUES_WITH_PAIRS,
            "minimum_regime_blocks": v2b.MIN_REGIME_BLOCKS,
            "minimum_comparable_pairs": v2b.MIN_COMPARABLE_PAIRS,
            "minimum_concordance": v2b.MIN_CONCORDANCE,
            "permutations": v2b.PERMUTATIONS,
            "permutation_seed": v2b.PERMUTATION_SEED,
            "maximum_pvalue": v2b.MAX_PVALUE,
        },
    }

    v2b_plan = v2b.build_v2b_plan(source)
    manifest = lock.build_lock_manifest(
        v2b_plan,
        rows,
        source_metadata_workflow_run_id="36218898253",
        source_metadata_artifact_id="10898297066",
        source_metadata_artifact_digest="e" * 64,
    )

    # Synthetic fixtures necessarily have different hashes than the real lock.
    # Patch only the immutable expected identity constants for unit-test data.
    monkeypatch.setattr(
        odds_plan, "EXPECTED_SELECTION_SHA256", manifest["selection_sha256"]
    )
    monkeypatch.setattr(
        odds_plan,
        "EXPECTED_FIXTURE_METADATA_SHA256",
        manifest["fixture_metadata_sha256"],
    )

    plan = odds_plan.build_acquisition_plan(
        manifest,
        source_lock_workflow_run_id=acquisition.EXPECTED_LOCK_RUN_ID,
        source_lock_artifact_id=acquisition.EXPECTED_LOCK_ARTIFACT_ID,
        source_lock_artifact_digest=acquisition.EXPECTED_LOCK_ARTIFACT_DIGEST,
    )
    return manifest, plan


class FakeProviderClient:
    calls = []

    def __init__(self, key):
        self.key = key
        self.request_count = 0

    def get(self, path, *, params):
        self.request_count += 1
        self.__class__.calls.append((path, dict(params)))
        fixture_id = path.split("/")[-2]
        return {
            "success": 1,
            "data": [{"fixture_id": fixture_id, "synthetic": True}],
        }


def _zip_output(output_dir: Path, zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in output_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(output_dir.parent))
    return zip_path


def test_batch1_fetches_exact_first_30_and_remains_partial(monkeypatch, tmp_path):
    manifest, plan = _manifest_and_plan(monkeypatch)
    FakeProviderClient.calls = []
    monkeypatch.setattr(acquisition.replication, "ProviderClient", FakeProviderClient)

    output_dir = tmp_path / "batch1"
    report = acquisition.acquire_batch(
        manifest,
        plan,
        batch_index=1,
        output_dir=output_dir,
        key="test-key",
    )

    expected_ids = plan["batches"][0]["fixture_ids"]
    assert len(expected_ids) == 30
    assert report["status"] == "ACQUISITION_PARTIAL"
    assert report["acquisition_complete"] is False
    assert report["captured_locked_raw_responses"] == 30
    assert report["missing_locked_fixture_count"] == 13
    assert report["missing_locked_fixture_ids"] == plan["batches"][1]["fixture_ids"]
    assert report["provider_http_requests_this_run"] == 30
    assert report["statistical_evaluation_performed"] is False
    assert report["normalization_performed"] is False
    assert report["fixture_discovery_performed"] is False

    called_ids = [path.split("/")[-2] for path, _ in FakeProviderClient.calls]
    assert called_ids == expected_ids
    assert all(params == {"market": "corner"} for _, params in FakeProviderClient.calls)
    assert all(
        (output_dir / "raw" / "odds" / f"{fixture_id}.json").exists()
        for fixture_id in expected_ids
    )


def test_batch2_reuses_30_and_fetches_only_remaining_13(monkeypatch, tmp_path):
    manifest, plan = _manifest_and_plan(monkeypatch)
    monkeypatch.setattr(acquisition.replication, "ProviderClient", FakeProviderClient)

    FakeProviderClient.calls = []
    batch1_dir = tmp_path / "batch1"
    first = acquisition.acquire_batch(
        manifest,
        plan,
        batch_index=1,
        output_dir=batch1_dir,
        key="test-key",
    )
    assert first["captured_locked_raw_responses"] == 30

    resume_zip = _zip_output(batch1_dir, tmp_path / "batch1.zip")
    FakeProviderClient.calls = []
    batch2_dir = tmp_path / "batch2"
    second = acquisition.acquire_batch(
        manifest,
        plan,
        batch_index=2,
        output_dir=batch2_dir,
        key="test-key",
        resume_zip=resume_zip,
    )

    expected_second_ids = plan["batches"][1]["fixture_ids"]
    called_ids = [path.split("/")[-2] for path, _ in FakeProviderClient.calls]
    assert called_ids == expected_second_ids
    assert len(called_ids) == 13
    assert second["status"] == "ACQUISITION_COMPLETE"
    assert second["acquisition_complete"] is True
    assert second["captured_locked_raw_responses"] == 43
    assert second["missing_locked_fixture_count"] == 0
    assert second["missing_locked_fixture_ids"] == []
    assert second["provider_http_requests_this_run"] == 13
    assert second["statistical_evaluation_performed"] is False
    assert second["normalization_performed"] is False

    assert len(list((batch2_dir / "raw" / "odds").glob("*.json"))) == 43


def test_batch2_requires_resume(monkeypatch, tmp_path):
    manifest, plan = _manifest_and_plan(monkeypatch)
    with pytest.raises(RuntimeError, match="batch 2 requires a resume artifact"):
        acquisition.acquire_batch(
            manifest,
            plan,
            batch_index=2,
            output_dir=tmp_path / "batch2",
            key="test-key",
        )


def test_resume_rejects_nonlocked_fixture(monkeypatch, tmp_path):
    manifest, plan = _manifest_and_plan(monkeypatch)
    path = tmp_path / "bad-resume.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "batch/raw/odds/999999999.json",
            json.dumps({"success": 1, "data": []}),
        )

    with pytest.raises(RuntimeError, match="non-locked fixture"):
        acquisition.acquire_batch(
            manifest,
            plan,
            batch_index=2,
            output_dir=tmp_path / "batch2",
            key="test-key",
            resume_zip=path,
        )


def test_resume_rejects_duplicate_locked_fixture(monkeypatch, tmp_path):
    manifest, plan = _manifest_and_plan(monkeypatch)
    fixture_id = plan["batches"][0]["fixture_ids"][0]
    path = tmp_path / "duplicate-resume.zip"
    with zipfile.ZipFile(path, "w") as zf:
        payload = json.dumps({"success": 1, "data": []})
        zf.writestr(f"a/raw/odds/{fixture_id}.json", payload)
        zf.writestr(f"b/raw/odds/{fixture_id}.json", payload)

    with pytest.raises(RuntimeError, match="duplicate resume raw response"):
        acquisition.acquire_batch(
            manifest,
            plan,
            batch_index=2,
            output_dir=tmp_path / "batch2",
            key="test-key",
            resume_zip=path,
        )


def test_tampered_plan_fails_before_provider(monkeypatch, tmp_path):
    manifest, plan = _manifest_and_plan(monkeypatch)
    bad = dict(plan)
    bad["selected_fixture_ids"] = list(reversed(plan["selected_fixture_ids"]))

    class ForbiddenProviderClient:
        def __init__(self, key):
            raise AssertionError("provider must not initialize for invalid plan")

    monkeypatch.setattr(
        acquisition.replication, "ProviderClient", ForbiddenProviderClient
    )
    with pytest.raises(RuntimeError):
        acquisition.acquire_batch(
            manifest,
            bad,
            batch_index=1,
            output_dir=tmp_path / "bad",
            key="test-key",
        )


def test_acquisition_source_has_no_fixture_discovery_or_evaluation():
    source = inspect.getsource(acquisition)
    assert "/v1/leagues/" not in source
    assert "normalize_corner_odds" not in source
    assert "evaluate_fresh_direction" not in source
    assert "evaluate_fresh(" not in source
    assert "params={\"market\": \"corner\"}" in source
