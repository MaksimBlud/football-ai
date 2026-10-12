"""No-cost EPL official schedule fallback: bounded, attributed, not fake AI/odds."""
from datetime import datetime, timezone
from types import SimpleNamespace

from product_fixture_schedule import (
    OFFICIAL_SCHEDULE_URL,
    OFFICIAL_WEEKS_7_8,
    fetch_upcoming_fixtures,
    official_week_6_fallback,
)


AS_OF = datetime(2026, 10, 12, 14, 0, tzinfo=timezone.utc)


def test_official_october_fallback_has_future_rounds_without_duplicates():
    fixtures = official_week_6_fallback(now_utc=AS_OF)
    assert len(OFFICIAL_WEEKS_7_8) == 17
    assert len(fixtures) == 18  # 1 remaining week-6 + 10 week-7 + 7 week-8
    assert len({f["schedule_id"] for f in fixtures}) == len(fixtures)
    assert len({(f["kickoff_utc"], f["home_team"], f["away_team"]) for f in fixtures}) == len(fixtures)
    assert len([f for f in fixtures if f["match_date_uk"] in {"2026-10-17", "2026-10-18", "2026-10-19"}]) == 10
    assert len([f for f in fixtures if f["match_date_uk"] in {"2026-10-23", "2026-10-24", "2026-10-25"}]) == 7
    assert all(f["league"] == "EPL" for f in fixtures)
    assert all(f["schedule_source"] == "premier_league_official_published_schedule" for f in fixtures)
    assert all(f["model_forecast_status"] == "not_available" for f in fixtures)
    assert all(f["bookmaker_odds_status"] == "not_available" for f in fixtures)
    assert all(datetime.fromisoformat(f["kickoff_utc"]) > AS_OF for f in fixtures)
    assert all(datetime.fromisoformat(f["kickoff_utc"]) < AS_OF.replace(day=26) for f in fixtures)
    assert any(f["home_team"] == "Everton" and f["away_team"] == "Chelsea"
               and f["kickoff_utc"] == "2026-10-17T11:30:00+00:00" for f in fixtures)
    assert any(f["home_team"] == "Sunderland" and f["away_team"] == "Leeds United"
               and f["kickoff_utc"] == "2026-10-25T16:30:00+00:00" for f in fixtures)


def test_sources_do_not_invent_ambiguous_broadcast_fixture():
    fixtures = official_week_6_fallback(now_utc=AS_OF)
    assert not any(f["home_team"] == "Liverpool" and
                   f["away_team"] == "Brighton and Hove Albion"
                   and f["match_date_uk"] in {"2026-10-24", "2026-10-25"}
                   for f in fixtures)
    assert not any(f["home_team"] == "Crystal Palace" and
                   f["away_team"] == "Newcastle United" and
                   f["match_date_uk"] == "2026-10-25" for f in fixtures)


def test_london_dst_transition_is_explicit_not_server_timezone():
    fixtures = official_week_6_fallback(now_utc=AS_OF)
    assert next(f for f in fixtures if f["home_team"] == "Coventry City" and
                f["match_date_uk"] == "2026-10-24")["kickoff_utc"] == "2026-10-24T14:00:00+00:00"
    assert next(f for f in fixtures if f["home_team"] == "Hull City" and
                f["match_date_uk"] == "2026-10-25")["kickoff_utc"] == "2026-10-25T14:00:00+00:00"


def test_fallback_expires_after_october_and_never_creates_future_fixtures():
    late=datetime(2026, 11, 3, 10, tzinfo=timezone.utc)
    assert official_week_6_fallback(now_utc=late) == []
    def offline(*args, **kwargs):
        raise OSError("no free schedule connectivity")
    payload=fetch_upcoming_fixtures(now_utc=late, get=offline)
    assert payload["schema_version"] == "public-fixtures.v1"
    assert payload["source_mode"] == "unavailable"
    assert payload["fixtures"] == []
    assert payload["has_model_forecasts"] is False
    assert payload["has_bookmaker_odds"] is False


def test_free_schedule_failure_uses_official_dated_source_only():
    def offline(*args, **kwargs):
        raise OSError("ESPN blocked at this runtime")
    payload=fetch_upcoming_fixtures(now_utc=AS_OF, get=offline)
    assert payload["schema_version"] == "public-fixtures.v1"
    assert payload["source_mode"] == "official_published_schedule_fallback"
    assert payload["source_url"] == OFFICIAL_SCHEDULE_URL
    assert len(payload["fixtures"]) == 18
    assert payload["has_model_forecasts"] is False
    assert payload["has_bookmaker_odds"] is False


def test_available_keyless_espn_schedule_takes_precedence():
    event={
        "id":"123", "date":"2026-10-20T14:00:00Z",
        "status":{"type":{"state":"pre","completed":False}},
        "competitions":[{"competitors":[
            {"homeAway":"home","team":{"displayName":"Home"}},
            {"homeAway":"away","team":{"displayName":"Away"}}
        ]}]
    }
    def ok(*args, **kwargs):
        return SimpleNamespace(status_code=200,json=lambda:{"events":[event]})
    payload=fetch_upcoming_fixtures(now_utc=AS_OF,get=ok)
    assert payload["source_mode"] == "espn_public_schedule"
    assert len(payload["fixtures"]) == 1
    assert payload["fixtures"][0]["schedule_id"] == "espn:123"
