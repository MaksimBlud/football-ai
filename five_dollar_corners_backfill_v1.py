"""Acquisition-only historical Bet365 corner-market backfill for frozen V1.

No model metrics are computed here. The runner fails closed if the API plan does
not expose the preregistered historical window.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from five_dollar_corners_source_pilot_v1 import BASE_URL, KEY_ENV

EXPERIMENT_ID = "FIVE_DOLLAR_CORNERS_BACKFILL_V1"
LEAGUES = {
    "EPL": "4160026622",
    "LA_LIGA": "4212821298",
    "SERIE_A": "3405541143",
}
SEASONS = (
    "2016-17", "2017-18", "2018-19", "2019-20", "2020-21",
    "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
)
FORBIDDEN_SEASON = "2026-27"
PER_PAGE = 50
MAX_PROVIDER_REQUESTS = 300
REQUEST_INTERVAL_SECONDS = 1.6


class HistoryAccessRequired(RuntimeError):
    pass


class HistoryPreflightFailed(RuntimeError):
    pass


@dataclass
class RateLimiter:
    interval_seconds: float = REQUEST_INTERVAL_SECONDS
    last_request_at: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self.last_request_at is not None:
            remaining = self.interval_seconds - (now - self.last_request_at)
            if remaining > 0:
                time.sleep(remaining)
        self.last_request_at = time.monotonic()


def _require_key(key: str | None = None) -> str:
    value = (key or os.getenv(KEY_ENV, "")).strip()
    if not value:
        raise RuntimeError(f"{KEY_ENV} is required; refusing historical backfill without an explicit key")
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _season_window(season: str) -> tuple[int, int]:
    if season == FORBIDDEN_SEASON:
        raise ValueError(f"forbidden season: {season}")
    if season not in SEASONS:
        raise ValueError(f"season outside frozen backfill: {season}")
    start_year = int(season[:4])
    start = int(datetime(start_year, 7, 1, tzinfo=timezone.utc).timestamp())
    end = int(datetime(start_year + 1, 7, 1, tzinfo=timezone.utc).timestamp())
    return start, end


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _valid_stage(stage: Any) -> dict[str, float] | None:
    if not isinstance(stage, dict):
        return None
    line = _number(stage.get("line"))
    over = _number(stage.get("over"))
    under = _number(stage.get("under"))
    if line is None or over is None or under is None or over <= 1.0 or under <= 1.0:
        return None
    return {"line": line, "over": over, "under": under}


def _inline_bookmakers(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    odds = fixture.get("odds")
    if isinstance(odds, list):
        return [item for item in odds if isinstance(item, dict)]
    if not isinstance(odds, dict):
        return []
    if isinstance(odds.get("bookmakers"), list):
        return [item for item in odds["bookmakers"] if isinstance(item, dict)]
    data = odds.get("data")
    if isinstance(data, dict) and isinstance(data.get("bookmakers"), list):
        return [item for item in data["bookmakers"] if isinstance(item, dict)]
    return []


def normalize_fixture_market(fixture: dict[str, Any], league: str, season: str) -> dict[str, Any] | None:
    if str(fixture.get("status") or "").lower() != "finished":
        return None
    fixture_id = str(fixture.get("id") or "").strip()
    kickoff = str(fixture.get("kickoff_utc") or "").strip()
    teams = fixture.get("teams") or {}
    home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
    away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
    league_obj = fixture.get("league") or {}
    if not (fixture_id.isdigit() and kickoff and home and away):
        return None
    if str((league_obj or {}).get("id") or "") != LEAGUES[league]:
        return None

    bet365 = None
    for bookmaker in _inline_bookmakers(fixture):
        if str(bookmaker.get("slug") or "").lower() == "bet365":
            bet365 = bookmaker
            break
    if bet365 is None:
        return None
    odds = bet365.get("odds")
    if not isinstance(odds, dict):
        return None
    corner_line = odds.get("corner_line")
    if not isinstance(corner_line, dict):
        return None
    opening = _valid_stage(corner_line.get("opening"))
    if opening is None:
        return None
    closing = _valid_stage(corner_line.get("closing"))

    row: dict[str, Any] = {
        "fixture_id": fixture_id,
        "league": league,
        "league_id": LEAGUES[league],
        "season": season,
        "kickoff_utc": kickoff,
        "home_team": str(home),
        "away_team": str(away),
        "bookmaker": "bet365",
        "opening_line": opening["line"],
        "opening_over": opening["over"],
        "opening_under": opening["under"],
        "closing_line": closing["line"] if closing else None,
        "closing_over": closing["over"] if closing else None,
        "closing_under": closing["under"] if closing else None,
        "source": "5DOLLARFOOTBALLAPI",
    }
    return row


def _extract_error_code(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("code") or error.get("type") or "")
    return str(payload.get("code") or "")


def _request_page(
    *,
    key: str,
    league_id: str,
    start_time: int,
    end_time: int,
    page: int,
    per_page: int,
    limiter: RateLimiter,
) -> dict[str, Any]:
    limiter.wait()
    response = requests.get(
        f"{BASE_URL}/v1/leagues/{league_id}/fixtures",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        params={
            "status": "finished",
            "include": "odds",
            "order": "asc",
            "start_time": start_time,
            "end_time": end_time,
            "page": page,
            "per_page": per_page,
        },
        timeout=45,
    )
    try:
        payload = response.json()
    except Exception:
        payload = {}
    if response.status_code == 403 and _extract_error_code(payload) in {"insufficient_plan", "permission_error"}:
        raise HistoryAccessRequired("provider plan does not expose frozen historical bulk odds window")
    response.raise_for_status()
    if payload.get("success") != 1 or not isinstance(payload.get("data"), list):
        raise RuntimeError(f"unexpected provider payload: error={payload.get('error')}")
    return payload


def preflight_history_access(key: str | None = None, limiter: RateLimiter | None = None) -> dict[str, Any]:
    key = _require_key(key)
    limiter = limiter or RateLimiter()
    start, end = _season_window(SEASONS[0])
    payload = _request_page(
        key=key,
        league_id=LEAGUES["EPL"],
        start_time=start,
        end_time=end,
        page=1,
        per_page=1,
        limiter=limiter,
    )
    fixtures = [item for item in payload["data"] if isinstance(item, dict)]
    if not fixtures:
        raise HistoryPreflightFailed("earliest frozen season returned no finished fixture")
    parsed = normalize_fixture_market(fixtures[0], "EPL", SEASONS[0])
    if parsed is None:
        raise HistoryPreflightFailed("earliest frozen fixture did not expose parseable inline Bet365 opening corner odds")
    return {"status": "PASS", "league": "EPL", "season": SEASONS[0], "fixture_id": parsed["fixture_id"]}


def _coverage_report(rows: list[dict[str, Any]], fixture_counts: dict[tuple[str, str], int], request_count: int) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for league in LEAGUES:
        seasons: dict[str, Any] = {}
        for season in SEASONS:
            season_rows = [row for row in rows if row["league"] == league and row["season"] == season]
            fixture_count = fixture_counts.get((league, season), 0)
            kickoffs = sorted(row["kickoff_utc"] for row in season_rows)
            seasons[season] = {
                "finished_fixtures": fixture_count,
                "valid_opening_corner_markets": len(season_rows),
                "opening_market_coverage_rate": len(season_rows) / fixture_count if fixture_count else 0.0,
                "earliest_market_kickoff": kickoffs[0] if kickoffs else None,
                "latest_market_kickoff": kickoffs[-1] if kickoffs else None,
            }
        reports[league] = seasons
    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "acquisition_only": True,
        "model_evaluation_performed": False,
        "betting_enabled": False,
        "seasons": list(SEASONS),
        "league_reports": reports,
        "normalized_market_rows": len(rows),
        "provider_requests": request_count,
        "provider_request_budget": MAX_PROVIDER_REQUESTS,
        "status": "BACKFILL_COMPLETE",
    }


def run_backfill(output_dir: Path, key: str | None = None) -> dict[str, Any]:
    key = _require_key(key)
    limiter = RateLimiter()
    preflight = preflight_history_access(key, limiter)
    _write_json(output_dir / "preflight.json", preflight)
    request_count = 1
    normalized: list[dict[str, Any]] = []
    fixture_counts: dict[tuple[str, str], int] = {}

    for league, league_id in LEAGUES.items():
        for season in SEASONS:
            start, end = _season_window(season)
            page = 1
            season_fixture_ids: set[str] = set()
            while True:
                if request_count >= MAX_PROVIDER_REQUESTS:
                    raise RuntimeError("provider request budget exceeded")
                payload = _request_page(
                    key=key,
                    league_id=league_id,
                    start_time=start,
                    end_time=end,
                    page=page,
                    per_page=PER_PAGE,
                    limiter=limiter,
                )
                request_count += 1
                _write_json(output_dir / "raw" / league / season / f"page-{page}.json", payload)
                for fixture in payload["data"]:
                    if not isinstance(fixture, dict):
                        continue
                    fixture_id = str(fixture.get("id") or "").strip()
                    if fixture_id.isdigit():
                        season_fixture_ids.add(fixture_id)
                    row = normalize_fixture_market(fixture, league, season)
                    if row is not None:
                        normalized.append(row)
                pagination = payload.get("pagination") or {}
                if not bool(pagination.get("has_more")):
                    break
                page += 1
                if page > 50:
                    raise RuntimeError(f"unexpected pagination beyond 50 pages for {league} {season}")
            fixture_counts[(league, season)] = len(season_fixture_ids)

    normalized.sort(key=lambda row: (row["league"], row["season"], row["kickoff_utc"], int(row["fixture_id"])))
    normalized_path = output_dir / "normalized" / "bet365_corner_markets.jsonl"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    with normalized_path.open("w") as handle:
        for row in normalized:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    report = _coverage_report(normalized, fixture_counts, request_count)
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/five_dollar_corners_backfill_v1"))
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.preflight_only:
        print(json.dumps(preflight_history_access(), indent=2, sort_keys=True))
        return
    report = run_backfill(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
