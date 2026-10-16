"""Russian Premier League 2026/27: read-only final 120 seconds and 4 matches per round.
Uses football match second-half wallclock start and match-ended timestamps from
FotMob, and recorded goal minute; when goal minute overlaps final 120s boundary,
never guess exact goal second. Records certain vs unresolved risk bounds.
"""
import collections,concurrent.futures as cf,datetime as dt,json,math,pathlib,re,time,urllib.parse,urllib.request
ROOT=pathlib.Path('research/last120_20261015/rpl_results')
ROOT.mkdir(parents=True,exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0','Accept':'application/json'}
def get(path,**kwargs):
    url='https://www.fotmob.com/api/data/'+path+'?'+urllib.parse.urlencode(kwargs)
    for i in range(3):
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=16) as f:return json.load(f)
        except Exception as e:
            if i==2:raise RuntimeError(str(e)[:150])
            time.sleep(i+1)
def timestamp(t):
    if not t:return None
    for fmt in ('%d.%m.%Y %H:%M:%S','%Y-%m-%dT%H:%M:%S.%fZ','%Y-%m-%dT%H:%M:%SZ'):
        try:return dt.datetime.strptime(t,fmt)
        except ValueError:pass
    return None
def minute(e):
    s=str(e.get('timeStr') or e.get('time') or '').replace("'",'').replace(' ','').strip()
    m=re.fullmatch(r'(\d+)(?:\+(\d+))?',s)
    return int(m.group(1))+int(m.group(2) or 0) if m else None
def inspect(fixture):
    row={'id':str(fixture['id']),'round':int(fixture['round']),'home':fixture['home']['name'],
         'away':fixture['away']['name'],'score':fixture['status']['scoreStr'],
         'match_date':fixture['status']['utcTime'][:10]}
    try:
        doc=get('matchDetails',matchId=row['id'])
        general=doc.get('general') or {}
        st=(doc.get('header') or {}).get('status') or {}
        teams=(doc.get('header') or {}).get('teams') or []
        half=st.get('halfs') or {}
        start=timestamp(half.get('secondHalfStarted'))
        end=timestamp(half.get('gameEnded'))
        seconds=(end-start).total_seconds()+2700 if start and end else None
        if seconds is not None and not 5400<=seconds<=6900:seconds=None
        ev=((doc.get('content') or {}).get('matchFacts') or {}).get('events',{}).get('events',[])
        goals=[e for e in ev if e.get('type')=='Goal' and not e.get('isPenaltyShootoutEvent')]
        m=[minute(x) for x in goals]
        recorded_goals=sum(int(x['score']) for x in teams) if len(teams)==2 and all(x.get('score') is not None for x in teams) else None
        row.update(goal_minutes=m,recorded_goals=recorded_goals,goal_events=len(goals),
                   final_second_estimate=seconds,final_whistle=end.isoformat() if end else None,
                   second_half_start=start.isoformat() if start else None)
        if str(general.get('matchId'))!=row['id'] or not general.get('finished') or not st.get('finished') or int(general.get('leagueId') or -1)!=63:
            result,reason='UNKNOWN','MATCH_METADATA_MISMATCH'
        elif int(general.get('matchRound') or -1)!=row['round']:
            result,reason='UNKNOWN','MATCH_ROUND_MISMATCH'
        elif recorded_goals is None or len(goals)!=recorded_goals:
            result,reason='UNKNOWN','GOALS_SCORE_MISMATCH'
        elif any(v is None for v in m):
            result,reason='UNKNOWN','UNPARSEABLE_GOAL_MINUTE'
        elif not m or max(m)<=88:
            result,reason='NO_GOAL','GOALS_END_BY_88'
        elif seconds is None:
            result,reason='UNKNOWN','NO_FINISH_TIMESTAMP'
        else:
            cutoff=seconds-120
            definitely_late=any((v-1)*60>=cutoff and (v-1)*60<=seconds for v in m)
            definitely_early=all(v*60<=cutoff for v in m)
            if definitely_late:result,reason='GOAL','GOAL_MINUTE_ENTIRELY_INSIDE_FINAL_120'
            elif definitely_early:result,reason='NO_GOAL','LAST_GOAL_EARLIER_THAN_FINAL_120'
            else:result,reason='UNKNOWN','GOAL_MINUTE_OVERLAPS_FINAL_120'
            row['cutoff_second_estimate']=cutoff
        row.update(result=result,reason=reason)
    except Exception as e:
        row.update(result='UNKNOWN',reason='FETCH_OR_PARSE_ERROR',error=str(e)[:170])
    return row
def prob_round(arr):
    n=len(arr)
    p=sum(x['result']=='GOAL' for x in arr)
    unknown=sum(x['result']=='UNKNOWN' for x in arr)
    combos=math.comb(n,4) if n>=4 else 0
    def chance(g):return 1-math.comb(n-g,4)/combos if n-g>=4 else 1.0
    return {'round':arr[0]['round'],'matches':n,'positive':p,'negative':n-p-unknown,
       'unknown':unknown,'prob_min':chance(p),'prob_max':chance(p+unknown),
       'total_combinations':combos,
       'combinations_min':int(round(chance(p)*combos)),
       'combinations_max':int(round(chance(p+unknown)*combos))}
def main():
    league=get('leagues',id=63)
    matches=[m for m in (league.get('fixtures') or {}).get('allMatches',[])
             if m.get('status',{}).get('finished')
             and '2026-07-24'<=(m.get('status',{}).get('utcTime') or '')[:10]<='2026-10-14'
             and str(m.get('round','')).isdigit()]
    if len(matches)!=80:raise RuntimeError(f'Expected 80 RPL matches, got {len(matches)}')
    with cf.ThreadPoolExecutor(max_workers=6) as pool: rows=list(pool.map(inspect,matches))
    summary={'league':'RPL','season':'2026/27','range':'2026-07-24 .. 2026-10-14',
             'matches':len(rows),'count':dict(collections.Counter(v['result'] for v in rows)),
             'unknown_reasons':dict(collections.Counter(v['reason'] for v in rows if v['result']=='UNKNOWN'))}
    groups=collections.defaultdict(list)
    for r in rows:groups[r['round']].append(r)
    rounds=[prob_round(groups[i]) for i in sorted(groups)]
    if len(rounds)!=10 or any(x['matches']!=8 for x in rounds):
        raise RuntimeError('Unfinished or inconsistent RPL round coverage')
    summary['rounds']=rounds
    summary['mean_uniform_round_min']=sum(r['prob_min'] for r in rounds)/10
    summary['mean_uniform_round_max']=sum(r['prob_max'] for r in rounds)/10
    summary['goal_games_min']=summary['count'].get('GOAL',0)
    summary['goal_games_max']=summary['goal_games_min']+summary['count'].get('UNKNOWN',0)
    summary['unknown_matches']=[{k:v.get(k) for k in ('id','match_date','round','home','away','score','goal_minutes','cutoff_second_estimate','reason')} for v in rows if v['result']=='UNKNOWN']
    summary['confirmed_goal_matches']=[{k:v.get(k) for k in ('id','match_date','round','home','away','score','goal_minutes','cutoff_second_estimate')} for v in rows if v['result']=='GOAL']
    ROOT.joinpath('matches.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    ROOT.joinpath('summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print('RPL_FULL_SUMMARY='+json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
