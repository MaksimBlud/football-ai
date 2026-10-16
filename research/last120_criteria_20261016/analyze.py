"""Football AI research-only late-goal signal screen, pre-match and in-play.
Same-source Opta second-resolution events (type 16 Goal, 30 period 2 End).
Seasons 2022/23..2026/27 (2026 season cut 2026-10-14).
No Supabase, no paid API, no production PKL, no post-hoc selection on holdouts.
"""
import collections, concurrent.futures as cf, datetime as dt, json, math, pathlib, tempfile, urllib.request
from itertools import groupby
import numpy as np
import pandas as pd
import pyarrow as pa, pyarrow.compute as pc, pyarrow.parquet as pq
from scipy.stats import fisher_exact, chi2_contingency
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

LEAGUES=["EPL","La_Liga","Bundesliga","Serie_A","Ligue_1"]
SEASONS=["2022-2023","2023-2024","2024-2025","2025-2026","2026-2027"]
BASE="https://github.com/peteowen1/pannadata/releases/download/opta-latest/"
OUT=pathlib.Path("research/last120_criteria_20261016/results");OUT.mkdir(parents=True,exist_ok=True)

def download(name,where):
    req=urllib.request.Request(BASE+name,headers={"User-Agent":"football-ai-research-criteria"})
    with urllib.request.urlopen(req,timeout=130) as r,open(where,"wb") as w:
        while True:
            chunk=r.read(2*1024*1024)
            if not chunk:break
            w.write(chunk)
    print("DOWNLOADED",name,round(where.stat().st_size/1e6,1),"MB",flush=True)

with tempfile.TemporaryDirectory() as temp:
    root=pathlib.Path(temp)
    fp=root/"fixtures.parquet";download("opta_fixtures.parquet",fp)
    fixtures=pq.read_table(fp).to_pylist()
    fixtures=[f for f in fixtures if f.get("competition") in LEAGUES
        and f.get("season") in SEASONS and f.get("match_status")=="Played"
        and str(f.get("match_date",""))[:10]<="2026-10-14"
        and f.get("home_score") is not None and f.get("away_score") is not None]
    ids=[str(x["match_id"]) for x in fixtures]
    assert len(ids)==len(set(ids)), "Fixture duplicate IDs"
    fixture_by_id={str(x["match_id"]):x for x in fixtures}
    print("TOTAL_PLAYED_FIXTURES",len(fixtures),"SEASON_COUNTS",
        dict(collections.Counter(f["season"] for f in fixtures)),flush=True)
    byid=collections.defaultdict(list)
    for league in LEAGUES:
        relevant={str(x["match_id"]) for x in fixtures if x["competition"]==league}
        path=root/(league+".parquet")
        download("events_"+league+".parquet",path)
        parquet=pq.ParquetFile(path)
        cols=["match_id","type_id","minute","second","period_id","team_id"]
        assert all(x in parquet.schema_arrow.names for x in cols),(league,parquet.schema_arrow)
        event_rows=0
        for batch in parquet.iter_batches(batch_size=45000,columns=cols):
            tbl=pa.Table.from_batches([batch])
            match_ids=pc.is_in(tbl["match_id"],value_set=pa.array(list(relevant),type=tbl["match_id"].type))
            kind=pc.is_in(tbl["type_id"],value_set=pa.array([13,14,15,16,17,30],type=tbl["type_id"].type))
            selected=tbl.filter(pc.and_(match_ids,kind))
            for ev in selected.to_pylist():
                byid[str(ev["match_id"])].append(ev)
                event_rows+=1
        print("LEAGUE_EVENTS",league,"fixtures",len(relevant),"key_events",event_rows,flush=True)
        path.unlink()

    def sec(e):
        m,s=e.get("minute"),e.get("second")
        return m*60+s if isinstance(m,(int,float)) and isinstance(s,(int,float)) else None

    verified={}
    reasons=collections.Counter()
    for f in fixtures:
        key=str(f["match_id"]);events=byid.get(key,[])
        goals=[v for v in events if int(v["type_id"])==16 and int(v.get("period_id") or 0) in (1,2) and sec(v) is not None]
        ends=[v for v in events if int(v["type_id"])==30 and int(v.get("period_id") or 0)==2 and sec(v) is not None]
        n=int(f["home_score"])+int(f["away_score"])
        reason=None
        if len(goals)!=n:reason="GOAL_EVENT_SCORE_MISMATCH"
        elif not ends:reason="NO_PERIOD_2_END"
        elif len(set(sec(v) for v in ends))>1 and max(sec(v) for v in ends)-min(sec(v) for v in ends)>3:
            reason="CONFLICTING_END_TIMES"
        else:
            final=max(sec(v) for v in ends)
            if not (5400<=final<=7200):reason="IMPOSSIBLE_FULL_TIME"
            elif any(sec(g)>final or sec(g)<0 for g in goals):reason="GOAL_AFTER_END"
        if reason:
            reasons[reason]+=1
            continue
        home_id,away_id=str(f["home_team_id"]),str(f["away_team_id"])
        if any(str(g.get("team_id")) not in (home_id,away_id) for g in goals):
            reasons["GOAL_TEAM_UNKNOWN"]+=1
            continue
        if sum(str(g["team_id"])==home_id for g in goals)!=int(f["home_score"]):
            reasons["HOME_SCORE_MISMATCH"]+=1
            continue
        if sum(str(g["team_id"])==away_id for g in goals)!=int(f["away_score"]):
            reasons["AWAY_SCORE_MISMATCH"]+=1
            continue
        verified[key]={"final":final,"goals":goals,"events":events,
            "y":int(any(final-120<=sec(g)<=final for g in goals)),
            "end_vs_90":(final-5400)/60}
    print("VERIFY_MATCHES",len(verified),"REASONS",dict(reasons),flush=True)
    if len(verified)<2000:raise RuntimeError("Insufficient historical exact-second sample")
    # Extract pre-match form only from earlier dates, strictly same season.
    # Update team state for same-day matches only AFTER all their pre-features generated.
    allfixtures=sorted(fixtures,key=lambda f:(f["season"],str(f["match_date"])[:10],str(f["match_id"])))
    form=collections.defaultdict(list)
    prematch={}
    for (_season,date),same_date in groupby(allfixtures,key=lambda f:(f["season"],str(f["match_date"])[:10])):
        on_date=list(same_date)
        for f in on_date:
            k=str(f["match_id"]);h=str(f["home_team_id"]);a=str(f["away_team_id"])
            lh=form[(f["season"],h)][-5:];la=form[(f["season"],a)][-5:]
            if len(lh)>=5 and len(la)>=5:
                hg=np.mean([v[0] for v in lh]);ha=np.mean([v[1] for v in lh])
                ag=np.mean([v[0] for v in la]);aa=np.mean([v[1] for v in la])
                hp=np.mean([v[2] for v in lh]);ap=np.mean([v[2] for v in la])
                draws=sum(v[3] for v in lh+la)
                prematch[k]={"pre_total":float((hg+ha+ag+aa)/2),
                  "pre_points_gap":float(abs(hp-ap)),
                  "pre_draws_last10":int(draws),
                  "pre_best_defense":float(min(ha,aa)),
                  "pre_both_defense_good":bool(ha<=1 and aa<=1),
                  "pre_both_attack_weak":bool(hg<=1 and ag<=1)}
        for f in on_date:
            h=str(f["home_team_id"]);a=str(f["away_team_id"])
            hs,as_=int(f["home_score"]),int(f["away_score"])
            form[(f["season"],h)].append((hs,as_,3 if hs>as_ else 1 if hs==as_ else 0,int(hs==as_)))
            form[(f["season"],a)].append((as_,hs,3 if as_>hs else 1 if hs==as_ else 0,int(hs==as_)))
    data=[]
    for f in fixtures:
        k=str(f["match_id"])
        if k not in verified:continue
        v=verified[k];ev=v["events"];goals=v["goals"]
        def at(t):
            earlier=[g for g in goals if sec(g)<t]
            h=sum(str(g["team_id"])==str(f["home_team_id"]) for g in earlier)
            a=len(earlier)-h
            shots=[e for e in ev if int(e["type_id"]) in (13,14,15,16) and int(e.get("period_id") or 0) in (1,2) and sec(e) is not None and sec(e)<t]
            last10=sum(t-600<=sec(e)<t for e in shots)
            last15=sum(t-900<=sec(e)<t for e in shots)
            recent_goals=sum(t-900<=sec(e)<t for e in earlier)
            return {"goals":len(earlier),"gap":abs(h-a),
                    "home_goals":h,"away_goals":a,"shots10":last10,
                    "shots15":last15,"recent_goals15":recent_goals}
        at85=at(85*60);at90=at(90*60)
        date=str(f["match_date"])[:10]
        row={"id":k,"league":f["competition"],"season":f["season"],"date":date,
             "home_team_id":str(f["home_team_id"]),"away_team_id":str(f["away_team_id"]),
             "home":f["home_team"],"away":f["away_team"],
             "goal_last120":v["y"],"final_min":v["final"]/60,
             "last120_goals":sum(v["final"]-120<=sec(g)<=v["final"] for g in goals),
             "pre_available":int(k in prematch)}
        for timing,snapshot in (("85",at85),("90",at90)):
            row.update({f"{timing}_{kk}":vv for kk,vv in snapshot.items()})
        row.update(prematch.get(k,{}))
        data.append(row)
    frame=pd.DataFrame(data).sort_values(["season","date","league","id"])
    frame.to_csv(OUT/"matched_features.csv",index=False)
    print("VALID_SEASON_COUNTS",frame.groupby(["season","league"]).size().to_dict(),flush=True)
    print("POSITIVE_BY_SEASON",frame.groupby("season")["goal_last120"].agg(["count","sum","mean"]).to_dict("index"),flush=True)

    # Prespecified, semantically useful filters. Each row one match, before or at observation time.
    # No use of actual length of game, final score or late goal before selecting.
    tests={
      "PRE_low_goal_expectation_le2.0":lambda x:x.pre_available and x.pre_total<=2.0,
      "PRE_high_goal_expectation_ge3.2":lambda x:x.pre_available and x.pre_total>=3.2,
      "PRE_weak_form_gap_le0.4":lambda x:x.pre_available and x.pre_points_gap<=0.4,
      "PRE_strong_form_gap_ge1.2":lambda x:x.pre_available and x.pre_points_gap>=1.2,
      "PRE_both_defenses_le1.0":lambda x:x.pre_available and x.pre_both_defense_good,
      "PRE_both_attacks_le1.0":lambda x:x.pre_available and x.pre_both_attack_weak,
      "PRE_draws_last10_ge4":lambda x:x.pre_available and x.pre_draws_last10>=4,
      "PRE_draws_last10_le1":lambda x:x.pre_available and x.pre_draws_last10<=1,
      "LIVE85_score_nil_nil":lambda x:x["85_goals"]==0,
      "LIVE85_score_total_eq1":lambda x:x["85_goals"]==1,
      "LIVE85_score_total_ge3":lambda x:x["85_goals"]>=3,
      "LIVE85_score_draw":lambda x:x["85_gap"]==0,
      "LIVE85_score_gap_eq1":lambda x:x["85_gap"]==1,
      "LIVE85_score_gap_ge2":lambda x:x["85_gap"]>=2,
      "LIVE85_no_goals_15m":lambda x:x["85_recent_goals15"]==0,
      "LIVE85_any_goal_15m":lambda x:x["85_recent_goals15"]>=1,
      "LIVE85_no_shots_10m":lambda x:x["85_shots10"]==0,
      "LIVE85_low_shots10_le2":lambda x:x["85_shots10"]<=2,
      "LIVE85_high_shots10_ge5":lambda x:x["85_shots10"]>=5,
      "LIVE85_no_shots_15m":lambda x:x["85_shots15"]==0,
      "LIVE85_high_shots15_ge7":lambda x:x["85_shots15"]>=7,
      "LIVE90_score_draw":lambda x:x["90_gap"]==0,
      "LIVE90_gap_eq1":lambda x:x["90_gap"]==1,
      "LIVE90_gap_ge2":lambda x:x["90_gap"]>=2,
      "LIVE90_no_shots_10m":lambda x:x["90_shots10"]==0,
      "LIVE90_shots10_ge5":lambda x:x["90_shots10"]>=5,
      "LIVE90_no_goals_15m":lambda x:x["90_recent_goals15"]==0,
      "LIVE90_any_goal_15m":lambda x:x["90_recent_goals15"]>=1,
    }
    # Define all filters before looking at held-out outcomes.
    def select_rows(df,name):
        if name.startswith("PRE_"):eligible=df[df["pre_available"]==1]
        else:eligible=df
        selected=eligible.loc[eligible.apply(tests[name],axis=1)]
        return eligible,selected
    DEV=["2022-2023","2023-2024"]
    VAL=["2024-2025"]
    TEST=["2025-2026"]
    FUTURE=["2026-2027"]
    def rates(df):
        k=len(df);x=int(df["goal_last120"].sum()) if k else 0
        return {"n":k,"goal_games":x,"rate":round(x/k,6) if k else None}
    splits={"development":DEV,"validation":VAL,"test":TEST,"current_2026_27":FUTURE}
    report={"dataset":{"n":len(frame),"goal_count":int(frame["goal_last120"].sum()),
             "invalid_reasons":dict(reasons),
             "eligible_splits":{z:rates(frame[frame.season.isin(v)]) for z,v in splits.items()},
             "pre_form_available":int(frame["pre_available"].sum())},
      "hypotheses":{},"season_league_baselines":frame.groupby(["season","league"])["goal_last120"].agg(["count","sum","mean"]).reset_index().to_dict("records")}
    for name in tests:
        pack={}
        for split,seasonset in splits.items():
            eligible,selected=select_rows(frame[frame.season.isin(seasonset)],name)
            non=eligible.loc[~eligible.index.isin(selected.index)]
            sel=rates(selected);nonsel=rates(non)
            improvement=sel["rate"]-nonsel["rate"] if sel["rate"] is not None and nonsel["rate"] is not None else None
            pack[split]={"selected":sel,"others":nonsel,"goal_rate_difference":round(improvement,6) if improvement is not None else None}
            if len(selected)>=10 and len(non)>=10:
                contingency=[[sel["goal_games"],sel["n"]-sel["goal_games"]],
                   [nonsel["goal_games"],nonsel["n"]-nonsel["goal_games"]]]
                pack[split]["fisher_p_two_sided"]=round(float(fisher_exact(contingency)[1]),8)
        report["hypotheses"][name]=pack

    # Train simplest tiny regularized pre-match model, and in-play model @85
    # on DEV only; scoring on VAL, TEST, and FUTURE without refitting.
    ml_report={}
    configs={
      "PREMATCH_L2":{"columns":["pre_total","pre_points_gap","pre_draws_last10","pre_best_defense"],"requires_pre":True},
      "LIVE85_L2":{"columns":["85_goals","85_gap","85_shots10","85_shots15","85_recent_goals15"],"requires_pre":False}
    }
    for modelname,conf in configs.items():
        d=frame.dropna(subset=conf["columns"])
        if conf["requires_pre"]:d=d[d.pre_available==1]
        train=d[d.season.isin(DEV)]
        xtrain=train[conf["columns"]].astype(float).to_numpy()
        ytrain=train.goal_last120.to_numpy().astype(int)
        means=xtrain.mean(axis=0);std=np.maximum(xtrain.std(axis=0),1e-6)
        reg=LogisticRegression(C=0.2,max_iter=600,class_weight=None,random_state=42)
        reg.fit((xtrain-means)/std,ytrain)
        obj={"columns":conf["columns"],"train_size":len(train),"train_goals":int(sum(ytrain)),
            "coefficients":reg.coef_[0].round(5).tolist(),"intercept":float(reg.intercept_[0]),
            "scores":{}}
        for split,ss in splits.items():
            t=d[d.season.isin(ss)]
            if len(t)<10:continue
            y=t.goal_last120.to_numpy().astype(int)
            probs=reg.predict_proba((t[conf["columns"]].astype(float).to_numpy()-means)/std)[:,1]
            base=np.full(len(y),float(np.mean(ytrain)))
            low_mask=probs <= np.quantile(probs,0.25)
            obj["scores"][split]={"n":len(y),"positive":int(sum(y)),
                "brier":round(float(brier_score_loss(y,probs)),6),
                "baseline_train_brier":round(float(brier_score_loss(y,base)),6),
                "auc":round(float(roc_auc_score(y,probs)),5) if len(set(y))>1 else None,
                "lowest_risk_quartile":rates(t.iloc[np.flatnonzero(low_mask)])}
        ml_report[modelname]=obj
    report["models"]=ml_report

    # Stratification for label and association only, never deploy selection
    b=frame.copy()
    b["final_length_bucket"]=pd.cut(b["final_min"],bins=[0,94,97,100,120],labels=["<=94","94-97","97-100",">100"])
    report["postmatch_diagnostic_leakage_only"]=b.groupby("final_length_bucket",observed=True)["goal_last120"].agg(["count","sum","mean"]).reset_index().to_dict("records")
    (OUT/"criteria_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
    print("DATASET="+json.dumps(report["dataset"],ensure_ascii=False),flush=True)
    print("FEATURE_RESULTS="+json.dumps(report["hypotheses"],ensure_ascii=False),flush=True)
    print("MODEL_RESULTS="+json.dumps(ml_report,ensure_ascii=False),flush=True)
    print("WHISTLE_DURATION_DIAGNOSTIC="+json.dumps(report["postmatch_diagnostic_leakage_only"],ensure_ascii=False),flush=True)
