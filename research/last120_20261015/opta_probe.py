"""Independently check ambiguous last-120s goal timestamps against public Opta.
All downloads are read-only; no Supabase, production model, or paid APIs.
"""
import collections
import json
import pathlib
import re
import tempfile
import unicodedata
import urllib.request
import pyarrow.parquet as pq

ROOT=pathlib.Path('research/last120_20261015')
BASE='https://github.com/peteowen1/pannadata/releases/download/opta-latest/'
LEAGUE={'EPL':'EPL','LA_LIGA':'La_Liga','BUNDESLIGA':'Bundesliga','SERIE_A':'Serie_A','LIGUE_1':'Ligue_1'}
GUARD_SECONDS=15  # conservative cross-vendor timing guard, not a betting threshold
matches=json.loads((ROOT/'matches.json').read_text())
unresolved=[r for r in matches if r['result']=='UNKNOWN']

def normalized(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s)).lower() if c.isalnum())

def same_team(a,b):
    x,y=normalized(a),normalized(b)
    return bool(x and y and (x in y or y in x or 
       any(len(w)>=5 and normalized(w) in y for w in str(a).split())))

def download(name, path):
    req=urllib.request.Request(BASE+name, headers={'User-Agent':'research-last120'})
    with urllib.request.urlopen(req,timeout=90) as response, open(path,'wb') as target:
        while True:
            chunk=response.read(2*1024*1024)
            if not chunk: break
            target.write(chunk)
    print('DOWNLOADED',name,path.stat().st_size,flush=True)

def match_fixture(target,fixtures):
    league=LEAGUE[target['league']]
    date=target['date']
    score=target['score']
    candidates=[r for r in fixtures if r.get('competition')==league
        and date in str(r.get('match_date',''))
        and f"{r.get('home_score')} - {r.get('away_score')}"==score]
    strict=[r for r in candidates if same_team(target['home'],r['home_team'])
        and same_team(target['away'],r['away_team'])]
    if len(strict)==1:return strict[0],None
    if len(candidates)==1 and same_team(target['away'],candidates[0]['away_team']):
        return candidates[0],None
    return None,f"JOIN_AMBIGUOUS:{len(candidates)} candidates; {len(strict)} strict"

with tempfile.TemporaryDirectory() as folder:
    directory=pathlib.Path(folder)
    fixtures_file=directory/'fixtures.parquet'
    download('opta_fixtures.parquet',fixtures_file)
    fixtures=pq.read_table(fixtures_file).to_pylist()
    decisions=[]
    ids=set()
    for target in unresolved:
        match,error=match_fixture(target,fixtures)
        decisions.append({'fotmob_match_id':target['id'],'league':target['league'],
          'date':target['date'],'home':target['home'],'away':target['away'],
          'score':target['score'],'opta_match_id':match['match_id'] if match else None,
          'join_error':error,'cutoff_second':target['final_clock_seconds']-120,
          'fotmob_goal_minutes':target['goal_minutes']})
        if match:ids.add(str(match['match_id']))
    print('MATCHED_OPTA_FIXTURES',len(ids),'OF',len(unresolved),flush=True)
    event_file=directory/'events.parquet'
    download('opta_events.parquet',event_file)
    table=pq.read_table(event_file)
    index=table.column('match_id').to_pylist()
    subset=table.take([i for i,k in enumerate(index) if str(k) in ids]).to_pylist()
    byid=collections.defaultdict(list)
    for ev in subset:
        if str(ev.get('event_type','')).lower() in ('goal','own_goal'):
            byid[str(ev['match_id'])].append(ev)
    resolved={}
    for rec in decisions:
        old=next(r for r in unresolved if r['id']==rec['fotmob_match_id'])
        result='UNKNOWN';reason=rec['join_error'] or 'UNVERIFIED_GOAL_SECONDS'
        if rec['opta_match_id']:
            events=byid[rec['opta_match_id']]
            wanted_total=sum(int(v.strip()) for v in rec['score'].split('-'))
            rec['opta_goal_total']=len(events)
            if len(events)!=wanted_total:
                reason='OPTA_GOAL_SCORE_MISMATCH'
            else:
                cutoff=rec['cutoff_second']
                ambiguous=[m for m in old['goal_minutes'] if (m-1)*60 < cutoff < m*60]
                joined=[]
                for m in ambiguous:
                    candidates=[x for x in events if x.get('minute') is not None
                       and int(x['minute'])==m-1 and x.get('second') is not None]
                    joined.extend(candidates)
                if len(joined)==1:
                    event=joined[0]
                    elapsed=float(event['minute'])*60+float(event['second'])
                    delta=elapsed-cutoff
                    rec['opta_goal']={'minute':event['minute'],'second':event['second'],
                       'scorer':event.get('player_name'),'elapsed_seconds':elapsed}
                    rec['delta_seconds_from_window_start']=round(delta,2)
                    if float(event['second'])==0:
                        reason='OPTA_SECOND_ZERO_POTENTIALLY_IMPUTED'
                    elif delta>GUARD_SECONDS:
                        result='GOAL';reason='CROSS_SOURCE_CONFIRMED_IN_WINDOW'
                    elif delta < -GUARD_SECONDS:
                        result='NO_GOAL';reason='CROSS_SOURCE_CONFIRMED_OUTSIDE_WINDOW'
                    else:
                        reason='CROSS_SOURCE_CLOCK_WITHIN_15S'
                else:
                    reason=f'GOAL_EVENT_JOIN_NOT_UNIQUE:{len(joined)}'
        rec.update({'result':result,'reason':reason,'clock_guard_seconds':GUARD_SECONDS})
        resolved[rec['fotmob_match_id']]=rec
        print('OPTA_RESOLUTION='+json.dumps(rec,ensure_ascii=False),flush=True)
    combined=[]
    for row in matches:
        r=dict(row)
        if r['id'] in resolved:
            evidence=resolved[r['id']]
            if evidence['result']!='UNKNOWN':
                r['result']=evidence['result']
                r['reason']=evidence['reason']
            r['opta_crosscheck']=evidence
        combined.append(r)
    summaries={}
    for league in LEAGUE:
        items=[v for v in combined if v['league']==league]
        summaries[league]={'matches':len(items),'status':dict(collections.Counter(v['result'] for v in items))}
    total=dict(collections.Counter(v['result'] for v in combined))
    report={'matches':len(combined),'status':total,'leagues':summaries,
       'remaining_unknown':[{k:r.get(k) for k in ('id','date','league','home','away','reason')}
         for r in combined if r['result']=='UNKNOWN'],
       'clock_cross_source_guard_seconds':GUARD_SECONDS}
    (ROOT/'opta_resolution.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2))
    (ROOT/'combined_matches.json').write_text(json.dumps(combined,ensure_ascii=False,indent=2))
    (ROOT/'combined_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('FINAL_LAST120='+json.dumps(report,ensure_ascii=False),flush=True)
