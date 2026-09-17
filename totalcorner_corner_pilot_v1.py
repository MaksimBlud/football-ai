"""Acquisition-only TotalCorner historical corner source pilot.

The pilot qualifies source coverage and fixture identity only. It never computes
model, betting, edge, ROI, or outcome-prediction metrics.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests

import cross_league_direct_markets_v1 as direct
from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from team_names import normalize_team_name
from totalcorner_corner_history import BASE_URL, TOKEN_ENV, normalize_corner_history

EXPERIMENT_ID = "TOTALCORNER_CORNER_PILOT_V1"
LEAGUE_IDS = {"EPL": "1", "LA_LIGA": "14", "SERIE_A": "12"}
SEASON = "2025-2026"
SEASON_START = datetime(2025, 8, 1)
SEASON_END = datetime(2026, 6, 15, 23, 59, 59)
SAMPLE_SIZE = 10
MIN_COVERED = 8
MAX_SCHEDULE_PAGES = 40
MIN_REQUEST_INTERVAL_SECONDS = 2.05

_SOURCE_ALIASES = {
    "AC Milan": "Milan",
    "Inter Milan": "Inter",
    "Internazionale": "Inter",
    "Athletic Club": "Ath Bilbao",
    "Atletico Madrid": "Ath Madrid",
    "Atl Madrid": "Ath Madrid",
    "Nottm Forest": "Nott'm Forest",
    "Nottingham Forest": "Nott'm Forest",
    "Man Utd": "Man United",
    "Manchester United": "Man United",
    "Manchester City": "Man City",
    "Tottenham Hotspur": "Tottenham",
    "Newcastle United": "Newcastle",
    "Leeds United": "Leeds",
    "Hull City": "Hull",
}


def _parse_ts(value: str) -> datetime:
    return datetime.strptime(str(value).strip(), "%Y-%m-%d %H:%M:%S")


def _team_key(value: str) -> str:
    name = _SOURCE_ALIASES.get(str(value).strip(), str(value).strip())
    name = normalize_team_name(name)
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


class TotalCornerClient:
    """Minimal official API client with fail-closed token gate and pacing."""

    def __init__(
        self,
        token: str | None = None,
        *,
        min_interval_seconds: float = MIN_REQUEST_INTERVAL_SECONDS,
        get: Callable[..., Any] = requests.get,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.token = (token or os.getenv(TOKEN_ENV, "")).strip()
        if not self.token:
            raise RuntimeError(
                f"{TOKEN_ENV} is required; refusing TotalCorner pilot before any HTTP request"
            )
        self.min_interval_seconds = float(min_interval_seconds)
        self._get = get
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request_at: float | None = None

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        now = self._monotonic()
        if self._last_request_at is not None:
            wait = self.min_interval_seconds - (now - self._last_request_at)
            if wait > 0:
                self._sleep(wait)
        query = {"token": self.token, **(params or {})}
        response = self._get(f"{BASE_URL}{path}", params=query, timeout=30)
        self._last_request_at = self._monotonic()
        response.raise_for_status()
        payload = response.json()
        if payload.get("success") != 1:
            raise RuntimeError(f"TotalCorner API error: {payload.get('error') or {}}")
        return payload


def _schedule_matches(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("league schedule payload.data must be an object")
    matches = data.get("matches")
    if not isinstance(matches, list):
        raise ValueError("league schedule payload.data.matches must be a list")
    return [row for row in matches if isinstance(row, dict)]


def _eligible_schedule_row(row: dict[str, Any], league_id: str) -> dict[str, Any] | None:
    match_id = str(row.get("id") or "").strip()
    home = str(row.get("h") or "").strip()
    away = str(row.get("a") or "").strip()
    start_raw = str(row.get("start") or "").strip()
    if not (match_id.isdigit() and home and away and start_raw):
        return None
    if row.get("l_id") not in (None, "", league_id, int(league_id)):
        return None
    try:
        kickoff = _parse_ts(start_raw)
    except ValueError:
        return None
    if kickoff < SEASON_START or kickoff > SEASON_END:
        return None
    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "kickoff": start_raw,
        "league_id": league_id,
    }


def discover_sample(
    client: TotalCornerClient,
    league: str,
    raw_dir: Path,
    *,
    max_pages: int = MAX_SCHEDULE_PAGES,
) -> list[dict[str, Any]]:
    league_id = LEAGUE_IDS[league]
    found: dict[str, dict[str, Any]] = {}
    seen_target_window = False
    for page in range(1, max_pages + 1):
        payload = client.get_json(
            f"/league/schedule/{league_id}",
            params={"page": page},
        )
        _json_write(raw_dir / league / "schedule" / f"page_{page:03d}.json", payload)
        page_rows = _schedule_matches(payload)
        page_dates: list[datetime] = []
        for row in page_rows:
            try:
                page_dates.append(_parse_ts(str(row.get("start") or "")))
            except ValueError:
                pass
            eligible = _eligible_schedule_row(row, league_id)
            if eligible is not None:
                seen_target_window = True
                found[eligible["match_id"]] = eligible
        pagination = payload.get("pagination") or {}
        if pagination.get("next") is False:
            break
        if seen_target_window and page_dates and max(page_dates) < SEASON_START:
            break

    selected = sorted(
        found.values(),
        key=lambda row: (_parse_ts(row["kickoff"]), int(row["match_id"])),
        reverse=True,
    )[:SAMPLE_SIZE]
    return selected


def _football_data_fixture_manifest(league: str) -> list[dict[str, Any]]:
    config = direct.LEAGUES[league]
    code = next(
        code
        for code, season in config.historical_source.season_codes.items()
        if season == SEASON
    )
    url = direct.BASE.format(code=code, comp=config.historical_source.competition_code)
    response = _official_or_pinned_mirror_get(url, timeout=60)
    response.raise_for_status()
    frame = pd.read_csv(pd.io.common.BytesIO(response.content))
    frame["match_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    manifest: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        if pd.isna(row["match_date"]):
            continue
        manifest.append(
            {
                "date": row["match_date"].to_pydatetime().date(),
                "home_team": str(row["HomeTeam"]),
                "away_team": str(row["AwayTeam"]),
                "home_key": _team_key(str(row["HomeTeam"])),
                "away_key": _team_key(str(row["AwayTeam"])),
            }
        )
    return manifest


def reconcile_fixture(
    fixture: dict[str, Any],
    football_data_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    kickoff_date = _parse_ts(fixture["kickoff"]).date()
    home_key = _team_key(fixture["home_team"])
    away_key = _team_key(fixture["away_team"])
    candidates = []
    for row in football_data_manifest:
        if row["home_key"] != home_key or row["away_key"] != away_key:
            continue
        if abs((row["date"] - kickoff_date).days) <= 1:
            candidates.append(row)
    if len(candidates) != 1:
        return {
            "identity_ok": False,
            "candidate_count": len(candidates),
            "football_data_home": None,
            "football_data_away": None,
            "football_data_date": None,
        }
    match = candidates[0]
    return {
        "identity_ok": True,
        "candidate_count": 1,
        "football_data_home": match["home_team"],
        "football_data_away": match["away_team"],
        "football_data_date": match["date"].isoformat(),
    }


def run_pilot(
    output_dir: Path,
    *,
    token: str | None = None,
    client: TotalCornerClient | None = None,
    manifest_loader: Callable[[str], list[dict[str, Any]]] = _football_data_fixture_manifest,
) -> dict[str, Any]:
    # Constructing the client is deliberately first: missing token fails before
    # TotalCorner or Football-Data network access.
    client = client or TotalCornerClient(token)
    raw_dir = output_dir / "raw"
    normalized_dir = output_dir / "normalized"
    league_reports: list[dict[str, Any]] = []

    for league in LEAGUE_IDS:
        selected = discover_sample(client, league, raw_dir)
        manifest = manifest_loader(league)
        normalized_rows: list[dict[str, Any]] = []
        fixture_reports: list[dict[str, Any]] = []

        for fixture in selected:
            identity = reconcile_fixture(fixture, manifest)
            payload = client.get_json(
                f"/match/odds/{fixture['match_id']}",
                params={"columns": "cornerList"},
            )
            _json_write(
                raw_dir / league / "odds" / f"{fixture['match_id']}.json",
                payload,
            )
            rows = normalize_corner_history(payload)
            for row in rows:
                row = {**row, "project_league": league}
                normalized_rows.append(row)
            fixture_reports.append(
                {
                    **fixture,
                    **identity,
                    "valid_pre_match_snapshots": len(rows),
                    "has_valid_pre_match_snapshot": bool(rows),
                }
            )

        normalized_path = normalized_dir / f"{league.lower()}.jsonl"
        normalized_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in normalized_rows)
        )

        selected_count = len(selected)
        covered_count = sum(
            int(row["has_valid_pre_match_snapshot"]) for row in fixture_reports
        )
        identity_ok_count = sum(int(row["identity_ok"]) for row in fixture_reports)
        passed = bool(
            selected_count == SAMPLE_SIZE
            and covered_count >= MIN_COVERED
            and identity_ok_count == SAMPLE_SIZE
        )
        league_reports.append(
            {
                "league": league,
                "totalcorner_league_id": LEAGUE_IDS[league],
                "selected_count": selected_count,
                "covered_count": covered_count,
                "identity_ok_count": identity_ok_count,
                "coverage_threshold": MIN_COVERED,
                "sample_size": SAMPLE_SIZE,
                "status": "PASS" if passed else "FAIL",
                "fixtures": fixture_reports,
            }
        )

    overall_pass = all(row["status"] == "PASS" for row in league_reports)
    report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "acquisition_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "season": SEASON,
        "sample_size_per_league": SAMPLE_SIZE,
        "minimum_covered_per_league": MIN_COVERED,
        "league_reports": league_reports,
        "decision": "PASS_SOURCE_PILOT" if overall_pass else "FAIL_SOURCE_PILOT",
        "model_metrics_computed": False,
    }
    _json_write(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/totalcorner_corner_pilot_v1"),
    )
    args = parser.parse_args()
    report = run_pilot(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
