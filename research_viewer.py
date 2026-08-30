"""Read-only data assembly for the Research Viewer.

This module never writes to Supabase, never loads production model artifacts,
and never triggers prediction/training code. It only projects canonical ledger
and finished-result state for human inspection.

Settlement identity intentionally mirrors ``evaluate_league_predictions``:
league-local match date plus normalized home/away team names. The viewer also
uses the canonical latest eligible pre-kickoff snapshot per league/event.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from league_config import get_league_config
from team_names import normalize_team_name


LEDGER_COLUMNS = (
    "prediction_key,league,event_id,home_team,away_team,kickoff_utc,"
    "prediction_time_utc,snapshot_time_utc,hours_to_kickoff,"
    "market_home_prob,market_draw_prob,market_away_prob,market_pick,"
    "market_pick_probability,structural_status,structural_home_prob,"
    "structural_draw_prob,structural_away_prob,structural_pick,"
    "structural_pick_probability,structural_score,structural_applied,"
    "prediction_mode,observation_key"
)

RESULT_COLUMNS = (
    "league,season,match_date,home_team,away_team,home_goals,away_goals,result"
)

ACTIVE_LEAGUES = (
    "EPL",
    "LA_LIGA",
    "RPL",
    "SERIE_A",
    "BUNDESLIGA",
    "LIGUE_1",
    "EREDIVISIE",
)


def _utc(value: Any) -> pd.Timestamp:
    return pd.to_datetime(value, utc=True, errors="coerce")


def _team_key(value: Any) -> str:
    return normalize_team_name(str(value))


def _result_key(row: pd.Series) -> tuple[str, str, str, str]:
    date_value = pd.to_datetime(row["match_date"], errors="coerce")
    date_text = date_value.date().isoformat() if pd.notna(date_value) else ""
    return (
        str(row["league"]),
        _team_key(row["home_team"]),
        _team_key(row["away_team"]),
        date_text,
    )


def _ledger_result_key(row: pd.Series) -> tuple[str, str, str, str]:
    league = str(row["league"])
    kickoff = _utc(row["kickoff_utc"])
    if pd.isna(kickoff):
        date_text = ""
    else:
        timezone_name = get_league_config(league).timezone
        date_text = kickoff.tz_convert(timezone_name).date().isoformat()
    return (
        league,
        _team_key(row["home_team"]),
        _team_key(row["away_team"]),
        date_text,
    )


def _prob(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def _iso(value: Any) -> str | None:
    timestamp = _utc(value)
    return timestamp.isoformat() if pd.notna(timestamp) else None


def assemble_viewer_payload(
    ledger_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a human-facing snapshot from canonical read-only records."""

    now_ts = pd.Timestamp(now or datetime.now(timezone.utc))
    if now_ts.tzinfo is None:
        now_ts = now_ts.tz_localize("UTC")
    else:
        now_ts = now_ts.tz_convert("UTC")

    ledger = pd.DataFrame(ledger_rows)
    results = pd.DataFrame(result_rows)

    if ledger.empty:
        return {
            "generated_at_utc": now_ts.isoformat(),
            "active_leagues": list(ACTIVE_LEAGUES),
            "summary": {
                "predictions": 0,
                "upcoming": 0,
                "settled": 0,
                "awaiting_result": 0,
            },
            "matches": [],
        }

    required = {
        "prediction_key",
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "prediction_time_utc",
        "snapshot_time_utc",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "market_pick",
        "prediction_mode",
    }
    missing = required - set(ledger.columns)
    if missing:
        raise ValueError("Missing ledger columns: " + ", ".join(sorted(missing)))

    ledger["kickoff_utc"] = pd.to_datetime(
        ledger["kickoff_utc"], utc=True, errors="coerce"
    )
    ledger["prediction_time_utc"] = pd.to_datetime(
        ledger["prediction_time_utc"], utc=True, errors="coerce"
    )
    ledger["snapshot_time_utc"] = pd.to_datetime(
        ledger["snapshot_time_utc"], utc=True, errors="coerce"
    )
    ledger = ledger.dropna(
        subset=["kickoff_utc", "prediction_time_utc", "snapshot_time_utc"]
    )
    ledger = ledger[ledger["snapshot_time_utc"] < ledger["kickoff_utc"]]

    # Canonical contract: latest eligible pre-kickoff snapshot per league/event.
    ledger = ledger.sort_values(["league", "event_id", "snapshot_time_utc"])
    ledger = ledger.drop_duplicates(subset=["league", "event_id"], keep="last")

    result_map: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if not results.empty:
        for _, row in results.iterrows():
            key = _result_key(row)
            if key in result_map:
                raise ValueError(f"Duplicate canonical finished-result identity: {key!r}")
            result_map[key] = row.to_dict()

    cards: list[dict[str, Any]] = []
    for _, row in ledger.sort_values("kickoff_utc").iterrows():
        result = result_map.get(_ledger_result_key(row))
        kickoff = row["kickoff_utc"]
        status = "SETTLED" if result is not None else (
            "UPCOMING" if kickoff >= now_ts else "AWAITING_RESULT"
        )

        market = {
            "home": _prob(row.get("market_home_prob")),
            "draw": _prob(row.get("market_draw_prob")),
            "away": _prob(row.get("market_away_prob")),
            "pick": row.get("market_pick"),
            "pick_probability": _prob(row.get("market_pick_probability")),
        }

        structural = None
        structural_values = [
            row.get("structural_home_prob"),
            row.get("structural_draw_prob"),
            row.get("structural_away_prob"),
        ]
        if all(value is not None and not pd.isna(value) for value in structural_values):
            deltas = [
                float(row.get("structural_home_prob")) - float(row.get("market_home_prob")),
                float(row.get("structural_draw_prob")) - float(row.get("market_draw_prob")),
                float(row.get("structural_away_prob")) - float(row.get("market_away_prob")),
            ]
            structural = {
                "home": _prob(row.get("structural_home_prob")),
                "draw": _prob(row.get("structural_draw_prob")),
                "away": _prob(row.get("structural_away_prob")),
                "pick": row.get("structural_pick"),
                "pick_probability": _prob(row.get("structural_pick_probability")),
                "status": row.get("structural_status"),
                "score": _prob(row.get("structural_score")),
                "applied": bool(row.get("structural_applied", False)),
                "max_abs_delta": round(max(abs(value) for value in deltas), 6),
            }

        result_payload = None
        if result is not None:
            result_payload = {
                "home_goals": int(result["home_goals"]),
                "away_goals": int(result["away_goals"]),
                "result": str(result["result"]),
            }

        cards.append({
            "prediction_key": row["prediction_key"],
            "league": row["league"],
            "event_id": row["event_id"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "kickoff_utc": _iso(kickoff),
            "prediction_time_utc": _iso(row["prediction_time_utc"]),
            "snapshot_time_utc": _iso(row["snapshot_time_utc"]),
            "hours_to_kickoff": _prob(row.get("hours_to_kickoff")),
            "prediction_mode": row["prediction_mode"],
            "status": status,
            "market": market,
            "structural": structural,
            "result": result_payload,
        })

    return {
        "generated_at_utc": now_ts.isoformat(),
        "active_leagues": list(ACTIVE_LEAGUES),
        "summary": {
            "predictions": len(cards),
            "upcoming": sum(card["status"] == "UPCOMING" for card in cards),
            "settled": sum(card["status"] == "SETTLED" for card in cards),
            "awaiting_result": sum(
                card["status"] == "AWAITING_RESULT" for card in cards
            ),
        },
        "matches": cards,
    }


def fetch_viewer_payload(supabase_client: Any) -> dict[str, Any]:
    """Read canonical state from Supabase; no mutation methods are used."""

    ledger_response = (
        supabase_client.table("league_prediction_ledger")
        .select(LEDGER_COLUMNS)
        .order("kickoff_utc", desc=False)
        .limit(2000)
        .execute()
    )
    result_response = (
        supabase_client.table("league_finished_results")
        .select(RESULT_COLUMNS)
        .order("match_date", desc=True)
        .limit(2000)
        .execute()
    )
    return assemble_viewer_payload(
        ledger_response.data or [],
        result_response.data or [],
    )
