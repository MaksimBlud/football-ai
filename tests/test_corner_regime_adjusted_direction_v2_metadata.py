import inspect
import json
import zipfile

import pandas as pd

import corner_regime_adjusted_direction_v2_metadata as m


def _selected_payload():
    counts = {
        "EPL": 10,
        "LA_LIGA": 10,
        "SERIE_A": 10,
        "BUNDESLIGA": 6,
        "LIGUE_1": 10,
    }
    payload = {}
    fid = 5000
    for league in m.v2.LEAGUE_ORDER:
        rows = []
        for _ in range(counts[league]):
            rows.append({"fixture_id": str(fid), "league": league})
            fid += 1
        payload[league] = rows
    return payload


def test_selected_fixture_reader_accepts_exact_v1_direction_shape(tmp_path):
    path = tmp_path / "direction.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "artifacts/corner_regime_adjusted_direction_v1/selected_fixtures.json",
            json.dumps(_selected_payload()),
        )

    ids = m.load_selected_fixture_ids(path)
    assert len(ids) == m.EXPECTED_V1_DIRECTION_IDS == 46


def test_prior_exclusion_contract_requires_151_unique_ids(monkeypatch, tmp_path):
    discovery_ids = [str(1000 + i) for i in range(55)]
    replication_ids = {str(2000 + i) for i in range(50)}

    monkeypatch.setattr(
        m.market_v1,
        "load_market_rows",
        lambda pilot, screen: pd.DataFrame({"fixture_id": discovery_ids}),
    )
    monkeypatch.setattr(
        m.direction_v1,
        "load_previous_selected_fixture_ids",
        lambda path: replication_ids,
    )

    path = tmp_path / "direction.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("x/selected_fixtures.json", json.dumps(_selected_payload()))

    all_ids, counts = m.load_all_prior_fixture_ids(
        tmp_path / "pilot.zip",
        tmp_path / "screen.zip",
        tmp_path / "replication.zip",
        path,
    )
    assert counts == {"discovery": 55, "replication": 50, "v1_direction": 46}
    assert len(all_ids) == 151


def test_page_cutoff_detection_is_metadata_only():
    assert m._page_reaches_before_cutoff(
        [{"kickoff_utc": "2026-09-18T22:00:00Z"}]
    )
    assert not m._page_reaches_before_cutoff(
        [{"kickoff_utc": "2026-09-19T12:00:00Z"}]
    )


def test_fetch_future_metadata_stops_when_page_reaches_cutoff(monkeypatch, tmp_path):
    calls = []

    def raw_fixture(fid, kickoff):
        return {
            "id": str(fid),
            "status": "finished",
            "kickoff_utc": kickoff,
            "teams": {
                "home": {"name": f"H{fid}"},
                "away": {"name": f"A{fid}"},
            },
        }

    class FakeClient:
        def __init__(self, key):
            self.request_count = 0

        def get_fixture_page(self, league_id, page):
            self.request_count += 1
            calls.append((league_id, page))
            return {
                "success": 1,
                "data": [
                    raw_fixture(f"{league_id}1", "2026-09-20T15:00:00Z"),
                    raw_fixture(f"{league_id}2", "2026-09-18T15:00:00Z"),
                ],
                "pagination": {"has_more": True},
            }

    monkeypatch.setattr(m, "MetadataProviderClient", FakeClient)
    rows, requests = m.fetch_future_fixture_metadata(tmp_path, key="test")

    assert requests == len(m.v2.LEAGUE_ORDER) == 5
    assert len(calls) == 5
    assert all(page == 1 for _, page in calls)
    assert len(rows) == 10
    assert all(row["status"] == "finished" for row in rows)


def test_metadata_runner_has_no_market_price_endpoint():
    source = inspect.getsource(m)
    assert '"/odds"' not in source
    assert "'/odds'" not in source
    assert "get_fixture_page" in source
    assert m.MAX_PAGES_PER_LEAGUE == 2
    assert m.MAX_METADATA_REQUESTS == 10
