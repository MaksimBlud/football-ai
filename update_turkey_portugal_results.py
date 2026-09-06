"""Sync immutable Turkey/Portugal finished results from public Football-Data CSV."""
from __future__ import annotations
import argparse
import league_supabase_persistence as persistence
from football_data_current_results import fetch_current_finished_results
from turkey_portugal_market_only import config_for
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG

RUNTIME={"TURKEY_SUPER_LIG":TURKEY_SUPER_LIG_RUNTIME_CONFIG,"PRIMEIRA_LIGA":PRIMEIRA_LIGA_RUNTIME_CONFIG}


def sync_results(league: str, *, write: bool=False, client=None):
    config_for(league)
    runtime=RUNTIME[league]
    provider=fetch_current_finished_results(runtime)
    frame=provider["frame"]
    print(league,"PUBLIC FOOTBALL-DATA RESULTS")
    print("source:",provider["source_url"])
    print("source rows:",provider["source_rows"],"finished rows:",len(frame))
    print("paid provider requests:",provider["paid_provider_requests"])
    if not write:
        return {"status":"DRY_RUN","finished_rows":len(frame),"inserted":0,"unchanged":0,"conflicts":0,"paid_provider_requests":0}
    if client is None:
        from database import supabase as client
    m=persistence.persist_results(client,frame,runtime)
    return {"status":"WRITTEN","finished_rows":len(frame),"inserted":int(m["inserted"]),"unchanged":int(m["unchanged"]),"conflicts":int(m["conflicts"]),"paid_provider_requests":0}


def main():
    p=argparse.ArgumentParser(); p.add_argument("league",choices=list(RUNTIME)); p.add_argument("--write",action="store_true"); a=p.parse_args(); print(sync_results(a.league,write=a.write))
if __name__=="__main__": main()
