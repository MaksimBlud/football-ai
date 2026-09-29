"""Zero-cost full-calendar load feasibility audit for the frozen V2B cohort.

Research-only. Reconstructs the exact 14-day pre-match schedule window by combining:
- public Understat league match dates for 2026/27;
- a frozen manifest of official non-league fixtures in the relevant 2026-09-05..18
  window (UEFA Champions League, UEFA Europa League, Carabao Cup, Coppa Italia).

No V2B market rows, centre_delta, target outcomes, betting, or provider odds calls.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from v2b_corners10_replay_feasibility import _validate_lock
from v2b_true_xg_replay_feasibility_v1 import (
    LEAGUE_SLUGS,
    fetch_understat_league,
    prepare_team_histories,
    resolve_team_title,
)

EXPERIMENT_ID = "V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1"
EXPECTED_LOCKED_FIXTURES = 43
LOOKBACK_DAYS = 14
SEASON = 2026

SOURCE_COVERAGE = {
    "UEFA_CHAMPIONS_LEAGUE_MD1": {
        "window": "2026-09-08..2026-09-10",
        "official_source": (
            "https://www.uefa.com/uefachampionsleague/news/"
            "02a8-2174c9e9019d-f909a77bd77a-1000--"
            "2026-27-champions-league-all-the-league-phase-fixtures/"
        ),
    },
    "UEFA_EUROPA_LEAGUE_MD1": {
        "window": "2026-09-16..2026-09-17",
        "official_source": (
            "https://www.uefa.com/uefaeuropaleague/news/"
            "02a8-2174cafa5bb6-82bbc20c9b92-1000--"
            "2026-27-europa-league-all-the-league-phase-fixtures/"
        ),
    },
    "CARABAO_CUP_R3": {
        "window": "2026-09-08..2026-09-17",
        "official_source": (
            "https://www.efl.com/news/2026/august/28/"
            "carabao-cup--third-round-dates-confirmed/"
        ),
    },
    "COPPA_ITALIA_SEDICESIMI": {
        "window": "2026-09-15",
        "official_source": (
            "https://www.legaseriea.it/coppa-italia/news/"
            "ecco-quando-si-giocano-i-sedicesimi"
        ),
    },
    "DFB_POKAL": {
        "window": "no fixtures inside 14-day target lookback; first round ended 2026-09-02",
        "official_source": (
            "https://www.dfb.de/news/dates-and-kick-off-times-confirmed-for-dfb-pokal-first-round"
        ),
    },
    "COPA_DEL_REY": {
        "window": "no professional-club fixtures before V2B targets; preliminary ties start 2026-09-26",
        "official_source": (
            "https://rfef.es/es/noticias/la-eliminatoria-previa-ya-tiene-emparejamientos"
        ),
    },
    "COUPE_DE_FRANCE": {
        "window": "no Ligue 1 entry before V2B targets; Ligue 1 enters 2026-12-20",
        "official_source": (
            "https://occitanie.fff.fr/simple/competitons-tirages-a-venir/"
        ),
    },
    "UEFA_CONFERENCE_LEAGUE": {
        "window": "league phase starts 2026-10-15, after V2B targets",
        "official_source": (
            "https://www.uefa.com/uefaconferenceleague/news/"
            "02a8-2174cb200f25-b94693ddff4e-1000--"
            "202627-conference-league-all-the-league-phase-fixtures/"
        ),
    },
}

# Frozen before any schedule-direction comparison.
# Only target-team participation is needed for load features; fixture_label preserves
# the official fixture identity for auditability.
NON_LEAGUE_FIXTURES: tuple[dict[str, Any], ...] = (
    # UEFA Champions League, Matchday 1.
    {"date": "2026-09-08", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Club Brugge vs Aston Villa", "target_teams": ["Aston Villa"]},
    {"date": "2026-09-08", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Borussia Dortmund vs Villarreal", "target_teams": ["Borussia Dortmund", "Villarreal"]},
    {"date": "2026-09-08", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Porto vs Manchester City", "target_teams": ["Man City"]},
    {"date": "2026-09-08", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Lille vs Real Betis", "target_teams": ["Lille", "Real Betis"]},
    {"date": "2026-09-08", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Real Madrid vs Inter", "target_teams": ["Real Madrid", "Inter Milan"]},
    {"date": "2026-09-09", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Barcelona vs Feyenoord", "target_teams": ["Barcelona"]},
    {"date": "2026-09-09", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Stuttgart vs Viking", "target_teams": ["VfB Stuttgart"]},
    {"date": "2026-09-09", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Liverpool vs Atletico Madrid", "target_teams": ["Liverpool", "Atletico Madrid"]},
    {"date": "2026-09-09", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Paris Saint-Germain vs Slovan Bratislava", "target_teams": ["PSG"]},
    {"date": "2026-09-09", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Napoli vs Arsenal", "target_teams": ["Napoli", "Arsenal"]},
    {"date": "2026-09-10", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Fenerbahce vs Roma", "target_teams": ["Roma"]},
    {"date": "2026-09-10", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Como vs RB Leipzig", "target_teams": ["Como", "RB Leipzig"]},
    {"date": "2026-09-10", "competition": "UEFA_CHAMPIONS_LEAGUE", "fixture_label": "Manchester United vs Sabah", "target_teams": ["Man Utd"]},

    # Carabao Cup Round 3.
    {"date": "2026-09-08", "competition": "CARABAO_CUP", "fixture_label": "Crystal Palace vs Middlesbrough", "target_teams": ["Crystal Palace"]},
    {"date": "2026-09-08", "competition": "CARABAO_CUP", "fixture_label": "Sunderland vs Hull City", "target_teams": ["Sunderland", "Hull"]},
    {"date": "2026-09-08", "competition": "CARABAO_CUP", "fixture_label": "Bournemouth vs Lincoln City", "target_teams": ["Bournemouth"]},
    {"date": "2026-09-08", "competition": "CARABAO_CUP", "fixture_label": "Millwall vs Newcastle United", "target_teams": ["Newcastle"]},
    {"date": "2026-09-09", "competition": "CARABAO_CUP", "fixture_label": "Chelsea vs Leeds United", "target_teams": ["Leeds"]},
    {"date": "2026-09-15", "competition": "CARABAO_CUP", "fixture_label": "Ipswich Town vs Arsenal", "target_teams": ["Ipswich", "Arsenal"]},
    {"date": "2026-09-15", "competition": "CARABAO_CUP", "fixture_label": "Liverpool vs Tottenham Hotspur", "target_teams": ["Liverpool", "Tottenham"]},
    {"date": "2026-09-15", "competition": "CARABAO_CUP", "fixture_label": "West Ham United vs Fulham", "target_teams": ["Fulham"]},
    {"date": "2026-09-16", "competition": "CARABAO_CUP", "fixture_label": "Everton vs Wolverhampton Wanderers", "target_teams": ["Everton"]},
    {"date": "2026-09-16", "competition": "CARABAO_CUP", "fixture_label": "Manchester United vs Brighton & Hove Albion", "target_teams": ["Man Utd", "Brighton"]},
    {"date": "2026-09-16", "competition": "CARABAO_CUP", "fixture_label": "Coventry City vs Aston Villa", "target_teams": ["Coventry", "Aston Villa"]},
    {"date": "2026-09-17", "competition": "CARABAO_CUP", "fixture_label": "Manchester City vs Norwich City", "target_teams": ["Man City"]},

    # UEFA Europa League, Matchday 1.
    {"date": "2026-09-16", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Omonia vs Celta", "target_teams": ["Celta Vigo"]},
    {"date": "2026-09-16", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Milan vs Benfica", "target_teams": ["AC Milan"]},
    {"date": "2026-09-16", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Leverkusen vs Celje", "target_teams": ["Bayer Leverkusen"]},
    {"date": "2026-09-16", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Anderlecht vs Lyon", "target_teams": ["Lyon"]},
    {"date": "2026-09-16", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Sturm Graz vs Rennes", "target_teams": ["Rennes"]},
    {"date": "2026-09-16", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Sunderland vs AZ Alkmaar", "target_teams": ["Sunderland"]},
    {"date": "2026-09-17", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "OFI Crete vs Hoffenheim", "target_teams": ["TSG Hoffenheim"]},
    {"date": "2026-09-17", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Besiktas vs Marseille", "target_teams": ["Marseille"]},
    {"date": "2026-09-17", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Crystal Palace vs Lech Poznan", "target_teams": ["Crystal Palace"]},
    {"date": "2026-09-17", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Juventus vs NEC Nijmegen", "target_teams": ["Juventus"]},
    {"date": "2026-09-17", "competition": "UEFA_EUROPA_LEAGUE", "fixture_label": "Real Sociedad vs Bournemouth", "target_teams": ["Real Sociedad", "Bournemouth"]},

    # Coppa Italia, fixtures inside the exact 14-day V2B target lookback.
    {"date": "2026-09-15", "competition": "COPPA_ITALIA", "fixture_label": "Genoa vs Sudtirol", "target_teams": ["Genoa"]},
    {"date": "2026-09-15", "competition": "COPPA_ITALIA", "fixture_label": "Fiorentina vs Pisa", "target_teams": ["Fiorentina"]},
)


def _date(value: Any) -> pd.Timestamp:
    stamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(stamp):
        raise ValueError(f"invalid date {value!r}")
    return pd.Timestamp(stamp).normalize()


def _league_dates_for_team(
    history: pd.DataFrame,
    *,
    target_kickoff_utc: str,
) -> list[pd.Timestamp]:
    target_date = _date(pd.Timestamp(target_kickoff_utc).tz_convert("UTC").tz_localize(None))
    dates = [
        _date(value)
        for value in history["match_date"].tolist()
        if _date(value) < target_date
    ]
    return sorted(set(dates))


def _nonleague_by_team() -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for fixture in NON_LEAGUE_FIXTURES:
        match_date = _date(fixture["date"])
        for team in fixture["target_teams"]:
            result.setdefault(str(team), []).append(
                {
                    "date": match_date,
                    "competition": fixture["competition"],
                    "fixture_label": fixture["fixture_label"],
                }
            )
    return result


def _snapshot(
    *,
    team: str,
    target_kickoff_utc: str,
    league_dates: list[pd.Timestamp],
    nonleague_events: list[dict[str, Any]],
) -> dict[str, Any]:
    target_date = _date(pd.Timestamp(target_kickoff_utc).tz_convert("UTC").tz_localize(None))
    start14 = target_date - pd.Timedelta(days=LOOKBACK_DAYS)
    start7 = target_date - pd.Timedelta(days=7)

    league_prior = sorted({d for d in league_dates if d < target_date})
    league14 = [d for d in league_prior if d >= start14]
    league7 = [d for d in league_prior if d >= start7]

    nonleague_prior = [
        e for e in nonleague_events
        if start14 <= e["date"] < target_date
    ]
    nonleague_dates = sorted({e["date"] for e in nonleague_prior})
    nonleague7 = [d for d in nonleague_dates if d >= start7]

    full_dates = sorted(set(league14) | set(nonleague_dates))
    last_league = league_prior[-1] if league_prior else None
    last_full = full_dates[-1] if full_dates else last_league

    league_rest = None if last_league is None else int((target_date - last_league).days)
    full_rest = None if last_full is None else int((target_date - last_full).days)

    return {
        "team": team,
        "target_date": target_date.strftime("%Y-%m-%d"),
        "league_previous_match_date": None if last_league is None else last_league.strftime("%Y-%m-%d"),
        "full_previous_match_date": None if last_full is None else last_full.strftime("%Y-%m-%d"),
        "league_rest_days": league_rest,
        "full_rest_days": full_rest,
        "league_matches_7d": len(league7),
        "full_matches_7d": len(set(league7) | set(nonleague7)),
        "league_matches_14d": len(league14),
        "full_matches_14d": len(full_dates),
        "nonleague_matches_7d": len(nonleague7),
        "nonleague_matches_14d": len(nonleague_dates),
        "nonleague_events_14d": [
            {
                "date": e["date"].strftime("%Y-%m-%d"),
                "competition": e["competition"],
                "fixture_label": e["fixture_label"],
            }
            for e in nonleague_prior
        ],
        "load_changed_vs_league_only": bool(
            full_rest != league_rest
            or len(set(league7) | set(nonleague7)) != len(league7)
            or len(full_dates) != len(league14)
        ),
    }


def audit_from_payloads(
    lock: dict[str, Any],
    payloads_by_league: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    targets = _validate_lock(lock)
    target_teams = {
        str(row["home_team"]) for row in targets
    } | {
        str(row["away_team"]) for row in targets
    }

    manifest_teams = {
        str(team)
        for fixture in NON_LEAGUE_FIXTURES
        for team in fixture["target_teams"]
    }
    unknown_manifest_teams = sorted(manifest_teams - target_teams)
    if unknown_manifest_teams:
        raise RuntimeError(
            "non-league manifest contains non-target teams: "
            + ",".join(unknown_manifest_teams)
        )

    histories_by_league: dict[str, dict[str, pd.DataFrame]] = {}
    titles_by_league: dict[str, list[str]] = {}
    source_summary: dict[str, Any] = {}
    for league in LEAGUE_SLUGS:
        payload = payloads_by_league.get(league)
        if not payload:
            source_summary[league] = {"status": "SOURCE_FETCH_FAILED"}
            continue
        histories, titles = prepare_team_histories([(SEASON, payload)])
        histories_by_league[league] = histories
        titles_by_league[league] = titles
        source_summary[league] = {
            "status": "SOURCE_READY",
            "source_team_count": len(titles),
            "valid_team_histories": len(histories),
            "valid_team_match_rows": int(sum(len(frame) for frame in histories.values())),
        }

    nonleague = _nonleague_by_team()
    rows: list[dict[str, Any]] = []
    identity_matched = 0
    team_sides_with_nonleague = 0
    fixtures_changed = 0

    for target in targets:
        league = str(target["league"])
        home = str(target["home_team"])
        away = str(target["away_team"])
        titles = titles_by_league.get(league, [])
        histories = histories_by_league.get(league, {})
        home_title = resolve_team_title(
            league=league, target_team=home, source_titles=titles
        )
        away_title = resolve_team_title(
            league=league, target_team=away, source_titles=titles
        )
        identity_ok = home_title is not None and away_title is not None
        if identity_ok:
            identity_matched += 1

        row: dict[str, Any] = {
            "fixture_id": str(target["fixture_id"]),
            "league": league,
            "kickoff_utc": str(target["kickoff_utc"]),
            "home_team": home,
            "away_team": away,
            "understat_home_team": home_title,
            "understat_away_team": away_title,
            "identity_status": "MATCHED" if identity_ok else "UNMATCHED",
        }

        if not identity_ok:
            row["full_calendar_feasible"] = False
            row["home_load"] = None
            row["away_load"] = None
        else:
            home_load = _snapshot(
                team=home,
                target_kickoff_utc=str(target["kickoff_utc"]),
                league_dates=_league_dates_for_team(
                    histories[home_title],
                    target_kickoff_utc=str(target["kickoff_utc"]),
                ),
                nonleague_events=nonleague.get(home, []),
            )
            away_load = _snapshot(
                team=away,
                target_kickoff_utc=str(target["kickoff_utc"]),
                league_dates=_league_dates_for_team(
                    histories[away_title],
                    target_kickoff_utc=str(target["kickoff_utc"]),
                ),
                nonleague_events=nonleague.get(away, []),
            )
            feasible = (
                home_load["league_previous_match_date"] is not None
                and away_load["league_previous_match_date"] is not None
            )
            row["full_calendar_feasible"] = bool(feasible)
            row["home_load"] = home_load
            row["away_load"] = away_load

            team_sides_with_nonleague += int(home_load["nonleague_matches_14d"] > 0)
            team_sides_with_nonleague += int(away_load["nonleague_matches_14d"] > 0)
            changed = bool(
                home_load["load_changed_vs_league_only"]
                or away_load["load_changed_vs_league_only"]
            )
            fixtures_changed += int(changed)

        rows.append(row)

    frame = pd.DataFrame(rows)
    if len(frame) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected V2B fixture count")
    if frame["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate V2B fixture ID")

    feasible_count = int(frame["full_calendar_feasible"].fillna(False).sum())
    by_league: dict[str, Any] = {}
    for league in LEAGUE_SLUGS:
        group = frame[frame["league"] == league]
        changed = 0
        for _, row in group.iterrows():
            if isinstance(row["home_load"], dict) and isinstance(row["away_load"], dict):
                changed += int(
                    row["home_load"]["load_changed_vs_league_only"]
                    or row["away_load"]["load_changed_vs_league_only"]
                )
        by_league[league] = {
            "locked_fixtures": int(len(group)),
            "identity_matched": int((group["identity_status"] == "MATCHED").sum()),
            "full_calendar_feasible": int(group["full_calendar_feasible"].fillna(False).sum()),
            "fixtures_changed_vs_league_only": int(changed),
        }

    if any(
        source_summary.get(league, {}).get("status") != "SOURCE_READY"
        for league in LEAGUE_SLUGS
    ):
        status = "SOURCE_FETCH_GAPS"
    elif identity_matched < EXPECTED_LOCKED_FIXTURES:
        status = "IDENTITY_GAPS"
    elif feasible_count == EXPECTED_LOCKED_FIXTURES:
        status = "FULL_43_RECONSTRUCTABLE_14D"
    else:
        status = "PARTIAL_FULL_CALENDAR_FEASIBILITY"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_audit": True,
        "lookback_days": LOOKBACK_DAYS,
        "league_source": "UNDERSTAT_PUBLIC_2026_27",
        "nonleague_manifest_frozen": True,
        "nonleague_manifest_fixture_count": len(NON_LEAGUE_FIXTURES),
        "source_coverage_contract": SOURCE_COVERAGE,
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "identity_matched_fixture_count": identity_matched,
        "full_calendar_feasible_fixture_count": feasible_count,
        "team_sides_with_nonleague_event_14d": int(team_sides_with_nonleague),
        "fixtures_changed_vs_league_only": int(fixtures_changed),
        "status": status,
        "market_rows_read": False,
        "v2b_odds_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "source_summary": source_summary,
        "by_league": by_league,
        "rows": rows,
    }


def run_live_audit(
    lock: dict[str, Any],
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    owned = session is None
    if session is None:
        session = requests.Session()
    payloads: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    try:
        for league in LEAGUE_SLUGS:
            try:
                payloads[league] = fetch_understat_league(
                    session,
                    league=league,
                    season=SEASON,
                )
            except Exception as exc:
                errors[league] = f"{type(exc).__name__}:{str(exc)[:300]}"
    finally:
        if owned:
            session.close()

    report = audit_from_payloads(lock, payloads)
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
