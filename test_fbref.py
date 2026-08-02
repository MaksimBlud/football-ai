
import soccerdata as sd

fb = sd.FBref(leagues="ENG-Premier League", seasons=2025)

matches = fb.read_schedule()

print(matches.head())
print()
print("Количество матчей:", len(matches))