"""Sync immutable Turkey/Portugal finished results with quota safety."""
from __future__ import annotations
import argparse
import pandas as pd
import league_supabase_persistence as persistence
from scheduled_turkey_portugal_odds import QUOTA_START_FLOOR, zero_cost_quota
from turkey_portugal_market_only import build_finished_row, config_for
from turkey_portugal_scores_service import get_scores
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG

RUNTIME={"TURKEY_SUPER_LIG":TURKEY_SUPER_LIG_RUNTIME_CONFIG,"PRIMEIRA_LIGA":PRIMEIRA_LIGA_RUNTIME_CONFIG}
RESULT_COLUMNS=["league","season","match_date","match_time","home_team","away_team","home_goals","away_goals","result","source","source_competition"]

def build_finished_frame(league: str, events) -> pd.DataFrame:
    config_for(league); rows=[r for e in events if (r:=build_finished_row(league,e)) is not None]
    frame=pd.DataFrame(rows,columns=RESULT_COLUMNS)
    if not frame.empty and frame.duplicated(subset=["league","season","match_date","home_team","away_team"]).any(): raise ValueError("Duplicate finished-result identity")
    return frame

def sync_results(league: str, *, write: bool=False, client=None):
    config_for(league); q=zero_cost_quota()
    if q["remaining"]<QUOTA_START_FLOOR:
        print(f"{league} RESULTS=BLOCKED_LOW_QUOTA remaining={q['remaining']} floor={QUOTA_START_FLOOR}; paid requests=0")
        return {"status":"BLOCKED_LOW_QUOTA","finished_rows":0,"inserted":0,"unchanged":0,"conflicts":0}
    provider=get_scores(league,days_from=3); frame=build_finished_frame(league,provider["events"])
    print(league,"finished rows:",len(frame),"quota:",provider["quota"])
    if not write:return {"status":"DRY_RUN","finished_rows":len(frame),"inserted":0,"unchanged":0,"conflicts":0}
    if client is None:
        from database import supabase as client
    m=persistence.persist_results(client,frame,RUNTIME[league]); return {"status":"WRITTEN","finished_rows":len(frame),"inserted":int(m["inserted"]),"unchanged":int(m["unchanged"]),"conflicts":int(m["conflicts"])}

def main():
    p=argparse.ArgumentParser(); p.add_argument("league",choices=list(RUNTIME)); p.add_argument("--write",action="store_true"); a=p.parse_args(); print(sync_results(a.league,write=a.write))
if __name__=="__main__": main()
