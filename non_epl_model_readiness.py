"""Fail-closed repository audit for eight non-EPL AI model candidates."""
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LEAGUES={
 "LA_LIGA": dict(seasons=10,data=["build_la_liga_historical_dataset.py","OFFLINE_HISTORY_COMPLETENESS_STATUS.md"],pit=["build_la_liga_temporal_features.py","add_la_liga_elo_features.py"],norm=["la_liga_canonical_names.py","normalize_la_liga_history.py"],oos=["evaluate_la_liga_oos_candidate.py","league_model_sweep.py","league_model_diagnostics.py"],market=["league_runtime_config.py","la_liga_live_cycle.py"],builder="train_la_liga_1x2_candidate.py"),
 "SERIE_A": dict(seasons=10,data=["serie_a_runtime_config.py","OFFLINE_HISTORY_COMPLETENESS_STATUS.md","league_offline_history.py"],pit=["league_offline_features.py"],norm=["serie_a_runtime_config.py","league_offline_history.py"],oos=["historical_football_signal_runner.py","historical_football_signal_lab.py"],market=["serie_a_runtime_config.py","serie_a_live_cycle.py"]),
 "BUNDESLIGA": dict(seasons=10,data=["bundesliga_runtime_config.py","OFFLINE_HISTORY_COMPLETENESS_STATUS.md","league_offline_history.py"],pit=["league_offline_features.py"],norm=["bundesliga_runtime_config.py","league_offline_history.py"],oos=[],market=["bundesliga_runtime_config.py","bundesliga_live_cycle.py"]),
 "LIGUE_1": dict(seasons=10,data=["ligue1_runtime_config.py","OFFLINE_HISTORY_COMPLETENESS_STATUS.md","league_offline_history.py"],pit=["league_offline_features.py"],norm=["ligue1_runtime_config.py","league_offline_history.py"],oos=[],market=["ligue1_runtime_config.py","ligue1_live_cycle.py"]),
 "EREDIVISIE": dict(seasons=9,data=["eredivisie_runtime_config.py","OFFLINE_HISTORY_COMPLETENESS_STATUS.md","league_offline_history.py"],pit=["league_offline_features.py"],norm=["eredivisie_runtime_config.py","league_offline_history.py"],oos=[],market=["eredivisie_runtime_config.py","eredivisie_live_cycle.py"]),
 "RPL": dict(seasons=0,data=[],pit=[],norm=[],oos=[],market=["rpl_source_contract.py","rpl_live_cycle.py"]),
 "PRIMEIRA_LIGA": dict(seasons=10,data=["primeira_liga_runtime_config.py","audit_turkey_portugal_historical_foundation.py","league_offline_history.py"],pit=["league_offline_features.py"],norm=["primeira_liga_runtime_config.py","audit_turkey_portugal_team_identity.py"],oos=[],market=["primeira_liga_runtime_config.py","scheduled_turkey_portugal_odds.py"]),
 "SUPER_LIG": dict(seasons=10,data=["turkey_super_lig_runtime_config.py","audit_turkey_portugal_historical_foundation.py","league_offline_history.py"],pit=["league_offline_features.py"],norm=["turkey_super_lig_runtime_config.py","audit_turkey_portugal_team_identity.py"],oos=[],market=["turkey_super_lig_runtime_config.py","scheduled_turkey_portugal_odds.py"]),
}
OOS_DECLARED={"LA_LIGA","SERIE_A"}


def _all(root, paths): return bool(paths) and all((root/p).is_file() for p in paths)

def _manifest(root, league): return root/"artifacts"/"candidates"/league.lower()/"manifest.json"

def _valid_manifest(path, league):
    if not path.is_file(): return False
    try: x=json.loads(path.read_text())
    except (OSError,json.JSONDecodeError): return False
    keys=("model_artifact_sha256","calibrator_sha256","code_commit_sha","historical_cutoff","feature_schema_sha256")
    return x.get("league")==league and all(x.get(k) for k in keys) and all(isinstance(x.get(k),dict) and x[k].get("status")=="PASSED" for k in ("oos_validation","calibration"))

def audit_league(league, root=ROOT):
    c=LEAGUES[league]
    data=_all(root,c["data"])
    pit=data and _all(root,c["pit"])
    norm=data and _all(root,c["norm"])
    oos=data and pit and norm and league in OOS_DECLARED and _all(root,c["oos"])
    market=_all(root,c["market"])
    builder=bool(c.get("builder") and (root/c["builder"]).is_file())
    model=oos and builder and _valid_manifest(_manifest(root,league),league)
    statuses={"DATA_READY":data,"PIT_READY":pit,"NORMALIZATION_READY":norm,"OOS_READY":oos,"MODEL_READY":model,"CALIBRATION_READY":model,"PROVENANCE_READY":model,"MARKET_READY":market,"PROSPECTIVE_READY":False}
    score=sum(statuses[k] for k in ("DATA_READY","PIT_READY","NORMALIZATION_READY","OOS_READY","MARKET_READY"))+builder
    return {"league":league,"historical_seasons":c["seasons"],"statuses":statuses,"candidate_builder_ready":builder,"foundation_score":score}

def build_matrix(root=ROOT):
    rows=[audit_league(k,root) for k in LEAGUES]
    ranked=sorted(rows,key=lambda r:(r["foundation_score"],r["historical_seasons"],r["league"]=="LA_LIGA"),reverse=True)
    return {"version":1,"prospective_outcomes_read":False,"paid_provider_requests":0,"recommended_first_league":ranked[0]["league"],"rows":rows}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); a=p.parse_args(); m=build_matrix()
    if a.json: print(json.dumps(m,indent=2)); return 0
    print("recommended first league:",m["recommended_first_league"])
    for r in m["rows"]: print(r["league"],r["foundation_score"],r["statuses"])
    return 0

if __name__=="__main__": raise SystemExit(main())
