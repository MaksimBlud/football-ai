"""Read-only last-120-second research: no production/database writes."""
import concurrent.futures as cf
import datetime as D
import json, pathlib, re, time, urllib.parse, urllib.request
from collections import Counter
LEAGUES={47:'EPL',87:'LA_LIGA',54:'BUNDESLIGA',55:'SERIE_A',53:'LIGUE_1'}
OUTPUT=pathlib.Path('research/last120_20261015'); OUTPUT.mkdir(parents=True,exist_ok=True)

def get(name,**args):
 url='https://www.fotmob.com/api/data/'+name+'?'+urllib.parse.urlencode(args)
 for i in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
   with urllib.request.urlopen(req,timeout=15) as response:return json.load(response)
  except Exception as error:
   if i==2:raise RuntimeError(str(error)[:150])
   time.sleep((i+1)*2)

def datestring(s):
 if not s:return None
 for fmt in ('%d.%m.%Y %H:%M:%S','%Y-%m-%dT%H:%M:%S.%fZ'):
  try:return D.datetime.strptime(s,fmt)
  except ValueError:pass
 return None

def find_day(day):
 obj=get('matches',date=day.strftime('%Y%m%d')); ret=[]
 for group in obj.get('leagues',[]):
  code=int(group.get('primaryId') or group.get('id') or -1)
  if code not in LEAGUES:continue
  for match in group.get('matches',[]):
   status=match.get('status') or {}
   if not status.get('finished') or status.get('cancelled') or status.get('awarded'):continue
   ret.append({'id':str(match['id']),'date':str(day),'league':LEAGUES[code],
     'home':(match.get('home') or {}).get('name'),'away':(match.get('away') or {}).get('name'),
     'score':status.get('scoreStr'),'list_halfs':status.get('halfs') or {}})
 return ret

def minute(goal):
 s=str(goal.get('timeStr') or goal.get('time') or '').strip().replace("'",'').replace(' ','')
 m=re.match(r'^(\d+)(?:\+(\d+))?$',s)
 return int(m[1])+int(m[2] or 0) if m else None

def audit(item):
 out=dict(item)
 try:
  doc=get('matchDetails',matchId=item['id']); status=(doc.get('header') or {}).get('status') or {}
  half=status.get('halfs') or {}; extra=item['list_halfs']
  start=datestring(half.get('secondHalfStarted') or extra.get('secondHalfStarted'))
  end=datestring(half.get('gameEnded') or extra.get('gameEnded'))
  endsec=2700+(end-start).total_seconds() if start and end else None
  if endsec is not None and not 5400<=endsec<=6900:endsec=None
  events=((((doc.get('content') or {}).get('matchFacts') or {}).get('events') or {}).get('events') or [])
  goals=[x for x in events if x.get('type')=='Goal' and not x.get('isPenaltyShootoutEvent')]
  teams=(doc.get('header') or {}).get('teams') or []
  n=sum(int(x['score']) for x in teams) if len(teams)==2 and all(x.get('score') is not None for x in teams) else None
  mins=[minute(x) for x in goals];out['unparsed_goal_clocks']=[{'time':x.get('time'),'timeStr':x.get('timeStr'),'overloadTime':x.get('overloadTime')} for x in goals if minute(x) is None];out.update({'goal_minutes':mins,'final_clock_seconds':endsec,
   'second_half_started':start.isoformat() if start else None,'game_ended':end.isoformat() if end else None})
  if not status.get('finished') or n is None or n!=len(goals):ans='UNKNOWN';reason='GOALS_VS_SCORE_MISMATCH'
  elif any(m is None for m in mins):ans='UNKNOWN';reason='MINUTE_MISSING'
  elif not mins or max(mins)<=88:ans='NO_GOAL';reason='NO_GOALS_AFTER_88'
  elif endsec is None:ans='UNKNOWN';reason='FINAL_WHISTLE_OR_HALF_START_MISSING'
  else:
   cutoff=endsec-120
   if any((m-1)*60>=cutoff and (m-1)*60<endsec for m in mins):ans='GOAL';reason='PROVEN_BY_MINUTE_RANGE'
   elif all(m*60<=cutoff for m in mins):ans='NO_GOAL';reason='PROVEN_BY_MINUTE_RANGE'
   else:ans='UNKNOWN';reason='BOUNDARY_SECOND_UNKNOWN'
  out.update(result=ans,reason=reason)
 except Exception as error:out.update(result='UNKNOWN',reason='FETCH_ERROR',error=str(error)[:160])
 return out

def main():
 start=D.date(2026,8,1);days=[start+D.timedelta(days=i) for i in range((D.date(2026,10,14)-start).days+1)]
 raw=[];errors=[]
 with cf.ThreadPoolExecutor(max_workers=6) as pool:
  tasks={pool.submit(find_day,d):str(d) for d in days}
  for f in cf.as_completed(tasks):
   try:raw.extend(f.result())
   except Exception as e:errors.append([tasks[f],str(e)])
 matches=list({x['id']:x for x in raw}.values()); print('FOUND_MATCHES',len(matches),'DATE_ERRORS',len(errors),flush=True)
 with cf.ThreadPoolExecutor(max_workers=5) as pool:result=list(pool.map(audit,matches))
 summary={'matches':len(result),'failed_dates':errors,'leagues':{},'totals':dict(Counter(x['result'] for x in result))}
 for name in LEAGUES.values():
  league=[x for x in result if x['league']==name]
  summary['leagues'][name]={'matches':len(league),'status':dict(Counter(x['result'] for x in league)),
    'unknown_reasons':dict(Counter(x['reason'] for x in league if x['result']=='UNKNOWN'))}
 (OUTPUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 (OUTPUT/'matches.json').write_text(json.dumps(sorted(result,key=lambda r:(r['league'],r['date'],r['id'])),ensure_ascii=False,indent=2))
 print('LAST120_SUMMARY='+json.dumps(summary,ensure_ascii=False),flush=True)
 print('LAST120_POSITIVE='+json.dumps([x for x in result if x['result']=='GOAL'],ensure_ascii=False),flush=True)
 print('LAST120_UNCERTAIN='+json.dumps([x for x in result if x['result']=='UNKNOWN'][:15],ensure_ascii=False),flush=True)
 if not matches:raise SystemExit('No matches available — fetch blocked')
if __name__=='__main__':main()
