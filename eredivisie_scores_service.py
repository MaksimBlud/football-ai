"""Read Eredivisie completed scores from The Odds API."""
import requests
from config import THE_ODDS_API_KEY
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG

BASE_URL="https://api.the-odds-api.com/v4"; DAYS_FROM=3

def get_eredivisie_scores(*,days_from=DAYS_FROM):
    if not THE_ODDS_API_KEY: raise RuntimeError("THE_ODDS_API_KEY not configured")
    if days_from<1 or days_from>3: raise ValueError("days_from must be between 1 and 3")
    response=requests.get(f"{BASE_URL}/sports/{EREDIVISIE_RUNTIME_CONFIG.identity.odds_sport_key}/scores/",params={"apiKey":THE_ODDS_API_KEY,"daysFrom":days_from,"dateFormat":"iso"},timeout=30)
    if response.status_code!=200:
        try: payload=response.json()
        except Exception: payload={}
        raise RuntimeError(f"The Odds API scores error: HTTP {response.status_code} | {payload.get('error_code')} | {payload.get('message')}")
    return {"events":response.json(),"quota":{"remaining":response.headers.get("x-requests-remaining"),"used":response.headers.get("x-requests-used"),"last_cost":response.headers.get("x-requests-last")}}
