"""Robustness and multiple-comparison checks of frozen 120s feature-screen.
Reads only outcome/feature artifact from complete multi-season GitHub run.
Composite signals are explicitly exploratory (invented after validation).
"""
import json,math,pathlib
import numpy as np,pandas as pd
from scipy.stats import fisher_exact,chi2
from statistics import NormalDist

ROOT=pathlib.Path("research/last120_criteria_20261016/results")
ROOT.mkdir(parents=True,exist_ok=True)
src=list(pathlib.Path("inputs").rglob("matched_features.csv"))
if len(src)!=1:raise RuntimeError("Expected one frozen features CSV: "+str(src))
f=pd.read_csv(src[0])
f["season"]=f["season"].astype(str)
assert len(f)==7350 and f["id"].nunique()==7350
sname={"dev":["2022-2023","2023-2024"],
    "validation":["2024-2025"],"test":["2025-2026"],
    "holdout_26_27":["2026-2027"],
    "validated_24_to_26":["2024-2025","2025-2026"]}
def one(s):
 x=s.goal_last120.sum();n=len(s)
 return {"n":n,"late_goals":int(x),"rate":round(x/n,7) if n else None}
def compare(data,selector):
 a=data.loc[selector];b=data.loc[~selector]
 left=one(a);right=one(b)
 pa=left["rate"];pb=right["rate"]
 odds,p=fisher_exact([[left["late_goals"],len(a)-left["late_goals"]],
                      [right["late_goals"],len(b)-right["late_goals"]]]) if len(a) and len(b) else (None,None)
 return {"eligible_total":len(data),"selected":left,"others":right,
 "relative_risk":round(pa/pb,5) if pa is not None and pb else None,
 "fisher_p":round(float(p),9) if p is not None else None}
def mask(data,name):
 if name=="DRAW85":return data["85_gap"]==0
 if name=="DRAW90":return data["90_gap"]==0
 if name=="NIL85":return data["85_goals"]==0
 if name=="DRAW85_AND_LOW_SHOTS10":return (data["85_gap"]==0)&(data["85_shots10"]<=2)
 if name=="DRAW85_AND_NO_GOAL15":return (data["85_gap"]==0)&(data["85_recent_goals15"]==0)
 if name=="DRAW85_WITH_2PLUS":return (data["85_gap"]==0)&(data["85_goals"]>=2)
 if name=="GAP_GE2_85":return data["85_gap"]>=2
 if name=="GOALS_85_GE3":return data["85_goals"]>=3
 if name=="SHOTS10_LOW_85":return data["85_shots10"]<=2
 if name=="SHOTS15_HIGH_85":return data["85_shots15"]>=7
 raise ValueError(name)
def test(name,seasonlist,league=None):
 d=f[f.season.isin(seasonlist)]
 if league:d=d[d.league==league]
 if name.startswith(("DRAW","GAP")):d=d[d.score_team_valid==1]
 return compare(d,mask(d,name))

names=["DRAW85","DRAW90","NIL85","DRAW85_AND_LOW_SHOTS10",
       "DRAW85_AND_NO_GOAL15","DRAW85_WITH_2PLUS",
       "GAP_GE2_85","GOALS_85_GE3","SHOTS10_LOW_85","SHOTS15_HIGH_85"]
tables={name:{"by_period":{period:test(name,periods) for period,periods in sname.items()},
               "by_league_heldout":{league:test(name,sname["validated_24_to_26"],league)
                 for league in sorted(f.league.unique())}} for name in names}

# Apply BH correction to original 28 prespecified one-feature hypotheses,
# excluding composites which were created after looking at outcomes.
srcj=list(pathlib.Path("inputs").rglob("criteria_report.json"))
assert len(srcj)==1
old=json.loads(srcj[0].read_text())
presets=old["hypotheses"]
pvals=[]
for name,pieces in presets.items():
    p1=pieces["validation"]["selected"];q1=pieces["validation"]["others"]
    p2=pieces["test"]["selected"];q2=pieces["test"]["others"]
    a=p1["goal_games"]+p2["goal_games"];n=p1["n"]+p2["n"]
    c=q1["goal_games"]+q2["goal_games"];m=q1["n"]+q2["n"]
    p=fisher_exact([[a,n-a],[c,m-c]])[1]
    pvals.append((name,p,a,n,c,m))
ordered=sorted(pvals,key=lambda row:row[1])
adjusted={}
last=1
for idx in range(len(ordered)-1,-1,-1):
    name,p,a,n,c,m=ordered[idx]
    last=min(last,p*len(ordered)/(idx+1))
    adjusted[name]={"fisher_p":p,"BH_FDR_q":last,
        "selected_n":n,"selected_goals":a,"selected_rate":a/n if n else None,
        "comparison_rate":c/m if m else None}
stat={"multiple_testing":{"n_prespecified":len(pvals),"all":adjusted,
         "fdr_below_05":[k for k,v in adjusted.items() if v["BH_FDR_q"]<0.05]}}
# CMH stratified by league x season, no lookahead / season spillover
d=f[f.season.isin(sname["validated_24_to_26"]) & (f.score_team_valid==1)]
expected=0;var=0;sa=0;sad=0;sbc=0;detail=[]
for (league,season),rows in d.groupby(["league","season"]):
    yes=mask(rows,"DRAW85")
    a=int(rows.loc[yes,"goal_last120"].sum());b=int(yes.sum())-a
    c=int(rows.loc[~yes,"goal_last120"].sum());dd=int((~yes).sum())-c
    n=a+b+c+dd
    ea=(a+b)*(a+c)/n
    va=(a+b)*(c+dd)*(a+c)*(b+dd)/(n*n*(n-1))
    expected+=ea;var+=va;sa+=a
    sad+=a*dd/n;sbc+=b*c/n
    detail.append({"league":league,"season":season,"draw_n":a+b,"draw_goals":a,
       "not_draw_n":c+dd,"not_draw_goals":c})
stat["cmh_draw85"]={"observed_draw_goals":sa,"expected_draw_goals_under_null":round(expected,3),
   "odds_ratio":round(sad/sbc,4),"chi2":round((sa-expected)**2/var,5),
   "p_value":float(chi2.sf((sa-expected)**2/var,df=1)),"strata":detail}
stat["comparisons"]=tables

# 2026 holding-out check of 1 draw per league possible filters, not executable odds.
d=f[(f.season=="2026-2027") & (f.score_team_valid==1)]
stat["current_league_draw85"]={league:compare(g,mask(g,"DRAW85"))
    for league,g in d.groupby("league")}
# Directly calculate historically break-even odds, *not* actual quote and not strategy ROI.
for name,info in tables.items():
    v=info["by_period"]["validated_24_to_26"]["selected"]
    if v["rate"] is not None and v["rate"]<1:
        info["indicative_fair_no_late_goal_decimal_odds"]=round(1/(1-v["rate"]),5)
ROOT.joinpath("robustness.json").write_text(json.dumps(stat,ensure_ascii=False,indent=2))
print("SCREEN_FDR="+json.dumps({"N":stat["multiple_testing"]["n_prespecified"],
 "below_05":stat["multiple_testing"]["fdr_below_05"],
 "top":list(adjusted.items())[:12]},ensure_ascii=False),flush=True)
print("CMH_DRAW85="+json.dumps(stat["cmh_draw85"],ensure_ascii=False),flush=True)
print("CRITERIA_PERIODS="+json.dumps({k:v["by_period"] for k,v in tables.items()},ensure_ascii=False),flush=True)
print("CRITERIA_BY_LEAGUE="+json.dumps({k:v["by_league_heldout"] for k,v in tables.items()},ensure_ascii=False),flush=True)
print("CURRENT_LEAGUE_DRAW85="+json.dumps(stat["current_league_draw85"],ensure_ascii=False),flush=True)
