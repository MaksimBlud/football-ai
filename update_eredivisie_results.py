"""Sync immutable Eredivisie finished results from The Odds API scores endpoint."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from database import supabase
import league_supabase_persistence as persistence
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from eredivisie_scores_service import get_eredivisie_scores

LEAGUE="EREDIVISIE"; SEASON=EREDIVISIE_RUNTIME_CONFIG.finished_results_source.season; SOURCE="the-odds-api"; SOURCE_COMPETITION=EREDIVISIE_RUNTIME_CONFIG.identity.odds_sport_key; TIMEZONE=ZoneInfo(EREDIVISIE_RUNTIME_CONFIG.identity.timezone)

def result_from_score(home_goals,away_goals): return "H" if home_goals>away_goals else "A" if away_goals>home_goals else "D"
def _score_map(event):
    result={}
    for row in event.get("scores") or []:
        name=str(row.get("name") or "").strip(); score=row.get("score")
        if name and score is not None: result[name]=int(score)
    return result

def build_finished_row(event):
    if not bool(event.get("completed")): return None
    home=str(event.get("home_team") or "").strip(); away=str(event.get("away_team") or "").strip(); commence=event.get("commence_time")
    if not home or not away or not commence:return None
    scores=_score_map(event)
    if home not in scores or away not in scores:return None
    kickoff=datetime.fromisoformat(str(commence).replace("Z","+00:00")).astimezone(TIMEZONE); hg=int(scores[home]); ag=int(scores[away]); aliases=EREDIVISIE_RUNTIME_CONFIG.aliases
    return {"league":LEAGUE,"season":SEASON,"match_date":kickoff.strftime("%Y-%m-%d"),"match_time":kickoff.strftime("%H:%M"),"home_team":aliases.get(home,home),"away_team":aliases.get(away,away),"home_goals":hg,"away_goals":ag,"result":result_from_score(hg,ag),"source":SOURCE,"source_competition":SOURCE_COMPETITION}

def build_finished_frame(events):
    columns=["league","season","match_date","match_time","home_team","away_team","home_goals","away_goals","result","source","source_competition"]
    frame=pd.DataFrame([row for event in events if (row:=build_finished_row(event)) is not None],columns=columns)
    if frame.empty:return frame
    identity=["league","season","match_date","home_team","away_team"]
    if frame.duplicated(subset=identity).any():raise ValueError("Duplicate Eredivisie finished-result identity from provider")
    return frame

def sync_results(*,write):
    provider=get_eredivisie_scores(days_from=3); frame=build_finished_frame(provider["events"])
    print("EREDIVISIE FINISHED RESULTS SYNC");print("provider events:",len(provider["events"]));print("finished rows:",len(frame));print("quota:",provider["quota"])
    if not frame.empty:print(frame.to_string(index=False))
    if not write:print("DRY RUN: no Supabase writes");return {"inserted":0,"unchanged":0,"conflicts":0,"finished_rows":len(frame)}
    metrics=persistence.persist_results(supabase,frame,EREDIVISIE_RUNTIME_CONFIG); result={"inserted":int(metrics["inserted"]),"unchanged":int(metrics["unchanged"]),"conflicts":int(metrics["conflicts"]),"finished_rows":len(frame)}
    print("persistence:",result);print("production model used:",False);print("Structural V2 used:",False);return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--write",action="store_true");args=parser.parse_args();sync_results(write=args.write)
if __name__=="__main__":main()
