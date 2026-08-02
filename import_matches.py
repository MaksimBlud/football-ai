
import pandas as pd
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Читаю CSV...")

df = pd.read_csv("data/raw/epl_2025_2026.csv")

df["Date"] = pd.to_datetime(
df["Date"],
format="%d/%m/%Y"
).dt.strftime("%Y-%m-%d")

print(f"Матчей: {len(df)}")

for _, row in df.iterrows():

    match = {
        "season": "2025/2026",
        "league": "EPL",

        "match_date": row["Date"],
        "match_time": row["Time"],

        "home_team": row["HomeTeam"],
        "away_team": row["AwayTeam"],

        "home_goals": row["FTHG"],
        "away_goals": row["FTAG"],
        "result": row["FTR"],

        "home_shots": row["HS"],
        "away_shots": row["AS"],

        "home_shots_target": row["HST"],
        "away_shots_target": row["AST"],

        "home_corners": row["HC"],
        "away_corners": row["AC"],

        "home_yellow": row["HY"],
        "away_yellow": row["AY"],

        "home_red": row["HR"],
        "away_red": row["AR"],

        "home_odds": row["AvgH"],
        "draw_odds": row["AvgD"],
        "away_odds": row["AvgA"],
    }

    supabase.table("matches").insert(match).execute()

print("✅ Импорт завершён!")