import json,urllib.request
url='https://www.fotmob.com/api/data/leagues?id=63'
req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
with urllib.request.urlopen(req,timeout=20) as r: data=json.load(r)
print('LEAGUE_KEYS',list(data))
print('FIXTURES_KEYS',list((data.get('fixtures') or {}).keys()))
print('SEASON',json.dumps(data.get('details'),ensure_ascii=False)[:1600])
print('FIXTURES',json.dumps(data.get('fixtures'),ensure_ascii=False)[:1600])
