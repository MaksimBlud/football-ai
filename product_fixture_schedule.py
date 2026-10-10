"""Read-only upcoming EPL fixtures, independent of AI predictions and bookmaker odds.

ESPN's public/keyless scoreboard is a *schedule* source, never an AI or odds
source. The fixed PL matchweek-6 fallback is from the official published
2026-10-10--12 schedule, expires automatically and is labelled as such.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

import json
from types import SimpleNamespace
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _public_get(url, *, params, timeout, allow_redirects):
    """Single keyless request, bounded body and no redirects or secret headers."""
    if url != ESPN_URL or allow_redirects is not False:
        raise ValueError("only the fixed keyless ESPN URL is allowed")
    request = Request(url + "?" + urlencode(params), headers={"User-Agent": "FootballAI-Fixtures/1.0"})
    with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
        status = int(response.status)
        payload = json.loads(response.read(2_000_001).decode("utf-8"))
        if status != 200 or len(json.dumps(payload)) > 2_000_000:
            raise ValueError("invalid keyless schedule response")
    return SimpleNamespace(status_code=status, json=lambda: payload)

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
OFFICIAL_SCHEDULE_URL = "https://www.premierleague.com/en/news/4688862/fixture-amendments-for-premier-league-matches-in-october-and-november"
LONDON = ZoneInfo("Europe/London")

# Source: official Premier League broadcast-amended fixtures, 17 August 2026.
# London-local kickoff times, never disguised as provider IDs or model output.
OFFICIAL_WEEK_6 = (
    ("2026-10-10T12:30:00", "Arsenal", "Leeds United"),
    ("2026-10-10T15:00:00", "Aston Villa", "Brentford"),
    ("2026-10-10T15:00:00", "Chelsea", "Bournemouth"),
    ("2026-10-10T15:00:00", "Ipswich Town", "Fulham"),
    ("2026-10-10T15:00:00", "Sunderland", "Brighton"),
    ("2026-10-10T17:30:00", "Manchester United", "Tottenham"),
    ("2026-10-11T14:00:00", "Crystal Palace", "Nottingham Forest"),
    ("2026-10-11T14:00:00", "Hull City", "Everton"),
    ("2026-10-11T16:30:00", "Liverpool", "Manchester City"),
    ("2026-10-12T20:00:00", "Coventry City", "Newcastle United"),
)


def _utc(value):
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("fixture timestamps must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _fixture(*, kickoff, home, away, source_id, source):
    when = _utc(kickoff)
    if not home or not away or home.casefold() == away.casefold():
        raise ValueError("invalid fixture teams")
    return {
        "schedule_id": str(source_id),
        "league": "EPL",
        "kickoff_utc": when.isoformat(),
        "match_date_uk": when.astimezone(LONDON).strftime("%Y-%m-%d"),
        "match_time_uk": when.astimezone(LONDON).strftime("%H:%M"),
        "home_team": home,
        "away_team": away,
        "schedule_source": source,
        "model_forecast_status": "not_available",
        "bookmaker_odds_status": "not_available",
    }


def parse_espn_schedule(payload, *, now_utc, horizon_days=14):
    """Reject schema drift; only pre-kickoff EPL fixtures with exact home/away."""
    now = _utc(now_utc)
    horizon = now + timedelta(days=horizon_days)
    events = payload.get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list) or len(events) > 100:
        raise ValueError("ESPN events must be a bounded list")
    found = {}
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("invalid ESPN event")
        status_container = event.get("status")
        if not isinstance(status_container, dict):
            raise ValueError("ESPN event status missing or invalid")
        status = status_container.get("type")
        if not isinstance(status, dict):
            raise ValueError("ESPN event status type missing or invalid")
        if status.get("state") != "pre" or status.get("completed") is True:
            continue
        kickoff = _utc(event.get("date"))
        if not now < kickoff < horizon:
            continue
        competitions = event.get("competitions")
        if not isinstance(competitions, list) or len(competitions) != 1:
            raise ValueError("ESPN competition count invalid")
        if not isinstance(competitions[0], dict):
            raise ValueError("ESPN competition schema invalid")
        sides = competitions[0].get("competitors")
        if not isinstance(sides, list) or len(sides) != 2:
            raise ValueError("ESPN teams count invalid")
        clubs = {}
        for side in sides:
            if not isinstance(side, dict) or not isinstance(side.get("team"), dict):
                raise ValueError("ESPN competitor schema invalid")
            position = side.get("homeAway")
            team = side["team"].get("displayName")
            if position not in {"home", "away"} or position in clubs:
                raise ValueError("ESPN home/away identity invalid")
            if not isinstance(team, str) or not team.strip():
                raise ValueError("ESPN team name missing")
            clubs[position] = team.strip()
        event_id = str(event.get("id") or "").strip()
        if not event_id or event_id in found:
            raise ValueError("ESPN fixture ID missing or duplicated")
        found[event_id] = _fixture(
            kickoff=kickoff, home=clubs["home"], away=clubs["away"],
            source_id="espn:" + event_id, source="espn_public_schedule",
        )
    return sorted(found.values(), key=lambda f: (f["kickoff_utc"], f["schedule_id"]))


def official_week_6_fallback(*, now_utc):
    """Time-limited, explicitly attributed schedule, never inferred prices."""
    now = _utc(now_utc)
    rows = []
    for local_str, home, away in OFFICIAL_WEEK_6:
        kickoff = datetime.fromisoformat(local_str).replace(tzinfo=LONDON)
        if now < kickoff.astimezone(timezone.utc) < now + timedelta(days=14):
            rows.append(_fixture(
                kickoff=kickoff, home=home, away=away,
                source_id="pl-official:" + local_str + ":" + home.lower().replace(" ", "-"),
                source="premier_league_official_published_schedule",
            ))
    return rows


def fetch_upcoming_fixtures(*, now_utc=None, get=None):
    now = _utc(now_utc or datetime.now(timezone.utc))
    from_date = now.date().strftime("%Y%m%d")
    until_date = (now + timedelta(days=14)).date().strftime("%Y%m%d")
    try:
        response = (get or _public_get)(
            ESPN_URL, params={"dates": from_date + "-" + until_date},
            timeout=12, allow_redirects=False,
        )
        if response.status_code != 200:
            raise RuntimeError("ESPN schedule HTTP " + str(response.status_code))
        fixtures = parse_espn_schedule(response.json(), now_utc=now)
        if not fixtures:
            raise RuntimeError("ESPN returned no upcoming fixtures")
        return {
            "schema_version": "public-fixtures.v1",
            "source_mode": "espn_public_schedule",
            "source_url": ESPN_URL,
            "fixtures": fixtures,
            "has_model_forecasts": False,
            "has_bookmaker_odds": False,
        }
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        fixtures = official_week_6_fallback(now_utc=now)
        return {
            "schema_version": "public-fixtures.v1",
            "source_mode": "official_published_schedule_fallback" if fixtures else "unavailable",
            "source_url": OFFICIAL_SCHEDULE_URL if fixtures else None,
            "fixtures": fixtures,
            "has_model_forecasts": False,
            "has_bookmaker_odds": False,
        }


@lru_cache(maxsize=8)
def _cached_schedule(quarter_hour: int):
    return fetch_upcoming_fixtures()


def live_upcoming_fixtures():
    """Read-only public endpoint. Cache the keyless request for 15 minutes."""
    now = datetime.now(timezone.utc)
    return _cached_schedule(int(now.timestamp()) // 900)
