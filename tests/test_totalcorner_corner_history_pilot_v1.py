from pathlib import Path

import pytest

import totalcorner_corner_history_pilot_v1 as pilot


def _schedule_payload(matches, *, next_page=False):
    return {
        "success": 1,
        "pagination": {"current": 1, "next": next_page},
        "data": matches,
    }


def _match(match_id: int, league_id: str, kickoff: str):
    return {
        "id": str(match_id),
        "l_id": league_id,
        "l": f"League {league_id}",
        "start": kickoff,
        "h": f"Home {match_id}",
        "a": f"Away {match_id}",
    }


def _selected_ten_each():
    selected = {}
    base = 1000
    for league_index, (league, league_id) in enumerate(pilot.LEAGUES.items()):
        fixtures = []
        for index in range(10):
            match_id = str(base + league_index * 100 + index)
            fixtures.append(
                {
                    "match_id": match_id,
                    "league": league,
                    "league_id": league_id,
                    "kickoff": f"2025-05-25 {10 + index:02d}:00:00",
                    "home_team": f"H {match_id}",
                    "away_team": f"A {match_id}",
                }
            )
        selected[league] = fixtures
    return selected


def test_extract_schedule_matches_supports_list_and_matches_object():
    match = _match(1, "1", "2025-05-25 16:00:00")
    assert pilot.extract_schedule_matches(_schedule_payload([match])) == [match]
    payload = {"success": 1, "data": {"matches": [match]}}
    assert pilot.extract_schedule_matches(payload) == [match]


def test_select_pilot_fixtures_is_deterministic_deduplicated_and_capped():
    matches = []
    for league_id in pilot.LEAGUES.values():
        for index in range(12):
            matches.append(_match(10000 + int(league_id) * 100 + index, league_id, f"2025-05-25 {index:02d}:00:00"))
    # Duplicate one early match and add an unrelated league.
    matches.append(dict(matches[0]))
    matches.append(_match(99999, "999", "2025-05-25 00:00:00"))

    selected = pilot.select_pilot_fixtures([_schedule_payload(list(reversed(matches)))])
    assert set(selected) == set(pilot.LEAGUES)
    for league, fixtures in selected.items():
        assert len(fixtures) == 10
        assert len({fixture["match_id"] for fixture in fixtures}) == 10
        assert fixtures == sorted(fixtures, key=lambda row: (row["kickoff"], int(row["match_id"])))
        assert all(fixture["league_id"] == pilot.LEAGUES[league] for fixture in fixtures)


def test_schedule_has_next_page_uses_documented_pagination_flag():
    assert pilot.schedule_has_next_page(_schedule_payload([], next_page=True)) is True
    assert pilot.schedule_has_next_page(_schedule_payload([], next_page=False)) is False


def test_coverage_gate_passes_at_eight_of_ten_and_qualifies_all_three():
    selected = _selected_ten_each()
    normalized = {}
    for fixtures in selected.values():
        for fixture in fixtures[:8]:
            normalized[fixture["match_id"]] = [{"corner_line": 9.5}]

    report = pilot.build_coverage_summary(selected, normalized)
    assert report["decision"] == "SOURCE_QUALIFIED"
    for league in pilot.LEAGUES:
        league_report = report["league_reports"][league]
        assert league_report["selected_fixtures"] == 10
        assert league_report["covered_fixtures"] == 8
        assert league_report["status"] == "PASS"


def test_coverage_gate_fails_at_seven_of_ten():
    selected = _selected_ten_each()
    normalized = {}
    for league, fixtures in selected.items():
        limit = 7 if league == "EPL" else 8
        for fixture in fixtures[:limit]:
            normalized[fixture["match_id"]] = [{"corner_line": 9.5}]

    report = pilot.build_coverage_summary(selected, normalized)
    assert report["league_reports"]["EPL"]["status"] == "FAIL"
    assert report["decision"] == "SOURCE_NOT_QUALIFIED"


def test_insufficient_fixture_count_fails_closed():
    selected = _selected_ten_each()
    selected["LA_LIGA"] = selected["LA_LIGA"][:9]
    report = pilot.build_coverage_summary(selected, {})
    assert report["league_reports"]["LA_LIGA"]["status"] == "INSUFFICIENT_FIXTURES"
    assert report["decision"] == "SOURCE_NOT_QUALIFIED"


def test_run_pilot_refuses_before_any_network_without_token(monkeypatch, tmp_path: Path):
    monkeypatch.delenv(pilot.TOKEN_ENV, raising=False)
    called = False

    def forbidden_get(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be called")

    monkeypatch.setattr(pilot.requests, "get", forbidden_get)
    with pytest.raises(RuntimeError, match=pilot.TOKEN_ENV):
        pilot.run_pilot(tmp_path)
    assert called is False


def test_frozen_request_budget_is_exactly_thirty():
    assert pilot.MAX_ODDS_REQUESTS == 30
    assert pilot.MAX_ODDS_REQUESTS == len(pilot.LEAGUES) * pilot.FIXTURES_PER_LEAGUE
