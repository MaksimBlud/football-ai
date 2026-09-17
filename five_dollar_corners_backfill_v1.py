"""Historical Bet365 corner-market acquisition for CORNERS10_BET365_MARKET_V1.

Research-only. This module acquires provider history and coverage metadata only.
It never evaluates predictive metrics, betting returns, or production models.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

EXPERIMENT_ID = "CORNERS10_BET365_MARKET_V1"
ACQUISITION_ID = "FIVE_DOLLAR_CORNERS_BACKFILL_V1"
BASE_URL = "https://api.5dollarfootballapi.com"
KEY_ENV = "FIVE_DOLLAR_FOOTBALL_API_KEY"
LEAGUES = {
    "EPL": "4160026622",
    "LA_LIGA": "4212821298",
    "SERIE_A": "3405541143",
}
SEASONS = (
    "2016-17", "2017-18", "2018-19", "2019-20", "2020-21",
    "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
)
PER_PAGE = 50
MAX_PAGES_PER_LEAGUE_SEASON = 12
MAX_PROVIDER_REQUESTS = len(LEAGUES) * len(SEASONS) * MAX_PAGES_PER_LEAGUE_SEASON + 1
REQUEST_INTERVAL_SECONDS = 1.6
MIN_FINISHED_FIXTURES_PER_SEASON = 300
PROBE_LEAGUE = "EPL"
PROBE_SEASON = "2016-17"


def _require_key(key: str | None = None) -> str:
    value = (key or os.getenv(KEY_ENV, "")).strip()
    if not value:
        raise RuntimeError(f"{KEY_ENV} is required; refusing provider access without an explicit key")
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _number(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _season_window(season: str) -> tuple[int, int]:
    if season not in SEASONS:
        raise ValueError(f"season outside frozen V1: {season}")
    start_year = int(season[:4])
    start = datetime(start_year, 7, 1, tzinfo=timezone.utc)
    end = datetime(start_year + 1, 7, 1, tzinfo=timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


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
    if isinstance(odds, dict) and isinstance(odds.get("bookmakers"), list):
        return [x for x in odds["bookmakers"] if isinstance(x, dict)]
    return []


def normalize_inline_corner_market(
    fixture: dict[str, Any], league: str, season: str
) -> dict[str, Any] | None:
    """Normalize one inline Bet365 full-time corner opening/closing snapshot."""
    if str(fixture.get("status") or "").lower() != "finished":
        return None
    fixture_id = str(fixture.get("id") or "").strip()
    league_obj = fixture.get("league") or {}
    teams = fixture.get("teams") or {}
    home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
    away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
    kickoff = str(fixture.get("kickoff_utc") or "").strip()
    if (
        not fixture_id.isdigit()
        or str((league_obj or {}).get("id") or "") != LEAGUES[league]
        or not home
        or not away
        or not kickoff
    ):
        return None

    bet365 = next(
        (b for b in _inline_bookmakers(fixture) if str(b.get("slug") or "").lower() == "bet365"),
        None,
    )
    if bet365 is None:
        return None
    bookmaker_odds = bet365.get("odds")
    if not isinstance(bookmaker_odds, dict):
        return None
    corner = bookmaker_odds.get("corner_line")
    if not isinstance(corner, dict):
        return None
    opening = _valid_stage(corner.get("opening"))
    if opening is None:
        return None
    closing = _valid_stage(corner.get("closing"))

    row = {
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
        "source": "5DOLLARFOOTBALLAPI",
    }
    if closing is not None:
        row.update(
            {
                "closing_line": closing["line"],
                "closing_over": closing["over"],
                "closing_under": closing["under"],
            }
        )
    else:
        row.update({"closing_line": None, "closing_over": None, "closing_under": None})
    return row


def _safe_error_payload(response: requests.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except Exception:
        body = {"message": response.text[:500]}
    return {"http_status": response.status_code, "body": body}


def probe_history_access(output_dir: Path, key: str | None = None) -> dict[str, Any]:
    """Use one request to verify whether the frozen old-history window is legally exposed."""
    key = _require_key(key)
    start_ts, end_ts = _season_window(PROBE_SEASON)
    response = requests.get(
        f"{BASE_URL}/v1/leagues/{LEAGUES[PROBE_LEAGUE]}/fixtures",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        params={
            "start_time": start_ts,
            "end_time": end_ts,
            "status": "finished",
            "include": "odds",
            "order": "asc",
            "page": 1,
            "per_page": PER_PAGE,
        },
        timeout=30,
    )

    if response.status_code == 403:
        payload = _safe_error_payload(response)
        report = {
            "acquisition_id": ACQUISITION_ID,
            "experiment_id": EXPERIMENT_ID,
            "probe_league": PROBE_LEAGUE,
            "probe_season": PROBE_SEASON,
            "provider_requests": 1,
            "research_only": True,
            "model_evaluation_performed": False,
            "betting_enabled": False,
            "status": "HISTORY_ACCESS_BLOCKED_BY_PLAN",
            "provider_response": payload,
        }
        _write_json(output_dir / "entitlement_probe.json", report)
        return report

    response.raise_for_status()
    payload = response.json()
    _write_json(output_dir / "raw" / "entitlement_probe_page.json", payload)
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = data if isinstance(data, list) else []
    normalized = [normalize_inline_corner_market(x, PROBE_LEAGUE, PROBE_SEASON) for x in rows if isinstance(x, dict)]
    corner_rows = [x for x in normalized if x is not None]
    status = "HISTORY_ACCESS_CONFIRMED" if rows else "HISTORY_ACCESS_UNCONFIRMED_EMPTY"
    report = {
        "acquisition_id": ACQUISITION_ID,
        "experiment_id": EXPERIMENT_ID,
        "probe_league": PROBE_LEAGUE,
        "probe_season": PROBE_SEASON,
        "provider_requests": 1,
        "research_only": True,
        "model_evaluation_performed": False,
        "betting_enabled": False,
        "status": status,
        "returned_fixtures": len(rows),
        "returned_bet365_corner_rows": len(corner_rows),
    }
    _write_json(output_dir / "entitlement_probe.json", report)
    return report


def _request_page(
    *, league: str, season: str, page: int, key: str
) -> tuple[dict[str, Any], requests.Response]:
    start_ts, end_ts = _season_window(season)
    response = requests.get(
        f"{BASE_URL}/v1/leagues/{LEAGUES[league]}/fixtures",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        params={
            "start_time": start_ts,
            "end_time": end_ts,
            "status": "finished",
            "include": "odds",
            "order": "asc",
            "page": page,
            "per_page": PER_PAGE,
        },
        timeout=30,
    )
    if response.status_code == 403:
        raise RuntimeError(
            f"{league} {season}: provider denied requested historical window/include=odds: "
            f"{_safe_error_payload(response)}"
        )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("success") != 1:
        raise RuntimeError(f"{league} {season}: invalid provider envelope")
    return payload, response


def _season_complete(finished_fixtures: int) -> bool:
    return finished_fixtures >= MIN_FINISHED_FIXTURES_PER_SEASON


def run_backfill(output_dir: Path, key: str | None = None) -> dict[str, Any]:
    key = _require_key(key)
    probe = probe_history_access(output_dir, key)
    if probe["status"] != "HISTORY_ACCESS_CONFIRMED":
        raise RuntimeError(
            "Frozen historical window is not exposed by the current plan; refusing a shortened backfill"
        )

    provider_requests = int(probe["provider_requests"])
    normalized_rows: list[dict[str, Any]] = []
    coverage: dict[str, dict[str, Any]] = {}

    for league in LEAGUES:
        coverage[league] = {}
        for season in SEASONS:
            fixture_count = 0
            market_count = 0
            half_line_count = 0
            page = 1
            while True:
                if page > MAX_PAGES_PER_LEAGUE_SEASON:
                    raise RuntimeError(f"{league} {season}: pagination exceeded safety cap")
                if provider_requests >= MAX_PROVIDER_REQUESTS:
                    raise RuntimeError("provider request safety budget exceeded")
                payload, _ = _request_page(league=league, season=season, page=page, key=key)
                provider_requests += 1
                _write_json(output_dir / "raw" / league / season / f"page_{page:02d}.json", payload)
                data = payload.get("data")
                if not isinstance(data, list):
                    raise RuntimeError(f"{league} {season}: data must be a list")

                for fixture in data:
                    if not isinstance(fixture, dict):
                        continue
                    fixture_count += 1
                    row = normalize_inline_corner_market(fixture, league, season)
                    if row is not None:
                        normalized_rows.append(row)
                        market_count += 1
                        if abs((row["opening_line"] % 1.0) - 0.5) < 1e-9:
                            half_line_count += 1

                pagination = payload.get("pagination") or {}
                has_more = bool(pagination.get("has_more")) if isinstance(pagination, dict) else False
                if not has_more:
                    break
                page += 1
                time.sleep(REQUEST_INTERVAL_SECONDS)

            coverage[league][season] = {
                "finished_fixtures": fixture_count,
                "bet365_corner_opening_rows": market_count,
                "opening_half_line_rows": half_line_count,
                "season_complete": _season_complete(fixture_count),
            }
            if not _season_complete(fixture_count):
                _write_json(
                    output_dir / "coverage_partial.json",
                    {
                        "acquisition_id": ACQUISITION_ID,
                        "experiment_id": EXPERIMENT_ID,
                        "provider_requests": provider_requests,
                        "coverage": coverage,
                        "status": "INCOMPLETE_HISTORY_WINDOW",
                        "model_evaluation_performed": False,
                    },
                )
                raise RuntimeError(
                    f"{league} {season}: only {fixture_count} finished fixtures; refusing silent partial history"
                )

    normalized_path = output_dir / "normalized" / "bet365_corner_opening_closing.jsonl"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    with normalized_path.open("w") as handle:
        for row in normalized_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    report = {
        "acquisition_id": ACQUISITION_ID,
        "experiment_id": EXPERIMENT_ID,
        "provider_requests": provider_requests,
        "provider_request_budget": MAX_PROVIDER_REQUESTS,
        "research_only": True,
        "model_evaluation_performed": False,
        "betting_enabled": False,
        "seasons": list(SEASONS),
        "leagues": list(LEAGUES),
        "normalized_market_rows": len(normalized_rows),
        "coverage": coverage,
        "status": "BACKFILL_COMPLETE",
    }
    _write_json(output_dir / "coverage_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/five_dollar_corners_backfill_v1"),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.probe_only:
        report = probe_history_access(args.output_dir)
    else:
        report = run_backfill(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
