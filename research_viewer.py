"""Read-only data assembly for the Research Viewer.

This module never writes to Supabase, never loads production model artifacts,
and never triggers prediction/training code. It only projects canonical ledger,
finished-result state, and optional research-only multi-market snapshots.
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
RESULT_COLUMNS = "league,season,match_date,home_team,away_team,home_goals,away_goals,result"
MULTI_MARKET_COLUMNS = "league,event_id,kickoff_utc,snapshot_time_utc,payload"

ACTIVE_LEAGUES = (
    "EPL", "LA_LIGA", "RPL", "SERIE_A", "BUNDESLIGA", "LIGUE_1", "EREDIVISIE",
    "TURKEY_SUPER_LIG", "PRIMEIRA_LIGA",
)


def _utc(value: Any) -> pd.Timestamp:
    return pd.to_datetime(value, utc=True, errors="coerce")


def _team_key(value: Any) -> str:
    return normalize_team_name(str(value))


def _result_key(row: pd.Series) -> tuple[str, str, str, str]:
    date_value = pd.to_datetime(row["match_date"], errors="coerce")
    date_text = date_value.date().isoformat() if pd.notna(date_value) else ""
    return (str(row["league"]), _team_key(row["home_team"]), _team_key(row["away_team"]), date_text)


def _ledger_result_key(row: pd.Series) -> tuple[str, str, str, str]:
    league = str(row["league"])
    kickoff = _utc(row["kickoff_utc"])
    date_text = "" if pd.isna(kickoff) else kickoff.tz_convert(get_league_config(league).timezone).date().isoformat()
    return (league, _team_key(row["home_team"]), _team_key(row["away_team"]), date_text)


def _prob(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def _iso(value: Any) -> str | None:
    timestamp = _utc(value)
    return timestamp.isoformat() if pd.notna(timestamp) else None


def _multi_market_map(rows: list[dict[str, Any]] | None) -> dict[tuple[str, str], dict[str, Any]]:
    if not rows:
        return {}
    frame = pd.DataFrame(rows)
    required = {"league", "event_id", "kickoff_utc", "snapshot_time_utc", "payload"}
    if not required <= set(frame.columns):
        return {}
    frame["kickoff_utc"] = pd.to_datetime(frame["kickoff_utc"], utc=True, errors="coerce")
    frame["snapshot_time_utc"] = pd.to_datetime(frame["snapshot_time_utc"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["league", "event_id", "kickoff_utc", "snapshot_time_utc"])
    frame = frame[frame["snapshot_time_utc"] < frame["kickoff_utc"]]
    frame = frame.sort_values(["league", "event_id", "snapshot_time_utc"]).drop_duplicates(["league", "event_id"], keep="last")
    result = {}
    for _, row in frame.iterrows():
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        card = payload.get("card") if isinstance(payload.get("card"), dict) else None
        if card:
            result[(str(row["league"]), str(row["event_id"]))] = {
                **card,
                "snapshot_time_utc": _iso(row["snapshot_time_utc"]),
            }
    return result


def assemble_viewer_payload(
    ledger_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    *,
    multi_market_rows: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now_ts = pd.Timestamp(now or datetime.now(timezone.utc))
    now_ts = now_ts.tz_localize("UTC") if now_ts.tzinfo is None else now_ts.tz_convert("UTC")
    ledger = pd.DataFrame(ledger_rows)
    results = pd.DataFrame(result_rows)
    multi_map = _multi_market_map(multi_market_rows)

    if ledger.empty:
        return {"generated_at_utc": now_ts.isoformat(), "active_leagues": list(ACTIVE_LEAGUES),
                "summary": {"predictions": 0, "upcoming": 0, "settled": 0, "awaiting_result": 0}, "matches": []}

    required = {"prediction_key", "league", "event_id", "home_team", "away_team", "kickoff_utc",
                "prediction_time_utc", "snapshot_time_utc", "market_home_prob", "market_draw_prob",
                "market_away_prob", "market_pick", "prediction_mode"}
    missing = required - set(ledger.columns)
    if missing:
        raise ValueError("Missing ledger columns: " + ", ".join(sorted(missing)))

    for column in ("kickoff_utc", "prediction_time_utc", "snapshot_time_utc"):
        ledger[column] = pd.to_datetime(ledger[column], utc=True, errors="coerce")
    ledger = ledger.dropna(subset=["kickoff_utc", "prediction_time_utc", "snapshot_time_utc"])
    ledger = ledger[ledger["snapshot_time_utc"] < ledger["kickoff_utc"]]
    ledger = ledger.sort_values(["league", "event_id", "snapshot_time_utc"]).drop_duplicates(["league", "event_id"], keep="last")

    result_map: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if not results.empty:
        for _, row in results.iterrows():
            key = _result_key(row)
            if key in result_map:
                raise ValueError(f"Duplicate canonical finished-result identity: {key!r}")
            result_map[key] = row.to_dict()

    cards = []
    for _, row in ledger.sort_values("kickoff_utc").iterrows():
        result = result_map.get(_ledger_result_key(row))
        kickoff = row["kickoff_utc"]
        status = "SETTLED" if result is not None else ("UPCOMING" if kickoff >= now_ts else "AWAITING_RESULT")
        market = {"home": _prob(row.get("market_home_prob")), "draw": _prob(row.get("market_draw_prob")),
                  "away": _prob(row.get("market_away_prob")), "pick": row.get("market_pick"),
                  "pick_probability": _prob(row.get("market_pick_probability"))}

        structural = None
        structural_values = [row.get("structural_home_prob"), row.get("structural_draw_prob"), row.get("structural_away_prob")]
        if all(value is not None and not pd.isna(value) for value in structural_values):
            deltas = [float(row.get("structural_home_prob")) - float(row.get("market_home_prob")),
                      float(row.get("structural_draw_prob")) - float(row.get("market_draw_prob")),
                      float(row.get("structural_away_prob")) - float(row.get("market_away_prob"))]
            structural = {"home": _prob(row.get("structural_home_prob")), "draw": _prob(row.get("structural_draw_prob")),
                          "away": _prob(row.get("structural_away_prob")), "pick": row.get("structural_pick"),
                          "pick_probability": _prob(row.get("structural_pick_probability")), "status": row.get("structural_status"),
                          "score": _prob(row.get("structural_score")), "applied": bool(row.get("structural_applied", False)),
                          "max_abs_delta": round(max(abs(value) for value in deltas), 6)}

        result_payload = None if result is None else {"home_goals": int(result["home_goals"]), "away_goals": int(result["away_goals"]), "result": str(result["result"])}
        cards.append({
            "prediction_key": row["prediction_key"], "league": row["league"], "event_id": row["event_id"],
            "home_team": row["home_team"], "away_team": row["away_team"], "kickoff_utc": _iso(kickoff),
            "prediction_time_utc": _iso(row["prediction_time_utc"]), "snapshot_time_utc": _iso(row["snapshot_time_utc"]),
            "hours_to_kickoff": _prob(row.get("hours_to_kickoff")), "prediction_mode": row["prediction_mode"],
            "status": status, "market": market, "multi_market": multi_map.get((str(row["league"]), str(row["event_id"]))),
            "structural": structural, "result": result_payload,
        })

    upcoming_cards = [card for card in cards if card["status"] == "UPCOMING"]
    historical_cards = [card for card in cards if card["status"] != "UPCOMING"]
    cards = upcoming_cards + list(reversed(historical_cards))
    return {"generated_at_utc": now_ts.isoformat(), "active_leagues": list(ACTIVE_LEAGUES),
            "summary": {"predictions": len(cards), "upcoming": sum(c["status"] == "UPCOMING" for c in cards),
                        "settled": sum(c["status"] == "SETTLED" for c in cards),
                        "awaiting_result": sum(c["status"] == "AWAITING_RESULT" for c in cards)}, "matches": cards}


def fetch_viewer_payload(supabase_client: Any) -> dict[str, Any]:
    ledger_response = supabase_client.table("league_prediction_ledger").select(LEDGER_COLUMNS).order("kickoff_utc", desc=False).limit(2000).execute()
    result_response = supabase_client.table("league_finished_results").select(RESULT_COLUMNS).order("match_date", desc=True).limit(2000).execute()
    multi_rows = []
    try:
        multi_response = supabase_client.table("league_multi_market_snapshots").select(MULTI_MARKET_COLUMNS).order("snapshot_time_utc", desc=True).limit(4000).execute()
        multi_rows = multi_response.data or []
    except Exception:
        # Multi-Market V1 is additive. The legacy viewer remains available while
        # its dedicated schema is externally gated or an event lacks coverage.
        multi_rows = []
    return assemble_viewer_payload(ledger_response.data or [], result_response.data or [], multi_market_rows=multi_rows)
