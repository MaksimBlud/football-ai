import inspect

import corner_regime_adjusted_direction_v1 as v1
import corner_regime_adjusted_direction_v2 as v2


def _fixture(fid, league, date, *, status="finished"):
    return {
        "fixture_id": str(fid),
        "league": league,
        "kickoff_utc": f"{date}T15:00:00Z",
        "status": status,
    }


def _dense_rows(dates=("2026-09-20", "2026-09-27", "2026-10-04")):
    rows = []
    fid = 1000
    for date in dates:
        for league in v2.LEAGUE_ORDER:
            for _ in range(5):
                rows.append(_fixture(fid, league, date))
                fid += 1
    return rows


def test_v2_preserves_v1_statistical_gate_exactly():
    assert v2.EXPERIMENT_ID == "CORNER_REGIME_ADJUSTED_DIRECTION_V2"
    assert v2.FUTURE_CUTOFF_UTC == "2026-09-19T00:00:00Z"
    assert v2.MIN_TOTAL_ROWS == v1.MIN_TOTAL_ROWS == 30
    assert v2.MIN_LEAGUES_WITH_PAIRS == v1.MIN_LEAGUES_WITH_PAIRS == 4
    assert v2.MIN_REGIME_BLOCKS == v1.MIN_REGIME_BLOCKS == 8
    assert v2.MIN_COMPARABLE_PAIRS == v1.MIN_COMPARABLE_PAIRS == 40
    assert v2.MIN_CONCORDANCE == v1.MIN_CONCORDANCE == 0.60
    assert v2.PERMUTATIONS == v1.PERMUTATIONS == 20_000
    assert v2.PERMUTATION_SEED == v1.PERMUTATION_SEED == 20_260_918
    assert v2.MAX_PVALUE == v1.MAX_PVALUE == 0.10


def test_metadata_planner_locks_earliest_dense_prefix_without_odds():
    report = v2.plan_future_cohort(_dense_rows(), excluded_ids=set())

    assert report["status"] == "COHORT_LOCKED"
    assert report["locked"] is True
    assert report["metadata_only"] is True
    assert report["odds_endpoint_used"] is False
    assert report["match_outcome_used"] is False
    assert report["football_state_used"] is False
    assert report["selected_block_count"] == 12
    assert report["selected_fixture_count"] == 60
    assert report["metadata_potential_pairs"] == 120
    assert all(report["blocks_by_league"][league] >= 2 for league in v2.LEAGUE_ORDER)

    # Whole blocks only: each included dense block keeps all five fixtures.
    assert all(block["fixture_count"] == 5 for block in report["selected_blocks"])
    assert all(block["potential_pairs"] == 10 for block in report["selected_blocks"])


def test_planner_is_future_only_excludes_prior_ids_and_singletons():
    rows = _dense_rows()
    excluded_id = rows[0]["fixture_id"]
    rows.extend(
        [
            _fixture("old", "EPL", "2026-09-18"),
            _fixture("future-singleton", "EPL", "2026-10-11"),
            _fixture("not-finished", "EPL", "2026-10-12", status="scheduled"),
            _fixture("other-league", "OTHER", "2026-10-12"),
        ]
    )

    report = v2.plan_future_cohort(rows, excluded_ids={excluded_id})
    candidate_ids = {
        fixture_id
        for block in report["candidate_blocks"]
        for fixture_id in block["fixture_ids"]
    }

    assert excluded_id not in candidate_ids
    assert "old" not in candidate_ids
    assert "future-singleton" not in candidate_ids
    assert "not-finished" not in candidate_ids
    assert "other-league" not in candidate_ids


def test_wait_for_cohort_fail_closed_without_dense_future_blocks():
    rows = []
    fid = 1
    for league in v2.LEAGUE_ORDER:
        for date in ("2026-09-20", "2026-09-27"):
            rows.extend(
                [
                    _fixture(fid, league, date),
                    _fixture(fid + 1, league, date),
                ]
            )
            fid += 2

    report = v2.plan_future_cohort(rows, excluded_ids=set())
    assert report["status"] == "WAIT_FOR_COHORT"
    assert report["locked"] is False
    assert report["selected_blocks"] == []
    assert report["selected_fixture_ids"] == []
    assert report["metadata_potential_pairs"] == 10


def test_locked_prefix_is_stable_when_later_metadata_arrives():
    base = _dense_rows()
    first = v2.plan_future_cohort(base, excluded_ids=set())
    assert first["locked"]

    later = list(base)
    fid = 9000
    for date in ("2026-10-11", "2026-10-18"):
        for league in v2.LEAGUE_ORDER:
            for _ in range(7):
                later.append(_fixture(fid, league, date))
                fid += 1

    second = v2.plan_future_cohort(later, excluded_ids=set())
    assert second["locked"]
    assert second["selected_fixture_ids"] == first["selected_fixture_ids"]
    assert second["selected_blocks"] == first["selected_blocks"]


def test_v2_module_has_no_live_odds_transport():
    source = inspect.getsource(v2)
    assert "import requests" not in source
    assert "requests.get" not in source
    assert "ProviderClient" not in source
    assert "/odds" not in source
