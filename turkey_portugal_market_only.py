"""Shared MARKET_ONLY foundation for Turkey Super Lig and Primeira Liga.

Research-only. No structural/model probabilities are produced here.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from fixture_identity import require_league
from save_odds_snapshot import DB_COLUMNS, DB_CONFLICT_TARGET, SUPABASE_TABLE
from the_odds_service import aggregate_event_h2h, get_h2h_odds
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG

@dataclass(frozen=True)
class MarketOnlyLeague:
    identifier: str
    timezone: str
    sport_key: str
    output: Path

LEAGUES = {
    "TURKEY_SUPER_LIG": MarketOnlyLeague("TURKEY_SUPER_LIG", "Europe/Istanbul", TURKEY_SUPER_LIG_RUNTIME_CONFIG.identity.odds_sport_key, Path("data/odds_snapshots/turkey_super_lig_h2h_snapshots.csv")),
    "PRIMEIRA_LIGA": MarketOnlyLeague("PRIMEIRA_LIGA", "Europe/Lisbon", PRIMEIRA_LIGA_RUNTIME_CONFIG.identity.odds_sport_key, Path("data/odds_snapshots/primeira_liga_h2h_snapshots.csv")),
}
REGION = "eu"

def config_for(league: str) -> MarketOnlyLeague:
    if league not in LEAGUES:
        raise ValueError(f"Unsupported league: {league}")
    return LEAGUES[league]

def build_snapshot_rows(league: str, events, snapshot_time_utc: str) -> pd.DataFrame:
    cfg = config_for(league); rows=[]
    for event in events:
        a=aggregate_event_h2h(event)
        if a is None: continue
        rows.append({"league":cfg.identifier,"snapshot_time_utc":snapshot_time_utc,"event_id":a["event_id"],"commence_time_utc":a["commence_time"],"home_team":a["home_team"],"away_team":a["away_team"],"bookmakers_count":a["bookmakers_count"],"home_odds":a["home_odds"],"draw_odds":a["draw_odds"],"away_odds":a["away_odds"],"home_probability":a["home_probability"],"draw_probability":a["draw_probability"],"away_probability":a["away_probability"]})
    return pd.DataFrame(rows, columns=DB_COLUMNS)

def build_db_rows(league: str, frame: pd.DataFrame):
    cfg=config_for(league); frame=require_league(frame, legacy_epl=False)
    if not frame.empty and not frame["league"].eq(cfg.identifier).all():
        raise ValueError("Foreign-league snapshot payload")
    missing=set(DB_COLUMNS).difference(frame.columns)
    if missing: raise ValueError(f"Missing DB columns: {sorted(missing)}")
    return frame[DB_COLUMNS].where(pd.notna(frame[DB_COLUMNS]),None).to_dict(orient="records")

def save_supabase(league: str, frame: pd.DataFrame, supabase_client=None):
    if supabase_client is None:
        from database import supabase as supabase_client
    response=supabase_client.table(SUPABASE_TABLE).upsert(build_db_rows(league,frame),on_conflict=DB_CONFLICT_TARGET).execute()
    return len(response.data or [])

def collect_snapshot(league: str, *, persist: bool=True):
    cfg=config_for(league); result=get_h2h_odds(cfg.sport_key, regions=REGION)
    now=datetime.now(timezone.utc).isoformat(); frame=build_snapshot_rows(league,result["events"],now)
    if frame.empty: raise RuntimeError(f"No usable {league} h2h odds")
    persisted=save_supabase(league,frame) if persist else 0
    return {"league":league,"rows":len(frame),"persisted":persisted,"quota":result["quota"],"frame":frame}

def result_from_score(home:int, away:int)->str:
    return "H" if home>away else "A" if away>home else "D"

def build_finished_row(league: str, event: dict):
    cfg=config_for(league)
    if not bool(event.get("completed")): return None
    home=str(event.get("home_team") or "").strip(); away=str(event.get("away_team") or "").strip(); commence=event.get("commence_time")
    if not home or not away or not commence: return None
    score_map={str(r.get("name") or "").strip():int(r["score"]) for r in (event.get("scores") or []) if r.get("name") and r.get("score") is not None}
    if home not in score_map or away not in score_map: return None
    local=datetime.fromisoformat(str(commence).replace("Z","+00:00")).astimezone(ZoneInfo(cfg.timezone)); hg=score_map[home]; ag=score_map[away]
    return {"league":league,"season":"2026-2027","match_date":local.strftime("%Y-%m-%d"),"match_time":local.strftime("%H:%M"),"home_team":home,"away_team":away,"home_goals":hg,"away_goals":ag,"result":result_from_score(hg,ag),"source":"the-odds-api","source_competition":cfg.sport_key}
