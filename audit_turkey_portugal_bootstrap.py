"""Zero-cost bootstrap audit for Turkey Super Lig and Primeira Liga.
Uses The Odds API /sports endpoint only; no paid odds request and no DB write occurs.
"""
import requests
from config import THE_ODDS_API_KEY
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG

URL="https://api.the-odds-api.com/v4/sports/"
CONFIGS=(TURKEY_SUPER_LIG_RUNTIME_CONFIG,PRIMEIRA_LIGA_RUNTIME_CONFIG)

def fetch_sports():
    if not THE_ODDS_API_KEY: raise RuntimeError("THE_ODDS_API_KEY missing")
    r=requests.get(URL,params={"apiKey":THE_ODDS_API_KEY,"all":"true"},timeout=30)
    if r.status_code!=200: raise RuntimeError(f"sports catalog HTTP {r.status_code}")
    return r.json(),{"remaining":r.headers.get("x-requests-remaining"),"used":r.headers.get("x-requests-used"),"last_cost":r.headers.get("x-requests-last")}

def audit(rows):
    by_key={str(x.get("key")):x for x in rows}; out=[]
    for cfg in CONFIGS:
        key=cfg.identity.odds_sport_key; row=by_key.get(key)
        out.append({"league":cfg.identity.identifier,"sport_key":key,"catalog_present":row is not None,"active":bool((row or {}).get("active"))})
    return out

def main():
    rows,quota=fetch_sports(); report=audit(rows)
    print("TURKEY / PORTUGAL ZERO-COST BOOTSTRAP AUDIT")
    for row in report: print(row)
    print("quota:",quota)
    if str(quota.get("last_cost")) not in {"0","0.0","None"}: raise RuntimeError("Expected zero-cost sports catalog request")
    if not all(r["catalog_present"] for r in report): raise RuntimeError("Requested sport key absent from provider catalog")
    print("DB writes: 0"); print("production model used:",False)
if __name__=="__main__": main()
