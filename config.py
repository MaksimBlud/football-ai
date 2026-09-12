import os
from dotenv import load_dotenv

load_dotenv()

# Public web configuration. Supabase publishable keys are intentionally safe to
# expose in browser/server source when paired with least-privilege grants + RLS.
# Secret/service-role credentials must still come only from environment variables.
DEFAULT_PUBLIC_SUPABASE_URL = "https://besxwboamipygwvrsblz.supabase.co"
DEFAULT_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_Ytw_dvKaKHSM8slbuQpneQ_MaQq-Daf"

SUPABASE_URL = os.getenv("SUPABASE_URL") or DEFAULT_PUBLIC_SUPABASE_URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY") or DEFAULT_SUPABASE_PUBLISHABLE_KEY
)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")
