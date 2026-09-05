"""Sync immutable Bundesliga finished results from configured public Football-Data CSV."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from database import supabase
from football_data_current_results import fetch_current_finished_results
import league_supabase_persistence as persistence
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
LEAGUE="BUNDESLIGA"; SEASON="2026-2027"; TIMEZONE=ZoneInfo("Europe/Berlin")
def result_from_score(h,a): return "H" if h>a else "A" if a>h else "D"
def _score_map(event):
    out={}
    for row in event.get("scores") or []:
        name=str(row.get("name") or "").strip(); score=row.get("score")
        if name and score is not None: out[name]=int(score)
    return out
def build_finished_row(event):
    """Compatibility helper; operational sync no longer reads The Odds API scores."""
    if not bool(event.get("completed")): return None
    home=str(event.get("home_team") or "").strip(); away=str(event.get("away_team") or "").strip(); commence=event.get("commence_time")
    if not home or not away or not commence:return None
    scores=_score_map(event)
    if home not in scores or away not in scores:return None
    local=datetime.fromisoformat(str(commence).replace("Z","+00:00")).astimezone(TIMEZONE); hg=int(scores[home]); ag=int(scores[away]); aliases=BUNDESLIGA_RUNTIME_CONFIG.aliases
    return {"league":LEAGUE,"season":SEASON,"match_date":local.strftime("%Y-%m-%d"),"match_time":local.strftime("%H:%M"),"home_team":aliases.get(home,home),"away_team":aliases.get(away,away),"home_goals":hg,"away_goals":ag,"result":result_from_score(hg,ag),"source":"the-odds-api","source_competition":BUNDESLIGA_RUNTIME_CONFIG.identity.odds_sport_key}
def build_finished_frame(events):
    cols=["league","season","match_date","match_time","home_team","away_team","home_goals","away_goals","result","source","source_competition"]
    f=pd.DataFrame([r for e in events if (r:=build_finished_row(e)) is not None],columns=cols)
    if not f.empty and f.duplicated(subset=["league","season","match_date","home_team","away_team"]).any(): raise ValueError("Duplicate Bundesliga finished-result identity")
    return f
def sync_results(write=False):
    provider=fetch_current_finished_results(BUNDESLIGA_RUNTIME_CONFIG); frame=provider["frame"]
    print("BUNDESLIGA FINISHED RESULTS SYNC — PUBLIC FOOTBALL-DATA CSV"); print("source:",provider["source_url"]); print("source rows:",provider["source_rows"]); print("finished rows:",len(frame)); print("paid provider requests:",provider["paid_provider_requests"])
    if not write: print("DRY RUN: no Supabase writes"); return {"inserted":0,"unchanged":0,"conflicts":0,"finished_rows":len(frame),"paid_provider_requests":0}
    m=persistence.persist_results(supabase,frame,BUNDESLIGA_RUNTIME_CONFIG); out={"inserted":int(m["inserted"]),"unchanged":int(m["unchanged"]),"conflicts":int(m["conflicts"]),"finished_rows":len(frame),"paid_provider_requests":0}; print("persistence:",out); print("production model used:",False); print("Structural V2 used:",False); return out
def main():
    p=argparse.ArgumentParser(); p.add_argument("--write",action="store_true"); a=p.parse_args(); sync_results(write=a.write)
if __name__=="__main__": main()
