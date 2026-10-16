"""Research-only: final 180 seconds, season 2026/27, six leagues.
Use frozen round identifiers and exact second-level Opta evidence for Big Five,
FotMob minute intervals and end clock for RPL. Never impute boundary events.
"""
import collections
import json
import math
from pathlib import Path

OUT = Path("research/last120_20261015/last180_results")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = Path("inputs")
FULL = {"EPL":10, "LA_LIGA":10, "BUNDESLIGA":9, "SERIE_A":10, "LIGUE_1":9, "RPL":8}

def load(name):
    paths = list(ROOT.rglob(name))
    if len(paths) != 1:
        raise RuntimeError(f"{name}: expected one copy, found {paths}")
    return json.loads(paths[0].read_text(encoding="utf8"))

big5 = load("round4_matches.json")
rpl = load("matches.json")
assert len(big5) == 297 and len(rpl) == 80, (len(big5), len(rpl))
assert len(set(x["id"] for x in big5+rpl)) == 377
assert all(x.get("round") and x.get("result") in ("GOAL","NO_GOAL") for x in big5)

results=[]
for m in big5:
    finish=m.get("opta_final_second")
    goals=m.get("opta_goal_event_seconds")
    if finish is None or goals is None:
        raise RuntimeError(f"Opta missing full-second evidence: {m['id']}")
    if not (5400 <= finish <= 7200) or any(x>finish for x in goals):
        raise RuntimeError(f"Opta clock error: {m['id']}")
    eligible = [round(finish-x,2) for x in goals if 0 <= finish-x <= 180]
    positive = bool(eligible)
    if m["result"] == "GOAL" and not positive:
        raise RuntimeError(f"Monotonicity: 120s GOAL not 180s GOAL {m['id']}")
    results.append({"id":m["id"],"league":m["league"],"round":int(m["round"]),
       "date":m["date"],"home":m["home"],"away":m["away"],
       "score":m["score"],"result":"GOAL" if positive else "NO_GOAL",
       "seconds_before_whistle":eligible,"source":"OPTA_SAME_CLOCK"})

for m in rpl:
    mins=m.get("goal_minutes")
    finish=m.get("final_second_estimate")
    if mins is None or any(x is None for x in mins):
        status="UNKNOWN";reason="INCOMPLETE_GOAL_MINUTES"
    elif not mins or max(mins) <= 87:
        status="NO_GOAL";reason="ALL_GOALS_FINISHED_BEFORE_87TH_MINUTE"
    elif finish is None:
        status="UNKNOWN";reason="NO_FINAL_WHISTLE_TIMESTAMP_WITH_LATE_GOALS"
    else:
        cutoff=finish-180
        if any((x-1)*60 >= cutoff for x in mins):
            status="GOAL";reason="MINUTE_FULLY_IN_LAST180"
        elif all(x*60 <= cutoff for x in mins):
            status="NO_GOAL";reason="GOAL_MINUTES_BEFORE_LAST180"
        else:
            status="UNKNOWN";reason="GOAL_MINUTE_STRADDLES_180S_BOUNDARY"
    if m["result"] == "GOAL" and status == "NO_GOAL":
        raise RuntimeError(f"RPL monotonicity error {m['id']}")
    results.append({"id":m["id"],"league":"RPL","round":int(m["round"]),
       "date":m["match_date"],"home":m["home"],"away":m["away"],
       "score":m["score"],"result":status,"reason":reason,
       "goal_minutes":mins,"estimated_cutoff":None if finish is None else finish-180,
       "source":"FOTMOB_MINUTE_AND_WHISTLE_ESTIMATE"})

byround=collections.defaultdict(list)
for row in results:
    byround[(row["league"],row["round"])].append(row)

def choose(n,k):
    return math.comb(n,k) if n>=k>=0 else 0
def any_goal(n,g):
    return 1 - choose(n-g,4)/choose(n,4)

rounds=[]
for (league,round_id),items in sorted(byround.items()):
    n=len(items)
    g=sum(x["result"]=="GOAL" for x in items)
    u=sum(x["result"]=="UNKNOWN" for x in items)
    if n < 4: raise RuntimeError(f"Round too small {league} {round_id} {n}")
    rounds.append({"league":league,"round":round_id,"matches":n,
       "complete":n==FULL[league],"positive":g,"negative":n-g-u,
       "unknown":u,"p_any_goal_min":any_goal(n,g),
       "p_any_goal_max":any_goal(n,g+u),
       "num_combinations":choose(n,4)})

def overview(eligible):
    if not eligible: return {}
    n=len(eligible)
    return {"rounds":n,"matches":sum(x["matches"] for x in eligible),
      "known_positive":sum(x["positive"] for x in eligible),
      "unknown_matches":sum(x["unknown"] for x in eligible),
      "mean_p_any_goal_min":sum(x["p_any_goal_min"] for x in eligible)/n,
      "mean_p_any_goal_max":sum(x["p_any_goal_max"] for x in eligible)/n,
      "all_four_no_goal_min":1-sum(x["p_any_goal_max"] for x in eligible)/n,
      "all_four_no_goal_max":1-sum(x["p_any_goal_min"] for x in eligible)/n,
      "rounds_zero_confirmed":sum(x["positive"]==0 for x in eligible),
      "rounds_at_least_two_confirmed":sum(x["positive"]>=2 for x in eligible),
      "total_combinations":sum(x["num_combinations"] for x in eligible),
      "pooled_combination_risk_min":
       sum(int(round(x["p_any_goal_min"]*x["num_combinations"])) for x in eligible)
        /sum(x["num_combinations"] for x in eligible),
      "pooled_combination_risk_max":
       sum(int(round(x["p_any_goal_max"]*x["num_combinations"])) for x in eligible)
        /sum(x["num_combinations"] for x in eligible)}

complete=[x for x in rounds if x["complete"]]
assert len(complete)==39 and len(rounds)==41
summary={"matches":377,
 "known_goal":sum(x["result"]=="GOAL" for x in results),
 "known_no_goal":sum(x["result"]=="NO_GOAL" for x in results),
 "unknown":sum(x["result"]=="UNKNOWN" for x in results),
 "complete_rounds":overview(complete),
 "all_observed_rounds":overview(rounds),
 "big5":overview([x for x in complete if x["league"]!="RPL"]),
 "rpl":overview([x for x in complete if x["league"]=="RPL"]),
 "by_league":{league:{"matches":len([x for x in results if x["league"]==league]),
   "known_goal":sum(x["result"]=="GOAL" for x in results if x["league"]==league),
   "known_no_goal":sum(x["result"]=="NO_GOAL" for x in results if x["league"]==league),
   "unknown":sum(x["result"]=="UNKNOWN" for x in results if x["league"]==league),
   "complete_rounds":overview([x for x in complete if x["league"]==league]),
   "rounds":[x for x in rounds if x["league"]==league]}
   for league in FULL},
 "confirmed_goal_games":[x for x in results if x["result"]=="GOAL"],
 "unknown_games":[x for x in results if x["result"]=="UNKNOWN"],
 "rounds":rounds}
assert summary["known_goal"]+summary["known_no_goal"]+summary["unknown"]==377
OUT.joinpath("matches.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
OUT.joinpath("summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print("LAST180_GLOBAL="+json.dumps({k:summary[k] for k in ["matches","known_goal","known_no_goal","unknown","complete_rounds","big5","rpl"]},ensure_ascii=False),flush=True)
print("LAST180_LEAGUES="+json.dumps({k:{x:v for x,v in d.items() if x!="rounds"} for k,d in summary["by_league"].items()},ensure_ascii=False),flush=True)
print("LAST180_ROUNDS="+json.dumps(rounds,ensure_ascii=False),flush=True)
print("LAST180_GOAL_GAMES="+json.dumps(summary["confirmed_goal_games"],ensure_ascii=False),flush=True)
print("LAST180_UNKNOWN="+json.dumps(summary["unknown_games"],ensure_ascii=False),flush=True)
