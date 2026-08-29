"""One-command research-only Eredivisie MARKET_ONLY live cycle."""
from dataclasses import dataclass
import pandas as pd
from database import supabase
import export_eredivisie_upcoming_matches as fixture_export
import generate_eredivisie_market_shadow as market_shadow
import league_supabase_persistence as persistence
import persist_eredivisie_market_observations as observation_mirror
import persist_eredivisie_prediction_ledger as prediction_ledger
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG

@dataclass(frozen=True)
class EredivisieLiveCycleResult:
    fixture_source_rows:int; fixture_rows:int; market_snapshot_rows:int; market_shadow_rows:int; market_ok_rows:int; history_rows:int; observations_before:int; observations_after:int; observations_inserted:int; observations_unchanged:int; observation_conflicts:int; ledger_before:int; ledger_after:int; ledger_inserted:int; ledger_unchanged:int; ledger_conflicts:int; results_before:int; results_after:int

def assert_market_only_runtime():
    s=EREDIVISIE_RUNTIME_CONFIG.structural_v2
    if s.calibration_status!="CALIBRATION_REQUIRED" or s.structural_alpha is not None or s.edge_threshold is not None: raise RuntimeError("Eredivisie Structural V2 must remain calibration-required")
def durable_counts(): return len(persistence.fetch_observations(supabase,EREDIVISIE_RUNTIME_CONFIG)),len(persistence.fetch_results(supabase,EREDIVISIE_RUNTIME_CONFIG))
def ledger_count():
    r=supabase.table(prediction_ledger.TABLE).select("prediction_key",count="exact").eq("league","EREDIVISIE").execute(); return int(r.count) if r.count is not None else len(r.data or [])
def run_cycle():
    assert_market_only_runtime(); schema=persistence.check_schema(supabase)
    if schema.status!="PASS": raise RuntimeError("Generic persistence unavailable: "+schema.detail)
    ob0,res0=durable_counts(); led0=ledger_count(); snaps=fixture_export.fetch_eredivisie_snapshots(); upcoming=fixture_export.prepare_upcoming_fixtures(snaps)
    if upcoming.empty or upcoming["event_id"].duplicated().any(): raise RuntimeError("Invalid future Eredivisie fixtures")
    path=EREDIVISIE_RUNTIME_CONFIG.paths.upcoming_fixtures; path.parent.mkdir(parents=True,exist_ok=True); upcoming.to_csv(path,index=False)
    market_snaps=market_shadow.fetch_eredivisie_snapshots(); latest=market_shadow.build_market_shadow(market_shadow.load_upcoming(),market_snaps,previous_history=market_shadow.load_previous_history())
    if latest.empty or latest["event_id"].duplicated().any(): raise RuntimeError("Invalid Eredivisie market shadow")
    if not (latest["league"].astype(str)=="EREDIVISIE").all() or not (latest["market_only"].astype(str).str.lower()=="true").all(): raise RuntimeError("Eredivisie MARKET_ONLY safety failed")
    history=market_shadow.write_market_shadow_outputs(latest,latest_path=EREDIVISIE_RUNTIME_CONFIG.paths.market_shadow,history_path=EREDIVISIE_RUNTIME_CONFIG.paths.market_history)
    ok=latest.loc[latest["market_shadow_status"]=="OK"].copy()
    if ok.empty: raise RuntimeError("No valid Eredivisie market shadows")
    st=pd.to_datetime(ok["snapshot_time_utc"],utc=True,errors="coerce"); kt=pd.to_datetime(ok["commence_time_utc"],utc=True,errors="coerce")
    if st.isna().any() or kt.isna().any() or not (st<kt).all(): raise RuntimeError("Eredivisie timestamp safety failed")
    probs=ok[["market_home_probability","market_draw_probability","market_away_probability"]].apply(pd.to_numeric,errors="coerce")
    if probs.isna().any().any() or not (probs.sum(axis=1).sub(1.0).abs()<=1e-12).all(): raise RuntimeError("Eredivisie market probabilities invalid")
    persisted=observation_mirror.load_market_shadow()
    if len(persisted)!=len(latest) or set(persisted["event_id"].astype(str))!=set(latest["event_id"].astype(str)): raise RuntimeError("Persisted Eredivisie shadow mismatch")
    durable=observation_mirror.build_market_only_observations(persisted); om=persistence.persist_observations(supabase,durable,EREDIVISIE_RUNTIME_CONFIG)
    if int(om["conflicts"])!=0: raise RuntimeError("Eredivisie observation conflict")
    ob1,res1=durable_counts()
    if res1!=res0 or ob1!=ob0+int(om["inserted"]): raise RuntimeError("Eredivisie durable count mismatch")
    lm=prediction_ledger.persist_current_predictions()
    if int(lm["conflicts"])!=0: raise RuntimeError("Eredivisie ledger conflict")
    led1=ledger_count()
    if led1!=led0+int(lm["inserted"]): raise RuntimeError("Eredivisie ledger count mismatch")
    return EredivisieLiveCycleResult(len(snaps),len(upcoming),len(market_snaps),len(latest),len(ok),len(history),ob0,ob1,int(om["inserted"]),int(om["unchanged"]),int(om["conflicts"]),led0,led1,int(lm["inserted"]),int(lm["unchanged"]),int(lm["conflicts"]),res0,res1)
def main():
    r=run_cycle(); print("EREDIVISIE MARKET-ONLY LIVE CYCLE")
    for k,v in r.__dict__.items(): print(k+":",v)
    print("AI model used:",False); print("Structural V2 used:",False); print("production model used:",False)
if __name__=="__main__": main()
