"""Persist immutable MARKET_ONLY predictions for Turkey Super Lig and Primeira Liga."""
from __future__ import annotations
import argparse
import pandas as pd
from league_prediction_ledger import build_market_only_predictions, persist_predictions
from turkey_portugal_market_only import config_for


def _argmax(row):
    values={"H":float(row["home_probability"]),"D":float(row["draw_probability"]),"A":float(row["away_probability"])}
    return max(values,key=values.get)


def snapshots_to_market_shadow(league: str, frame: pd.DataFrame) -> pd.DataFrame:
    config_for(league)
    required={"league","event_id","home_team","away_team","commence_time_utc","snapshot_time_utc","home_probability","draw_probability","away_probability"}
    missing=required-set(frame.columns)
    if missing: raise ValueError(f"Snapshot frame missing columns: {sorted(missing)}")
    work=frame.copy()
    if not work.empty and not work["league"].eq(league).all(): raise ValueError("Foreign league in snapshot frame")
    work=work.loc[pd.to_datetime(work["snapshot_time_utc"],utc=True)<pd.to_datetime(work["commence_time_utc"],utc=True)].copy()
    if work.empty: return pd.DataFrame(columns=["league","event_id","home_team","away_team","commence_time_utc","snapshot_time_utc","market_home_probability","market_draw_probability","market_away_probability","market_argmax","market_shadow_status","market_only"])
    work["market_home_probability"]=pd.to_numeric(work["home_probability"],errors="raise")
    work["market_draw_probability"]=pd.to_numeric(work["draw_probability"],errors="raise")
    work["market_away_probability"]=pd.to_numeric(work["away_probability"],errors="raise")
    work["market_argmax"]=work.apply(_argmax,axis=1)
    work["market_shadow_status"]="OK"; work["market_only"]=True
    cols=["league","event_id","home_team","away_team","commence_time_utc","snapshot_time_utc","market_home_probability","market_draw_probability","market_away_probability","market_argmax","market_shadow_status","market_only"]
    return work[cols].reset_index(drop=True)


def persist_from_snapshots(league: str, frame: pd.DataFrame, client=None):
    shadow=snapshots_to_market_shadow(league,frame)
    if shadow.empty:return {"inserted":0,"unchanged":0,"conflicts":0,"predictions":0}
    predictions=build_market_only_predictions(shadow)
    if client is None:
        from database import supabase as client
    metrics=persist_predictions(client,predictions)
    return {**metrics,"predictions":len(predictions)}


def fetch_recent_snapshots(league: str, client=None):
    config_for(league)
    if client is None:
        from database import supabase as client
    r=client.table("odds_snapshots").select("league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc,home_probability,draw_probability,away_probability").eq("league",league).order("snapshot_time_utc",desc=True).limit(500).execute()
    return pd.DataFrame(r.data or [])


def main():
    p=argparse.ArgumentParser(); p.add_argument("league",choices=["TURKEY_SUPER_LIG","PRIMEIRA_LIGA"]); a=p.parse_args()
    frame=fetch_recent_snapshots(a.league); out=persist_from_snapshots(a.league,frame); print(a.league,"prediction ledger:",out)
if __name__=="__main__": main()
