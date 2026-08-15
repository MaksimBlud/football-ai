import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")
