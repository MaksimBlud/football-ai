#!/usr/bin/env python3
"""Research-only pre-match predictors for a goal in the actual final 120 seconds."""
from __future__ import annotations
import datetime as dt, json, math, re, time, unicodedata, urllib.request, shutil
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

END = dt.date(2026,10,19)
SEASONS = ["2022-2023","2023-2024","2024-2025","2025-2026","2026-2027"]
SEASON_CODES = {"2223":"2022-2023","2324":"2023-2024","2425":"2024-2025","2526":"2025-2026","2627":"2026-2027"}
LEAGUES = {"EPL":("E0","АПЛ"),"La_Liga":("SP1","Ла Лига"),"Bundesliga":("D1","Бундеслига"),"Serie_A":("I1","Серия A"),"Ligue_1":("F1","Лига 1")}
BASE = "https://github.com/peteowen1/pannadata/releases/download/opta-latest/"
OUT = Path("artifacts/last120_prematch_criteria_v1")
OUT.mkdir(parents=True,exist_ok=True)
GROUPS = [
["manchester city","man city"],["manchester united","man united","man utd"],["newcastle united","newcastle"],
["nottingham forest","nott'm forest","nottm forest","nottingham"],["tottenham hotspur","tottenham","spurs"],
["brighton and hove albion","brighton & hove albion","brighton"],["wolverhampton wanderers","wolves","wolverhampton"],
["west ham united","west ham"],["athletic club","ath bilbao","athletic bilbao"],["atletico madrid","ath madrid","atletico de madrid"],
["real betis","betis"],["paris saint germain","paris sg","psg"],["borussia dortmund","dortmund"],
["borussia monchengladbach","m'gladbach","gladbach","monchengladbach"],["bayern munich","bayern"],
["bayer leverkusen","leverkusen"],["eintracht frankfurt","frankfurt"],["werder bremen","werder"],
["mainz 05","mainz"],["tsg hoffenheim","hoffenheim"],["rb leipzig","leipzig"],["union berlin","fc union berlin"],
["parma calcio","parma"],["internazionale","inter","inter milan"],["ac milan","milan"],["as roma","roma"],
["hellas verona","verona"],["ssc napoli","napoli"],["juventus fc","juventus"],["stade rennais","rennes"],
["strasbourg alsace","strasbourg"],
["real betis balompie","real betis","betis"],
["reial club deportiu espanyol de barcelona","rcd espanyol","espanyol barcelona","espanyol"],
["real club celta de vigo","celta de vigo","celta vigo","celta"],
["real sociedad de futbol","real sociedad","sociedad"],
["club atletico de madrid","atletico de madrid","atletico madrid","at madrid"],
["real madrid cf","real madrid"],
["real valladolid cf","real valladolid","valladolid"],
["real club deportivo mallorca","rcd mallorca","mallorca"],
["deportivo alaves","alaves"],
["rayo vallecano de madrid","rayo vallecano"],
["ca osasuna","osasuna"],
["ud las palmas","las palmas"],
["girona fc","girona"],
["valencia cf","valencia"],
["sevilla fc","sevilla"],
["getafe cf","getafe"],
["cd leganes","leganes"],
["villarreal cf","villarreal"],
["athletic club","ath bilbao","athletic bilbao"],
["bochum","vfl bochum 1848","vfl bochum"],
["holstein kiel","kieler sv holstein 1900","holstein kiel"],
["heidenheim","1 fc heidenheim 1846","fc heidenheim"],
["wolfsburg","vfl wolfsburg"],
["stuttgart","vfb stuttgart 1893","vfb stuttgart"],
["mainz 05","1 fsv mainz 05","mainz"],
["augsburg","fc augsburg"],
["bayern munich","fc bayern munchen","bayern munchen","bayern"],
["freiburg","sc freiburg"],
["union berlin","1 fc union berlin","fc union berlin"],
["st pauli","fc st pauli"],
["borussia monchengladbach","borussia vfl monchengladbach","m'gladbach","gladbach"],
["leipzig","rasenballsport leipzig","rb leipzig"],
["paris saint germain","paris saint-germain fc","psg","paris sg"],
["olympique de marseille","marseille","om"],
["olympique lyonnais","lyon"],
["stade de reims","reims"],
["stade brestois 29","brest"],
["racing club de lens","lens"],
["ogc nice cote d azur","nice"],
["rc strasbourg alsace","strasbourg"],
["as saint etienne","saint etienne","st etienne"],
["as monaco fc","monaco"],
["montpellier hsc","montpellier"],
["le havre ac","le havre"],
["fc nantes","nantes"],
["toulouse fc","toulouse"],
["angers sporting club de l ouest","angers"],
["fc internazionalemilano","fc internazionale milano","inter milan","internazionale","inter"],
["parma calcio 1913","parma calcio","parma"],
["cagliari calcio","cagliari"],
["calcio como 1907","como"],
["torino fc","torino"],
["ss lazio","lazio"],
["bologna fc 1909","bologna"],
["ac monza","monza"],
["us lecce","lecce"],
["genoa cfc","genoa"],
["acf fiorentina","fiorentina"],
["ssc napoli","napoli"],
["udinese calcio","udinese"]
]
def norm(s):
    x=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","",x)
ALIASES={norm(a):norm(g[0]) for g in GROUPS for a in g}
def team(s):
    x=norm(s)
    if x in ALIASES:
        return ALIASES[x]
    # Provider names often prepend competition/company forms (FC, VfL, RCD)
    # or append FC/CF and foundation-year digits. Try conservative variants;
    # if no explicit alias matches, return the cleaned key for exact joins.
    variants = [x]
    y = re.sub(r"^(?:\\d+)?(?:fc|cf|sc|afc|fsv|vfl|vfb|sv|tsg|acf|rcd|rc|cd|ud|ca|us|ss)", "", x)
    y = re.sub(r"(?:fc|cf|afc|calcio|footballclub)$", "", y)
    y = re.sub(r"\\d+$", "", y)
    y = re.sub(r"(?:defutbol|balompie)$", "", y)
    variants.extend([y])
    # Handles "Real Club Deportivo Mallorca", "Real Sociedad de Fútbol",
    # and legal registered team names that differ from Football-Data labels.
    for prefix in ("realclubdeportivo", "reialclubdeportiu", "clubdeportivo", "realclub", "realclubcelta", "clubatletico", "associationjeunesse", "racingclub", "rasenballsport", "borussiavfl", "fcinternazionale", "internazionalemilano"):
        if y.startswith(prefix):
            variants.append(y[len(prefix):])
    for v in variants:
        if v in ALIASES:
            return ALIASES[v]
    return y
def download(url,path,timeout=180):
    req=urllib.request.Request(url,headers={"User-Agent":"FootballAI-Research/1.0"})
    last=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=timeout) as src, open(path,"wb") as dst:
                while True:
                    b=src.read(2*1024*1024)
                    if not b: break
                    dst.write(b)
            if Path(path).stat().st_size < 100: raise RuntimeError("too-small download")
            print("DOWNLOADED",Path(path).name,Path(path).stat().st_size,flush=True); return
        except Exception as e:
            last=e; time.sleep(1+attempt)
    raise RuntimeError(f"download failed {url}: {last}")
def sec(e):
    try: return float(e["minute"])*60+float(e["second"])
    except (TypeError,ValueError,KeyError): return None
def classify(f,evs):
    goals=[e for e in evs if int(e.get("type_id") or 0)==16 and int(e.get("period_id") or 0) in (1,2) and sec(e) is not None]
    ends=[e for e in evs if int(e.get("type_id") or 0)==30 and int(e.get("period_id") or 0)==2 and sec(e) is not None]
    expected=int(f["home_score"])+int(f["away_score"])
    row={"date":str(f.get("match_date",""))[:10],"season":str(f["season"]),"league":str(f["competition"]),
         "home":str(f["home_team"]),"away":str(f["away_team"]),"score":f'{f["home_score"]}-{f["away_score"]}',
         "match_id":str(f["match_id"]),"goal_minutes":""}
    row["goal_minutes"]=",".join(str(int(sec(g)//60+1)) for g in goals)
    row.update({"A_goal_late":np.nan,"final_elapsed_sec":np.nan,"late_goal_seconds_before_whistle":"","reason_a":""})
    if len(goals)!=expected: row["reason_a"]="GOAL_EVENT_SCORE_MISMATCH"; return row
    if not ends: row["reason_a"]="NO_PERIOD_2_END"; return row
    ends_sec=[sec(e) for e in ends]
    if max(ends_sec)-min(ends_sec)>3: row["reason_a"]="CONFLICTING_END_TIMES"; return row
    final=max(ends_sec); row["final_elapsed_sec"]=final
    if not 5400<=final<=7200 or any(sec(g)>final for g in goals):
        row["reason_a"]="INVALID_FINAL_TIME"; return row
    late=[g for g in goals if final-120<=sec(g)<=final]
    row["A_goal_late"]=int(bool(late)); row["late_goal_seconds_before_whistle"]=",".join(str(round(final-sec(g),1)) for g in late)
    row["reason_a"]="EXACT_SECOND_WINDOW"; return row
def load_targets(tmp):
    fp=tmp/"opta_fixtures.parquet"; download(BASE+"opta_fixtures.parquet",fp)
    tbl=pq.read_table(fp,columns=["match_id","competition","season","match_date","match_status","home_team","away_team","home_score","away_score"])
    fixtures=[f for f in tbl.to_pylist() if f.get("competition") in LEAGUES and str(f.get("season")) in SEASONS
      and str(f.get("match_date",""))[:10]<=END.isoformat() and f.get("home_score") is not None and f.get("away_score") is not None
      and str(f.get("match_status","")).lower() in ("played","finished","complete","completed")]
    rows=[]
    for league in LEAGUES:
        fs=[f for f in fixtures if f["competition"]==league]
        if not fs: continue
        ids={str(f["match_id"]) for f in fs}; p=tmp/f"events_{league}.parquet"
        download(BASE+f"events_{league}.parquet",p)
        reader=pq.ParquetFile(p); byid={}
        id_type=reader.schema_arrow.field("match_id").type; typ=reader.schema_arrow.field("type_id").type
        id_arr=pa.array(list(ids),type=id_type); typ_arr=pa.array([16,30],type=typ)
        for batch in reader.iter_batches(batch_size=75000,columns=["match_id","type_id","minute","second","period_id"]):
            t=pa.Table.from_batches([batch])
            sel=t.filter(pc.and_(pc.is_in(t["match_id"],value_set=id_arr),pc.is_in(t["type_id"],value_set=typ_arr)))
            for e in sel.to_pylist(): byid.setdefault(str(e["match_id"]),[]).append(e)
        rows.extend(classify(f,byid.get(str(f["match_id"]),[])) for f in fs)
        p.unlink(missing_ok=True)
        print("OPTA",league,len(fs),flush=True)
    d=pd.DataFrame(rows); d["date_key"]=pd.to_datetime(d["date"],errors="coerce").dt.date
    if d.empty: raise RuntimeError("No completed Opta fixtures in frozen season range.")
    print("TARGET COUNTS",json.dumps({"rows":len(d),"goal":int(d["A_goal_late"].fillna(0).sum()),"unknown":int(d["A_goal_late"].isna().sum())},default=str),flush=True)
    return d
def load_odds(tmp):
    frames=[]
    for code,season in SEASON_CODES.items():
        for league,(comp,_) in LEAGUES.items():
            p=tmp/f"fd_{league}_{code}.csv"
            try:
                download(f"https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv",p,60)
                x=pd.read_csv(p,encoding="latin-1",low_memory=False)
            except Exception as e:
                print("ODDS SOURCE UNAVAILABLE",league,season,str(e)[:180],flush=True); continue
            req={"Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"}
            if not req.issubset(x.columns): print("MISSING COLUMNS",league,season,flush=True); continue
            x["league"]=league; x["season"]=season
            x["date_key"]=pd.to_datetime(x["Date"],dayfirst=True,errors="coerce").dt.date
            x["home_key"]=x["HomeTeam"].map(team); x["away_key"]=x["AwayTeam"].map(team)
            x["hg"]=pd.to_numeric(x["FTHG"],errors="coerce"); x["ag"]=pd.to_numeric(x["FTAG"],errors="coerce")
            x=x[x["FTR"].astype(str).isin(["H","D","A"]) & x["date_key"].notna() & x["hg"].notna() & x["ag"].notna()].copy()
            frames.append(x); print("ODDS",league,season,len(x),flush=True)
    if not frames: raise RuntimeError("No historical odds rows downloaded.")
    return pd.concat(frames,ignore_index=True,sort=False)
def join_odds(targets,odds):
    idx={k:g.reset_index(drop=True) for k,g in odds.groupby(["league","season"],sort=False)}
    rows=[]; misses=Counter()
    for _,t in targets.iterrows():
        r=t.to_dict(); pool=idx.get((t["league"],t["season"])); chosen=None
        if pool is not None and pd.notna(t["date_key"]):
            d=t["date_key"]
            cand=pool[pool["date_key"].map(lambda x:x is not None and abs((x-d).days)<=1)].copy()
            parts=str(t["score"]).split("-")
            cand=cand[(cand["hg"].astype(int)==int(parts[0]))&(cand["ag"].astype(int)==int(parts[1]))]
            if not cand.empty:
                hk,ak=team(t["home"]),team(t["away"])
                cand["identity"]=cand.apply(lambda z: SequenceMatcher(None,hk,z["home_key"]).ratio()+SequenceMatcher(None,ak,z["away_key"]).ratio()-0.08*abs((z["date_key"]-d).days),axis=1)
                exact=cand[(cand["home_key"]==hk)&(cand["away_key"]==ak)]
                if len(exact)==1: chosen=exact.iloc[0]
                elif len(cand)==1 and cand.iloc[0]["identity"]>=1.72: chosen=cand.iloc[0]
                elif len(cand)>1:
                    c=cand.sort_values("identity",ascending=False)
                    if c.iloc[0]["identity"]>=1.82 and c.iloc[0]["identity"]-c.iloc[1]["identity"]>=0.08: chosen=c.iloc[0]
        r["odds_join_status"]="MATCHED" if chosen is not None else "UNMATCHED"
        if chosen is None: misses[f"{t['league']}|{t['season']}"]+=1
        else:
            for col,val in chosen.items():
                if col not in r: r[col]=val.item() if hasattr(val,"item") else val
            r["fd_home"]=str(chosen["HomeTeam"]); r["fd_away"]=str(chosen["AwayTeam"])
        rows.append(r)
    out=pd.DataFrame(rows)
    print("ODDS JOIN",json.dumps({"matched":int(out["odds_join_status"].eq("MATCHED").sum()),"unmatched":int(out["odds_join_status"].eq("UNMATCHED").sum()),"misses":dict(misses)},ensure_ascii=False),flush=True)
    return out
TRIPLES=[
("AVG_CLOSE",("AvgCH","AvgCD","AvgCA")),("B365_CLOSE",("B365CH","B365CD","B365CA")),
("PINNACLE_CLOSE",("PSCH","PSCD","PSCA")),("AVG_STANDARD",("AvgH","AvgD","AvgA")),
("B365_STANDARD",("B365H","B365D","B365A")),("PINNACLE_STANDARD",("PSH","PSD","PSA"))]
OU=[
("AVG_CLOSE",("AvgC>2.5","AvgC<2.5")),("B365_CLOSE",("B365C>2.5","B365C<2.5")),
("AVG_STANDARD",("Avg>2.5","Avg<2.5")),("B365_STANDARD",("B365>2.5","B365<2.5"))]
def num(x):
    try:
        v=float(x); return v if math.isfinite(v) else np.nan
    except (TypeError,ValueError): return np.nan
def valid(row,cols):
    a=[num(row.get(c,np.nan)) for c in cols]; return all(np.isfinite(v) and v>1 for v in a)
def devig(vals):
    q=1/np.array(vals,dtype=float); return q/q.sum()
def overprob(a,b): return (1/a)/(1/a+1/b) if np.isfinite(a) and np.isfinite(b) and a>1 and b>1 else np.nan
def implied_total(p):
    if not np.isfinite(p) or p<=0 or p>=1: return np.nan
    def f(l): return 1-math.exp(-l)*(1+l+l*l/2)-p
    lo,hi=.05,8.
    for _ in range(60):
        mid=(lo+hi)/2
        if f(mid)>0: hi=mid
        else: lo=mid
    return (lo+hi)/2
def features(row):
    z={"market_source_1x2":"","market_source_total":"","p_home":np.nan,"p_draw":np.nan,"p_away":np.nan,"favorite_probability":np.nan,
       "favorite_odds":np.nan,"favorite_is_home":np.nan,"favorite_gap":np.nan,"p_over25":np.nan,"implied_total_goals_poisson":np.nan,
       "market_1x2_move_l1":np.nan,"favorite_probability_move":np.nan,"p_over25_move":np.nan}
    chosen=None
    for name,cols in TRIPLES:
        if valid(row,cols): chosen=(name,cols,[num(row.get(c)) for c in cols]); break
    if chosen:
        name,cols,prices=chosen; p=devig(prices); i=int(np.argmax(p))
        z.update({"market_source_1x2":name,"p_home":float(p[0]),"p_draw":float(p[1]),"p_away":float(p[2]),
          "favorite_probability":float(p[i]),"favorite_odds":float(prices[i]),"favorite_is_home":int(i==0),
          "favorite_gap":float(max(p)-np.sort(p)[-2])})
    for name,cols in OU:
        if valid(row,cols):
            p=overprob(num(row.get(cols[0])),num(row.get(cols[1])))
            if np.isfinite(p): z.update({"market_source_total":name,"p_over25":p,"implied_total_goals_poisson":implied_total(p)}); break
    for std,close in [(("AvgH","AvgD","AvgA"),("AvgCH","AvgCD","AvgCA")),(("B365H","B365D","B365A"),("B365CH","B365CD","B365CA")),(("PSH","PSD","PSA"),("PSCH","PSCD","PSCA"))]:
        if valid(row,std) and valid(row,close):
            p0,p1=devig([num(row.get(c)) for c in std]),devig([num(row.get(c)) for c in close])
            z["market_1x2_move_l1"]=float(np.abs(p1-p0).sum()); z["favorite_probability_move"]=float(max(p1)-max(p0)); break
    for a,b in [(("Avg>2.5","Avg<2.5"),("AvgC>2.5","AvgC<2.5")),(("B365>2.5","B365<2.5"),("B365C>2.5","B365C<2.5"))]:
        if valid(row,a) and valid(row,b):
            z["p_over25_move"]=float(overprob(num(row.get(b[0])),num(row.get(b[1])))-overprob(num(row.get(a[0])),num(row.get(a[1])))); break
    return z
def wilson(k,n):
    if not n:return (np.nan,np.nan)
    z=1.95996398454;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h,c+h
def summarize_bins(df,feat,edges,labels):
    d=df[df["A_goal_late"].notna()&df[feat].notna()].copy()
    if d.empty:return []
    d["bucket"]=pd.cut(d[feat],bins=edges,labels=labels,include_lowest=True,right=False); base=d["A_goal_late"].mean(); out=[]
    for b,g in d.groupby("bucket",observed=False,dropna=True):
        n=len(g);k=int(g["A_goal_late"].sum());lo,hi=wilson(k,n)
        out.append({"feature":feat,"bucket":str(b),"matches":n,"late_goals":k,"rate_pct":100*k/n if n else None,
          "ci95_low_pct":100*lo if n else None,"ci95_high_pct":100*hi if n else None,"overall_rate_pct":100*base,
          "lift_vs_overall_pct":100*(k/n)/base if n and base else None})
    return out
def scores(y,p,b):
    y=np.asarray(y,dtype=int);p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6);b=np.clip(np.asarray(b,dtype=float),1e-6,1-1e-6)
    if not len(y):return {"n":0}
    return {"n":len(y),"events":int(y.sum()),"rate_pct":100*y.mean(),"brier":float(brier_score_loss(y,p)),
      "base_brier":float(brier_score_loss(y,b)),"brier_skill":float(1-brier_score_loss(y,p)/brier_score_loss(y,b)),
      "logloss":float(log_loss(y,p,labels=[0,1])),"base_logloss":float(log_loss(y,b,labels=[0,1])),
      "auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,"average_precision":float(average_precision_score(y,p)) if len(np.unique(y))==2 else None}
def evaluate_model(df):
    numeric=["p_home","p_draw","p_away","favorite_probability","favorite_odds","favorite_is_home","favorite_gap","p_over25","implied_total_goals_poisson","market_1x2_move_l1","favorite_probability_move","p_over25_move"]
    x=df[df["A_goal_late"].notna()&df["odds_join_status"].eq("MATCHED")&df["p_home"].notna()].copy()
    x=x[x["season"].isin(SEASONS[:4])].copy(); x["A_goal_late"]=x["A_goal_late"].astype(int)
    prep=ColumnTransformer([("num",Pipeline([("imp",SimpleImputer(strategy="median",add_indicator=True)),("scale",StandardScaler())]),numeric),
        ("league",OneHotEncoder(handle_unknown="ignore"),["league"])])
    res=[]
    for label,tr_seasons,te_season in [("VALIDATION_2024_25",SEASONS[:2],"2024-2025"),("OOT_2025_26",SEASONS[:3],"2025-2026")]:
        tr=x[x["season"].isin(tr_seasons)]; te=x[x["season"].eq(te_season)]
        if len(tr)<1000 or len(te)<500 or tr["A_goal_late"].nunique()<2 or te["A_goal_late"].nunique()<2:
            res.append({"split":label,"status":"INSUFFICIENT_SAMPLE","train_n":len(tr),"test_n":len(te)}); continue
        pipe=Pipeline([("prep",prep),("logit",LogisticRegression(C=.2,max_iter=2000))])
        pipe.fit(tr[numeric+["league"]],tr["A_goal_late"]); pred=pipe.predict_proba(te[numeric+["league"]])[:,1]
        rates=tr.groupby("league")["A_goal_late"].mean().to_dict(); b=np.array([rates.get(l,tr["A_goal_late"].mean()) for l in te["league"]])
        res.append({"split":label,"status":"POOLED","train_seasons":tr_seasons,"test_season":te_season,**scores(te["A_goal_late"],pred,b)})
        scored=te.copy();scored["pred"]=pred;scored["base"]=b
        for league,g in scored.groupby("league"):
            res.append({"split":label,"status":"LEAGUE","league":league,**scores(g["A_goal_late"],g["pred"],g["base"])})
        if label=="OOT_2025_26":
            scored["decile"]=pd.qcut(scored["pred"].rank(method="first"),10,labels=False)
            for d,g in scored.groupby("decile",observed=False):
                res.append({"split":label,"status":"CALIBRATION_DECILE","bucket":int(d)+1,"matches":len(g),"events":int(g["A_goal_late"].sum()),
                    "observed_rate_pct":100*g["A_goal_late"].mean(),"mean_predicted_pct":100*g["pred"].mean()})
    return res
def main():
    tmp=OUT/"tmp";tmp.mkdir(parents=True,exist_ok=True)
    try:
        targets=load_targets(tmp); odds=load_odds(tmp); joined=join_odds(targets,odds)
        feat=joined.apply(lambda r:pd.Series(features(r)),axis=1); joined=pd.concat([joined.reset_index(drop=True),feat.reset_index(drop=True)],axis=1)
        joined["date"]=joined["date"].astype(str); joined.to_csv(OUT/"match_level.csv",index=False,encoding="utf-8-sig")
        valid=joined[joined["A_goal_late"].notna()].copy(); valid["A_goal_late"]=valid["A_goal_late"].astype(int)
        matched=valid[valid["odds_join_status"].eq("MATCHED")].copy()
        bins=[]
        bins+=summarize_bins(matched,"favorite_probability",[0,.38,.42,.46,.50,.55,.60,.70,1.01],["<=38%","38-42%","42-46%","46-50%","50-55%","55-60%","60-70%",">=70%"])
        bins+=summarize_bins(matched,"favorite_odds",[1,1.30,1.50,1.80,2.20,2.80,4,20],["1.00-1.29","1.30-1.49","1.50-1.79","1.80-2.19","2.20-2.79","2.80-3.99",">=4.00"])
        bins+=summarize_bins(matched,"p_draw",[0,.20,.23,.26,.29,.32,.35,.42,1],["<20%","20-23%","23-26%","26-29%","29-32%","32-35%","35-42%",">=42%"])
        bins+=summarize_bins(matched,"implied_total_goals_poisson",[0,2,2.3,2.6,2.9,3.2,3.5,8.1],["<2.0","2.0-2.29","2.3-2.59","2.6-2.89","2.9-3.19","3.2-3.49",">=3.5"])
        bins+=summarize_bins(matched,"p_over25",[0,.35,.42,.48,.52,.58,.65,1.01],["<35%","35-41%","42-47%","48-51%","52-57%","58-64%",">=65%"])
        bins+=summarize_bins(matched,"favorite_gap",[0,.03,.06,.10,.15,.22,.40,1],["<3pp","3-5pp","6-9pp","10-14pp","15-21pp","22-39pp",">=40pp"])
        bins+=summarize_bins(matched,"market_1x2_move_l1",[0,.01,.025,.05,.10,.20,2],["<1pp","1-2.4pp","2.5-4.9pp","5-9.9pp","10-19.9pp",">=20pp"])
        bins+=summarize_bins(matched,"p_over25_move",[-2,-.10,-.04,-.01,.01,.04,.10,2],["<=-10pp","-10 to -4pp","-4 to -1pp","stable -1 to +1pp","+1 to +4pp","+4 to +10pp",">+10pp"])
        pd.DataFrame(bins).to_csv(OUT/"market_bin_rates.csv",index=False,encoding="utf-8-sig")
        stability=[]
        for season,g in matched.groupby("season"):
            for scope_name,scope in [("POOLED_BIG5",g)]+[(l,z) for l,z in g.groupby("league")]:
                for f,edges,labels in [("favorite_probability",[0,.42,.50,.60,1.01],["<=42%","42-50%","50-60%",">=60%"]),("implied_total_goals_poisson",[0,2.3,2.6,2.9,8.1],["<2.3","2.3-2.59","2.6-2.89",">=2.9"])]:
                    xx=scope[scope[f].notna()].copy();xx["bucket"]=pd.cut(xx[f],bins=edges,labels=labels,include_lowest=True,right=False)
                    for b,z in xx.groupby("bucket",observed=False):
                        stability.append({"season":season,"league_scope":scope_name,"feature":f,"bucket":str(b),"matches":len(z),"late_goals":int(z["A_goal_late"].sum()),
                          "late_goal_rate_pct":100*z["A_goal_late"].mean() if len(z) else None})
        pd.DataFrame(stability).to_csv(OUT/"season_league_stability.csv",index=False,encoding="utf-8-sig")
        pd.DataFrame(evaluate_model(joined)).to_csv(OUT/"temporal_model_scores.csv",index=False,encoding="utf-8-sig")
        cov=[]
        for league in LEAGUES:
            for season in SEASONS:
                g=joined[(joined["league"]==league)&(joined["season"]==season)];known=g[g["A_goal_late"].notna()]
                cov.append({"league":league,"season":season,"target_matches":len(g),"A_resolved":len(known),"A_goals":int(known["A_goal_late"].sum()),
                    "A_rate_pct":100*known["A_goal_late"].mean() if len(known) else None,"odds_matched":int(g["odds_join_status"].eq("MATCHED").sum()),
                    "odds_join_rate_pct":100*g["odds_join_status"].eq("MATCHED").mean() if len(g) else None,"1X2_coverage_pct":100*g["p_home"].notna().mean() if len(g) else None,
                    "OU25_coverage_pct":100*g["p_over25"].notna().mean() if len(g) else None})
        pd.DataFrame(cov).to_csv(OUT/"coverage_by_league_season.csv",index=False,encoding="utf-8-sig")
        overall={"experiment":"LAST120_PREMATCH_CRITERIA_V1","snapshot_through":END.isoformat(),
          "target":"goal during actual final 120 seconds before actual second-half end; exact-second Opta","leagues":list(LEAGUES),"seasons":SEASONS,
          "target_rows":int(len(joined)),"resolved_target_rows":int(joined["A_goal_late"].notna().sum()),"A_goals":int(joined["A_goal_late"].fillna(0).sum()),
          "A_rate_resolved_pct":float(100*joined.loc[joined["A_goal_late"].notna(),"A_goal_late"].mean()),
          "odds_joined_rows":int(joined["odds_join_status"].eq("MATCHED").sum()),"resolved_and_odds_joined":int(len(matched)),
          "market_analysed_A_goals":int(matched["A_goal_late"].sum()),"market_analysed_A_rate_pct":float(100*matched["A_goal_late"].mean()) if len(matched) else None,
          "target_unknown_reasons":joined.loc[joined["A_goal_late"].isna(),"reason_a"].value_counts().to_dict(),
          "model_validation":"train 2022/23-2023/24; test 2024/25","model_OOT":"train 2022/23-2024/25; test 2025/26",
          "model":"fixed L2 logistic C=0.2; median imputation, standardization, league one-hot; fixed feature set",
          "baseline":"training-only late-goal base rate per league",
          "criterion_B":"not fully tested: no reliable per-match announced-added-time field in the event archive",
          "rpl":"excluded from the odds-feature model because a comparable paired historical pre-match quote table was not present in this analysis",
          "safety":"research-only; no production model or .pkl change; no Supabase writes; no paid API"}
        (OUT/"summary.json").write_text(json.dumps(overall,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        report=f"""# LAST120_PREMATCH_CRITERIA_V1 — предматчевые признаки позднего гола

Срез: матчи до {END.isoformat()} включительно. Статус: research-only; production, Supabase и .pkl не менялись.

## Определение и охват
Цель A — гол в последних 120 фактических секундах до события окончания второго тайма Opta. Неоднозначные события исключены из знаменателя.

- Матчей Opta: **{len(joined)}**; с разрешённой меткой A: **{overall['resolved_target_rows']}**.
- Голы A: **{overall['A_goals']}**; частота среди разрешённых: **{overall['A_rate_resolved_pct']:.2f}%**.
- Матчи с сопоставленным историческим рынком: **{overall['odds_joined_rows']}**.
- Odds-выборка с разрешённой меткой: **{overall['resolved_and_odds_joined']}** матчей; голы: **{overall['market_analysed_A_goals']}** ({overall['market_analysed_A_rate_pct']:.2f}%).

Включены АПЛ, Ла Лига, Бундеслига, Серия A и Лига 1. РПЛ не добавлена в модель коэффициентов без сопоставимого исторического ряда. Сначала берутся явные closing-колонки, затем standard-колонки. Standard price не считается гарантированным opening. Движение считается только при паре одного источника.

## Проверенные предматчевые группы
Частота гола и 95% интервалы Уилсона разбиты по силе фаворита и его котировке, вероятности ничьей, рыночной вероятности ТБ 2.5, Poisson-implied ожидаемому общему тоталу, разрыву между фаворитом и второй вероятностью, а также движению коэффициентов.

- market_bin_rates.csv — основные интервалы.
- season_league_stability.csv — сезонная и межлиговая устойчивость.
- coverage_by_league_season.csv — покрытие и соединение матчей.
- match_level.csv — матчевый ряд с исходными коэффициентами и выведенными признаками.
- temporal_model_scores.csv — holdout-метрики и калибровочные децили.

## Временная проверка
Фиксированная L2-логистическая регрессия (C=0.2), без подбора признаков по тестовому сезону:
- validation: 2022/23–2023/24 → 2024/25;
- temporal OOT: 2022/23–2024/25 → 2025/26.
Метрики: Brier, LogLoss, ROC-AUC, Average Precision и Brier skill против базовой частоты, рассчитанной только на train. Критерий считается полезным лишь при повторяемости на OOT и по лигам.

## Критерий B
Критерий B — последние две минуты объявленной добавки — не подменялся критерием A. Архив событий Opta не содержит надёжного значения добавленного времени, объявленного арбитром, для каждого исторического матча. Для B нужна отдельная проверенная разметка announced time.

## Ограничения
- 2026/27 — неполная описательная когорта, не доказательство OOT.
- Частота сегмента не является доказательством причинной связи или прибыльности.
- Никаких платных API, Supabase-записей или изменений production-модели.
"""
        (OUT/"FINAL_REPORT.md").write_text(report,encoding="utf-8")
        print("FINAL_SUMMARY="+json.dumps(overall,ensure_ascii=False,default=str),flush=True)
        print(report,flush=True)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
if __name__=="__main__":main()
