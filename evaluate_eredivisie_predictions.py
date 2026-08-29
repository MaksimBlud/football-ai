"""Read-only Eredivisie canonical prediction evaluator using Europe/Amsterdam."""
import pandas as pd
import evaluate_league_predictions as shared
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from team_names import normalize_team_name

LEAGUE="EREDIVISIE"; TIMEZONE=EREDIVISIE_RUNTIME_CONFIG.identity.timezone

def settle_eredivisie_predictions(ledger,results):
    ledger=shared._validate_ledger(ledger);results=shared._validate_results(results)
    if ledger.empty or results.empty:return pd.DataFrame()
    if not (ledger["league"].astype(str)==LEAGUE).all():raise ValueError("Eredivisie evaluator received foreign ledger rows")
    if not (results["league"].astype(str)==LEAGUE).all():raise ValueError("Eredivisie evaluator received foreign result rows")
    ledger=ledger.copy();results=results.copy();ledger["_match_date"]=ledger["kickoff_utc"].dt.tz_convert(TIMEZONE).dt.date
    ledger["_home_key"]=ledger["home_team"].map(lambda v:normalize_team_name(str(v)));ledger["_away_key"]=ledger["away_team"].map(lambda v:normalize_team_name(str(v)))
    results["_match_date"]=results["match_date"];results["_home_key"]=results["home_team"].map(lambda v:normalize_team_name(str(v)));results["_away_key"]=results["away_team"].map(lambda v:normalize_team_name(str(v)))
    identity=["_match_date","_home_key","_away_key"];view=results[identity+["result"]].copy()
    if view.duplicated(subset=identity,keep=False).any():raise ValueError("Duplicate Eredivisie finished-result fixture identity")
    settled=ledger.merge(view.rename(columns={"result":"actual_result"}),on=identity,how="inner",validate="many_to_one")
    if settled.empty:return settled
    settled["prediction_correct"]=settled["market_pick"]==settled["actual_result"]
    settled["actual_result_probability"]=[float(getattr(row,shared.PROBABILITY_COLUMNS[row.actual_result])) for row in settled.itertuples(index=False)]
    return settled

def evaluate_frames(ledger,results):
    ledger=shared._validate_ledger(ledger);results=shared._validate_results(results);settled=settle_eredivisie_predictions(ledger,results);latest=shared.latest_pre_kickoff(settled)
    return settled,latest,shared.calculate_metrics(settled,view="ALL_SNAPSHOTS"),shared.calculate_metrics(latest,view="LATEST_PRE_KICKOFF_PER_FIXTURE")

def main():
    ledger=shared.load_ledger(LEAGUE);results=shared.load_results(LEAGUE);settled,latest,all_metrics,latest_metrics=evaluate_frames(ledger,results)
    print("EREDIVISIE CANONICAL PREDICTION EVALUATION");print("ledger rows:",len(ledger));print("finished result rows:",len(results));print("settled rows:",len(settled));print("settled fixtures:",settled["event_id"].nunique() if not settled.empty else 0);print("MARKET_ONLY rows:",int((ledger.get("prediction_mode",pd.Series(dtype=str))=="MARKET_ONLY").sum()));print("Structural applied rows:",int(ledger.get("structural_applied",pd.Series(dtype=bool)).fillna(False).astype(bool).sum()));shared._print_metrics(all_metrics);shared._print_metrics(latest_metrics);print("evaluation timezone:",TIMEZONE);print("Supabase writes:",False);print("production model used:",False);print("Structural V2 activation:",False)
if __name__=="__main__":main()
