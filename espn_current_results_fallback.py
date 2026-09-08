"""Zero-cost ESPN scoreboard fallback for current finished results.

This is a secondary source only. Operational league syncs must try their
configured Football-Data source first and may call this module only after a
bounded transient outage. The endpoint is public/keyless but unofficial, so
schema or identity drift fails closed.
"""
from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd
import requests

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
PROVIDER = "ESPN_SCOREBOARD_FALLBACK"
DEFAULT_MAX_ATTEMPTS = 3
TRANSIENT_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})

LEAGUES = {
    "LA_LIGA": {"slug": "esp.1", "timezone": "Europe/Madrid"},
    "SERIE_A": {"slug": "ita.1", "timezone": "Europe/Rome"},
}

# ESPN display name -> project/source-compatible name. Everything else passes
# through unchanged and is still validated by the existing league normalizer.
TEAM_ALIASES = {
    "LA_LIGA": {
        "Athletic Club": "Ath Bilbao",
        "Deportivo La Coruna": "Dep. A Coruna",
        "Elche": "Elche",
        "Malaga": "Malaga",
        "Osasuna": "Osasuna",
        "Racing Santander": "Santander",
        "Rayo Vallecano": "Vallecano",
    },
    "SERIE_A": {
        "Atalanta": "Atalanta BC",
        "Internazionale": "Inter Milan",
        "Inter": "Inter Milan",
        "Milan": "AC Milan",
        "Roma": "AS Roma",
    },
}


class ESPNResultsSourceUnavailable(RuntimeError):
    def __init__(self, *, url: str, attempts: int, status_code: int | None, detail: str = ""):
        self.url = str(url)
        self.attempts = int(attempts)
        self.status_code = None if status_code is None else int(status_code)
        self.detail = str(detail)[:300]
        status = "NETWORK" if status_code is None else str(status_code)
        super().__init__(
            f"ESPN scoreboard unavailable ({status}) after {self.attempts} attempt(s): {self.detail}"
        )


def _request_json(
    url: str,
    *,
    params: dict[str, str],
    get: Callable = requests.get,
    timeout: int = 30,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict, int, str]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_network_error: Exception | None = None
    response = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            last_network_error = exc
            if attempt == max_attempts:
                raise ESPNResultsSourceUnavailable(
                    url=url,
                    attempts=attempt,
                    status_code=None,
                    detail=str(exc),
                ) from exc
            sleep(float(attempt))
            continue

        if int(response.status_code) == 200:
            try:
                payload = response.json()
            except Exception as exc:
                raise ValueError("ESPN scoreboard returned invalid JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError("ESPN scoreboard payload must be an object")
            return payload, attempt, str(getattr(response, "url", url))

        status = int(response.status_code)
        if status not in TRANSIENT_HTTP_STATUSES:
            raise RuntimeError(
                f"ESPN scoreboard HTTP {status}: {str(getattr(response, 'text', ''))[:300]}"
            )
        if attempt == max_attempts:
            raise ESPNResultsSourceUnavailable(
                url=url,
                attempts=attempt,
                status_code=status,
                detail=str(getattr(response, "text", ""))[:300],
            )
        sleep(float(attempt))

    # Defensive: loop always returns or raises.
    raise ESPNResultsSourceUnavailable(
        url=url,
        attempts=max_attempts,
        status_code=None,
        detail=str(last_network_error or "unknown error"),
    )


def _score(value, *, field: str) -> int:
    if value is None or isinstance(value, bool):
        raise ValueError(f"ESPN completed event missing {field}")
    text = str(value).strip()
    try:
        number = int(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"ESPN completed event has invalid {field}: {value!r}") from exc
    if str(number) != text and text not in {f"+{number}"}:
        raise ValueError(f"ESPN completed event has non-integer {field}: {value!r}")
    if number < 0:
        raise ValueError(f"ESPN completed event has negative {field}")
    return number


def _result(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    if away_goals > home_goals:
        return "A"
    return "D"


def build_football_data_like_frame(payload: dict, *, league: str) -> pd.DataFrame:
    """Convert completed ESPN events to the existing Football-Data-shaped contract."""
    if league not in LEAGUES:
        raise ValueError(f"Unsupported ESPN fallback league: {league}")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("ESPN scoreboard payload missing events list")

    timezone = ZoneInfo(LEAGUES[league]["timezone"])
    aliases = TEAM_ALIASES[league]
    rows: list[dict] = []

    for event in events:
        if not isinstance(event, dict):
            raise ValueError("ESPN scoreboard event must be an object")
        status = event.get("status") or {}
        status_type = status.get("type") or {}
        if status_type.get("completed") is not True:
            continue

        competitions = event.get("competitions")
        if not isinstance(competitions, list) or len(competitions) != 1:
            raise ValueError("ESPN completed event must contain exactly one competition")
        competitors = competitions[0].get("competitors")
        if not isinstance(competitors, list) or len(competitors) != 2:
            raise ValueError("ESPN completed event must contain exactly two competitors")

        sides: dict[str, dict] = {}
        for competitor in competitors:
            if not isinstance(competitor, dict):
                raise ValueError("ESPN competitor must be an object")
            side = str(competitor.get("homeAway") or "").strip()
            if side not in {"home", "away"} or side in sides:
                raise ValueError("ESPN completed event has invalid home/away identity")
            sides[side] = competitor
        if set(sides) != {"home", "away"}:
            raise ValueError("ESPN completed event missing home/away competitor")

        def team_name(side: str) -> str:
            team = sides[side].get("team") or {}
            name = str(team.get("displayName") or "").strip()
            if not name:
                raise ValueError("ESPN completed event missing team displayName")
            return aliases.get(name, name)

        home_goals = _score(sides["home"].get("score"), field="home score")
        away_goals = _score(sides["away"].get("score"), field="away score")
        kickoff = pd.to_datetime(event.get("date"), utc=True, errors="coerce")
        if pd.isna(kickoff):
            raise ValueError("ESPN completed event has invalid date")
        local_date = kickoff.tz_convert(timezone).strftime("%d/%m/%Y")

        rows.append(
            {
                "Date": local_date,
                "HomeTeam": team_name("home"),
                "AwayTeam": team_name("away"),
                "FTHG": home_goals,
                "FTAG": away_goals,
                "FTR": _result(home_goals, away_goals),
            }
        )

    frame = pd.DataFrame(rows, columns=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])
    if frame.empty:
        return frame

    identity = ["Date", "HomeTeam", "AwayTeam"]
    duplicated = frame[frame.duplicated(subset=identity, keep=False)]
    if not duplicated.empty:
        for _, group in duplicated.groupby(identity, dropna=False):
            signatures = set(zip(group["FTHG"], group["FTAG"], group["FTR"]))
            if len(signatures) > 1:
                raise ValueError("Conflicting duplicate fixture inside ESPN scoreboard")
        frame = frame.drop_duplicates(subset=identity, keep="last")

    return frame.sort_values(identity, kind="stable").reset_index(drop=True)


def fetch_football_data_like_results(
    *,
    league: str,
    start_date: str = "2026-08-01",
    now_utc: datetime | None = None,
    get: Callable = requests.get,
    timeout: int = 30,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Fetch current-season completed events from one keyless ESPN scoreboard request."""
    if league not in LEAGUES:
        raise ValueError(f"Unsupported ESPN fallback league: {league}")
    now_utc = now_utc or datetime.now(UTC)
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(now_utc).tz_convert("UTC").tz_localize(None)
    if start > end:
        raise ValueError("ESPN fallback start_date is after current date")

    slug = LEAGUES[league]["slug"]
    url = f"{BASE_URL}/{slug}/scoreboard"
    date_range = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    payload, attempts, resolved_url = _request_json(
        url,
        params={"dates": date_range},
        get=get,
        timeout=timeout,
        max_attempts=max_attempts,
        sleep=sleep,
    )
    frame = build_football_data_like_frame(payload, league=league)
    return {
        "frame": frame,
        "source_url": resolved_url,
        "source_provider": PROVIDER,
        "source_competition": slug,
        "public_http_requests": int(attempts),
        "paid_provider_requests": 0,
        "source_rows": int(len(payload.get("events") or [])),
        "finished_rows": int(len(frame)),
    }
