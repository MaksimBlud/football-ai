import inspect

import pytest

import corner_regime_adjusted_direction_v2b as v2b
import corner_regime_adjusted_direction_v2b_lock as lock
import corner_regime_adjusted_direction_v2b_odds_plan as plan
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


def _manifest():
    blocks = []
    rows = []
    next_id = 500000
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

    # The synthetic IDs create different hashes; substitute the expected real
    # immutable identities only after recomputing them from this synthetic lock
    # would be incorrect. Instead, the validator's fixed real hashes are tested
    # separately and build_acquisition_plan is exercised with a patched copy.
    return manifest


def _real_hash_compatible_manifest(monkeypatch):
    manifest = _manifest()
    monkeypatch.setattr(
        plan,
        "EXPECTED_SELECTION_SHA256",
        manifest["selection_sha256"],
    )
    monkeypatch.setattr(
        plan,
        "EXPECTED_FIXTURE_METADATA_SHA256",
        manifest["fixture_metadata_sha256"],
    )
    return manifest


def test_real_frozen_constants_are_exact():
    assert plan.EXPECTED_SELECTED_FIXTURES == 43
    assert plan.EXPECTED_SELECTED_BLOCKS == 10
    assert plan.EXPECTED_METADATA_POTENTIAL_PAIRS == 74
    assert plan.MAX_ODDS_REQUESTS_PER_BATCH == 30
    assert plan.EXPECTED_SELECTION_SHA256 == (
        "sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73"
    )
    assert plan.EXPECTED_FIXTURE_METADATA_SHA256 == (
        "sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb"
    )


def test_valid_lock_builds_exact_30_plus_13_plan(monkeypatch):
    manifest = _real_hash_compatible_manifest(monkeypatch)
    result = plan.build_acquisition_plan(
        manifest,
        source_lock_workflow_run_id="36219786013",
        source_lock_artifact_id="10899325930",
        source_lock_artifact_digest="a" * 64,
    )

    assert result["selected_fixture_count"] == 43
    assert result["total_planned_odds_requests"] == 43
    assert result["batch_count"] == 2
    assert [b["planned_requests"] for b in result["batches"]] == [30, 13]
    assert result["selected_fixture_ids"] == manifest["selected_fixture_ids"]
    assert result["selected_fixture_metadata"] == manifest["selected_fixture_metadata"]
    assert result["live_odds_acquisition_authorized"] is False
    assert result["requires_explicit_live_authorization"] is True
    assert result["fixture_reselection_allowed"] is False
    assert result["resume_rule"] == "REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT"


def test_tampered_lock_fails_closed(monkeypatch):
    manifest = _real_hash_compatible_manifest(monkeypatch)
    manifest["selected_fixture_ids"] = list(reversed(manifest["selected_fixture_ids"]))
    with pytest.raises(RuntimeError):
        plan.validate_lock_manifest(manifest)


def test_pre_authorized_odds_fails_closed(monkeypatch):
    manifest = _real_hash_compatible_manifest(monkeypatch)
    manifest["odds_acquisition_authorized"] = True
    with pytest.raises(RuntimeError, match="odds_acquisition_authorized"):
        plan.validate_lock_manifest(manifest)


def test_plan_module_has_no_network_transport():
    source = inspect.getsource(plan)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert "5dollarfootball" not in source.lower()
