import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import totalcorner_corner_pilot_v1 as pilot


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_client_missing_token_fails_before_http(monkeypatch):
    monkeypatch.delenv(pilot.TOKEN_ENV, raising=False)
    called = False

    def forbidden_get(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("HTTP must not be called")

    with pytest.raises(RuntimeError, match=pilot.TOKEN_ENV):
        pilot.TotalCornerClient(token=None, get=forbidden_get)
    assert called is False


def test_client_paces_requests():
    payload = {"success": 1, "data": {"matches": []}, "pagination": {"next": False}}
    times = iter([0.0, 0.0, 0.1, 2.1])
    sleeps = []
    client = pilot.TotalCornerClient(
        "token",
        min_interval_seconds=2.0,
        get=lambda *args, **kwargs: FakeResponse(payload),
        sleep=sleeps.append,
        monotonic=lambda: next(times),
    )
    client.get_json("/league/schedule/1")
    client.get_json("/league/schedule/1")
    assert sleeps == [pytest.approx(1.9)]


def _schedule_payload(league_id, fixtures, next_page=False):
    return {
        "success": 1,
        "pagination": {"next": next_page},
        "data": {"league": {"league_id": league_id}, "matches": fixtures},
    }


class ScheduleClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get_json(self, path, *, params=None):
        self.calls.append((path, params or {}))
        page = int((params or {}).get("page", 1))
        return self.payloads[page]


def test_discover_sample_is_latest_ten_and_persists_raw(tmp_path):
    fixtures = []
    for i in range(12):
        day = datetime(2026, 5, 1) + timedelta(days=i)
        fixtures.append(
            {
                "id": str(1000 + i),
                "h": f"Home {i}",
                "a": f"Away {i}",
                "l_id": "1",
                "start": day.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    client = ScheduleClient({1: _schedule_payload("1", fixtures)})
    selected = pilot.discover_sample(client, "EPL", tmp_path)
    assert len(selected) == 10
    assert selected[0]["match_id"] == "1011"
    assert selected[-1]["match_id"] == "1002"
    raw = tmp_path / "EPL" / "schedule" / "page_001.json"
    assert raw.exists()
    assert json.loads(raw.read_text())["success"] == 1


def test_reconcile_fixture_uses_alias_and_date_tolerance():
    fixture = {
        "home_team": "AC Milan",
        "away_team": "Inter Milan",
        "kickoff": "2026-05-24 19:45:00",
    }
    manifest = [
        {
            "date": datetime(2026, 5, 24).date(),
            "home_team": "Milan",
            "away_team": "Inter",
            "home_key": pilot._team_key("Milan"),
            "away_key": pilot._team_key("Inter"),
        }
    ]
    result = pilot.reconcile_fixture(fixture, manifest)
    assert result["identity_ok"] is True
    assert result["candidate_count"] == 1


class FullPilotClient:
    def __init__(self):
        self.fixture_by_id = {}
        for league_index, (league, league_id) in enumerate(pilot.LEAGUE_IDS.items()):
            for i in range(10):
                match_id = str(league_index * 1000 + 100 + i)
                kickoff = datetime(2026, 5, 10) + timedelta(days=i)
                self.fixture_by_id[match_id] = {
                    "league": league,
                    "league_id": league_id,
                    "match_id": match_id,
                    "home": f"{league} Home {i}",
                    "away": f"{league} Away {i}",
                    "kickoff": kickoff,
                }

    def get_json(self, path, *, params=None):
        if path.startswith("/league/schedule/"):
            league_id = path.rsplit("/", 1)[-1]
            fixtures = [
                {
                    "id": row["match_id"],
                    "h": row["home"],
                    "a": row["away"],
                    "l_id": league_id,
                    "start": row["kickoff"].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in self.fixture_by_id.values()
                if row["league_id"] == league_id
            ]
            return _schedule_payload(league_id, fixtures)
        if path.startswith("/match/odds/"):
            match_id = path.rsplit("/", 1)[-1]
            row = self.fixture_by_id[match_id]
            observed = row["kickoff"] - timedelta(hours=12)
            return {
                "success": 1,
                "data": [
                    {
                        "id": match_id,
                        "h": row["home"],
                        "a": row["away"],
                        "l": row["league"],
                        "start": row["kickoff"].strftime("%Y-%m-%d %H:%M:%S"),
                        "corner_list": [
                            [
                                "0",
                                "10.0",
                                "1.91",
                                "1.91",
                                observed.strftime("%Y-%m-%d %H:%M:%S"),
                                "0",
                                "0",
                            ]
                        ],
                    }
                ],
            }
        raise AssertionError(path)


def test_full_synthetic_pilot_passes_without_model_metrics(tmp_path):
    client = FullPilotClient()

    def manifest_loader(league):
        return [
            {
                "date": row["kickoff"].date(),
                "home_team": row["home"],
                "away_team": row["away"],
                "home_key": pilot._team_key(row["home"]),
                "away_key": pilot._team_key(row["away"]),
            }
            for row in client.fixture_by_id.values()
            if row["league"] == league
        ]

    report = pilot.run_pilot(tmp_path, client=client, manifest_loader=manifest_loader)
    assert report["decision"] == "PASS_SOURCE_PILOT"
    assert report["model_metrics_computed"] is False
    assert len(report["league_reports"]) == 3
    for league in report["league_reports"]:
        assert league["selected_count"] == 10
        assert league["covered_count"] == 10
        assert league["identity_ok_count"] == 10
        assert league["status"] == "PASS"
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "normalized" / "epl.jsonl").exists()
