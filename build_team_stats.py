
import pandas as pd

print("Читаю данные...")

df = pd.read_csv("data/raw/epl_2025_2026.csv")

stats = {}

for _, row in df.iterrows():

    home = row["HomeTeam"]
    away = row["AwayTeam"]

    for team in [home, away]:
        if team not in stats:
            stats[team] = {
                "team": team,
                "matches": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "corners": 0,
                "shots": 0,
                "shots_target": 0,
            }

    hg = int(row["FTHG"])
    ag = int(row["FTAG"])

    # Домашняя команда
    stats[home]["matches"] += 1
    stats[home]["goals_for"] += hg
    stats[home]["goals_against"] += ag
    stats[home]["corners"] += int(row["HC"])
    stats[home]["shots"] += int(row["HS"])
    stats[home]["shots_target"] += int(row["HST"])

    # Гостевая команда
    stats[away]["matches"] += 1
    stats[away]["goals_for"] += ag
    stats[away]["goals_against"] += hg
    stats[away]["corners"] += int(row["AC"])
    stats[away]["shots"] += int(row["AS"])
    stats[away]["shots_target"] += int(row["AST"])

    if hg > ag:
        stats[home]["wins"] += 1
        stats[away]["losses"] += 1
    elif hg < ag:
        stats[away]["wins"] += 1
        stats[home]["losses"] += 1
    else:
        stats[home]["draws"] += 1
        stats[away]["draws"] += 1

result = pd.DataFrame(stats.values())

result["avg_goals"] = result["goals_for"] / result["matches"]
result["avg_conceded"] = result["goals_against"] / result["matches"]
result["avg_corners"] = result["corners"] / result["matches"]
result["avg_shots"] = result["shots"] / result["matches"]
result["avg_shots_target"] = result["shots_target"] / result["matches"]

result = result.sort_values("wins", ascending=False)

result.to_csv("team_stats.csv", index=False)

print(result)

print("\n✅ Файл team_stats.csv создан.")