import os
from pathlib import Path

import pytest

import five_dollar_corners_source_pilot_v1 as pilot


def _fixture(idx: int, league: str = "EPL"):
    return {
        "id": 1000 + idx,
        "league": {"id": int(pilot.LEAGUES[league]), "name": league},
        "teams": {
            "home": {"name": f"Home {idx}"},
            "away": {"name": f"Away {idx}"},
        },
        "kickoff_utc": f"2026-09-{idx + 1:02d}T15:00:00+00:00",
        "status": "finished",
    }


def _odds_payload(*, opening=True, closing=True):
    corner_line = {}
    if opening:
        corner_line["opening"] = {"line": 9.5, "over": 1.90, "under": 1.90}
    if closing:
        corner_line["closing"] = {"line": 10.0, "over": 1.85, "under": 1.95}
    return {
        "success": 1,
        "data": {
            "fixture_id": 1000,
            "bookmakers": [
                {
                    "name": "Bet 365",
                    "slug": "bet365",
                    "odds": {"corner_line": corner_line},
                }
            ],
        },
    }


def test_missing_key_fails_before_network(monkeypatch, tmp_path):
    monkeypatch.delenv(pilot.KEY_ENV, raising=False)
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be called")

    monkeypatch.setattr(pilot.requests, "get", forbidden)
    with pytest.raises(RuntimeError, match=pilot.KEY_ENV):
        pilot.run_pilot(tmp_path)
    assert called is False


def test_selects_exactly_first_five_unique_finished_fixtures():
    data = [_fixture(i) for i in range(7)]
    data.insert(1, dict(data[0]))
    data.append({**_fixture(9), "status": "scheduled"})
    payload = {"success": 1, "data": data}

    selected = pilot.select_fixtures(payload, "EPL")
    assert len(selected) == 5
    assert [row["fixture_id"] for row in selected] == ["1000", "1001", "1002", "1003", "1004"]


def test_normalizes_complete_bet365_corner_opening_and_closing():
    fixture = {
        "fixture_id": "1000",
        "league": "EPL",
        "league_id": pilot.LEAGUES["EPL"],
        "kickoff_utc": "2026-09-01T15:00:00+00:00",
        "home_team": "Home",
        "away_team": "Away",
    }
    row = pilot.normalize_corner_odds(_odds_payload(), fixture)
    assert row is not None
    assert row["bookmaker"] == "bet365"
    assert row["opening_line"] == 9.5
    assert row["closing_line"] == 10.0
    assert row["opening_over"] == 1.9
    assert row["closing_under"] == 1.95


def test_missing_closing_market_is_not_covered():
    fixture = {
        "fixture_id": "1000",
        "league": "EPL",
        "league_id": pilot.LEAGUES["EPL"],
        "kickoff_utc": "2026-09-01T15:00:00+00:00",
        "home_team": "Home",
        "away_team": "Away",
    }
    assert pilot.normalize_corner_odds(_odds_payload(closing=False), fixture) is None


def test_gate_requires_four_of_five_in_every_league():
    selected = {}
    normalized = {}
    for league in pilot.LEAGUES:
        selected[league] = []
        for idx in range(5):
            fixture_id = f"{league}-{idx}"
            selected[league].append(
                {
                    "fixture_id": fixture_id,
                    "league": league,
                    "league_id": pilot.LEAGUES[league],
                    "kickoff_utc": "2026-09-01T15:00:00+00:00",
                    "home_team": "Home",
                    "away_team": "Away",
                }
            )
            normalized[fixture_id] = {"ok": True} if idx < 4 else None

    report = pilot.build_report(selected, normalized)
    assert report["decision"] == "SOURCE_QUALIFIED_FOR_BACKFILL"
    assert all(v["status"] == "PASS" for v in report["league_reports"].values())

    normalized["SERIE_A-3"] = None
    report = pilot.build_report(selected, normalized)
    assert report["decision"] == "SOURCE_NOT_QUALIFIED"
    assert report["league_reports"]["SERIE_A"]["status"] == "FAIL"


def test_frozen_request_budget_and_league_ids():
    assert pilot.LEAGUES == {
        "EPL": "4160026622",
        "LA_LIGA": "4212821298",
        "SERIE_A": "3405541143",
    }
    assert pilot.FIXTURES_PER_LEAGUE == 5
    assert pilot.COVERAGE_PASS_MIN == 4
    assert pilot.MAX_PROVIDER_REQUESTS == 18
