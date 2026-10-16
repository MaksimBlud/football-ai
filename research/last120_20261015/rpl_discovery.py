import json,urllib.request,urllib.parse,collections,datetime,time
base='https://www.fotmob.com/api/data/'
headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}
def get(path,**params):
 url=base+path+'?'+urllib.parse.urlencode(params)
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=16) as r:return json.load(r)
obj=get('leagues',id=63)
data=[x for x in (obj.get('fixtures') or {}).get('allMatches',[]) if x.get('status',{}).get('finished') and (x.get('status',{}).get('utcTime') or '')[:10]<='2026-10-14' and (x.get('status',{}).get('utcTime') or '')[:10]>='2026-07-24']
print('FINISHED_UNTIL_OCT14',len(data),'ROUNDS',dict(collections.Counter(str(x.get('round')) for x in data)),flush=True)
print('LAST_FIXTURES',json.dumps(data[-5:],ensure_ascii=False)[:1700],flush=True)
for m in [data[0],data[2],data[len(data)//2],data[-1]]:
 try:
  doc=get('matchDetails',matchId=m['id'])
  g=doc.get('general') or {};h=doc.get('header') or {};status=h.get('status') or {}
  events=((doc.get('content') or {}).get('matchFacts') or {}).get('events',{}).get('events',[])
  shots=(doc.get('content') or {}).get('shotmap') or {}
  shotarr=shots.get('shots') or []
  print('DETAIL',json.dumps({'id':m['id'],'round':g.get('matchRound'),'league':g.get('leagueId'),'score':status.get('scoreStr'),'halfs':status.get('halfs'),
 'event_total':len(events),'goal_times':[(x.get('timeStr'),x.get('time'),x.get('overloadTime')) for x in events if x.get('type')=='Goal'],
 'shot_count':len(shotarr),'shot_example_keys':list(shotarr[0].keys()) if shotarr else [],'goal_shots_sample':[x for x in shotarr if x.get('shotType')=='Goal'][-1:]},ensure_ascii=False)[:2600],flush=True)
 except Exception as e:print('ERROR_DETAIL',m['id'],str(e)[:200],flush=True)
