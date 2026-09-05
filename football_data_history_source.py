"""Config-driven Football-Data historical CSV source for offline research.

No Odds API calls.
No Supabase access.
No model training or promotion.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd
import requests

from league_offline_history import (
    REQUIRED_COLUMNS,
    validate_complete_double_round_robin,
)
from league_runtime_config import LeagueRuntimeConfig


BASE_URL = "https://www.football-data.co.uk/mmz4281"
EUROPEAN_SEASON_COMPLETION_MONTH = 7
EUROPEAN_SEASON_COMPLETION_DAY = 1


def completed_european_season_codes(
    config: LeagueRuntimeConfig,
    *,
    as_of: date,
) -> dict[str, str]:
    """Return configured seasons that are safely past the European season boundary."""
    completed: dict[str, str] = {}
    for code, season in config.historical_source.season_codes.items():
        start_text, end_text = season.split("-", 1)
        start_year = int(start_text)
        end_year = int(end_text)
        if end_year != start_year + 1:
            raise ValueError(f"Unexpected season range: {season}")

        completion_date = date(
            end_year,
            EUROPEAN_SEASON_COMPLETION_MONTH,
            EUROPEAN_SEASON_COMPLETION_DAY,
        )
        if as_of >= completion_date:
            completed[code] = season

    if not completed:
        raise ValueError(
            f"No completed historical seasons for {config.identity.identifier}"
        )
    return completed


def football_data_csv_url(
    *,
    season_code: str,
    competition_code: str,
) -> str:
    if not season_code.isdigit() or len(season_code) != 4:
        raise ValueError(f"Invalid Football-Data season code: {season_code!r}")
    if not competition_code or not competition_code.replace("_", "").isalnum():
        raise ValueError(
            f"Invalid Football-Data competition code: {competition_code!r}"
        )
    return f"{BASE_URL}/{season_code}/{competition_code}.csv"


def history_file_path(
    *,
    raw_directory: Path,
    file_prefix: str,
    season: str,
) -> Path:
    start_year = int(season.split("-", 1)[0])
    return raw_directory / f"{file_prefix}_{start_year}_{start_year + 1}.csv"


def _validate_downloaded_csv(content: bytes, *, season: str) -> pd.DataFrame:
    try:
        frame = pd.read_csv(BytesIO(content))
    except Exception as exc:  # pandas provides the useful parse detail
        raise ValueError(f"Invalid Football-Data CSV for {season}") from exc

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            f"Football-Data CSV for {season} missing columns: "
            + ", ".join(sorted(missing))
        )

    validate_complete_double_round_robin(frame, season=season)
    return frame


def download_configured_history(
    *,
    config: LeagueRuntimeConfig,
    raw_directory: Path,
    file_prefix: str,
    season_codes: Mapping[str, str],
    request_get: Callable[..., object] = requests.get,
    timeout: int = 30,
    overwrite: bool = False,
) -> list[dict[str, object]]:
    """Download and validate complete configured seasons before persisting them."""
    if not season_codes:
        raise ValueError("No historical seasons selected for download")

    raw_directory.mkdir(parents=True, exist_ok=True)
    reports: list[dict[str, object]] = []

    for season_code, season in season_codes.items():
        path = history_file_path(
            raw_directory=raw_directory,
            file_prefix=file_prefix,
            season=season,
        )
        if path.exists() and not overwrite:
            existing = path.read_bytes()
            frame = _validate_downloaded_csv(existing, season=season)
            reports.append(
                {
                    "season": season,
                    "season_code": season_code,
                    "path": str(path),
                    "rows": len(frame),
                    "status": "existing_valid",
                }
            )
            continue

        url = football_data_csv_url(
            season_code=season_code,
            competition_code=config.historical_source.competition_code,
        )
        response = request_get(url, timeout=timeout)
        response.raise_for_status()
        content = bytes(response.content)
        frame = _validate_downloaded_csv(content, season=season)

        path.write_bytes(content)
        reports.append(
            {
                "season": season,
                "season_code": season_code,
                "url": url,
                "path": str(path),
                "rows": len(frame),
                "status": "downloaded",
            }
        )

    return reports
