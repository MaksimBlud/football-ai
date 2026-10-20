#!/usr/bin/env python3
"""Research-only season snapshot for last-120s goals, 2026/27 through 2026-10-19.
Big Five uses Opta exact seconds. RPL uses FotMob minute intervals, with boundary cases UNKNOWN.
Also emits every goal after minute 90 so announced-added-time windows can be audited separately.
No production model, database, or paid API is touched.
"""
from __future__ import annotations
import collections, csv, datetime as dt, json, math, pathlib, re, tempfile, time, urllib.parse, urllib.request
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

END_DATE = "2026-10-19"
SEASON = "2026-2027"
OUT = pathlib.Path("research/last120_season_20261020/results")
OUT.mkdir(parents=True, exist_ok=True)
OPTABASE = "https://github.com/peteowen1/pannadata/releases/download/opta-latest/"
FOTMOB = "https://www.fotmob.com/api/data/"
BIG5 = ["EPL", "La_Liga", "Bundesliga", "Serie_A", "Ligue_1"]
LEAGUES = {47:"АПЛ", 87:"Ла Лига", 54:"Бундеслига", 55:"Серия A", 53:"Лига 1", 63:"РПЛ"}
OPTA_CODE = {"АПЛ":"EPL", "Ла Лига":"La_Liga", "Бундеслига":"Bundesliga", "Серия A":"Serie_A", "Лига 1":"Ligue_1"}
def http_json(url, retries=3):
    for n in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; FootballAIResearch/1.0)","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=40) as r: return json.load(r)
        except Exception:
            if n+1==retries: raise
            time.sleep(1.2*(n+1))
def download(name,path):
    req=urllib.request.Request(OPTABASE+name,headers={"User-Agent":"football-ai-research-20261020"})
    with urllib.request.urlopen(req,timeout=180) as src,open(path,"wb") as out:
        while True:
            b=src.read(2*1024*1024)
            if not b: break
            out.write(b)
    print("DOWNLOADED",name,path.stat().st_size,flush=True)
def sec(e):
    m,s=e.get("minute"),e.get("second")
    try: return float(m)*60+float(s)
    except (TypeError,ValueError): return None
def classify_exact(f,events):
    mid=str(f["match_id"]); gs=[e for e in events if int(e.get("type_id") or 0)==16 and int(e.get("period_id") or 0) in (1,2) and sec(e) is not None]
    ends=[e for e in events if int(e.get("type_id") or 0)==30 and int(e.get("period_id") or 0)==2 and sec(e) is not None]
    expected=int(f["home_score"])+int(f["away_score"])
    row={"date":str(f.get("match_date",""))[:10],"league":f["competition"],"home":f.get("home_team"),"away":f.get("away_team"),"score":f'{f["home_score"]}-{f["away_score"]}',"match_id":mid,"precision":"EXACT_OPTА_SECONDS"}
    row["goal_minutes"]=",".join(str(int(sec(g)//60+1)) for g in gs)
    row["final_elapsed_sec"]=None
    if len(gs)!=expected: row.update(result_a="UNKNOWN",reason_a="GOAL_EVENT_SCORE_MISMATCH"); return row,gs,None
    if not ends: row.update(result_a="UNKNOWN",reason_a="NO_PERIOD_2_END"); return row,gs,None
    endvals=[sec(e) for e in ends]
    if max(endvals)-min(endvals)>3: row.update(result_a="UNKNOWN",reason_a="CONFLICTING_END_TIMES"); return row,gs,None
    final=max(endvals); row["final_elapsed_sec"]=final
    if not 5400<=final<=7200 or any(sec(g)>final for g in gs):
        row.update(result_a="UNKNOWN",reason_a="INVALID_FINAL_TIME"); return row,gs,final
    late=[g for g in gs if final-120<=sec(g)<=final]
    row.update(result_a="GOAL" if late else "NO_GOAL",reason_a="EXACT_SECOND_WINDOW",late_goal_seconds=",".join(str(round(final-sec(g),1)) for g in late))
    return row,gs,final
def norm(s): return "".join(c for c in str(s).lower() if c.isalnum())
def parse_goal_minute(g):
    t=str(g.get("timeStr") or g.get("time") or "").strip().replace("'","").replace(" ","")
    m=re.fullmatch(r"(\d+)(?:\+(\d+))?",t)
    return int(m.group(1))+int(m.group(2) or 0) if m else None
def parse_datetime(s):
    if not s: return None
    try: return dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
    except ValueError: return None
def classify_rpl(t,doc):
    header=doc.get("header") or {}; status=header.get("status") or {}
    halfs=status.get("halfs") or {}
    start=parse_datetime(halfs.get("secondHalfStarted")); end=parse_datetime(halfs.get("gameEnded"))
    ev=((doc.get("content") or {}).get("matchFacts") or {}).get("events") or {}
    events=ev.get("events") or []
    goals=[e for e in events if e.get("type")=="Goal" and not e.get("isPenaltyShootoutEvent")]
    minutes=[parse_goal_minute(g) for g in goals]
    score_total=t["home_goals"]+t["away_goals"]
    row={"date":END_DATE if not t.get("date") else t["date"],"league":"РПЛ","home":t["home"],"away":t["away"],"score":f'{t["home_goals"]}-{t["away_goals"]}',"match_id":t["fotmob_id"],"precision":"MINUTE_INTERVAL_ONLY","goal_minutes":",".join(str(x) for x in minutes if x is not None)}
    if not status.get("finished") or len(goals)!=score_total or any(x is None for x in minutes):
        row.update(result_a="UNKNOWN",reason_a="FINISH_OR_GOAL_COUNT_UNVERIFIED"); return row,minutes,None, status
    if not start or not end:
        row.update(result_a="UNKNOWN",reason_a="MISSING_HALF_START_OR_FINAL_WHISTLE"); return row,minutes,None,status
    final=2700+(end-start).total_seconds(); row["final_elapsed_sec"]=final
    if not 5400<=final<=6900:
        row.update(result_a="UNKNOWN",reason_a="INVALID_FINAL_TIME"); return row,minutes,final,status
    cutoff=final-120; guard=15
    definitely=[m for m in minutes if (m-1)*60>=cutoff and (m-1)*60<final]
    if definitely:
        margin=min((m-1)*60-cutoff for m in definitely)
        if margin>=guard: row.update(result_a="GOAL",reason_a="MINUTE_INTERVAL_INSIDE_WINDOW")
        else: row.update(result_a="UNKNOWN",reason_a="GOAL_MINUTE_WITHIN_15S_OF_CUTOFF")
    elif all(m*60<=cutoff for m in minutes):
        margin=min((cutoff-m*60 for m in minutes),default=float("inf"))
        if margin>=guard: row.update(result_a="NO_GOAL",reason_a="ALL_GOALS_BEFORE_WINDOW")
        else: row.update(result_a="UNKNOWN",reason_a="LAST_GOAL_WITHIN_15S_OF_CUTOFF")
    else: row.update(result_a="UNKNOWN",reason_a="MINUTE_INTERVAL_OVERLAPS_WINDOW")
    return row,minutes,final,status
def main():
    allrows=[]; late_candidates=[]; announced_fields=collections.Counter()
    with tempfile.TemporaryDirectory() as td:
        root=pathlib.Path(td); fp=root/"opta_fixtures.parquet"; download("opta_fixtures.parquet",fp)
        ft=pq.read_table(fp,columns=["match_id","competition","season","match_date","match_status","home_team","away_team","home_score","away_score"])
        fixtures=[f for f in ft.to_pylist() if f.get("competition") in BIG5 and str(f.get("season")) in (SEASON,"2026-27") and str(f.get("match_date",""))[:10]<=END_DATE and f.get("home_score") is not None and f.get("away_score") is not None and str(f.get("match_status","")).lower() in ("played","finished","complete","completed")]
        print("OPTA_FIXTURES",len(fixtures),"BY_LEAGUE",dict(collections.Counter(f["competition"] for f in fixtures)),"STATUS",dict(collections.Counter(str(f.get("match_status")) for f in ft.to_pylist() if f.get("competition") in BIG5 and str(f.get("season")) in (SEASON,"2026-27") and str(f.get("match_date",""))[:10]<=END_DATE)),flush=True)
        for league in BIG5:
            lf=[f for f in fixtures if f["competition"]==league]; ids={str(f["match_id"]) for f in lf}
            if not lf: continue
            path=root/f"events_{league}.parquet"; download("events_"+league+".parquet",path)
            byid=collections.defaultdict(list); reader=pq.ParquetFile(path)
            cols=["match_id","type_id","minute","second","period_id","team_id"]
            for batch in reader.iter_batches(batch_size=50000,columns=cols):
                tbl=pa.Table.from_batches([batch])
                id_type=tbl.schema.field("match_id").type
                selected=tbl.filter(pc.and_(pc.is_in(tbl["match_id"],value_set=pa.array(list(ids),type=id_type)),pc.is_in(tbl["type_id"],value_set=pa.array([16,30],type=tbl.schema.field("type_id").type))))
                for e in selected.to_pylist(): byid[str(e["match_id"])].append(e)
            for f in lf:
                row,gs,final=classify_exact(f,byid.get(str(f["match_id"]),[])); row["league"]= {"EPL":"АПЛ","La_Liga":"Ла Лига","Bundesliga":"Бундеслига","Serie_A":"Серия A","Ligue_1":"Лига 1"}[league]
                allrows.append(row)
                after=[int(sec(g)//60+1) for g in gs if sec(g)>=5400]
                if after: late_candidates.append({**{k:row.get(k) for k in ("date","league","home","away","score","match_id","precision","final_elapsed_sec")},"goal_minutes":",".join(map(str,after)),"goal_minutes_all":row["goal_minutes"]})
            path.unlink(missing_ok=True)
    # RPL calendar scan: public FotMob scores + match detail timestamps, no paid API.
    start=dt.date(2026,7,24); end=dt.date.fromisoformat(END_DATE); day=start
    rpl_targets={}
    while day<=end:
        datekey=day.strftime("%Y%m%d")
        try:
            obj=http_json(FOTMOB+"matches?"+urllib.parse.urlencode({"date":datekey}))
            for group in obj.get("leagues",[]):
                try: lid=int(group.get("primaryId") or group.get("id") or -1)
                except (ValueError,TypeError): continue
                if lid!=63: continue
                for m in group.get("matches",[]):
                    st=m.get("status") or {}
                    if not st.get("finished") or st.get("cancelled") or st.get("awarded"): continue
                    h=(m.get("home") or {}).get("name"); a=(m.get("away") or {}).get("name")
                    sc=re.fullmatch(r"\s*(\d+)\s*[-–:]\s*(\d+)\s*",str(st.get("scoreStr") or ""))
                    if not h or not a or not sc: continue
                    rpl_targets[str(m.get("id"))]={"fotmob_id":str(m.get("id")),"date":day.isoformat(),"home":h,"away":a,"home_goals":int(sc.group(1)),"away_goals":int(sc.group(2))}
        except Exception as e: print("RPL_DAY_FETCH_ERROR",datekey,str(e)[:120],flush=True)
        day+=dt.timedelta(days=1)
    print("RPL_TARGETS",len(rpl_targets),flush=True)
    for idx,t in enumerate(rpl_targets.values(),1):
        try:
            doc=http_json(FOTMOB+"matchDetails?"+urllib.parse.urlencode({"matchId":t["fotmob_id"]}))
            row,minutes,final,status=classify_rpl(t,doc); allrows.append(row)
            for k,v in (status or {}).items():
                if any(x in str(k).lower() for x in ("added","injury","stoppage")): announced_fields[str(k)]+=1
            if any(m and m>=91 for m in minutes):
                late_candidates.append({**{k:row.get(k) for k in ("date","league","home","away","score","match_id","precision","final_elapsed_sec")},"goal_minutes":",".join(str(m) for m in minutes if m and m>=91),"goal_minutes_all":row["goal_minutes"]})
        except Exception as e:
            allrows.append({"date":t["date"],"league":"РПЛ","home":t["home"],"away":t["away"],"score":f'{t["home_goals"]}-{t["away_goals"]}',"match_id":t["fotmob_id"],"precision":"UNVERIFIED","result_a":"UNKNOWN","reason_a":"DETAIL_FETCH_ERROR"})
        if idx%20==0: print("RPL_DETAILS_PROGRESS",idx,"/",len(rpl_targets),flush=True)
    counts={}
    for league in LEAGUES.values():
        z=[r for r in allrows if r.get("league")==league]
        c=collections.Counter(r.get("result_a","UNKNOWN") for r in z)
        counts[league]={"matches":len(z),"GOAL":c["GOAL"],"NO_GOAL":c["NO_GOAL"],"UNKNOWN":c["UNKNOWN"],"precision":dict(collections.Counter(r.get("precision","") for r in z))}
    total=collections.Counter(r.get("result_a","UNKNOWN") for r in allrows)
    # Announced time is not represented by Opta event times. Probe the match-level FotMob status only;
    # never substitute actual elapsed time for the referee's announced board.
    summary={"season":SEASON,"through":END_DATE,"criterion_A":"goal in [actual final whistle - 120s, final whistle]","criterion_A_counts":counts,"criterion_A_total":{"matches":len(allrows),"GOAL":total["GOAL"],"NO_GOAL":total["NO_GOAL"],"UNKNOWN":total["UNKNOWN"]},"candidate_matches_with_goal_after_90":len(late_candidates),"match_level_announced_time_fields_found":dict(announced_fields)}
    (OUT/"matches.csv").write_text("",encoding="utf-8")
    with open(OUT/"matches.csv","w",encoding="utf-8-sig",newline="") as f:
        fields=sorted({k for r in allrows for k in r}); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(allrows)
    with open(OUT/"late_goal_candidates.csv","w",encoding="utf-8-sig",newline="") as f:
        fields=sorted({k for r in late_candidates for k in r}); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(late_candidates)
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SEASON_SUMMARY="+json.dumps(summary,ensure_ascii=False),flush=True)
    print("LATE_GOAL_CANDIDATES="+json.dumps(late_candidates,ensure_ascii=False),flush=True)
if __name__=="__main__": main()
