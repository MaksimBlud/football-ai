"""Exact random-four-match risk inside each actual 2026/27 league round.

Uses frozen all_opta_matches.json from the validated final-120-second
GitHub Actions run. Fetches FotMob matchDetails.general.matchRound strictly
for group membership. No API credits/odds/db writes.
"""
import collections, concurrent.futures as cf, itertools, json, math, pathlib, re, time, urllib.parse, urllib.request
EVIDENCE=pathlib.Path('evidence')
OUTPUT=pathlib.Path('research/last120_20261015/round4_results')
OUTPUT.mkdir(parents=True,exist_ok=True)
data=json.loads((EVIDENCE/'all_opta_matches.json').read_text())
leagues={'EPL':10,'LA_LIGA':10,'BUNDESLIGA':9,'SERIE_A':10,'LIGUE_1':9}

def read_round(rec):
    match_id=str(rec['id'])
    url='https://www.fotmob.com/api/data/matchDetails?'+urllib.parse.urlencode({'matchId':match_id})
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=15) as response:
                doc=json.load(response)
            general=doc.get('general') or {}
            if str(general.get('matchId'))!=match_id:
                raise RuntimeError('Mismatch match ID')
            matchround=str(general.get('matchRound','')).strip()
            if not matchround.isdigit() or not 1<=int(matchround)<=38:
                raise RuntimeError('Missing numeric round: '+matchround)
            if not general.get('finished'):
                raise RuntimeError('Match unfinished')
            home,away=rec['score'].split('-')
            header=doc.get('header') or {}
            teams=header.get('teams') or []
            if len(teams)!=2 or [int(x['score']) for x in teams]!=[int(home),int(away)]:
                raise RuntimeError('Score mismatch')
            return dict(rec,round=int(matchround),round_name=general.get('leagueRoundName'),
                        fotmob_league_id=general.get('leagueId'))
        except Exception as exc:
            if attempt==2: return dict(rec,round=None,round_error=str(exc)[:160])
            time.sleep(1+attempt)

with cf.ThreadPoolExecutor(max_workers=6) as pool:
    records=list(pool.map(read_round,data))
errors=[{k:r.get(k) for k in ('id','league','date','round_error')} for r in records if r.get('round') is None]
if errors:
    print('ROUND_LOOKUP_ERRORS='+json.dumps(errors,ensure_ascii=False),flush=True)
    raise SystemExit('Round metadata incomplete; fail-closed')
grouped=collections.defaultdict(list)
for rec in records:
    assert rec['result'] in ('GOAL','NO_GOAL'),rec
    grouped[(rec['league'],rec['round'])].append(rec)
assert len(records)==len({r['id'] for r in records})
def compute_round(league,roundno,arr):
    n=len(arr);goals=sum(x['result']=='GOAL' for x in arr)
    combos=math.comb(n,4) if n>=4 else 0
    failing=combos-math.comb(n-goals,4) if combos and n-goals>=4 else (combos if combos else 0)
    prob=failing/combos if combos else None
    ids=[x['id'] for x in arr]
    return {'league':league,'round':roundno,'matches':n,'expected_full_round':leagues[league],
      'complete':n==leagues[league],'goal_games':goals,'no_goal_games':n-goals,
      'total_combinations':combos,'combinations_with_goal':failing,
      'combinations_without_goal':combos-failing,'probability_any_goal':prob,
      'goal_game_ids':[x['id'] for x in arr if x['result']=='GOAL'],
      'match_ids':ids}
rounds=[compute_round(l,r,a) for (l,r),a in sorted(grouped.items())]
def summarize(groups):
    groups=[r for r in groups if r['total_combinations']>0]
    if not groups:return None
    total=sum(r['total_combinations'] for r in groups)
    return {'rounds':len(groups),'matches':sum(r['matches'] for r in groups),
      'late_goal_games':sum(r['goal_games'] for r in groups),
      'average_risk_equally_random_round':sum(r['probability_any_goal'] for r in groups)/len(groups),
      'pooling_every_combination_risk':sum(r['combinations_with_goal'] for r in groups)/total,
      'total_combinations':total,'combinations_with_goal':sum(r['combinations_with_goal'] for r in groups),
      'rounds_zero_late_goals':sum(r['goal_games']==0 for r in groups),
      'rounds_one_late_goal':sum(r['goal_games']==1 for r in groups),
      'rounds_two_plus_late_goals':sum(r['goal_games']>=2 for r in groups),
      'prob_all_four_no_goal':sum(1-r['probability_any_goal'] for r in groups)/len(groups)}
summary={'source_run_id':38764264517,'matches_checked':len(records),
         'rounds_total':len(rounds),'all_rounds':summarize(rounds),
         'complete_rounds_only':summarize([r for r in rounds if r['complete']]),
         'by_league':{}, 'rounds':rounds}
for league in leagues:
    allround=[r for r in rounds if r['league']==league]
    full=[r for r in allround if r['complete']]
    summary['by_league'][league]={'all_rounds':summarize(allround),
       'complete_rounds_only':summarize(full),
       'rounds':allround}
OUTPUT.joinpath('round4_matches.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
OUTPUT.joinpath('round4_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('ROUND4_COUNTS='+json.dumps([{'league':k,'round':r['round'],'n':r['matches'],
  'goal_matches':r['goal_games'],'complete':r['complete'],
  'probability':round(r['probability_any_goal'],6) if r['probability_any_goal'] is not None else None}
  for k in leagues for r in summary['by_league'][k]['rounds']],ensure_ascii=False),flush=True)
print('ROUND4_SUMMARY='+json.dumps({k:v for k,v in summary.items() if k not in ('rounds','by_league')},ensure_ascii=False),flush=True)
print('ROUND4_LEAGUES='+json.dumps({k:{'all':v['all_rounds'],'full':v['complete_rounds_only']} for k,v in summary['by_league'].items()},ensure_ascii=False),flush=True)
