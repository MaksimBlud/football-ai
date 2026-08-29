"""Read-only Ligue 1 canonical prediction evaluator using Europe/Paris settlement."""
import pandas as pd
import evaluate_league_predictions as shared
from team_names import normalize_team_name
LEAGUE="LIGUE_1";TIMEZONE="Europe/Paris"
def settle_ligue1_predictions(ledger,results):
    ledger=shared._validate_ledger(ledger);results=shared._validate_results(results)
    if ledger.empty or results.empty:return pd.DataFrame()
    if not (ledger["league"].astype(str)==LEAGUE).all() or not (results["league"].astype(str)==LEAGUE).all():raise ValueError("Ligue 1 evaluator received foreign league")
    ledger=ledger.copy();results=results.copy();ledger["_match_date"]=ledger["kickoff_utc"].dt.tz_convert(TIMEZONE).dt.date;ledger["_home_key"]=ledger["home_team"].map(lambda v:normalize_team_name(str(v)));ledger["_away_key"]=ledger["away_team"].map(lambda v:normalize_team_name(str(v)))
    results["_match_date"]=results["match_date"];results["_home_key"]=results["home_team"].map(lambda v:normalize_team_name(str(v)));results["_away_key"]=results["away_team"].map(lambda v:normalize_team_name(str(v)))
    identity=["_match_date","_home_key","_away_key"];rv=results[identity+["result"]].copy()
    if rv.duplicated(subset=identity,keep=False).any():raise ValueError("Duplicate Ligue 1 result fixture identity")
    settled=ledger.merge(rv.rename(columns={"result":"actual_result"}),on=identity,how="inner",validate="many_to_one")
    if settled.empty:return settled
    settled["prediction_correct"]=settled["market_pick"]==settled["actual_result"];settled["actual_result_probability"]=[float(getattr(r,shared.PROBABILITY_COLUMNS[r.actual_result])) for r in settled.itertuples(index=False)];return settled
def evaluate_frames(ledger,results):
    settled=settle_ligue1_predictions(ledger,results);latest=shared.latest_pre_kickoff(settled);return settled,latest,shared.calculate_metrics(settled,view="ALL_SNAPSHOTS"),shared.calculate_metrics(latest,view="LATEST_PRE_KICKOFF_PER_FIXTURE")
def main():
    ledger=shared.load_ledger(LEAGUE);results=shared.load_results(LEAGUE);settled,latest,a,b=evaluate_frames(ledger,results);print("LIGUE 1 CANONICAL PREDICTION EVALUATION");print("ledger rows:",len(ledger));print("finished result rows:",len(results));print("settled rows:",len(settled));print("MARKET_ONLY rows:",int((ledger.get("prediction_mode",pd.Series(dtype=str))=="MARKET_ONLY").sum()));print("Structural applied rows:",int(ledger.get("structural_applied",pd.Series(dtype=bool)).fillna(False).astype(bool).sum()));shared._print_metrics(a);shared._print_metrics(b);print("evaluation timezone:",TIMEZONE);print("Supabase writes:",False);print("production model used:",False);print("Structural V2 activation:",False)
if __name__=="__main__":main()
