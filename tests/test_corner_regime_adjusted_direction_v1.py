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
    assert m.MAX_FIXTURE_PAGES == 2
    assert len(m.replication.LEAGUES) * (m.MAX_FIXTURE_PAGES + m.FIXTURES_PER_LEAGUE) == m.replication.MAX_PROVIDER_REQUESTS
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



def test_third_sample_paginates_fixture_metadata_before_any_odds(monkeypatch, tmp_path):
    reverse_leagues = {value: key for key, value in m.replication.LEAGUES.items()}
    excluded = set()

    def fixture(fid, kickoff):
        return {
            "id": fid,
            "status": "finished",
            "kickoff_utc": kickoff,
            "teams": {
                "home": {"name": f"H{fid}"},
                "away": {"name": f"A{fid}"},
            },
        }

    page_payloads = {}
    for league_num, (league, league_id) in enumerate(m.replication.LEAGUES.items()):
        page1 = []
        for idx in range(50):
            fid = f"{league_num + 1}{idx:04d}"
            page1.append(fixture(fid, f"2026-09-{28 - (idx % 20):02d}T12:00:00Z"))
            if idx < 44:
                excluded.add(fid)
        page2 = [
            fixture(
                f"{league_num + 1}9{idx:03d}",
                f"2026-08-{28 - idx:02d}T12:00:00Z",
            )
            for idx in range(10)
        ]
        page_payloads[(league_id, 1)] = {"success": 1, "data": page1}
        page_payloads[(league_id, 2)] = {"success": 1, "data": page2}

    class FakeClient:
        last = None

        def __init__(self, key):
            self.key = key
            self.request_count = 0
            self.calls = []
            FakeClient.last = self

        def get(self, path, *, params):
            self.request_count += 1
            self.calls.append((path, dict(params)))
            if "/leagues/" in path:
                league_id = path.split("/")[3]
                return page_payloads[(league_id, int(params["page"]))]
            return {"success": 1, "data": []}

    monkeypatch.setattr(m.replication, "ProviderClient", FakeClient)
    monkeypatch.setattr(
        m.replication,
        "normalize_corner_odds",
        lambda payload, selected_fixture: selected_fixture,
    )
    monkeypatch.setattr(
        m.replication,
        "_normalize_holdout_row",
        lambda row: {
            "fixture_id": row["fixture_id"],
            "league": row["league"],
            "kickoff_utc": row["kickoff_utc"],
            "opening_lambda": 9.0,
            "closing_lambda": 9.1,
            "centre_delta": 0.1,
            "movement_magnitude": 0.1,
        },
    )

    fresh, request_count, selected = m.acquire_third_holdout(
        tmp_path,
        key="test",
        excluded_ids=excluded,
    )

    assert len(fresh) == 50
    assert sum(len(rows) for rows in selected.values()) == 50
    assert request_count == m.replication.MAX_PROVIDER_REQUESTS
    calls = FakeClient.last.calls
    assert all("/leagues/" in path for path, _ in calls[:10])
    assert all("/fixtures/" in path and "/odds" in path for path, _ in calls[10:])

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
