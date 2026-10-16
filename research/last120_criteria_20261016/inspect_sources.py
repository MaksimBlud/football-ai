"""Inspect publicly downloadable Opta data availability for leakage-safe historical research."""
import collections, json, pathlib, tempfile, urllib.request
import pyarrow.parquet as pq
BASE='https://github.com/peteowen1/pannadata/releases/download/opta-latest/'
def download(name,path):
 req=urllib.request.Request(BASE+name,headers={'User-Agent':'football-ai-research'})
 with urllib.request.urlopen(req,timeout=70) as r,open(path,'wb') as w:
  while True:
   b=r.read(1024*1024)
   if not b:break
   w.write(b)
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'fixtures.parquet';download('opta_fixtures.parquet',p)
 t=pq.read_table(p)
 print('FIXTURE_SCHEMA',str(t.schema),flush=True)
 rr=[x for x in t.to_pylist() if x.get('competition') in ('EPL','La_Liga','Bundesliga','Serie_A','Ligue_1')]
 print('FIXTURE_SEASON_COUNTS',sorted(collections.Counter((str(x.get('season')),x.get('competition')) for x in rr).items()),flush=True)
 print('FIXTURE_SAMPLE',json.dumps(rr[-2:],default=str,ensure_ascii=False),flush=True)
 p=pathlib.Path(d)/'events.parquet';download('opta_events.parquet',p)
 f=pq.ParquetFile(p);print('LATEST_EVENTS_SCHEMA',str(f.schema_arrow),flush=True)
 ev=f.read(columns=[k for k in ('match_id','minute','second','event_type','period_id','season','competition') if k in f.schema_arrow.names])
 print('LATEST_EVENTS_SAMPLE',json.dumps(ev.slice(0,3).to_pylist(),default=str,ensure_ascii=False),flush=True)
 p=pathlib.Path(d)/'matchstats.parquet'
 download('opta_match_stats.parquet',p)
 q=pq.ParquetFile(p); print('MATCH_STATS_SCHEMA',str(q.schema_arrow),flush=True)
 print('MATCH_STATS_ROWS',q.metadata.num_rows,flush=True)
