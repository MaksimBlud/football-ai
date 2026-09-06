"""Sync immutable Turkey/Portugal finished results from public Football-Data CSV."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import league_supabase_persistence as persistence
from football_data_current_results import PublicResultsSourceUnavailable, fetch_current_finished_results
from multi_market_policy import UNPUBLISHED_CURRENT_CORNER_SOURCE_LEAGUES
from turkey_portugal_market_only import config_for
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG

RUNTIME={"TURKEY_SUPER_LIG":TURKEY_SUPER_LIG_RUNTIME_CONFIG,"PRIMEIRA_LIGA":PRIMEIRA_LIGA_RUNTIME_CONFIG}


def sync_results(league: str, *, write: bool=False, client=None):
    config_for(league)
    runtime=RUNTIME[league]
    if league in UNPUBLISHED_CURRENT_CORNER_SOURCE_LEAGUES:
        source = runtime.finished_results_source
        print(league,"PUBLIC FOOTBALL-DATA RESULTS")
        print("source status: CURRENT_SEASON_NOT_PUBLISHED")
        print("target source:", f"{source.season_code}/{source.competition_code}.csv")
        return {
            "status":"SOURCE_NOT_PUBLISHED",
            "finished_rows":0,
            "inserted":0,
            "unchanged":0,
            "conflicts":0,
            "public_http_requests":0,
            "paid_provider_requests":0,
        }
    try:
        provider=fetch_current_finished_results(runtime)
    except PublicResultsSourceUnavailable as exc:
        print(league,"PUBLIC FOOTBALL-DATA RESULTS")
        print("source status: TRANSIENT_UNAVAILABLE")
        print("source:", exc.url)
        print("HTTP status:", exc.status_code, "attempts:", exc.attempts)
        return {
            "status":"SOURCE_UNAVAILABLE",
            "source_url":exc.url,
            "http_status":exc.status_code,
            "finished_rows":0,
            "inserted":0,
            "unchanged":0,
            "conflicts":0,
            "public_http_requests":exc.attempts,
            "paid_provider_requests":0,
        }
    frame=provider["frame"]
    print(league,"PUBLIC FOOTBALL-DATA RESULTS")
    print("source:",provider["source_url"])
    print("source rows:",provider["source_rows"],"finished rows:",len(frame))
    print("paid provider requests:",provider["paid_provider_requests"])
    if not write:
        return {"status":"DRY_RUN","source_url":provider["source_url"],"finished_rows":len(frame),"inserted":0,"unchanged":0,"conflicts":0,"public_http_requests":int(provider["public_http_requests"]),"paid_provider_requests":0}
    if client is None:
        from database import supabase as client
    m=persistence.persist_results(client,frame,runtime)
    return {"status":"WRITTEN","source_url":provider["source_url"],"finished_rows":len(frame),"inserted":int(m["inserted"]),"unchanged":int(m["unchanged"]),"conflicts":int(m["conflicts"]),"public_http_requests":int(provider["public_http_requests"]),"paid_provider_requests":0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("league",choices=list(RUNTIME))
    p.add_argument("--write",action="store_true")
    p.add_argument("--status-json")
    a=p.parse_args()
    try:
        result=sync_results(a.league,write=a.write)
    except Exception as exc:
        result={
            "status":"FAILED",
            "league":a.league,
            "error_type":type(exc).__name__,
            "error":str(exc)[:1000],
            "paid_provider_requests":0,
        }
        if a.status_json:
            path=Path(a.status_json); path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        raise
    result={"league":a.league,**result}
    if a.status_json:
        path=Path(a.status_json); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__": main()
