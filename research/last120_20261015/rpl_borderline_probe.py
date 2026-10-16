"""Check whether RPL source returns second-resolution timestamps of borderline goals."""
import json,urllib.request,urllib.parse
headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}
for mid in [5847125,5847135,5847147,5847165]:
 url='https://www.fotmob.com/api/data/matchDetails?matchId='+str(mid)
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=18) as r:d=json.load(r)
 content=d.get('content') or {}
 print('MATCH',mid,'CONTENT_KEYS',list(content),flush=True)
 facts=content.get('matchFacts') or {}
 ticker=content.get('liveticker') or {}
 print('TICKER_TYPE',type(ticker).__name__,'TICKER_KEYS',list(ticker)[:30] if isinstance(ticker,dict) else 'other',flush=True)
 print('TICKER_SAMPLE',json.dumps(ticker,ensure_ascii=False)[:2900],flush=True)
 eventpack=facts.get('events') or {}
 arr=eventpack.get('events') or []
 print('GOALS',json.dumps([x for x in arr if x.get('type')=='Goal'],ensure_ascii=False)[-2300:],flush=True)
 shots=(content.get('shotmap') or {}).get('shots') or []
 print('LATE_SHOTS',json.dumps([x for x in shots if (x.get('min') or 0)>=89],ensure_ascii=False)[-2800:],flush=True)
