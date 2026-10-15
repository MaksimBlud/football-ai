"""Research-only: resolve final 120s with *same-provider* Opta End events (type 30).
Never writes database or production. Match joins from verified Opta previous pass.
"""
import collections, json, pathlib, tempfile, urllib.request, math
import pyarrow.parquet as pq

DIR=pathlib.Path('research/last120_20261015')
MATCHES=json.loads((DIR/'combined_matches.json').read_text())
UNRESOLVED=[m for m in MATCHES if m['result']=='UNKNOWN']
LEAGUE={'SERIE_A':'Serie_A','LIGUE_1':'Ligue_1'}
BASE='https://github.com/peteowen1/pannadata/releases/download/opta-latest/'
BY_LEAGUE=collections.defaultdict(list)
for m in UNRESOLVED:
    ext=m.get('opta_crosscheck') or {}
    if ext.get('opta_match_id') and m['league'] in LEAGUE:
        BY_LEAGUE[m['league']].append(m)

def secs(e):
    if not isinstance(e.get('minute'),(int,float)) or not isinstance(e.get('second'),(int,float)):return None
    return float(e['minute'])*60+float(e['second'])

def fetch(name,file):
    req=urllib.request.Request(BASE+name,headers={'User-Agent':'football-ai-public-research'})
    with urllib.request.urlopen(req,timeout=120) as resp, open(file,'wb') as out:
        while True:
            part=resp.read(1024*1024)
            if not part:break
            out.write(part)
    print('FULL_OPTA_DOWNLOADED',name,file.stat().st_size,flush=True)

results={}
with tempfile.TemporaryDirectory() as td:
    for league,needed in BY_LEAGUE.items():
        target_ids={str(m['opta_crosscheck']['opta_match_id']) for m in needed}
        local=pathlib.Path(td)/f'{league}.parquet'
        fetch(f'events_{LEAGUE[league]}.parquet',local)
        reader=pq.ParquetFile(local)
        cols=reader.schema_arrow.names
        print('FULL_OPTA_COLUMNS',league,cols,flush=True)
        required={'match_id','minute','second','type_id'}
        if not required.issubset(cols):
            for m in needed:
                results[m['id']]={'result':'UNKNOWN','reason':'NO_WHISTLE_EVENT_COLUMNS'}
            continue
        use=[a for a in ('match_id','minute','second','type_id','period_id','period','event_id') if a in cols]
        matched=collections.defaultdict(list)
        for batch in reader.iter_batches(batch_size=12000,columns=use):
            for row in batch.to_pylist():
                if str(row['match_id']) in target_ids and str(row.get('type_id')) in ('30','30.0','16','16.0','37','37.0','32','32.0'):
                    matched[str(row['match_id'])].append(row)
        for m in needed:
            opta_id=str(m['opta_crosscheck']['opta_match_id'])
            evs=matched[opta_id]
            ends=sorted((v for v in evs if str(v.get('type_id')) in ('30','30.0') and secs(v) is not None),key=secs)
            goals=sorted((v for v in evs if str(v.get('type_id')) in ('16','16.0') and secs(v) is not None),key=secs)
            desired=int(m['score'].split('-')[0].strip())+int(m['score'].split('-')[1].strip())
            target_minute=m['goal_minutes'][-1]
            late_goals=[g for g in goals if math.ceil(secs(g)/60)==target_minute]
            rec={'league':league,'date':m['date'],'home':m['home'],'away':m['away'],'id':m['id'],
             'match_id_opta':opta_id,'end_events':ends[-4:],'recent_goal_events':goals[-4:],
             'opta_goals':len(goals),'expected_goals':desired,
             'final_fotmob_elapsed_seconds':m['final_clock_seconds']}
            if len(goals)!=desired:rec.update(result='UNKNOWN',reason='FULL_EVENTS_GOAL_COUNT_MISMATCH')
            elif not ends:rec.update(result='UNKNOWN',reason='NO_OPTA_END_EVENT')
            elif not late_goals:rec.update(result='UNKNOWN',reason='LATE_GOAL_NOT_UNIQUELY_MATCHED')
            elif len(late_goals)!=1:rec.update(result='UNKNOWN',reason='MULTIPLE_LATE_GOALS')
            else:
                final=secs(ends[-1])
                elapsed=secs(late_goals[-1])
                rec['end_seconds']=final
                rec['goal_seconds']=elapsed
                rec['seconds_to_whistle']=final-elapsed
                if final<90*60 or elapsed>final:rec.update(result='UNKNOWN',reason='INCONSISTENT_OPTA_END_CLOCK')
                elif final-elapsed<=120:rec.update(result='GOAL',reason='SAME_SOURCE_GOAL_WITHIN_120S')
                else:rec.update(result='NO_GOAL',reason='SAME_SOURCE_GOAL_BEFORE_120S')
            results[m['id']]=rec
            print('OPTA_WHISTLE_RESOLUTION='+json.dumps(rec,ensure_ascii=False,default=str),flush=True)

for m in MATCHES:
    new=results.get(m['id'])
    if new:
        m['opta_whistle_crosscheck']=new
        if new['result']!='UNKNOWN':m.update(result=new['result'],reason=new['reason'])
summ={'matches':len(MATCHES),'totals':dict(collections.Counter(m['result'] for m in MATCHES)),
      'leagues':{},'remaining_unknown':[], 'same_provider_whistle_check':results}
for league in ('EPL','LA_LIGA','BUNDESLIGA','SERIE_A','LIGUE_1'):
    subset=[m for m in MATCHES if m['league']==league]
    summ['leagues'][league]={'matches':len(subset),'outcomes':dict(collections.Counter(m['result'] for m in subset))}
summ['remaining_unknown']=[{k:m.get(k) for k in ('id','league','date','home','away','reason')} for m in MATCHES if m['result']=='UNKNOWN']
(DIR/'same_provider_whistle.json').write_text(json.dumps(summ,ensure_ascii=False,indent=2,default=str))
(DIR/'final_matches.json').write_text(json.dumps(MATCHES,ensure_ascii=False,indent=2,default=str))
print('FINAL_WHISTLE_AUDIT='+json.dumps({k:v for k,v in summ.items() if k!='same_provider_whistle_check'},ensure_ascii=False),flush=True)
