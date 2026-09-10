"""Research-only La Liga 1X2 candidate builder from completed history."""
import hashlib, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.metrics import accuracy_score, log_loss
import league_model_sweep as sweep

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/"data/la_liga_features_with_elo_trainable.csv"
OUT=ROOT/"artifacts/candidates/la_liga"
REPORT=ROOT/"experiments/la_liga_candidate_artifact/latest.json"
FINAL=sweep.FINAL_HOLDOUT_SEASON
SELECTION=tuple(sweep.SELECTION_TEST_SEASONS)
GRID=np.linspace(.50,2.50,401)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def prod_state():
    return {n:(sha(ROOT/n) if (ROOT/n).exists() else None) for n in sweep.PRODUCTION_ARTIFACTS}

def code_sha():
    value=os.getenv("GITHUB_SHA","").strip()
    if value: return value
    p=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True)
    if p.returncode or len(p.stdout.strip())<7: raise RuntimeError("code SHA unavailable")
    return p.stdout.strip()

def validate(frame):
    needed={"league","season","match_date","result"}
    if needed-set(frame): raise ValueError("historical frame missing required columns")
    if set(frame.league.dropna().astype(str).unique())!={"LA_LIGA"}: raise ValueError("expected pure LA_LIGA history")
    seasons=sorted(frame.season.dropna().astype(str).unique())
    if FINAL not in seasons: raise ValueError("locked completed holdout missing")
    if any(s>FINAL for s in seasons): raise ValueError("prospective/current season rows are forbidden")

def clip(p):
    p=np.clip(np.asarray(p,float),1e-9,1.0); return p/p.sum(axis=1,keepdims=True)

def temperature(p,t):
    x=np.log(clip(p))/float(t); x-=x.max(axis=1,keepdims=True); x=np.exp(x); return x/x.sum(axis=1,keepdims=True)

def brier(y,p): return float(np.mean(np.sum((p-np.eye(3)[y])**2,axis=1)))
def metrics(y,p):
    p=clip(p); return {"accuracy":float(accuracy_score(y,np.argmax(p,axis=1))),"logloss":float(log_loss(y,p,labels=[0,1,2])),"brier":brier(y,p)}

def fit_temp(p,y): return min((float(log_loss(y,temperature(p,t),labels=[0,1,2])),float(t)) for t in GRID)[1]

def select(frame):
    rows=[]
    for fs in sweep.FEATURE_SETS:
        for model in sweep.MODEL_VARIANTS:
            x=sweep.evaluate_selection_variant(frame,feature_set_name=fs,model_name=model)
            rows.append({"feature_set":fs,"model":model,**x})
    rows.sort(key=lambda x:(x["logloss"],x["brier"],-x["accuracy"]))
    return rows[0],rows

def oos(frame,seasons,fs,model_name):
    features=sweep.FEATURE_SETS[fs]; probs=[]; ys=[]
    for season in seasons:
        tr=frame[frame.season.astype(str)<season].dropna(subset=features+["target"])
        te=frame[frame.season.astype(str)==season].dropna(subset=features+["target"])
        if tr.empty or te.empty: raise RuntimeError(f"empty OOS fold {season}")
        model=sweep.make_model(model_name); model.fit(tr[features],tr.target.astype(int))
        probs.append(model.predict_proba(te[features])); ys.append(te.target.astype(int).to_numpy())
    return np.vstack(probs),np.concatenate(ys)

def holdout(frame,fs,model_name):
    features=sweep.FEATURE_SETS[fs]
    tr=frame[frame.season.astype(str)<FINAL].dropna(subset=features+["target"])
    te=frame[frame.season.astype(str)==FINAL].dropna(subset=features+["target","home_odds","draw_odds","away_odds"])
    if tr.empty or te.empty: raise RuntimeError("locked final holdout empty")
    model=sweep.make_model(model_name); model.fit(tr[features],tr.target.astype(int))
    return model.predict_proba(te[features]),sweep.market_probabilities(te),te.target.astype(int).to_numpy()

def gate(raw,cal,market):
    checks={"calibration_improves_logloss":cal["logloss"]<raw["logloss"],"calibration_not_worse_brier":cal["brier"]<=raw["brier"],"beats_market_accuracy":cal["accuracy"]>market["accuracy"],"beats_market_logloss":cal["logloss"]<market["logloss"],"beats_market_brier":cal["brier"]<market["brier"]}
    checks["passed"]=all(checks.values()); return checks

def write_report(x):
    REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(json.dumps(x,indent=2)+"\n"); return REPORT

def main():
    before=prod_state(); commit=code_sha(); frame=pd.read_csv(INPUT); validate(frame); frame=frame.copy(); frame["target"]=frame.result.map(sweep.TARGET_MAP)
    winner,candidates=select(frame); fs=winner["feature_set"]; model_name=winner["model"]; features=sweep.FEATURE_SETS[fs]
    p,y=oos(frame,SELECTION,fs,model_name); t=fit_temp(p,y)
    raw_p,market_p,yh=holdout(frame,fs,model_name); raw=metrics(yh,raw_p); cal=metrics(yh,temperature(raw_p,t)); market=metrics(yh,market_p); q=gate(raw,cal,market)
    report={"league":"LA_LIGA","research_only":True,"prospective_outcomes_read":False,"promotion_performed":False,"selection_seasons":list(SELECTION),"locked_final_holdout":FINAL,"winner":winner,"candidate_count":len(candidates),"temperature":t,"final_holdout":{"raw":raw,"calibrated":cal,"market":market},"quality_gate":q,"code_commit_sha":commit,"production_before":before}
    if not q["passed"]:
        report.update(status="REJECTED_NO_ARTIFACT",production_after=prod_state()); report["production_unchanged"]=report["production_after"]==before; write_report(report)
        if not report["production_unchanged"]: raise RuntimeError("production artifact changed")
        print("REJECTED_NO_ARTIFACT"); return 0
    train=frame[frame.season.astype(str)<=FINAL].dropna(subset=features+["target","match_date"]); model=sweep.make_model(model_name); model.fit(train[features],train.target.astype(int)); OUT.mkdir(parents=True,exist_ok=True)
    model_path=OUT/"model.joblib"; cal_path=OUT/"calibrator.json"; manifest_path=OUT/"manifest.json"; joblib.dump(model,model_path)
    cal_payload={"kind":"temperature_scaling","temperature":t,"fit_seasons":list(SELECTION),"validation_season":FINAL,"code_commit_sha":commit}; cal_path.write_text(json.dumps(cal_payload,indent=2)+"\n")
    schema=hashlib.sha256(json.dumps(features,separators=(",",":")).encode()).hexdigest(); cutoff=str(pd.to_datetime(train.match_date).max().date())
    manifest={"version":1,"league":"LA_LIGA","research_candidate_only":True,"promotion_performed":False,"model_artifact_sha256":sha(model_path),"calibrator_sha256":sha(cal_path),"code_commit_sha":commit,"historical_cutoff":cutoff,"features":features,"feature_schema_sha256":schema,"model_variant":model_name,"oos_validation":{"status":"PASSED",**q,"final_holdout":cal},"calibration":{"status":"PASSED","method":"temperature_scaling","temperature":t,"selection_oos_rows":int(len(y))},"created_at_utc":datetime.now(timezone.utc).isoformat()}; manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    after=prod_state()
    if after!=before:
        for p in (model_path,cal_path,manifest_path): p.unlink(missing_ok=True)
        raise RuntimeError("production artifact changed; candidate removed")
    report.update(status="CANDIDATE_ARTIFACT_WRITTEN",manifest=str(manifest_path.relative_to(ROOT)),production_after=after,production_unchanged=True); write_report(report); print("CANDIDATE_ARTIFACT_WRITTEN"); return 0

if __name__=="__main__": raise SystemExit(main())
