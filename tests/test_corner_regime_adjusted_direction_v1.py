import json
import zipfile

import pandas as pd

import corner_regime_adjusted_direction_v1 as m


def _fresh_row(fid, league, date, opening_lambda, delta):
    return {
        "fixture_id": str(fid),
        "league": league,
        "kickoff_utc": f"{date}T15:00:00Z",
        "opening_lambda": float(opening_lambda),
        "closing_lambda": float(opening_lambda + delta),
        "centre_delta": float(delta),
        "movement_magnitude": float(abs(delta)),
    }


def test_frozen_contract_constants():
    assert m.EXPERIMENT_ID == "CORNER_REGIME_ADJUSTED_DIRECTION_V1"
    assert m.FIXTURES_PER_LEAGUE == 10
    assert m.MIN_TOTAL_ROWS == 30
    assert m.MIN_LEAGUES_WITH_PAIRS == 4
    assert m.MIN_REGIME_BLOCKS == 8
    assert m.MIN_COMPARABLE_PAIRS == 40
    assert m.MIN_CONCORDANCE == 0.60
    assert m.PERMUTATIONS == 20_000
    assert m.PERMUTATION_SEED == 20_260_918
    assert m.MAX_PVALUE == 0.10


def test_prior_artifact_reader_uses_selected_fixture_metadata_only(tmp_path):
    payload = {}
    for league_num, league in enumerate(m.replication.LEAGUES):
        payload[league] = [
            {"fixture_id": str(league_num * 100 + idx), "league": league}
            for idx in range(10)
        ]
    path = tmp_path / "prior.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "artifacts/corner_repricing_direction_replication_v1/selected_fixtures.json",
            json.dumps(payload),
        )
        zf.writestr(
            "artifacts/corner_repricing_direction_replication_v1/evaluation_rows.csv",
            "fixture_id,centre_delta\nsecret,999\n",
        )

    fixture_ids = m.load_previous_selected_fixture_ids(path)
    assert len(fixture_ids) == 50
    assert "secret" not in fixture_ids


def test_pairwise_concordance_ignores_common_league_day_shift():
    rows = []
    for league_num, league in enumerate(m.replication.LEAGUES):
        for day_num, date in enumerate(["2026-09-05", "2026-09-12"]):
            common_shift = 3.0 if day_num == 0 else -2.0
            for idx, opening in enumerate([8.0, 9.0, 10.0, 11.0]):
                # Lower FAIR_CENTRE always has the stronger relative upward move.
                individual = 0.40 - 0.10 * idx
                rows.append(
                    _fresh_row(
                        f"{league_num}-{day_num}-{idx}",
                        league,
                        date,
                        opening,
                        common_shift + individual,
                    )
                )

    detail, report = m.evaluate_fresh_direction(pd.DataFrame(rows))
    assert len(detail) == 40
    assert report["sample_gate_pass"] is True
    assert report["contributing_regime_blocks"] == 10
    assert report["comparable_pairs"] == 60
    assert report["observed_concordance"] == 1.0
    assert report["permutation_pvalue"] < m.MAX_PVALUE
    assert report["direction_discrimination_confirmed"] is True
    assert report["verdict"] == "INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED"

    # The first day is massively upward and the second massively downward,
    # yet both are removed by within-block ordering.
    medians = detail.groupby("regime_block")["regime_median_delta"].first()
    assert medians.max() > 3.0
    assert medians.min() < -1.5


def test_pairwise_ties_are_not_counted():
    scores = pd.Series([-8.0, -8.0, -9.0]).to_numpy()
    deltas = pd.Series([0.3, 0.2, 0.2]).to_numpy()
    concordant, comparable = m._pair_counts(scores, deltas)
    assert comparable == 1
    assert concordant == 1


def test_sample_gate_fails_closed_with_too_few_regime_blocks():
    rows = []
    for league_num, league in enumerate(m.replication.LEAGUES):
        for idx in range(8):
            rows.append(
                _fresh_row(
                    f"{league_num}-{idx}",
                    league,
                    "2026-09-12",
                    8.0 + idx * 0.2,
                    0.4 - idx * 0.03,
                )
            )

    _, report = m.evaluate_fresh_direction(pd.DataFrame(rows))
    assert report["fresh_eligible_rows"] == 40
    assert report["contributing_regime_blocks"] == 5
    assert report["sample_gate_pass"] is False
    assert report["permutation_pvalue"] is None
    assert report["verdict"] == "SAMPLE_TOO_SMALL"
