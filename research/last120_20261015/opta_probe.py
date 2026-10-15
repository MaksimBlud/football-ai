"""Read-only Opta seconds probe for unresolved final-two-minute matches."""
import json,pathlib,tempfile,urllib.request
import pyarrow as pa,pyarrow.compute as pc,pyarrow.parquet as pq
BASE='https://github.com/peteowen1/pannadata/releases/download/opta-latest/'
IN=pathlib.Path('research/last120_20261015/matches.json')
targets=[v for v in json.loads(IN.read_text()) if v['result']=='UNKNOWN']
wanted_dates=set(x['date'] for x in targets)
def download(name,path):
 urllib.request.urlretrieve(BASE+name,str(path));print('OPTA_FILE',name,path.stat().st_size,flush=True)
def sample(row):
 return {x:row.get(x) for x in ('match_id','match_date','home_team','away_team','home_score','away_score','competition','season')}
with tempfile.TemporaryDirectory() as temp:
 root=pathlib.Path(temp)
 f=root/'fixtures.parquet'; download('opta_fixtures.parquet',f)
 pf=pq.ParquetFile(f);print('FIXTURES_SCHEMA',str(pf.schema_arrow),flush=True)
 t=pf.read();rows=[v for v in t.to_pylist() if str(v.get('match_date')) in wanted_dates and str(v.get('season','')).startswith('2026')]
 print('FIXTURES_IN_TARGET_DATES',len(rows),flush=True)
 for target in targets:
  close=[sample(v) for v in rows if str(v.get('match_date'))==target['date'] and
    target['home'].lower().split()[0] in str(v.get('home_team','')).lower() and
    target['away'].lower().split()[0] in str(v.get('away_team','')).lower()]
  print('OPTA_TARGET_FIXTURE='+json.dumps({'target':{k:target[k] for k in ('id','league','date','home','away','score')},'matches':close},default=str,ensure_ascii=False),flush=True)
 e=root/'events.parquet';download('opta_events.parquet',e)
 pe=pq.ParquetFile(e); print('OPTA_EVENTS_SCHEMA',str(pe.schema_arrow),flush=True)
 matches_ids=set(str(v['match_id']) for v in rows)
 data=pe.read();tcols=set(data.column_names)
 if 'event_type' not in tcols: raise RuntimeError('Missing event_type')
 event_rows=[v for v in data.to_pylist() if str(v.get('match_id')) in matches_ids and str(v.get('event_type','')).lower() in ('goal','own_goal')]
 print('OPTA_DATE_MATCH_GOALS',len(event_rows),flush=True)
 for v in event_rows:
  if v.get('minute',0)>=88:
   print('OPTA_GOAL='+json.dumps({k:v.get(k) for k in ('match_id','event_type','minute','second','player_name','team_id')},default=str,ensure_ascii=False),flush=True)
