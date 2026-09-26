import inspect
import json
import zipfile

import pytest

import corner_repricing_direction_replication_v1 as replication
import corner_regime_adjusted_direction_v2b as v2b
import corner_regime_adjusted_direction_v2b_evaluator as evaluator
import corner_regime_adjusted_direction_v2b_lock as lock
import corner_regime_adjusted_direction_v2b_odds_plan as odds_plan


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


def _lock_and_plan(monkeypatch):
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

    monkeypatch.setattr(
        odds_plan,
        "EXPECTED_SELECTION_SHA256",
        manifest["selection_sha256"],
    )
    monkeypatch.setattr(
        odds_plan,
        "EXPECTED_FIXTURE_METADATA_SHA256",
        manifest["fixture_metadata_sha256"],
    )

    plan = odds_plan.build_acquisition_plan(
        manifest,
        source_lock_workflow_run_id=evaluator.EXPECTED_LOCK_RUN_ID,
        source_lock_artifact_id=evaluator.EXPECTED_LOCK_ARTIFACT_ID,
        source_lock_artifact_digest=evaluator.EXPECTED_LOCK_ARTIFACT_DIGEST,
    )
    return manifest, plan


def _raw_zip(tmp_path, fixture_ids):
    path = tmp_path / "raw.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for fixture_id in fixture_ids:
            zf.writestr(
                f"artifact/raw/odds/{fixture_id}.json",
                json.dumps({"success": 1, "data": [{"fixture_id": fixture_id}]}),
            )
    return path


def _set_expected_raw_digest(monkeypatch, raw_zip):
    digest = evaluator.frozen._file_sha256(raw_zip)
    monkeypatch.setattr(evaluator, "EXPECTED_RAW_ARTIFACT_DIGEST", digest)
    return digest


def test_real_v2b_evaluator_provenance_constants_are_exact():
    assert evaluator.EXPECTED_LOCK_RUN_ID == "36219786013"
    assert evaluator.EXPECTED_LOCK_ARTIFACT_ID == "10899325930"
    assert evaluator.EXPECTED_PLAN_RUN_ID == "36220204953"
    assert evaluator.EXPECTED_PLAN_ARTIFACT_ID == "10899305926"
    assert evaluator.EXPECTED_RAW_RUN_ID == "36222282829"
    assert evaluator.EXPECTED_RAW_ARTIFACT_ID == "10899611444"
    assert evaluator.EXPECTED_RAW_ARTIFACT_DIGEST == (
        "sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57"
    )


def test_v2b_statistical_gate_remains_unchanged():
    assert v2b.MIN_TOTAL_ROWS == 30
    assert v2b.MIN_LEAGUES_WITH_PAIRS == 4
    assert v2b.MIN_REGIME_BLOCKS == 8
    assert v2b.MIN_COMPARABLE_PAIRS == 40
    assert v2b.MIN_CONCORDANCE == 0.60
    assert v2b.PERMUTATIONS == 20_000
    assert v2b.PERMUTATION_SEED == 20_260_918
    assert v2b.MAX_PVALUE == 0.10


def test_incomplete_raw_artifact_stops_before_normalization_and_statistics(
    monkeypatch, tmp_path
):
    manifest, plan = _lock_and_plan(monkeypatch)
    selected = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected[:-1])
    digest = _set_expected_raw_digest(monkeypatch, raw_zip)

    def forbidden(*args, **kwargs):
        raise AssertionError("normalization/statistics must not run")

    monkeypatch.setattr(evaluator.replication, "normalize_corner_odds", forbidden)
    monkeypatch.setattr(evaluator.direction_v1, "evaluate_fresh_direction", forbidden)

    rows, report = evaluator.evaluate(
        manifest,
        plan,
        raw_zip,
        raw_workflow_run_id=evaluator.EXPECTED_RAW_RUN_ID,
        raw_artifact_id=evaluator.EXPECTED_RAW_ARTIFACT_ID,
        raw_artifact_digest=digest,
    )

    assert rows.empty
    assert report["status"] == "ACQUISITION_INCOMPLETE"
    assert report["acquisition_complete"] is False
    assert report["statistical_evaluation_performed"] is False
    assert report["verdict"] is None
    assert report["captured_locked_raw_responses"] == 42
    assert report["missing_locked_fixture_ids"] == [selected[-1]]


def test_complete_raw_artifact_runs_existing_frozen_orchestration(
    monkeypatch, tmp_path
):
    manifest, plan = _lock_and_plan(monkeypatch)
    selected = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected)
    digest = _set_expected_raw_digest(monkeypatch, raw_zip)
    calls = {"normalize": 0, "direction": 0}

    def fake_normalize(payload, fixture):
        calls["normalize"] += 1
        return {
            "fixture_id": fixture["fixture_id"],
            "league": fixture["league"],
            "kickoff_utc": fixture["kickoff_utc"],
        }

    def fake_holdout(row):
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
        assert len(frame) == 43
        return frame.copy(), {
            "verdict": "SAMPLE_TOO_SMALL",
            "direction_discrimination_confirmed": False,
            "eligible_rows": 43,
        }

    monkeypatch.setattr(evaluator.replication, "normalize_corner_odds", fake_normalize)
    monkeypatch.setattr(evaluator.replication, "_normalize_holdout_row", fake_holdout)
    monkeypatch.setattr(
        evaluator.direction_v1,
        "evaluate_fresh_direction",
        fake_direction,
    )

    rows, report = evaluator.evaluate(
        manifest,
        plan,
        raw_zip,
        raw_workflow_run_id=evaluator.EXPECTED_RAW_RUN_ID,
        raw_artifact_id=evaluator.EXPECTED_RAW_ARTIFACT_ID,
        raw_artifact_digest=digest,
    )

    assert calls == {"normalize": 43, "direction": 1}
    assert len(rows) == 43
    assert report["status"] == "EVALUATED"
    assert report["acquisition_complete"] is True
    assert report["statistical_evaluation_performed"] is True
    assert report["eligible_normalized_rows"] == 43
    assert report["ineligible_selected_fixture_ids"] == []
    assert report["verdict"] == "SAMPLE_TOO_SMALL"


def test_structurally_ineligible_fixture_is_not_replaced(monkeypatch, tmp_path):
    manifest, plan = _lock_and_plan(monkeypatch)
    selected = manifest["selected_fixture_ids"]
    raw_zip = _raw_zip(tmp_path, selected)
    digest = _set_expected_raw_digest(monkeypatch, raw_zip)
    ineligible = selected[0]

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
        raw_workflow_run_id=evaluator.EXPECTED_RAW_RUN_ID,
        raw_artifact_id=evaluator.EXPECTED_RAW_ARTIFACT_ID,
        raw_artifact_digest=digest,
    )

    assert len(rows) == 42
    assert report["locked_fixture_count"] == 43
    assert report["ineligible_selected_fixture_ids"] == [ineligible]


def test_wrong_raw_provenance_fails_closed(monkeypatch, tmp_path):
    manifest, plan = _lock_and_plan(monkeypatch)
    raw_zip = _raw_zip(tmp_path, manifest["selected_fixture_ids"])
    digest = _set_expected_raw_digest(monkeypatch, raw_zip)

    with pytest.raises(RuntimeError, match="workflow run ID"):
        evaluator.evaluate(
            manifest,
            plan,
            raw_zip,
            raw_workflow_run_id="wrong",
            raw_artifact_id=evaluator.EXPECTED_RAW_ARTIFACT_ID,
            raw_artifact_digest=digest,
        )

    with pytest.raises(RuntimeError, match="artifact ID"):
        evaluator.evaluate(
            manifest,
            plan,
            raw_zip,
            raw_workflow_run_id=evaluator.EXPECTED_RAW_RUN_ID,
            raw_artifact_id="wrong",
            raw_artifact_digest=digest,
        )


def test_evaluator_adapter_has_no_network_or_provider_transport():
    source = inspect.getsource(evaluator)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert "FIVE_DOLLAR_FOOTBALL_API_KEY" not in source
    assert "/v1/fixtures/" not in source
