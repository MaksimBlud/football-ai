import hashlib
import json

import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2b as v2b
import corner_regime_adjusted_direction_v2b_lock as v2b_lock


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


def _source_plan_and_metadata():
    candidate_blocks = []
    fixture_rows = []
    next_id = 100000

    league_ids = {
        "EPL": "4160026622",
        "LA_LIGA": "4212821298",
        "SERIE_A": "3405541143",
        "BUNDESLIGA": "686337048",
        "LIGUE_1": "3614399544",
    }

    for league, date, size in BLOCK_SIZES:
        ids = []
        for idx in range(size):
            fixture_id = str(next_id)
            next_id += 1
            ids.append(fixture_id)
            fixture_rows.append(
                {
                    "fixture_id": fixture_id,
                    "league": league,
                    "league_id": league_ids[league],
                    "kickoff_utc": f"{date}T{12+idx:02d}:00:00+00:00",
                    "home_team": f"{league}_H_{fixture_id}",
                    "away_team": f"{league}_A_{fixture_id}",
                    "status": "finished",
                }
            )
        candidate_blocks.append(
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
        "experiment_id": v2.EXPERIMENT_ID,
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
        "candidate_blocks": candidate_blocks,
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
    return source, fixture_rows


def test_v2b_gate_is_exactly_10_blocks_and_74_pairs():
    assert v2b.EXPERIMENT_ID == "CORNER_REGIME_ADJUSTED_DIRECTION_V2B"
    assert v2b.MIN_BLOCKS_PER_LEAGUE == 2
    assert v2b.MIN_TOTAL_BLOCKS == 10
    assert v2b.MIN_METADATA_POTENTIAL_PAIRS == 74

    assert v2.MIN_TOTAL_BLOCKS == 12
    assert v2.MIN_METADATA_POTENTIAL_PAIRS == 80


def test_v2b_keeps_statistical_direction_gate_unchanged():
    assert v2b.MIN_TOTAL_ROWS == v2.MIN_TOTAL_ROWS == 30
    assert v2b.MIN_LEAGUES_WITH_PAIRS == v2.MIN_LEAGUES_WITH_PAIRS == 4
    assert v2b.MIN_REGIME_BLOCKS == v2.MIN_REGIME_BLOCKS == 8
    assert v2b.MIN_COMPARABLE_PAIRS == v2.MIN_COMPARABLE_PAIRS == 40
    assert v2b.MIN_CONCORDANCE == v2.MIN_CONCORDANCE == 0.60
    assert v2b.PERMUTATIONS == v2.PERMUTATIONS == 20_000
    assert v2b.PERMUTATION_SEED == v2.PERMUTATION_SEED == 20_260_918
    assert v2b.MAX_PVALUE == v2.MAX_PVALUE == 0.10


def test_current_10_block_shape_locks_43_fixtures_and_74_pairs():
    source, _ = _source_plan_and_metadata()
    plan = v2b.build_v2b_plan(source)

    assert plan["status"] == "COHORT_LOCKED"
    assert plan["locked"] is True
    assert plan["selected_block_count"] == 10
    assert plan["selected_fixture_count"] == 43
    assert plan["metadata_potential_pairs"] == 74
    assert plan["blocks_by_league"] == {
        "EPL": 2,
        "LA_LIGA": 2,
        "SERIE_A": 2,
        "BUNDESLIGA": 2,
        "LIGUE_1": 2,
    }


def test_v2b_uses_deterministic_earliest_prefix():
    source, _ = _source_plan_and_metadata()
    source["candidate_blocks"] = source["candidate_blocks"] + [
        {
            "regime_block": "EPL|2026-09-27",
            "league": "EPL",
            "kickoff_date_utc": "2026-09-27",
            "fixture_count": 8,
            "potential_pairs": 28,
            "fixture_ids": [str(900000 + i) for i in range(8)],
        }
    ]
    plan = v2b.build_v2b_plan(source)

    assert plan["selected_block_count"] == 10
    assert plan["metadata_potential_pairs"] == 74
    assert all(
        block["kickoff_date_utc"] in {"2026-09-19", "2026-09-20"}
        for block in plan["selected_blocks"]
    )


def test_v2b_lock_binds_exact_43_fixture_metadata_rows():
    source, fixture_rows = _source_plan_and_metadata()
    plan = v2b.build_v2b_plan(source)
    manifest = v2b_lock.build_lock_manifest(
        plan,
        fixture_rows,
        source_metadata_workflow_run_id="36218898253",
        source_metadata_artifact_id="10898297066",
        source_metadata_artifact_digest="e" * 64,
    )

    assert manifest["lock_status"] == "IMMUTABLE_COHORT_LOCKED"
    assert manifest["selected_block_count"] == 10
    assert manifest["selected_fixture_count"] == 43
    assert manifest["metadata_potential_pairs"] == 74
    assert len(manifest["selected_fixture_metadata"]) == 43
    assert [r["fixture_id"] for r in manifest["selected_fixture_metadata"]] == manifest[
        "selected_fixture_ids"
    ]
    assert manifest["odds_acquisition_authorized"] is False
    assert manifest["selection_sha256"].startswith("sha256:")
    assert manifest["fixture_metadata_sha256"].startswith("sha256:")


def test_v2b_lock_hash_is_stable():
    source, fixture_rows = _source_plan_and_metadata()
    plan = v2b.build_v2b_plan(source)

    first = v2b_lock.build_lock_manifest(
        plan,
        fixture_rows,
        source_metadata_workflow_run_id="1",
        source_metadata_artifact_id="2",
        source_metadata_artifact_digest="a" * 64,
    )
    second = v2b_lock.build_lock_manifest(
        dict(reversed(list(plan.items()))),
        list(fixture_rows),
        source_metadata_workflow_run_id="1",
        source_metadata_artifact_id="2",
        source_metadata_artifact_digest="a" * 64,
    )

    assert first["selection_sha256"] == second["selection_sha256"]
    assert first["fixture_metadata_sha256"] == second["fixture_metadata_sha256"]
