"""Full read-only 2026/27 actual-final-120-second independent Opta replay.

Both goal timestamps and second-half end (Opta period 2 event type 30) come
from the SAME source and same elapsed match clock. Strict fixture+score joins;
unverifiable matches remain UNKNOWN. No database writes, no model changes.
"""
import collections, json, math, pathlib, tempfile, unicodedata, urllib.request
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT=pathlib.Path('research/last120_20261015')
BASE='https://github.com/peteowen1/pannadata/releases/download/opta-latest/'
LEAGUES={'EPL':'EPL','LA_LIGA':'La_Liga','BUNDESLIGA':'Bundesliga',
         'SERIE_A':'Serie_A','LIGUE_1':'Ligue_1'}
OLD=json.loads((ROOT/'final_matches.json').read_text())

def norm(x):
    s=''.join(c for c in unicodedata.normalize('NFKD',str(x)).lower() if c.isalnum())
    if 'auxerroise' in s or 'auxerre' in s: return 'auxerre'
    if 'rennais' in s or 'rennes' in s: return 'rennes'
    return s

def same_team(a,b):
    x,y=norm(a),norm(b)
    if len(x)>=4 and (x in y or y in x):return True
    pieces=[norm(w) for w in str(a).split()]
    return any(len(w)>=5 and w in y for w in pieces)

def download(name,path):
    req=urllib.request.Request(BASE+name,headers={'User-Agent':'football-ai-free-research'})
    with urllib.request.urlopen(req,timeout=110) as src,open(path,'wb') as out:
        while True:
            data=src.read(2*1024*1024)
            if not data:break
            out.write(data)
    print('FULL_FILE',name,path.stat().st_size,flush=True)

def eventsec(x):
    m,s=x.get('minute'),x.get('second')
    return float(m)*60+float(s) if isinstance(m,(int,float)) and isinstance(s,(int,float)) else None

def pick(target,fixtures):
    home,away=target['score'].split('-')
    eligible=[x for x in fixtures if x['competition']==LEAGUES[target['league']]
         and target['date'] in str(x.get('match_date','')) and
         str(x.get('home_score'))==home.strip() and
         str(x.get('away_score'))==away.strip() and
         str(x.get('season'))=='2026-2027' and
         str(x.get('match_status'))=='Played']
    strict=[x for x in eligible if same_team(target['home'],x['home_team']) and same_team(target['away'],x['away_team'])]
    if len(strict)==1:return strict[0],'JOIN_BOTH_TEAMS_SCORE_DATE'
    if len(eligible)==1 and (same_team(target['home'],eligible[0]['home_team']) or same_team(target['away'],eligible[0]['away_team'])):
        return eligible[0],'JOIN_UNIQUE_FIXTURE_ONE_TEAM'
    return None,'JOIN_UNRESOLVED:%d candidates,%d both_team'%(len(eligible),len(strict))

def assess(m,fixture,events):
    base=dict(m)
    ends=[x for x in events if int(x['type_id'])==30 and int(x.get('period_id') or 0)==2 and eventsec(x) is not None]
    goals=[x for x in events if int(x['type_id'])==16 and eventsec(x) is not None and int(x.get('period_id') or 0) in (1,2)]
    n=int(fixture['home_score'])+int(fixture['away_score'])
    base['opta_end_events']=len(ends)
    base['opta_goal_events']=len(goals)
    base['opta_fixture_id']=str(fixture['match_id'])
    if len(goals)!=n or not ends:
        return base,'UNKNOWN','SAME_SOURCE_MISSING_GOALS_OR_END'
    end_times=sorted(set(eventsec(e) for e in ends))
    final=end_times[-1]
    if final<5400 or final>7200 or end_times[-1]-end_times[0]>3:
        return base,'UNKNOWN','INCONSISTENT_FINAL_END_EVENT'
    if any(eventsec(e)>final for e in goals):
        return base,'UNKNOWN','GOAL_AFTER_OPTAD_END'
    cutoff=final-120
    late=[e for e in goals if eventsec(e)>=cutoff and eventsec(e)<=final]
    before=[e for e in goals if eventsec(e)<cutoff]
    close_zero=[e for e in goals if e['second']==0 and abs(eventsec(e)-cutoff)<60]
    base.update(opta_final_second=final,opta_boundary_second=cutoff,
      opta_seconds_to_whistle=[round(final-eventsec(e),2) for e in late],
      opta_late_goal_count=len(late),
      opta_goal_event_seconds=[eventsec(e) for e in goals])
    if close_zero:
        return base,'UNKNOWN','OPTA_ZERO_SECOND_NEAR_CUTOFF'
    teams=(str(fixture['home_team_id']),str(fixture['away_team_id']))
    if all(str(e.get('team_id')) in teams for e in goals):
        if sum(str(e['team_id'])==teams[0] for e in goals)==int(fixture['home_score']) and sum(str(e['team_id'])==teams[1] for e in goals)==int(fixture['away_score']):
            h=sum(str(e['team_id'])==teams[0] for e in before)
            a=sum(str(e['team_id'])==teams[1] for e in before)
            base['score_at_window_start']=[h,a]
            base['score_gap_at_window_start']=abs(h-a)
    if not late and base.get('score_gap_at_window_start') is None:
        h,a=int(fixture['home_score']),int(fixture['away_score'])
        base['score_at_window_start']=[h,a]
        base['score_gap_at_window_start']=abs(h-a)
    return base,'GOAL' if late else 'NO_GOAL','SAME_SOURCE_OPTA_GOAL_AND_FINAL_END'

with tempfile.TemporaryDirectory() as td:
    tmp=pathlib.Path(td)
    f=tmp/'opta_fixtures.parquet';download('opta_fixtures.parquet',f)
    fixtures=pq.read_table(f).to_pylist()
    selected={};match_used=collections.defaultdict(list);join_errors=[]
    for m in OLD:
        fixture,why=pick(m,fixtures)
        if fixture:
            selected[m['id']]=(fixture,why)
            match_used[str(fixture['match_id'])].append(m['id'])
        else:
            join_errors.append({'id':m['id'],'league':m['league'],'date':m['date'],
                                'home':m['home'],'away':m['away'],'reason':why})
    collisions={k:v for k,v in match_used.items() if len(v)>1}
    for ids in collisions.values():
        for i in ids:
            selected.pop(i,None)
    print('FIXTURE_JOIN',json.dumps({'matched':len(selected),'total':len(OLD),
         'unmatched':join_errors,'collisions':collisions},ensure_ascii=False),flush=True)
    all_events=collections.defaultdict(list)
    for league,code in LEAGUES.items():
        required={str(f['match_id']) for i,(f,why) in selected.items() if next(m for m in OLD if m['id']==i)['league']==league}
        if not required:continue
        path=tmp/('events_'+code+'.parquet')
        download('events_'+code+'.parquet',path)
        reader=pq.ParquetFile(path)
        colnames=reader.schema_arrow.names
        needed=['match_id','type_id','minute','second','period_id','team_id']
        if any(x not in colnames for x in needed):
            print('MISSING_COLS',league,colnames,flush=True)
            continue
        for batch in reader.iter_batches(batch_size=50000,columns=needed):
            tbl=pa.Table.from_batches([batch])
            ids=pc.is_in(tbl['match_id'],value_set=pa.array(list(required),type=tbl['match_id'].type))
            kinds=pc.is_in(tbl['type_id'],value_set=pa.array([16,30],type=tbl['type_id'].type))
            filtered=tbl.filter(pc.and_(ids,kinds))
            for e in filtered.to_pylist():
                all_events[str(e['match_id'])].append(e)
        print('LEAGUE_LOADED',league,len(required),
            sum(len(all_events[mid]) for mid in required),flush=True)
        path.unlink()
    final=[]
    for m in OLD:
        row=dict(m);new_result='UNKNOWN';why='JOIN_UNRESOLVED'
        if m['id'] in selected:
            fixture,join=selected[m['id']]
            row,new_result,why=assess(m,fixture,all_events[str(fixture['match_id'])])
            row['opta_fixture_match_method']=join
        row['prior_result']=m['result']
        row.update(result=new_result,reason=why)
        final.append(row)
    report={'matches':len(final),'totals':dict(collections.Counter(m['result'] for m in final)),
        'leagues':{},'changed':[],'unknown':[],'by_score_gap':{},'join_errors':join_errors}
    for league in LEAGUES:
        rows=[x for x in final if x['league']==league]
        report['leagues'][league]={'matches':len(rows),'outcomes':dict(collections.Counter(x['result'] for x in rows))}
    for x in final:
        if x['prior_result']!=x['result']:
            report['changed'].append({k:x.get(k) for k in ('id','league','date','home','away','prior_result','result','opta_seconds_to_whistle','reason')})
        if x['result']=='UNKNOWN':
            report['unknown'].append({k:x.get(k) for k in ('id','league','date','home','away','reason')})
    for gap in ('0','1','2','3+'):
        subset=[m for m in final if m.get('score_gap_at_window_start') is not None and
            (str(m['score_gap_at_window_start'])==gap if gap!='3+' else m['score_gap_at_window_start']>=3)]
        report['by_score_gap'][gap]=dict(collections.Counter(x['result'] for x in subset))
    report['positive_matches']=[{'league':m['league'],'date':m['date'],'home':m['home'],
        'away':m['away'],'score':m['score'],'seconds_to_whistle':m.get('opta_seconds_to_whistle',[]),
        'goal_events':m.get('opta_late_goal_count',0)}
        for m in sorted(final,key=lambda v:(v['league'],v['date'],v['home'])) if m['result']=='GOAL']
    report['total_goals_last_120s']=sum(v.get('opta_late_goal_count',0) for v in final if v['result']=='GOAL')
    minute_bins=collections.Counter()
    for match in final:
        if match['result']=='UNKNOWN':continue
        for elapsed in match.get('opta_goal_event_seconds',[]):
            if elapsed>=5400:
                minute_bins[1+int((elapsed-5400)//60)]+=1
    report['goal_counts_by_stoppage_minute']={f'90+{m}':minute_bins[m] for m in sorted(minute_bins)}
    (ROOT/'all_opta_matches.json').write_text(json.dumps(final,ensure_ascii=False,indent=2))
    (ROOT/'all_opta_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('COMPLETE_OPTA_AUDIT='+json.dumps(report,ensure_ascii=False),flush=True)
