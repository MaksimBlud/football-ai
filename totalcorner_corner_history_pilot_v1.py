"""Frozen acquisition-only TotalCorner corner-history pilot V1.

The pilot qualifies source coverage only. It does not evaluate football models,
betting returns, market edge, or match outcomes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from totalcorner_corner_history import BASE_URL, TOKEN_ENV, normalize_corner_history

EXPERIMENT_ID = "TOTALCORNER_CORNER_HISTORY_PILOT_V1"
PILOT_DATES = ("20250523", "20250524", "20250525")
LEAGUES = {
    "EPL": "1",
    "SERIE_A": "3",
    "LA_LIGA": "5",
}
FIXTURES_PER_LEAGUE = 10
COVERAGE_PASS_MIN = 8
MAX_ODDS_REQUESTS = len(LEAGUES) * FIXTURES_PER_LEAGUE
REQUEST_INTERVAL_SECONDS = 2.1


@dataclass
class RateLimiter:
    interval_seconds: float = REQUEST_INTERVAL_SECONDS
    _last_request_at: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self._last_request_at is not None:
            remaining = self.interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = time.monotonic()


def _require_token(token: str | None = None) -> str:
    value = (token or os.getenv(TOKEN_ENV, "")).strip()
    if not value:
        raise RuntimeError(
            f"{TOKEN_ENV} is required; refusing to run the TotalCorner pilot without an explicit token"
        )
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _get_json(
    url: str,
    *,
    token: str,
    limiter: RateLimiter,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    limiter.wait()
    safe_params = dict(params or {})
    safe_params["token"] = token
    response = requests.get(url, params=safe_params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("success") != 1:
        raise RuntimeError(f"TotalCorner API error: {payload.get('error')}")
    return payload


def extract_schedule_matches(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("success") != 1:
        raise ValueError(f"TotalCorner schedule failure: {payload.get('error')}")
    data = payload.get("data")
    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict):
        matches = data.get("matches", [])
    else:
        raise ValueError("unexpected TotalCorner schedule data shape")
    if not isinstance(matches, list):
        raise ValueError("schedule matches must be a list")
    return [match for match in matches if isinstance(match, dict)]


def schedule_has_next_page(payload: dict[str, Any]) -> bool:
    pagination = payload.get("pagination") or {}
    return bool(pagination.get("next"))


def select_pilot_fixtures(
    payloads: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_league: dict[str, dict[str, dict[str, Any]]] = {league: {} for league in LEAGUES}
    id_to_league = {league_id: league for league, league_id in LEAGUES.items()}

    for payload in payloads:
        for match in extract_schedule_matches(payload):
            league = id_to_league.get(str(match.get("l_id") or ""))
            if league is None:
                continue
            match_id = str(match.get("id") or "").strip()
            kickoff = str(match.get("start") or "").strip()
            home = str(match.get("h") or "").strip()
            away = str(match.get("a") or "").strip()
            if not (match_id.isdigit() and kickoff and home and away):
                continue
            by_league[league].setdefault(
                match_id,
                {
                    "match_id": match_id,
                    "league": league,
                    "league_id": LEAGUES[league],
                    "kickoff": kickoff,
                    "home_team": home,
                    "away_team": away,
                },
            )

    selected: dict[str, list[dict[str, Any]]] = {}
    for league, matches in by_league.items():
        ordered = sorted(matches.values(), key=lambda row: (row["kickoff"], int(row["match_id"])))
        selected[league] = ordered[:FIXTURES_PER_LEAGUE]
    return selected


def build_coverage_summary(
    selected: dict[str, list[dict[str, Any]]],
    normalized_by_match: dict[str, list[dict[str, Any]]],
    errors_by_match: dict[str, str] | None = None,
) -> dict[str, Any]:
    errors_by_match = errors_by_match or {}
    league_reports: dict[str, Any] = {}

    for league in LEAGUES:
        fixtures = selected.get(league, [])
        fixture_reports = []
        covered = 0
        for fixture in fixtures:
            match_id = fixture["match_id"]
            rows = normalized_by_match.get(match_id, [])
            is_covered = len(rows) > 0
            covered += int(is_covered)
            fixture_reports.append(
                {
                    **fixture,
                    "covered": is_covered,
                    "valid_pre_match_snapshots": len(rows),
                    "error": errors_by_match.get(match_id),
                }
            )

        enough_fixtures = len(fixtures) == FIXTURES_PER_LEAGUE
        status = (
            "PASS"
            if enough_fixtures and covered >= COVERAGE_PASS_MIN
            else "INSUFFICIENT_FIXTURES"
            if not enough_fixtures
            else "FAIL"
        )
        league_reports[league] = {
            "selected_fixtures": len(fixtures),
            "covered_fixtures": covered,
            "coverage_rate": covered / len(fixtures) if fixtures else 0.0,
            "status": status,
            "fixtures": fixture_reports,
        }

    qualified = all(report["status"] == "PASS" for report in league_reports.values())
    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "acquisition_only": True,
        "betting_enabled": False,
        "model_evaluation_performed": False,
        "pilot_dates": list(PILOT_DATES),
        "fixtures_per_league": FIXTURES_PER_LEAGUE,
        "coverage_pass_min": COVERAGE_PASS_MIN,
        "league_reports": league_reports,
        "decision": "SOURCE_QUALIFIED" if qualified else "SOURCE_NOT_QUALIFIED",
    }


def run_pilot(output_dir: Path, token: str | None = None) -> dict[str, Any]:
    token = _require_token(token)
    limiter = RateLimiter()
    schedule_payloads: list[dict[str, Any]] = []

    for date in PILOT_DATES:
        page = 1
        while True:
            payload = _get_json(
                f"{BASE_URL}/match/schedule",
                token=token,
                limiter=limiter,
                params={"date": date, "page": page},
            )
            _write_json(output_dir / "raw" / "schedule" / f"{date}-page-{page}.json", payload)
            schedule_payloads.append(payload)
            if not schedule_has_next_page(payload):
                break
            page += 1
            if page > 50:
                raise RuntimeError(f"{date}: refusing unexpected schedule pagination beyond 50 pages")

    selected = select_pilot_fixtures(schedule_payloads)
    _write_json(output_dir / "selected_fixtures.json", selected)

    normalized_by_match: dict[str, list[dict[str, Any]]] = {}
    errors_by_match: dict[str, str] = {}
    normalized_rows: list[dict[str, Any]] = []
    odds_requests = 0

    for league in LEAGUES:
        for fixture in selected.get(league, []):
            if odds_requests >= MAX_ODDS_REQUESTS:
                raise RuntimeError("odds-history request budget exceeded")
            match_id = fixture["match_id"]
            odds_requests += 1
            try:
                payload = _get_json(
                    f"{BASE_URL}/match/odds/{match_id}",
                    token=token,
                    limiter=limiter,
                    params={"columns": "cornerList"},
                )
                _write_json(output_dir / "raw" / "odds" / f"{match_id}.json", payload)
                rows = normalize_corner_history(payload)
                normalized_by_match[match_id] = rows
                normalized_rows.extend(rows)
            except Exception as exc:  # fail closed per fixture and preserve the error in the report
                normalized_by_match[match_id] = []
                errors_by_match[match_id] = f"{type(exc).__name__}: {exc}"
                _write_json(
                    output_dir / "raw" / "odds" / f"{match_id}-error.json",
                    {"match_id": match_id, "error": errors_by_match[match_id]},
                )

    normalized_path = output_dir / "normalized" / "pre_match_corner_snapshots.jsonl"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    with normalized_path.open("w") as handle:
        for row in normalized_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = build_coverage_summary(selected, normalized_by_match, errors_by_match)
    summary["schedule_requests"] = len(schedule_payloads)
    summary["odds_history_requests"] = odds_requests
    summary["odds_history_request_budget"] = MAX_ODDS_REQUESTS
    _write_json(output_dir / "report.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/totalcorner_corner_history_pilot_v1"),
    )
    args = parser.parse_args()
    report = run_pilot(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
