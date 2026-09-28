"""Zero-cost Understat tactical-pressure feasibility for frozen V2B fixtures.

Research-only source audit. Uses prior completed-match Understat fields:
- deep / deep_allowed;
- ppda / ppda_allowed.

No V2B market rows, opening lines, centre_delta, or direction statistics are read.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from v2b_corners10_replay_feasibility import _validate_lock
from v2b_true_xg_replay_feasibility_v1 import (
    LEAGUE_SLUGS,
    SEASONS,
    fetch_understat_league,
    resolve_team_title,
)

EXPERIMENT_ID = "V2B_UNDERSTAT_TACTICAL_PRESSURE5_FEASIBILITY_V1"
EXPECTED_LOCKED_FIXTURES = 43
TACTICAL_FIELDS = ("deep", "deep_allowed", "ppda", "ppda_allowed")


def _finite_nonnegative(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _ppda_ratio(value: Any) -> float | None:
    """Normalize Understat PPDA payload to one positive numeric ratio.

    Understat history payloads may expose ppda as a dict with attack-pass
    numerator and defensive-action denominator. Numeric payloads are also
    accepted fail-closed.
    """
    if isinstance(value, dict):
        att = _finite_nonnegative(value.get("att"))
        deff = _finite_nonnegative(value.get("def"))
        if att is None or deff is None or deff <= 0:
            return None
        return float(att / deff)
    number = _finite_nonnegative(value)
    if number is None or number <= 0:
        return None
    return number


def prepare_tactical_histories(
    payloads: list[tuple[int, dict[str, Any]]],
) -> tuple[dict[str, pd.DataFrame], list[str], dict[str, Any]]:
    rows_by_team: dict[str, list[dict[str, Any]]] = {}
    titles: set[str] = set()
    history_keys_seen: set[str] = set()
    total_history_rows = 0
    valid_rows = 0

    for season, payload in payloads:
        teams = payload.get("teams")
        if not isinstance(teams, dict):
            continue
        for team_data in teams.values():
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
                total_history_rows += 1
                history_keys_seen.update(str(key) for key in match.keys())
                date = pd.to_datetime(match.get("date"), errors="coerce")
                if pd.isna(date):
                    continue

                deep = _finite_nonnegative(match.get("deep"))
                deep_allowed = _finite_nonnegative(match.get("deep_allowed"))
                ppda = _ppda_ratio(match.get("ppda"))
                ppda_allowed = _ppda_ratio(match.get("ppda_allowed"))
                if any(
                    value is None
                    for value in (deep, deep_allowed, ppda, ppda_allowed)
                ):
                    continue

                valid_rows += 1
                rows_by_team.setdefault(title, []).append(
                    {
                        "season_start": season,
                        "match_date": pd.Timestamp(date),
                        "venue": str(match.get("h_a") or ""),
                        "deep": deep,
                        "deep_allowed": deep_allowed,
                        "ppda": ppda,
                        "ppda_allowed": ppda_allowed,
                    }
                )

    histories = {
        title: pd.DataFrame(rows)
        .drop_duplicates(
            subset=["season_start", "match_date", "venue"],
            keep="last",
        )
        .sort_values(["match_date", "season_start", "venue"], kind="stable")
        for title, rows in rows_by_team.items()
    }
    capability = {
        "history_keys_seen": sorted(history_keys_seen),
        "required_fields_seen": {
            field: field in history_keys_seen for field in TACTICAL_FIELDS
        },
        "total_history_rows": int(total_history_rows),
        "valid_tactical_rows": int(valid_rows),
    }
    return histories, sorted(titles), capability


def _prior_snapshot(
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
    result: dict[str, Any] = {
        "prior_valid_tactical_matches": int(len(prior)),
        "tactical5_feasible": bool(len(recent) >= 5),
    }
    for column in TACTICAL_FIELDS:
        result[f"{column}_last5"] = (
            float(recent[column].mean()) if len(recent) >= 5 else None
        )
    return result


def audit_from_payloads(
    lock: dict[str, Any],
    payloads_by_league: dict[str, list[tuple[int, dict[str, Any]]]],
) -> dict[str, Any]:
    targets = _validate_lock(lock)
    source_summary: dict[str, dict[str, Any]] = {}
    histories_by_league: dict[str, dict[str, pd.DataFrame]] = {}

    for league in LEAGUE_SLUGS:
        payloads = payloads_by_league.get(league)
        if not payloads:
            source_summary[league] = {
                "status": "SOURCE_FETCH_FAILED",
                "source_team_titles": [],
                "team_count": 0,
                "valid_team_histories": 0,
                "valid_tactical_rows": 0,
                "required_fields_seen": {
                    field: False for field in TACTICAL_FIELDS
                },
            }
            continue
        histories, titles, capability = prepare_tactical_histories(payloads)
        histories_by_league[league] = histories
        required_ok = all(capability["required_fields_seen"].values())
        source_summary[league] = {
            "status": (
                "SOURCE_READY" if required_ok else "TACTICAL_SCHEMA_GAP"
            ),
            "source_team_titles": titles,
            "team_count": len(titles),
            "valid_team_histories": len(histories),
            "seasons": [season for season, _ in payloads],
            **capability,
        }

    rows: list[dict[str, Any]] = []
    for target in targets:
        league = str(target["league"])
        home = str(target["home_team"])
        away = str(target["away_team"])
        titles = source_summary.get(league, {}).get("source_team_titles", [])
        histories = histories_by_league.get(league, {})

        home_title = resolve_team_title(
            league=league,
            target_team=home,
            source_titles=titles,
        )
        away_title = resolve_team_title(
            league=league,
            target_team=away,
            source_titles=titles,
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

        if identity_ok and home_title in histories and away_title in histories:
            home_snapshot = _prior_snapshot(
                histories[home_title],
                target_kickoff_utc=str(target["kickoff_utc"]),
            )
            away_snapshot = _prior_snapshot(
                histories[away_title],
                target_kickoff_utc=str(target["kickoff_utc"]),
            )
            row.update(
                {
                    "home_prior_valid_tactical_matches": home_snapshot[
                        "prior_valid_tactical_matches"
                    ],
                    "away_prior_valid_tactical_matches": away_snapshot[
                        "prior_valid_tactical_matches"
                    ],
                    "home_tactical5_feasible": home_snapshot["tactical5_feasible"],
                    "away_tactical5_feasible": away_snapshot["tactical5_feasible"],
                    "both_teams_have_tactical5": bool(
                        home_snapshot["tactical5_feasible"]
                        and away_snapshot["tactical5_feasible"]
                    ),
                }
            )
            for prefix, snapshot in (
                ("home", home_snapshot),
                ("away", away_snapshot),
            ):
                for field in TACTICAL_FIELDS:
                    row[f"{prefix}_{field}_last5"] = snapshot[
                        f"{field}_last5"
                    ]
        else:
            row.update(
                {
                    "home_prior_valid_tactical_matches": None,
                    "away_prior_valid_tactical_matches": None,
                    "home_tactical5_feasible": False,
                    "away_tactical5_feasible": False,
                    "both_teams_have_tactical5": False,
                }
            )
            for prefix in ("home", "away"):
                for field in TACTICAL_FIELDS:
                    row[f"{prefix}_{field}_last5"] = None
        rows.append(row)

    frame = pd.DataFrame(rows)
    if len(frame) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected frozen V2B fixture count")
    if frame["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate V2B fixture ID")

    matched = int((frame["identity_status"] == "MATCHED").sum())
    feasible = int(frame["both_teams_have_tactical5"].sum())
    by_league: dict[str, Any] = {}
    for league in LEAGUE_SLUGS:
        group = frame[frame["league"] == league]
        by_league[league] = {
            "locked_fixtures": int(len(group)),
            "identity_matched": int((group["identity_status"] == "MATCHED").sum()),
            "tactical5_feasible": int(group["both_teams_have_tactical5"].sum()),
        }

    schema_ready = all(
        item.get("status") == "SOURCE_READY"
        for item in source_summary.values()
    )
    if not schema_ready:
        status = "TACTICAL_SCHEMA_OR_SOURCE_GAPS"
    elif matched < EXPECTED_LOCKED_FIXTURES:
        status = "IDENTITY_GAPS"
    elif feasible == EXPECTED_LOCKED_FIXTURES:
        status = "FULL_43_TACTICAL5_FEASIBLE"
    else:
        status = "PARTIAL_TACTICAL5_FEASIBLE"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_audit": True,
        "source": "UNDERSTAT_PUBLIC_LEAGUE_HISTORY",
        "candidate_family": "PRIOR_MATCH_DEEP_PPDA_TACTICAL_PRESSURE",
        "seasons_requested": list(SEASONS),
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "identity_matched_fixture_count": matched,
        "tactical5_feasible_fixture_count": feasible,
        "status": status,
        "market_rows_read": False,
        "v2b_odds_read": False,
        "opening_lambda_read": False,
        "fair_centre_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
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
        session.headers.update(
            {"User-Agent": "football-ai-v2b-understat-tactical-feasibility/1.0"}
        )

    payloads_by_league: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    errors: dict[str, list[str]] = {}
    try:
        for league in LEAGUE_SLUGS:
            items: list[tuple[int, dict[str, Any]]] = []
            for season in SEASONS:
                try:
                    items.append(
                        (
                            season,
                            fetch_understat_league(
                                session,
                                league=league,
                                season=season,
                            ),
                        )
                    )
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
