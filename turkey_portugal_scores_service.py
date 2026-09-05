"""Read Turkey Super Lig and Primeira Liga completed scores from The Odds API."""
from __future__ import annotations
import requests
from config import THE_ODDS_API_KEY
from the_odds_service import BASE_URL
from turkey_portugal_market_only import config_for

DAYS_FROM=3

def get_scores(league: str, days_from: int=DAYS_FROM):
    cfg=config_for(league)
    if not THE_ODDS_API_KEY: raise RuntimeError("THE_ODDS_API_KEY not configured")
    if days_from<1 or days_from>3: raise ValueError("days_from must be between 1 and 3")
    r=requests.get(f"{BASE_URL}/sports/{cfg.sport_key}/scores/",params={"apiKey":THE_ODDS_API_KEY,"daysFrom":days_from,"dateFormat":"iso"},timeout=30)
    if r.status_code!=200:
        try:p=r.json()
        except Exception:p={}
        raise RuntimeError(f"The Odds API scores error: HTTP {r.status_code} | {p.get('error_code')} | {p.get('message')}")
    return {"events":r.json(),"quota":{"remaining":r.headers.get("x-requests-remaining"),"used":r.headers.get("x-requests-used"),"last_cost":r.headers.get("x-requests-last")}}
