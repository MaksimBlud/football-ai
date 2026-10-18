"""Read-only analysis for matches played on 2026-10-17.
Big Five: exact Opta goal/event-second vs period-2 end event. RPL: conservative
minute interval using the observed second-half start and full-time timestamps.
No paid APIs, no database writes, no production model changes.
"""
from __future__ import annotations
import collections, concurrent.futures, csv, datetime as dt, json, math, pathlib, re, tempfile, time, unicodedata, urllib.parse, urllib.request
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

DAY = "2026-10-17"
DAY_ARG = "20261017"
OUT = pathlib.Path("research/last120_yesterday_20261017/evidence")
OUT.mkdir(parents=True, exist_ok=True)
FOTMOB = "https://www.fotmob.com/api/data/"
OPTABASE = "https://github.com/peteowen1/pannadata/releases/download/opta-latest/"
LEAGUES = {47:"EPL", 87:"LA_LIGA", 54:"BUNDESLIGA", 55:"SERIE_A", 53:"LIGUE_1", 63:"RPL"}
OPTA_CODE = {"EPL":"EPL", "LA_LIGA":"La_Liga", "BUNDESLIGA":"Bundesliga", "SERIE_A":"Serie_A", "LIGUE_1":"Ligue_1"}
OFFICIAL_NAMES = {"EPL":"Premier League", "LA_LIGA":"La Liga", "BUNDESLIGA":"Bundesliga", "SERIE_A":"Serie A", "LIGUE_1":"Ligue 1", "RPL":"Russian Premier League"}

def http_json(url, retries=3):
    for n in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; FootballAIResearch/1.0)","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)
        except Exception:
            if n+1==retries: raise
            time.sleep(1.5*(n+1))

def fotmob(name, **params):
    return http_json(FOTMOB+name+"?"+urllib.parse.urlencode(params))

def normal(s):
    s="".join(c for c in unicodedata.normalize("NFKD",str(s)).lower() if c.isalnum())
    aliases={"auxerroise":"auxerre","rennais":"rennes","atleticodemadrid":"atleticodemadrid","psg":"parissaintgermain","internazionale":"inter"}
    for a,b in aliases.items():
        if a in s: return s.replace(a,b)
    return s

def same_team(a,b):
    x,y=normal(a),normal(b)
    if x==y: return True
    if len(x)>=4 and (x in y or y in x): return True
    return False

def parse_score(s):
    if not s: return None
    m=re.fullmatch(r"\s*(\d+)\s*[-–:]\s*(\d+)\s*",str(s))
    return (int(m.group(1)),int(m.group(2))) if m else None

def find_matches():
    obj=fotmob("matches",date=DAY_ARG); ret=[]
    for group in obj.get("leagues",[]):
        raw_id=group.get("primaryId") or group.get("id") or -1
        try: lid=int(raw_id)
        except (ValueError,TypeError): continue
        league=LEAGUES.get(lid)
        if not league: continue
        for m in group.get("matches",[]):
            st=m.get("status") or {}
            if not st.get("finished") or st.get("cancelled") or st.get("awarded"): continue
            home=(m.get("home") or {}).get("name"); away=(m.get("away") or {}).get("name")
            score=parse_score(st.get("scoreStr"))
            if not home or not away or score is None: continue
            ret.append({"fotmob_id":str(m.get("id")),"date":DAY,"league":league,"home":home,"away":away,
                        "home_goals":score[0],"away_goals":score[1],"score":f"{score[0]}-{score[1]}",
                        "list_halfs":st.get("halfs") or {}})
    # duplicate IDs can occur through aliases/group metadata; retain one record only
    return list({x["fotmob_id"]:x for x in ret}.values())

def parse_datetime(s):
    if not s: return None
    text=str(s).strip()
    try:
        return dt.datetime.fromisoformat(text.replace("Z","+00:00"))
    except ValueError:
        for fmt in ("%d.%m.%Y %H:%M:%S","%Y-%m-%dT%H:%M:%S.%fZ","%Y-%m-%dT%H:%M:%SZ"):
            try: return dt.datetime.strptime(text,fmt)
            except ValueError: pass
    return None

def parse_goal_minute(g):
    text=str(g.get("timeStr") or g.get("time") or "").strip().replace("'","").replace(" ","")
    m=re.fullmatch(r"(\d+)(?:\+(\d+))?",text)
    return int(m.group(1))+int(m.group(2) or 0) if m else None

def download(name, path):
    req=urllib.request.Request(OPTABASE+name,headers={"User-Agent":"football-ai-free-research"})
    with urllib.request.urlopen(req,timeout=150) as src,open(path,"wb") as out:
        while True:
            b=src.read(2*1024*1024)
            if not b: break
            out.write(b)
    print("DOWNLOADED",name,path.stat().st_size,flush=True)

def evsec(e):
    try:
        m,s=e.get("minute"),e.get("second")
        if m is None or s is None: return None
        return float(m)*60+float(s)
    except (TypeError,ValueError): return None

def pick_optas(targets,fixtures):
    picked={}; errors=[]; used=collections.defaultdict(list)
    for t in targets:
        if t["league"] not in OPTA_CODE: continue
        eligible=[]
        for f in fixtures:
            season=str(f.get("season") or "").replace("/","-")
            date_text=str(f.get("match_date") or "")
            score=(int(f["home_score"]),int(f["away_score"])) if f.get("home_score") is not None and f.get("away_score") is not None else None
            if str(f.get("competition")) != OPTA_CODE[t["league"]]: continue
            if DAY not in date_text or season not in ("2026-2027","2026-27","2026-2027 "): continue
            if str(f.get("match_status") or "").lower() not in ("played","finished","complete","completed"): continue
            if score != (t["home_goals"],t["away_goals"]): continue
            eligible.append(f)
        strict=[f for f in eligible if same_team(t["home"],f.get("home_team","")) and same_team(t["away"],f.get("away_team",""))]
        chosen=strict[0] if len(strict)==1 else None
        method="JOIN_BOTH_TEAMS_DATE_SCORE"
        if chosen is None and len(eligible)==1 and (same_team(t["home"],eligible[0].get("home_team","")) or same_team(t["away"],eligible[0].get("away_team",""))):
            chosen=eligible[0]; method="GUARDED_UNIQUE_DATE_SCORE_ONE_TEAM"
        if chosen is None:
            errors.append({"league":t["league"],"home":t["home"],"away":t["away"],"score":t["score"],"why":f"OPT_JOIN_UNRESOLVED eligible={len(eligible)} strict={len(strict)}"})
            continue
        mid=str(chosen["match_id"]); picked[t["fotmob_id"]]={"fixture":chosen,"method":method}
        used[mid].append(t["fotmob_id"])
    collisions={mid:ids for mid,ids in used.items() if len(ids)>1}
    for mid,ids in collisions.items():
        for fid in ids: picked.pop(fid,None)
    if collisions: errors.append({"why":"OPT_ID_COLLISIONS","collisions":collisions})
    return picked,errors

def classify_opta(t,f,events,join_method):
    row={k:v for k,v in t.items() if k!="list_halfs"}
    row["source"]="Opta exact event seconds + FotMob fixture reconciliation"
    row["join_method"]=join_method
    end_events=[e for e in events if int(e.get("type_id") or 0)==30 and int(e.get("period_id") or 0)==2 and evsec(e) is not None]
    goals=[e for e in events if int(e.get("type_id") or 0)==16 and int(e.get("period_id") or 0) in (1,2) and evsec(e) is not None]
    goal_total=t["home_goals"]+t["away_goals"]
    row.update(opta_fixture_id=str(f.get("match_id")),score_verified=(int(f["home_score"])==t["home_goals"] and int(f["away_score"])==t["away_goals"]),
               opta_goal_events=len(goals), expected_goal_events=goal_total, final_end_events=len(end_events))
    if len(goals)!=goal_total or not end_events:
        row.update(result="UNKNOWN",reason="SAME_SOURCE_GOAL_COUNT_OR_END_MISSING")
        return row
    ends=sorted(set(evsec(e) for e in end_events)); final=ends[-1]
    if final<5400 or final>7200 or (ends[-1]-ends[0])>3:
        row.update(result="UNKNOWN",reason="INCONSISTENT_FINAL_END_EVENT")
        return row
    all_goal_seconds=[evsec(e) for e in goals]
    if any(x>final for x in all_goal_seconds):
        row.update(result="UNKNOWN",reason="GOAL_AFTER_FINAL_END_EVENT")
        return row
    cutoff=final-120
    late=[e for e in goals if cutoff<=evsec(e)<=final]
    # Conservative identical safeguard used in the previously validated audit.
    if any(float(e.get("second") or 0)==0 and abs(evsec(e)-cutoff)<60 for e in goals):
        row.update(result="UNKNOWN",reason="GOAL_ON_ZERO_SECOND_NEAR_WINDOW_BOUNDARY")
        return row
    row.update(final_whistle_elapsed_sec=final,last120_boundary_elapsed_sec=cutoff,
               goals_elapsed_sec=sorted(all_goal_seconds),
               seconds_from_goal_to_whistle=sorted([round(final-evsec(e),2) for e in late]),
               goal_count_in_last120s=len(late))
    if late:
        result="GOAL"; reason="OPTА_EXACT_SECONDS"
    else:
        result="NO_GOAL"; reason="OPTА_EXACT_SECONDS"
    # Score at start of the final-120s interval when scorer-team attribution reconciles.
    h_id,a_id=str(f.get("home_team_id")),str(f.get("away_team_id"))
    if all(str(e.get("team_id")) in (h_id,a_id) for e in goals):
        home_before=sum(1 for e in goals if str(e.get("team_id"))==h_id and evsec(e)<cutoff)
        away_before=sum(1 for e in goals if str(e.get("team_id"))==a_id and evsec(e)<cutoff)
        home_all=sum(1 for e in goals if str(e.get("team_id"))==h_id)
        away_all=sum(1 for e in goals if str(e.get("team_id"))==a_id)
        if home_all==t["home_goals"] and away_all==t["away_goals"]:
            row["score_at_window_start"]=f"{home_before}-{away_before}"
    if result=="NO_GOAL" and not row.get("score_at_window_start"):
        row["score_at_window_start"]=t["score"]
    row.update(result=result,reason=reason)
    return row

def classify_minute(t,doc,source_label=None):
    row={k:v for k,v in t.items() if k!="list_halfs"}
    row["source"]=source_label or "FotMob displayed goal minute + final-whistle timestamps (minute-level; conservative)"
    header=doc.get("header") or {}; status=header.get("status") or {}
    halfs=status.get("halfs") or t.get("list_halfs") or {}
    start=parse_datetime(halfs.get("secondHalfStarted")); end=parse_datetime(halfs.get("gameEnded"))
    teams=header.get("teams") or []
    score_total=t["home_goals"]+t["away_goals"]
    evts=((doc.get("content") or {}).get("matchFacts") or {}).get("events") or {}
    events=evts.get("events") or []
    goals=[e for e in events if e.get("type")=="Goal" and not e.get("isPenaltyShootoutEvent")]
    minutes=[parse_goal_minute(e) for e in goals]
    endsec=2700+(end-start).total_seconds() if start and end else None
    row.update(goal_minutes=minutes,goal_events=len(goals),expected_goal_events=score_total,
               second_half_started=start.isoformat() if start else None,game_ended=end.isoformat() if end else None,
               final_whistle_elapsed_sec=round(endsec,2) if endsec is not None else None)
    if not status.get("finished") or len(goals)!=score_total:
        row.update(result="UNKNOWN",reason="FINISH_OR_GOAL_COUNT_NOT_VERIFIED");return row
    if any(m is None for m in minutes):
        row.update(result="UNKNOWN",reason="GOAL_MINUTE_UNPARSEABLE");return row
    if endsec is None or not 5400<=endsec<=6900:
        row.update(result="UNKNOWN",reason="WHISTLE_OR_HALF_START_MISSING");return row
    cutoff=endsec-120
    # Displayed goal minute m occupies [(m-1)*60,m*60). Never guess the second.
    definitely_late=[m for m in minutes if (m-1)*60>=cutoff and (m-1)*60<endsec]
    if definitely_late:
        row.update(result="GOAL",reason="MINUTE_INTERVAL_ENTIRELY_INSIDE_LAST120",last120_boundary_elapsed_sec=round(cutoff,2));return row
    if all(m*60<=cutoff for m in minutes):
        row.update(result="NO_GOAL",reason="ALL_GOAL_MINUTE_INTERVALS_BEFORE_BOUNDARY",last120_boundary_elapsed_sec=round(cutoff,2));return row
    row.update(result="UNKNOWN",reason="DISPLAYED_MINUTE_OVERLAPS_120S_BOUNDARY",last120_boundary_elapsed_sec=round(cutoff,2))
    return row

def main():
    targets=find_matches()
    print("FOTMOB_FINISHED_TARGETS",len(targets),flush=True)
    if not targets: raise SystemExit("No finished matches found from FotMob for the target date.")
    targets_by=collections.Counter(t["league"] for t in targets)
    tmpdir=None; final_rows=[]; joins=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=pathlib.Path(td); fp=tmp/"opta_fixtures.parquet";download("opta_fixtures.parquet",fp)
        fixture_table=pq.read_table(fp,columns=["match_id","competition","season","match_date","match_status","home_team","away_team","home_score","away_score","home_team_id","away_team_id"])
        fixtures=fixture_table.to_pylist()
        selected,join_errors=pick_optas(targets,fixtures)
        joins.extend(join_errors)
        print("OPTА_JOIN",json.dumps({"matched":len(selected),"eligible_big5":sum(t["league"] in OPTA_CODE for t in targets),"errors":join_errors},ensure_ascii=False),flush=True)
        day_inventory=collections.Counter((str(f.get("competition")),str(f.get("season")),str(f.get("match_status"))) for f in fixtures if DAY in str(f.get("match_date") or ""))
        print("OPTA_FIXTURE_DAY_INVENTORY",json.dumps([{"competition":k[0],"season":k[1],"status":k[2],"count":v} for k,v in day_inventory.items()],ensure_ascii=False),flush=True)
        events_by_id=collections.defaultdict(list)
        for league,code in OPTA_CODE.items():
            required={str(x["fixture"]["match_id"]) for fid,x in selected.items() if next(t for t in targets if t["fotmob_id"]==fid)["league"]==league}
            if not required: continue
            p=tmp/("events_"+code+".parquet");download("events_"+code+".parquet",p)
            reader=pq.ParquetFile(p); cols=reader.schema_arrow.names
            need=["match_id","type_id","minute","second","period_id","team_id"]
            if not all(x in cols for x in need):
                joins.append({"league":league,"why":"OPTA_EVENT_SCHEMA_MISSING","columns":cols});continue
            id_type=reader.schema_arrow.field("match_id").type
            for batch in reader.iter_batches(batch_size=50000,columns=need):
                tbl=pa.Table.from_batches([batch])
                id_values=pa.array(list(required),type=id_type)
                ids=pc.is_in(tbl["match_id"],value_set=id_values)
                kinds=pc.is_in(tbl["type_id"],value_set=pa.array([16,30],type=tbl.schema.field("type_id").type))
                for e in tbl.filter(pc.and_(ids,kinds)).to_pylist(): events_by_id[str(e["match_id"])].append(e)
            print("OPTA_EVENTS_LOADED",league,len(required),sum(len(events_by_id[x]) for x in required),flush=True)
            p.unlink(missing_ok=True)
        for t in targets:
            hit=selected.get(t["fotmob_id"])
            opta_row=None
            if t["league"] in OPTA_CODE and hit:
                mid=str(hit["fixture"]["match_id"])
                opta_row=classify_opta(t,hit["fixture"],events_by_id[mid],hit["method"])
                if opta_row["result"] in ("GOAL","NO_GOAL"):
                    opta_row["precision"]="EXACT_OPTА_SECONDS"
                    final_rows.append(opta_row)
                    continue
            try:
                doc=fotmob("matchDetails",matchId=t["fotmob_id"])
                fallback_reason=(opta_row or {}).get("reason") or ("OPTA_FIXTURE_JOIN_FAILED" if t["league"] in OPTA_CODE else "RPL_HAS_NO_VERIFIED_OPTА_SECOND_STREAM")
                row=classify_minute(t,doc,source_label="FotMob minute intervals + observed second-half start/whistle time; conservative")
                row["precision"]="MINUTE_INTERVAL_ONLY"
                if t["league"] in OPTA_CODE:
                    row["exact_opta_status"]=(opta_row or {}).get("result","UNKNOWN")
                    row["exact_opta_reason"]=fallback_reason
                row["classification_rule"]="GOAL only if displayed minute interval is entirely inside last 120s; NO_GOAL only if every goal minute interval ends before cutoff; else UNKNOWN"
            except Exception as error:
                if opta_row is not None and opta_row.get("result")=="UNKNOWN":
                    row=opta_row
                else:
                    row={k:v for k,v in t.items() if k!="list_halfs"}
                    row.update(source="FotMob matchDetails unavailable",precision="UNVERIFIED",result="UNKNOWN",reason="DETAIL_FETCH_ERROR",error=str(error)[:180])
            final_rows.append(row)
    by_league={}
    for league in LEAGUES.values():
        z=[x for x in final_rows if x["league"]==league]
        by_league[league]={"matches":len(z),"outcomes":dict(collections.Counter(x["result"] for x in z)),
                           "unknown_reasons":dict(collections.Counter(x["reason"] for x in z if x["result"]=="UNKNOWN"))}
    summary={"date":DAY,"matches":len(final_rows),"targets_by_league":dict(targets_by),
             "overall":dict(collections.Counter(x["result"] for x in final_rows)),"by_league":by_league,
             "join_errors":joins,"positive_matches":[{k:x.get(k) for k in ("league","date","home","away","score","result","seconds_from_goal_to_whistle","goal_minutes","reason")} for x in final_rows if x["result"]=="GOAL"],
             "unknown_matches":[{k:x.get(k) for k in ("league","date","home","away","score","result","reason","goal_minutes","final_whistle_elapsed_sec")} for x in final_rows if x["result"]=="UNKNOWN"]}
    (OUT/"matches.json").write_text(json.dumps(final_rows,ensure_ascii=False,indent=2))
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    with open(OUT/"matches.csv","w",encoding="utf-8-sig",newline="") as f:
        fields=["date","league","home","away","score","result","reason","source","score_at_window_start","goal_count_in_last120s","seconds_from_goal_to_whistle","goal_minutes","final_whistle_elapsed_sec","last120_boundary_elapsed_sec","join_method","fotmob_id","opta_fixture_id"]
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(final_rows)
    lines=[f"# Анализ матчей за {DAY}: гол в последние 120 секунд", "",
           "**Строгое определение:** гол между фактическим концом второго тайма и 120 секундами до него. Для пяти лиг использованы секунды события гола и финального события второго тайма из одного массива Opta. Для РПЛ используется отдельная минутная классификация; пограничные события оставлены UNKNOWN.", "",
           "| Лига | Матчей | GOAL | NO_GOAL | UNKNOWN |", "|---|---:|---:|---:|---:|"]
    for league in LEAGUES.values():
        z=by_league[league];o=z["outcomes"];lines.append(f"| {OFFICIAL_NAMES[league]} | {z['matches']} | {o.get('GOAL',0)} | {o.get('NO_GOAL',0)} | {o.get('UNKNOWN',0)} |")
    lines += ["","## Подтверждённые голы в последние 120 секунд",""]
    if summary["positive_matches"]:
        for x in summary["positive_matches"]:
            desc=", ".join(f"{s:.0f} секунд до свистка" for s in (x.get("seconds_from_goal_to_whistle") or []))
            lines.append(f"- {x['league']}: {x['home']} — {x['away']} ({x['score']}), {desc or 'попадание подтверждено'}; {x.get('reason')}.")
    else: lines.append("Нет матчей с подтверждённым голом в окне среди проверенных событий.")
    lines += ["","## Неопределённые матчи",""]
    if summary["unknown_matches"]:
        for x in summary["unknown_matches"]: lines.append(f"- {x['league']}: {x['home']} — {x['away']} ({x['score']}): {x['reason']}.")
    else: lines.append("Нет.")
    lines += ["","## Ключевое ограничение","","Результат UNKNOWN — это недостаток или несогласованность временных данных, а не NO_GOAL. Оценка относится только к перечисленным завершённым матчам указанной даты.", "", "## Сводка JSON", "```json", json.dumps(summary,ensure_ascii=False,indent=2), "```"]
    (OUT/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("LAST120_YESTERDAY_SUMMARY="+json.dumps(summary,ensure_ascii=False),flush=True)
    if not final_rows: raise SystemExit("No classified target match results.")

if __name__=="__main__": main()
