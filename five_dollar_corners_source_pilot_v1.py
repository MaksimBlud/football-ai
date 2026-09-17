"""Acquisition-only 5DollarFootballAPI bookmaker-corners source pilot V1.

This module qualifies source coverage only. It never evaluates CORNERS10,
match outcomes, betting returns, or production models.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import requests

EXPERIMENT_ID = "FIVE_DOLLAR_CORNERS_SOURCE_PILOT_V1"
BASE_URL = "https://api.5dollarfootballapi.com"
KEY_ENV = "FIVE_DOLLAR_FOOTBALL_API_KEY"
LEAGUES = {
    "EPL": "4160026622",
    "LA_LIGA": "4212821298",
    "SERIE_A": "3405541143",
}
FIXTURES_PER_LEAGUE = 5
COVERAGE_PASS_MIN = 4
MAX_PROVIDER_REQUESTS = 18
REQUEST_INTERVAL_SECONDS = 0.5


def _require_key(key: str | None = None) -> str:
    value = (key or os.getenv(KEY_ENV, "")).strip()
    if not value:
        raise RuntimeError(
            f"{KEY_ENV} is required; refusing to call 5DollarFootballAPI without an explicit key"
        )
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


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
    if line is None or over is None or under is None:
        return None
    if over <= 1.0 or under <= 1.0:
        return None
    return {"line": line, "over": over, "under": under}


def normalize_corner_odds(payload: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any] | None:
    """Return one normalized Bet365 opening/closing corner row, or None."""
    if payload.get("success") != 1:
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    bookmakers = data.get("bookmakers")
    if not isinstance(bookmakers, list):
        return None

    bet365 = None
    for bookmaker in bookmakers:
        if isinstance(bookmaker, dict) and str(bookmaker.get("slug") or "").lower() == "bet365":
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
    closing = _valid_stage(corner_line.get("closing"))
    if opening is None or closing is None:
        return None

    return {
        "fixture_id": str(fixture["fixture_id"]),
        "league": fixture["league"],
        "league_id": fixture["league_id"],
        "kickoff_utc": fixture["kickoff_utc"],
        "home_team": fixture["home_team"],
        "away_team": fixture["away_team"],
        "bookmaker": "bet365",
        "opening_line": opening["line"],
        "opening_over": opening["over"],
        "opening_under": opening["under"],
        "closing_line": closing["line"],
        "closing_over": closing["over"],
        "closing_under": closing["under"],
        "source": "5DOLLARFOOTBALLAPI",
    }


def select_fixtures(payload: dict[str, Any], league: str) -> list[dict[str, Any]]:
    if payload.get("success") != 1:
        raise ValueError(f"{league}: fixture-list API failure")
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError(f"{league}: fixture-list data must be a list")

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in data:
        if not isinstance(raw, dict) or str(raw.get("status") or "").lower() != "finished":
            continue
        fixture_id = str(raw.get("id") or "").strip()
        league_obj = raw.get("league") or {}
        teams = raw.get("teams") or {}
        home = (teams.get("home") or {}).get("name") if isinstance(teams, dict) else None
        away = (teams.get("away") or {}).get("name") if isinstance(teams, dict) else None
        kickoff = str(raw.get("kickoff_utc") or "").strip()
        if not fixture_id.isdigit() or fixture_id in seen or not kickoff or not home or not away:
            continue
        if str((league_obj or {}).get("id") or "") != LEAGUES[league]:
            continue
        seen.add(fixture_id)
        selected.append(
            {
                "fixture_id": fixture_id,
                "league": league,
                "league_id": LEAGUES[league],
                "kickoff_utc": kickoff,
                "home_team": str(home),
                "away_team": str(away),
            }
        )
        if len(selected) == FIXTURES_PER_LEAGUE:
            break
    return selected


def build_report(
    selected: dict[str, list[dict[str, Any]]],
    normalized: dict[str, dict[str, Any] | None],
    errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    errors = errors or {}
    league_reports: dict[str, Any] = {}
    for league in LEAGUES:
        fixtures = selected.get(league, [])
        rows = []
        covered = 0
        for fixture in fixtures:
            fixture_id = fixture["fixture_id"]
            row = normalized.get(fixture_id)
            is_covered = row is not None
            covered += int(is_covered)
            rows.append({**fixture, "covered": is_covered, "error": errors.get(fixture_id)})

        enough = len(fixtures) == FIXTURES_PER_LEAGUE
        status = (
            "PASS"
            if enough and covered >= COVERAGE_PASS_MIN
            else "INSUFFICIENT_FIXTURES"
            if not enough
            else "FAIL"
        )
        league_reports[league] = {
            "selected_fixtures": len(fixtures),
            "covered_fixtures": covered,
            "coverage_rate": covered / len(fixtures) if fixtures else 0.0,
            "status": status,
            "fixtures": rows,
        }

    qualified = all(item["status"] == "PASS" for item in league_reports.values())
    return {
        "experiment_id": EXPERIMENT_ID,
        "provider": "5DollarFootballAPI",
        "research_only": True,
        "acquisition_only": True,
        "betting_enabled": False,
        "model_evaluation_performed": False,
        "fixtures_per_league": FIXTURES_PER_LEAGUE,
        "coverage_pass_min": COVERAGE_PASS_MIN,
        "league_reports": league_reports,
        "decision": "SOURCE_QUALIFIED_FOR_BACKFILL" if qualified else "SOURCE_NOT_QUALIFIED",
    }


def run_pilot(output_dir: Path, key: str | None = None) -> dict[str, Any]:
    key = _require_key(key)
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    request_count = 0
    selected: dict[str, list[dict[str, Any]]] = {}

    for league, league_id in LEAGUES.items():
        if request_count >= MAX_PROVIDER_REQUESTS:
            raise RuntimeError("provider request budget exceeded before fixture enumeration")
        response = requests.get(
            f"{BASE_URL}/v1/leagues/{league_id}/fixtures",
            headers=headers,
            params={"status": "finished", "order": "desc", "per_page": FIXTURES_PER_LEAGUE},
            timeout=30,
        )
        request_count += 1
        response.raise_for_status()
        payload = response.json()
        _write_json(output_dir / "raw" / "fixtures" / f"{league}.json", payload)
        selected[league] = select_fixtures(payload, league)
        time.sleep(REQUEST_INTERVAL_SECONDS)

    _write_json(output_dir / "selected_fixtures.json", selected)

    normalized_by_id: dict[str, dict[str, Any] | None] = {}
    errors: dict[str, str] = {}
    normalized_rows: list[dict[str, Any]] = []

    for league in LEAGUES:
        for fixture in selected.get(league, []):
            if request_count >= MAX_PROVIDER_REQUESTS:
                raise RuntimeError("provider request budget exceeded")
            fixture_id = fixture["fixture_id"]
            try:
                response = requests.get(
                    f"{BASE_URL}/v1/fixtures/{fixture_id}/odds",
                    headers=headers,
                    params={"market": "corner"},
                    timeout=30,
                )
                request_count += 1
                response.raise_for_status()
                payload = response.json()
                _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)
                row = normalize_corner_odds(payload, fixture)
                normalized_by_id[fixture_id] = row
                if row is not None:
                    normalized_rows.append(row)
                else:
                    errors[fixture_id] = "missing_or_invalid_bet365_opening_closing_corner_market"
            except Exception as exc:
                normalized_by_id[fixture_id] = None
                errors[fixture_id] = f"{type(exc).__name__}: {exc}"
                _write_json(
                    output_dir / "raw" / "odds" / f"{fixture_id}-error.json",
                    {"fixture_id": fixture_id, "error": errors[fixture_id]},
                )
            time.sleep(REQUEST_INTERVAL_SECONDS)

    normalized_path = output_dir / "normalized" / "bet365_corner_opening_closing.jsonl"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    with normalized_path.open("w") as handle:
        for row in normalized_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    report = build_report(selected, normalized_by_id, errors)
    report["provider_requests"] = request_count
    report["provider_request_budget"] = MAX_PROVIDER_REQUESTS
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/five_dollar_corners_source_pilot_v1"),
    )
    args = parser.parse_args()
    report = run_pilot(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
