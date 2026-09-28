"""Zero-cost true-xG replay feasibility audit for the frozen V2B cohort.

Research only. Uses public Understat league history for prior completed matches.
No V2B market rows, no current target outcome fields and no direction statistic.
"""
from __future__ import annotations

import argparse
import json
import math
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from v2b_corners10_replay_feasibility import _validate_lock

EXPERIMENT_ID = "V2B_TRUE_XG5_REPLAY_FEASIBILITY_V1"
EXPECTED_LOCKED_FIXTURES = 43
SEASONS = (2025, 2026)
UNDERSTAT_URL = "https://understat.com/getLeagueData/{slug}/{season}"
LEAGUE_SLUGS = {
    "EPL": "EPL",
    "LA_LIGA": "La_liga",
    "SERIE_A": "Serie_A",
    "BUNDESLIGA": "Bundesliga",
    "LIGUE_1": "Ligue_1",
}

# Provider-lock identity -> Understat title where naming is known to differ.
# This is identity plumbing only; it never changes fixture eligibility by result.
TARGET_ALIASES = {
    "EPL": {
        "Man City": "Manchester City",
        "Man Utd": "Manchester United",
        "Newcastle": "Newcastle United",
        "Nottm Forest": "Nottingham Forest",
    },
    "LA_LIGA": {
        "CD Alaves": "Alaves",
    },
    "SERIE_A": {
        "Inter Milan": "Inter",
    },
    "BUNDESLIGA": {
        "Borussia M'gladbach": "Borussia M.Gladbach",
        "TSG Hoffenheim": "Hoffenheim",
    },
    "LIGUE_1": {
        "PSG": "Paris Saint Germain",
    },
}

XG_FIELDS = ("xG", "xGA", "npxG", "npxGA")


def _identity_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _finite_nonnegative(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def fetch_understat_league(
    session: requests.Session,
    *,
    league: str,
    season: int,
) -> dict[str, Any]:
    slug = LEAGUE_SLUGS[league]
    url = UNDERSTAT_URL.format(slug=slug, season=season)
    response = session.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 football-ai-xg-feasibility/1.0",
            "Referer": f"https://understat.com/league/{slug}/{season}",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("teams"), dict):
        raise ValueError(f"{league} {season}: invalid Understat league payload")
    return payload


def prepare_team_histories(
    payloads: list[tuple[int, dict[str, Any]]],
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    rows_by_team: dict[str, list[dict[str, Any]]] = {}
    titles: set[str] = set()

    for season, payload in payloads:
        for team_data in payload["teams"].values():
            title = str(team_data.get("title") or "").strip()
            if not title:
                continue
            titles.add(title)
            history = team_data.get("history") or []
            if not isinstance(history, list):
                continue
            for match in history:
                if not isinstance(match, dict):
                    continue
                date = pd.to_datetime(match.get("date"), errors="coerce")
                if pd.isna(date):
                    continue
                values = {field: _finite_nonnegative(match.get(field)) for field in XG_FIELDS}
                if any(values[field] is None for field in XG_FIELDS):
                    continue
                rows_by_team.setdefault(title, []).append(
                    {
                        "season_start": season,
                        "match_date": pd.Timestamp(date),
                        "venue": str(match.get("h_a") or ""),
                        "xg": values["xG"],
                        "xga": values["xGA"],
                        "npxg": values["npxG"],
                        "npxga": values["npxGA"],
                    }
                )

    histories = {
        title: pd.DataFrame(rows).drop_duplicates(
            subset=["season_start", "match_date", "venue"], keep="last"
        ).sort_values(["match_date", "season_start", "venue"], kind="stable")
        for title, rows in rows_by_team.items()
    }
    return histories, sorted(titles)


def resolve_team_title(
    *,
    league: str,
    target_team: str,
    source_titles: list[str],
) -> str | None:
    desired = TARGET_ALIASES.get(league, {}).get(target_team, target_team)
    desired_key = _identity_key(desired)
    matches = [title for title in source_titles if _identity_key(title) == desired_key]
    if len(matches) == 1:
        return matches[0]
    return None


def _prior_xg_snapshot(
    history: pd.DataFrame,
    *,
    target_kickoff_utc: str,
) -> dict[str, Any]:
    kickoff = pd.Timestamp(target_kickoff_utc)
    if kickoff.tzinfo is not None:
        kickoff = kickoff.tz_convert("UTC").tz_localize(None)
    prior = history[history["match_date"] < kickoff].sort_values(
        "match_date", kind="stable"
    )
    recent = prior.tail(5)
    record: dict[str, Any] = {
        "prior_valid_xg_matches": int(len(prior)),
        "xg5_feasible": bool(len(recent) >= 5),
    }
    if len(recent) >= 5:
        for column in ("xg", "xga", "npxg", "npxga"):
            record[f"{column}_last5"] = float(recent[column].mean())
    else:
        for column in ("xg", "xga", "npxg", "npxga"):
            record[f"{column}_last5"] = None
    return record


def audit_from_payloads(
    lock: dict[str, Any],
    payloads_by_league: dict[str, list[tuple[int, dict[str, Any]]]],
) -> dict[str, Any]:
    targets = _validate_lock(lock)
    source: dict[str, dict[str, Any]] = {}
    histories_by_league: dict[str, dict[str, pd.DataFrame]] = {}

    for league in LEAGUE_SLUGS:
        payloads = payloads_by_league.get(league)
        if not payloads:
            source[league] = {
                "status": "SOURCE_FETCH_FAILED",
                "source_team_titles": [],
                "team_count": 0,
                "valid_team_histories": 0,
            }
            continue
        histories, titles = prepare_team_histories(payloads)
        histories_by_league[league] = histories
        all_rows = sum(len(frame) for frame in histories.values())
        source[league] = {
            "status": "SOURCE_READY",
            "source_team_titles": titles,
            "team_count": len(titles),
            "valid_team_histories": len(histories),
            "valid_team_match_rows": int(all_rows),
            "seasons": [season for season, _ in payloads],
        }

    rows: list[dict[str, Any]] = []
    for target in targets:
        league = str(target["league"])
        home = str(target["home_team"])
        away = str(target["away_team"])
        titles = source.get(league, {}).get("source_team_titles", [])
        histories = histories_by_league.get(league, {})

        home_title = resolve_team_title(
            league=league, target_team=home, source_titles=titles
        )
        away_title = resolve_team_title(
            league=league, target_team=away, source_titles=titles
        )
        identity_ok = home_title is not None and away_title is not None

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

        if identity_ok:
            home_snapshot = _prior_xg_snapshot(
                histories[home_title],
                target_kickoff_utc=str(target["kickoff_utc"]),
            )
            away_snapshot = _prior_xg_snapshot(
                histories[away_title],
                target_kickoff_utc=str(target["kickoff_utc"]),
            )
            row.update(
                {
                    "home_prior_valid_xg_matches": home_snapshot[
                        "prior_valid_xg_matches"
                    ],
                    "away_prior_valid_xg_matches": away_snapshot[
                        "prior_valid_xg_matches"
                    ],
                    "home_xg5_feasible": home_snapshot["xg5_feasible"],
                    "away_xg5_feasible": away_snapshot["xg5_feasible"],
                    "both_teams_have_xg5": bool(
                        home_snapshot["xg5_feasible"]
                        and away_snapshot["xg5_feasible"]
                    ),
                }
            )
            for prefix, snapshot in (
                ("home", home_snapshot),
                ("away", away_snapshot),
            ):
                for name in ("xg", "xga", "npxg", "npxga"):
                    row[f"{prefix}_{name}_last5"] = snapshot[f"{name}_last5"]
        else:
            row.update(
                {
                    "home_prior_valid_xg_matches": None,
                    "away_prior_valid_xg_matches": None,
                    "home_xg5_feasible": False,
                    "away_xg5_feasible": False,
                    "both_teams_have_xg5": False,
                }
            )
            for prefix in ("home", "away"):
                for name in ("xg", "xga", "npxg", "npxga"):
                    row[f"{prefix}_{name}_last5"] = None
        rows.append(row)

    frame = pd.DataFrame(rows)
    if len(frame) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected frozen V2B target count")
    if frame["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate V2B fixture ID")

    matched = int((frame["identity_status"] == "MATCHED").sum())
    feasible = int(frame["both_teams_have_xg5"].sum())
    by_league: dict[str, Any] = {}
    for league in LEAGUE_SLUGS:
        group = frame[frame["league"] == league]
        by_league[league] = {
            "locked_fixtures": int(len(group)),
            "identity_matched": int((group["identity_status"] == "MATCHED").sum()),
            "xg5_feasible": int(group["both_teams_have_xg5"].sum()),
        }

    if any(source[league]["status"] != "SOURCE_READY" for league in LEAGUE_SLUGS):
        status = "SOURCE_FETCH_GAPS"
    elif matched < EXPECTED_LOCKED_FIXTURES:
        status = "IDENTITY_GAPS"
    elif feasible == EXPECTED_LOCKED_FIXTURES:
        status = "FULL_43_XG5_FEASIBLE"
    else:
        status = "PARTIAL_XG5_FEASIBLE"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_audit": True,
        "source": "UNDERSTAT_PUBLIC_LEAGUE_HISTORY",
        "seasons_requested": list(SEASONS),
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "identity_matched_fixture_count": matched,
        "xg5_feasible_fixture_count": feasible,
        "status": status,
        "market_rows_read": False,
        "v2b_odds_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "source_summary": source,
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

    payloads_by_league: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    errors: dict[str, list[str]] = {}
    try:
        for league in LEAGUE_SLUGS:
            items: list[tuple[int, dict[str, Any]]] = []
            for season in SEASONS:
                try:
                    payload = fetch_understat_league(
                        session,
                        league=league,
                        season=season,
                    )
                    items.append((season, payload))
                except Exception as exc:
                    errors.setdefault(league, []).append(
                        f"{season}:{type(exc).__name__}:{str(exc)[:300]}"
                    )
            if len(items) == len(SEASONS):
                payloads_by_league[league] = items
    finally:
        if owned:
            session.close()

    report = audit_from_payloads(lock, payloads_by_league)
    for league, league_errors in errors.items():
        report["source_summary"][league]["fetch_errors"] = league_errors
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
