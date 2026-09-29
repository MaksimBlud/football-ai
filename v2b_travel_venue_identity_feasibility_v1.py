"""Audit venue/route identity feasibility for frozen V2B travel research.

Research-only. This block does NOT compute kilometers and does NOT read market direction.

It reconstructs the immediately previous competitive fixture for each of the 86
team-sides in the frozen 43-match V2B cohort using:
- Football-Data 2026/27 league result CSVs for league fixtures;
- the already-frozen official non-league manifest from
  V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1.

For each side it identifies:
- previous fixture date and competition;
- HOME/AWAY role;
- previous fixture venue identity (the fixture home team);
- target fixture venue identity (the V2B home team).

This is the prerequisite source layer for a later coordinate/distance audit.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from v2b_corners10_replay_feasibility import _validate_lock
from v2b_full_calendar_load_feasibility_v1 import NON_LEAGUE_FIXTURES

EXPERIMENT_ID = "V2B_TRAVEL_VENUE_IDENTITY_FEASIBILITY_V1"
EXPECTED_LOCKED_FIXTURES = 43
EXPECTED_TEAM_SIDES = 86
SEASON_CODE = "2627"

LEAGUE_CODES = {
    "EPL": "E0",
    "LA_LIGA": "SP1",
    "SERIE_A": "I1",
    "BUNDESLIGA": "D1",
    "LIGUE_1": "F1",
}

FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"

TARGET_VARIANTS: dict[str, tuple[str, ...]] = {
    "Man City": ("Manchester City",),
    "Man Utd": ("Manchester United", "Man United"),
    "Newcastle": ("Newcastle United",),
    "Nottm Forest": ("Nottingham Forest", "Nott'm Forest"),
    "Brighton": ("Brighton & Hove Albion", "Brighton and Hove Albion"),
    "Bournemouth": ("AFC Bournemouth",),
    "Ipswich": ("Ipswich Town",),
    "Hull": ("Hull City",),
    "Coventry": ("Coventry City",),
    "Leeds": ("Leeds United",),
    "Tottenham": ("Tottenham Hotspur",),
    "Athletic Club": ("Athletic Bilbao", "Ath Bilbao"),
    "Atletico Madrid": ("Atlético Madrid", "Ath Madrid", "Atl Madrid"),
    "CD Alaves": ("Alaves", "Deportivo Alaves"),
    "Deportivo A Coruna": ("Deportivo La Coruna", "La Coruna"),
    "Celta Vigo": ("Celta",),
    "Racing Santander": ("Santander",),
    "Rayo Vallecano": ("Vallecano",),
    "Real Betis": ("Betis",),
    "Real Sociedad": ("Sociedad",),
    "AC Milan": ("Milan",),
    "Inter Milan": ("Inter",),
    "Roma": ("AS Roma",),
    "Bayer Leverkusen": ("Leverkusen",),
    "Borussia Dortmund": ("Dortmund",),
    "Borussia M'gladbach": ("M'gladbach", "Borussia M.Gladbach"),
    "Eintracht Frankfurt": ("Ein Frankfurt",),
    "SC Freiburg": ("Freiburg",),
    "TSG Hoffenheim": ("Hoffenheim",),
    "VfB Stuttgart": ("Stuttgart",),
    "Cologne": ("FC Koln", "FC Cologne", "Koln", "Köln"),
    "Schalke": ("Schalke 04",),
    "Hamburg": ("Hamburger SV",),
    "Mainz": ("Mainz 05",),
    "RB Leipzig": ("RasenBallsport Leipzig",),
    "PSG": ("Paris Saint-Germain", "Paris Saint Germain", "Paris SG"),
}


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _variant_keys(target: str) -> set[str]:
    values = {target, *TARGET_VARIANTS.get(target, ())}
    return {_key(value) for value in values if str(value).strip()}


def _matches_target(target: str, source_name: Any) -> bool:
    return _key(source_name) in _variant_keys(target)


def _resolve_target(source_name: Any, targets: set[str]) -> str | None:
    matches = sorted(target for target in targets if _matches_target(target, source_name))
    if len(matches) == 1:
        return matches[0]
    return None


def _parse_date(value: Any) -> pd.Timestamp | None:
    stamp = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(stamp):
        return None
    return pd.Timestamp(stamp).normalize()


def _parse_fixture_label(label: str) -> tuple[str, str]:
    parts = re.split(r"\s+vs\s+", str(label).strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise RuntimeError(f"cannot parse fixture label: {label!r}")
    return parts[0].strip(), parts[1].strip()


def _league_events(
    *,
    league: str,
    frame: pd.DataFrame,
    targets: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    required = {"Date", "HomeTeam", "AwayTeam"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"{league}: league source missing {sorted(missing)}")

    events: list[dict[str, Any]] = []
    resolved_source_names: set[str] = set()
    unresolved_source_names: set[str] = set()

    for _, row in frame.iterrows():
        match_date = _parse_date(row["Date"])
        if match_date is None:
            continue
        home_raw = str(row["HomeTeam"]).strip()
        away_raw = str(row["AwayTeam"]).strip()
        if not home_raw or not away_raw:
            continue

        home_target = _resolve_target(home_raw, targets)
        away_target = _resolve_target(away_raw, targets)

        for raw, resolved in ((home_raw, home_target), (away_raw, away_target)):
            if resolved is not None:
                resolved_source_names.add(raw)
            elif raw:
                unresolved_source_names.add(raw)

        if home_target is not None:
            events.append(
                {
                    "team": home_target,
                    "date": match_date,
                    "competition": "LEAGUE",
                    "source": "FOOTBALL_DATA_CSV",
                    "role": "HOME",
                    "home_label": home_raw,
                    "away_label": away_raw,
                    "venue_label": home_raw,
                    "opponent_label": away_raw,
                }
            )
        if away_target is not None:
            events.append(
                {
                    "team": away_target,
                    "date": match_date,
                    "competition": "LEAGUE",
                    "source": "FOOTBALL_DATA_CSV",
                    "role": "AWAY",
                    "home_label": home_raw,
                    "away_label": away_raw,
                    "venue_label": home_raw,
                    "opponent_label": home_raw,
                }
            )

    return events, {
        "league": league,
        "source_rows": int(len(frame)),
        "resolved_source_team_names": sorted(resolved_source_names),
        "unresolved_source_team_names": sorted(unresolved_source_names),
    }


def _nonleague_events(targets: set[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for fixture in NON_LEAGUE_FIXTURES:
        match_date = _parse_date(fixture["date"])
        if match_date is None:
            raise RuntimeError("invalid frozen non-league fixture date")
        home_raw, away_raw = _parse_fixture_label(str(fixture["fixture_label"]))

        for target in fixture.get("target_teams") or []:
            target = str(target)
            if target not in targets:
                continue
            home_match = _matches_target(target, home_raw)
            away_match = _matches_target(target, away_raw)
            if home_match == away_match:
                raise RuntimeError(
                    f"cannot resolve frozen non-league role for {target}: "
                    f"{fixture['fixture_label']}"
                )
            role = "HOME" if home_match else "AWAY"
            events.append(
                {
                    "team": target,
                    "date": match_date,
                    "competition": str(fixture["competition"]),
                    "source": "FROZEN_OFFICIAL_NONLEAGUE_MANIFEST",
                    "role": role,
                    "home_label": home_raw,
                    "away_label": away_raw,
                    "venue_label": home_raw,
                    "opponent_label": away_raw if role == "HOME" else home_raw,
                }
            )
    return events


def _latest_prior_event(
    *,
    team: str,
    target_kickoff_utc: str,
    events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    kickoff = pd.Timestamp(target_kickoff_utc)
    if kickoff.tzinfo is not None:
        kickoff = kickoff.tz_convert("UTC").tz_localize(None)
    target_date = kickoff.normalize()
    candidates = [
        event for event in events
        if event["team"] == team and event["date"] < target_date
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            item["date"],
            1 if item["source"] == "FROZEN_OFFICIAL_NONLEAGUE_MANIFEST" else 0,
            item["competition"],
            item["home_label"],
            item["away_label"],
        )
    )
    return candidates[-1]


def audit_from_frames(
    lock: dict[str, Any],
    league_frames: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    targets = _validate_lock(lock)
    all_target_teams = {
        str(row["home_team"]) for row in targets
    } | {
        str(row["away_team"]) for row in targets
    }
    targets_by_league = {
        league: {
            str(row["home_team"])
            for row in targets
            if str(row["league"]) == league
        } | {
            str(row["away_team"])
            for row in targets
            if str(row["league"]) == league
        }
        for league in LEAGUE_CODES
    }

    all_events: list[dict[str, Any]] = []
    source_summary: dict[str, Any] = {}
    for league in LEAGUE_CODES:
        frame = league_frames.get(league)
        if frame is None:
            source_summary[league] = {"status": "SOURCE_FETCH_FAILED"}
            continue
        league_events, summary = _league_events(
            league=league,
            frame=frame,
            targets=targets_by_league[league],
        )
        all_events.extend(league_events)
        source_summary[league] = {
            "status": "SOURCE_READY",
            **summary,
            "target_team_count": len(targets_by_league[league]),
            "target_teams_with_any_league_event": len(
                {event["team"] for event in league_events}
            ),
        }

    nonleague_events = _nonleague_events(all_target_teams)
    all_events.extend(nonleague_events)

    rows: list[dict[str, Any]] = []
    side_count = 0
    resolved_sides = 0
    previous_away_sides = 0
    previous_nonleague_sides = 0
    venue_identity_changed_sides = 0
    fixtures_both_sides_resolved = 0

    for fixture in targets:
        fixture_rows: list[dict[str, Any]] = []
        target_home = str(fixture["home_team"])
        for target_role, team in (
            ("HOME", target_home),
            ("AWAY", str(fixture["away_team"])),
        ):
            side_count += 1
            event = _latest_prior_event(
                team=team,
                target_kickoff_utc=str(fixture["kickoff_utc"]),
                events=all_events,
            )
            record: dict[str, Any] = {
                "fixture_id": str(fixture["fixture_id"]),
                "league": str(fixture["league"]),
                "kickoff_utc": str(fixture["kickoff_utc"]),
                "target_team": team,
                "target_role": target_role,
                "target_venue_label": target_home,
                "previous_event_resolved": event is not None,
            }
            if event is None:
                record.update(
                    {
                        "previous_event_date": None,
                        "previous_event_source": None,
                        "previous_competition": None,
                        "previous_role": None,
                        "previous_home_label": None,
                        "previous_away_label": None,
                        "previous_venue_label": None,
                        "previous_opponent_label": None,
                        "previous_event_was_away": None,
                        "venue_transition_identity_feasible": False,
                        "venue_identity_changed": None,
                    }
                )
            else:
                resolved_sides += 1
                previous_away = event["role"] == "AWAY"
                previous_nonleague = event["source"] == "FROZEN_OFFICIAL_NONLEAGUE_MANIFEST"
                venue_changed = not _matches_target(
                    target_home,
                    event["venue_label"],
                )
                previous_away_sides += int(previous_away)
                previous_nonleague_sides += int(previous_nonleague)
                venue_identity_changed_sides += int(venue_changed)
                record.update(
                    {
                        "previous_event_date": event["date"].strftime("%Y-%m-%d"),
                        "previous_event_source": event["source"],
                        "previous_competition": event["competition"],
                        "previous_role": event["role"],
                        "previous_home_label": event["home_label"],
                        "previous_away_label": event["away_label"],
                        "previous_venue_label": event["venue_label"],
                        "previous_opponent_label": event["opponent_label"],
                        "previous_event_was_away": previous_away,
                        "venue_transition_identity_feasible": True,
                        "venue_identity_changed": venue_changed,
                    }
                )
            fixture_rows.append(record)
            rows.append(record)

        if all(row["venue_transition_identity_feasible"] for row in fixture_rows):
            fixtures_both_sides_resolved += 1

    if len(targets) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected frozen V2B fixture count")
    if side_count != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected team-side count")

    by_league: dict[str, Any] = {}
    frame = pd.DataFrame(rows)
    for league in LEAGUE_CODES:
        group = frame[frame["league"] == league]
        by_league[league] = {
            "team_sides": int(len(group)),
            "previous_event_resolved": int(group["previous_event_resolved"].sum()),
            "previous_event_away": int(
                group["previous_event_was_away"].fillna(False).sum()
            ),
            "previous_event_nonleague": int(
                (group["previous_event_source"] == "FROZEN_OFFICIAL_NONLEAGUE_MANIFEST").sum()
            ),
            "venue_identity_changed": int(
                group["venue_identity_changed"].fillna(False).sum()
            ),
        }

    source_ready = all(
        source_summary.get(league, {}).get("status") == "SOURCE_READY"
        for league in LEAGUE_CODES
    )
    if not source_ready:
        status = "SOURCE_FETCH_GAPS"
    elif resolved_sides == EXPECTED_TEAM_SIDES:
        status = "FULL_86_VENUE_IDENTITY_FEASIBLE"
    else:
        status = "PARTIAL_VENUE_IDENTITY_FEASIBILITY"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_audit": True,
        "season_code": SEASON_CODE,
        "league_source": "FOOTBALL_DATA_CSV_2026_27",
        "league_source_urls": {
            league: FOOTBALL_DATA_URL.format(season=SEASON_CODE, code=code)
            for league, code in LEAGUE_CODES.items()
        },
        "nonleague_source": "FROZEN_OFFICIAL_NONLEAGUE_MANIFEST",
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "team_side_count": EXPECTED_TEAM_SIDES,
        "previous_event_resolved_team_sides": resolved_sides,
        "fixtures_with_both_sides_resolved": fixtures_both_sides_resolved,
        "previous_event_away_team_sides": previous_away_sides,
        "previous_event_nonleague_team_sides": previous_nonleague_sides,
        "venue_identity_changed_team_sides": venue_identity_changed_sides,
        "status": status,
        "coordinate_layer_applied": False,
        "distance_km_computed": False,
        "market_rows_read": False,
        "v2b_odds_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "source_summary": source_summary,
        "nonleague_event_rows": len(nonleague_events),
        "by_league": by_league,
        "rows": rows,
    }


def fetch_league_frames(
    *,
    session: requests.Session | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "football-ai-v2b-travel-venue-feasibility/1.0"}
        )
    frames: dict[str, pd.DataFrame] = {}
    errors: dict[str, str] = {}
    try:
        for league, code in LEAGUE_CODES.items():
            url = FOOTBALL_DATA_URL.format(season=SEASON_CODE, code=code)
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()
                frames[league] = pd.read_csv(StringIO(response.text))
            except Exception as exc:
                errors[league] = f"{type(exc).__name__}:{str(exc)[:300]}"
    finally:
        if owned:
            session.close()
    return frames, errors


def run_live_audit(
    lock: dict[str, Any],
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    frames, errors = fetch_league_frames(session=session)
    report = audit_from_frames(lock, frames)
    for league, error in errors.items():
        report["source_summary"].setdefault(league, {})["fetch_error"] = error
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lock = json.loads(args.lock_manifest.read_text(encoding="utf-8"))
    report = run_live_audit(lock)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
