"""Zero-cost current-season finished results from configured Football-Data CSV.

This module is deliberately independent of The Odds API and production models.
It uses an explicitly configured Football-Data season/division CSV as primary.
If and only if that primary CSV exhausts bounded transient HTTP retries, it may
fall back to Football-Data's official combined current-season
``Latest_Results.csv`` and filter the exact configured division.
"""
from __future__ import annotations

from io import StringIO
import time
from typing import Callable

import pandas as pd
import requests

from league_offline_history import normalize_football_data_frame
from league_runtime_config import LeagueRuntimeConfig

BASE_URL = "https://www.football-data.co.uk/mmz4281"
PROVIDER = "FOOTBALL_DATA_CSV"
TRANSIENT_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})
DEFAULT_MAX_ATTEMPTS = 3
RESULT_COLUMNS = (
    "league",
    "season",
    "match_date",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
)


class PublicResultsSourceUnavailable(RuntimeError):
    """Bounded transient failure from the zero-cost public results source."""

    def __init__(self, *, url: str, status_code: int, attempts: int, detail: str = ""):
        self.url = str(url)
        self.status_code = int(status_code)
        self.attempts = int(attempts)
        self.detail = str(detail)[:300]
        super().__init__(
            f"Football-Data current results HTTP {self.status_code} after {self.attempts} attempt(s): "
            + self.detail
        )


def _validated_source_parts(config: LeagueRuntimeConfig) -> tuple[str, str]:
    source = config.finished_results_source
    if source.provider != PROVIDER:
        raise ValueError(
            f"{config.identity.identifier} finished-results provider is not {PROVIDER}"
        )
    season_code = str(source.season_code).strip()
    competition_code = str(source.competition_code).strip()
    if len(season_code) != 4 or not season_code.isdigit():
        raise ValueError("Football-Data current season_code must be four digits")
    if not competition_code:
        raise ValueError("Football-Data competition_code is required")
    return season_code, competition_code


def configured_current_csv_url(config: LeagueRuntimeConfig) -> str:
    season_code, competition_code = _validated_source_parts(config)
    return f"{BASE_URL}/{season_code}/{competition_code}.csv"


def configured_latest_results_csv_url(config: LeagueRuntimeConfig) -> str:
    season_code, _competition_code = _validated_source_parts(config)
    return f"{BASE_URL}/{season_code}/Latest_Results.csv"


def latest_results_csv_url(season_code: str) -> str:
    value = str(season_code).strip()
    if len(value) != 4 or not value.isdigit():
        raise ValueError("Football-Data current season_code must be four digits")
    return f"{BASE_URL}/{value}/Latest_Results.csv"


def build_finished_frame(raw: pd.DataFrame, config: LeagueRuntimeConfig) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            "Missing Football-Data current-result columns: "
            + ", ".join(sorted(missing))
        )

    ftr = raw["FTR"].fillna("").astype(str).str.strip()
    unexpected = sorted(set(ftr[(ftr != "") & ~ftr.isin({"H", "D", "A"})]))
    if unexpected:
        raise ValueError("Unexpected Football-Data full-time result: " + repr(unexpected[:10]))

    finished = raw.loc[ftr.isin({"H", "D", "A"})].copy()
    if finished.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    home_goals = pd.to_numeric(finished["FTHG"], errors="coerce")
    away_goals = pd.to_numeric(finished["FTAG"], errors="coerce")
    if home_goals.isna().any() or away_goals.isna().any():
        raise ValueError("Finished Football-Data row has missing/non-numeric goals")
    if ((home_goals % 1) != 0).any() or ((away_goals % 1) != 0).any():
        raise ValueError("Finished Football-Data row has non-integer goals")
    if (home_goals < 0).any() or (away_goals < 0).any():
        raise ValueError("Finished Football-Data row has negative goals")

    normalized = normalize_football_data_frame(
        finished,
        config=config,
        season=config.finished_results_source.season,
        require_complete=False,
    )
    return normalized.loc[:, RESULT_COLUMNS].copy()


def _fetch_csv_response(
    url: str,
    *,
    get: Callable,
    timeout: int,
    max_attempts: int,
    sleep: Callable[[float], None],
):
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    response = None
    for attempt in range(1, max_attempts + 1):
        response = get(url, timeout=timeout)
        if response.status_code == 200:
            return response, attempt
        if response.status_code not in TRANSIENT_HTTP_STATUSES or attempt == max_attempts:
            break
        sleep(float(attempt))
    assert response is not None
    status_code = int(response.status_code)
    detail = str(getattr(response, "text", ""))[:300]
    attempts = max_attempts if status_code in TRANSIENT_HTTP_STATUSES else 1
    if status_code in TRANSIENT_HTTP_STATUSES:
        raise PublicResultsSourceUnavailable(
            url=url,
            status_code=status_code,
            attempts=attempts,
            detail=detail,
        )
    raise RuntimeError(
        f"Football-Data current results HTTP {status_code} after {attempts} attempt(s): " + detail
    )


def fetch_division_raw_results(
    *,
    primary_url: str,
    season_code: str,
    competition_code: str,
    get: Callable = requests.get,
    timeout: int = 30,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Fetch one division, with availability-only fallback to official latest CSV.

    The primary response is returned unmodified. For fallback, ``Div`` is
    mandatory and only the exact requested division is returned. CSV parse or
    data-contract errors are hard failures and are never converted into another
    provider path.
    """
    competition = str(competition_code).strip()
    if not competition:
        raise ValueError("Football-Data competition_code is required")
    fallback_url = latest_results_csv_url(season_code)
    try:
        response, primary_attempts = _fetch_csv_response(
            primary_url,
            get=get,
            timeout=timeout,
            max_attempts=max_attempts,
            sleep=sleep,
        )
    except PublicResultsSourceUnavailable as primary_error:
        try:
            fallback_response, fallback_attempts = _fetch_csv_response(
                fallback_url,
                get=get,
                timeout=timeout,
                max_attempts=max_attempts,
                sleep=sleep,
            )
        except PublicResultsSourceUnavailable as fallback_error:
            raise PublicResultsSourceUnavailable(
                url=fallback_error.url,
                status_code=fallback_error.status_code,
                attempts=primary_error.attempts + fallback_error.attempts,
                detail=(
                    "primary and official Latest_Results.csv exhausted transient retries; "
                    + fallback_error.detail
                ),
            ) from fallback_error
        raw = pd.read_csv(StringIO(fallback_response.text))
        if "Div" not in raw.columns:
            raise ValueError("Missing Football-Data latest-results division column: Div")
        divisions = raw["Div"].fillna("").astype(str).str.strip()
        selected = raw.loc[divisions.eq(competition)].copy()
        if selected.empty:
            raise ValueError(
                f"Football-Data latest-results CSV missing configured division {competition}"
            )
        return {
            "raw": selected,
            "source_url": fallback_url,
            "primary_source_url": primary_url,
            "fallback_used": True,
            "primary_unavailable_status": primary_error.status_code,
            "public_http_requests": primary_error.attempts + fallback_attempts,
            "source_rows": int(len(selected)),
        }

    raw = pd.read_csv(StringIO(response.text))
    return {
        "raw": raw,
        "source_url": primary_url,
        "primary_source_url": primary_url,
        "fallback_used": False,
        "public_http_requests": primary_attempts,
        "source_rows": int(len(raw)),
    }


def fetch_current_finished_results(
    config: LeagueRuntimeConfig,
    *,
    get: Callable = requests.get,
    timeout: int = 30,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Fetch and validate one explicitly configured public results source.

    ``paid_provider_requests`` is always zero because this path never calls
    The Odds API. Permanent HTTP errors and schema/semantic validation errors
    remain hard failures and never activate a fallback.
    """
    season_code, competition_code = _validated_source_parts(config)
    fetched = fetch_division_raw_results(
        primary_url=configured_current_csv_url(config),
        season_code=season_code,
        competition_code=competition_code,
        get=get,
        timeout=timeout,
        max_attempts=max_attempts,
        sleep=sleep,
    )
    frame = build_finished_frame(fetched["raw"], config)
    return {
        "frame": frame,
        "source_url": fetched["source_url"],
        "primary_source_url": fetched["primary_source_url"],
        "fallback_used": bool(fetched["fallback_used"]),
        **(
            {"primary_unavailable_status": fetched["primary_unavailable_status"]}
            if fetched["fallback_used"]
            else {}
        ),
        "public_http_requests": int(fetched["public_http_requests"]),
        "paid_provider_requests": 0,
        "source_rows": int(fetched["source_rows"]),
        "finished_rows": int(len(frame)),
    }
