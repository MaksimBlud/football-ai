"""Download EPL, La Liga and Serie A history and run Historical Football Signal Lab."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import requests
from historical_football_signal_lab import build_point_in_time_features, write_reports
from historical_football_window_audit import write_window_reports
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

LEAGUES={"EPL":EPL_RUNTIME_CONFIG,"LA_LIGA":LA_LIGA_RUNTIME_CONFIG,"SERIE_A":SERIE_A_RUNTIME_CONFIG}
BASE="https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv"

def download(config, league: str, raw_dir: Path):
    raw_frames=[]
    raw_dir.mkdir(parents=True,exist_ok=True)
    for code,season in config.historical_source.season_codes.items():
        url=BASE.format(code=code,comp=config.historical_source.competition_code)
        r=requests.get(url,timeout=60); r.raise_for_status()
        path=raw_dir/f"{league.lower()}_{code}.csv"; path.write_bytes(r.content)
        df=pd.read_csv(path); df["_season"]=season; raw_frames.append(df)
        print(f"{league} {season}: raw={len(df)}")
    raw=pd.concat(raw_frames,ignore_index=True)
    features=build_point_in_time_features(raw,league,"MULTI_SEASON")
    keys=raw[["Date","HomeTeam","AwayTeam","_season"]].copy(); keys["match_date"]=pd.to_datetime(keys["Date"],dayfirst=True,errors="coerce")
    keys=keys.rename(columns={"HomeTeam":"home_team","AwayTeam":"away_team","_season":"season"})[["match_date","home_team","away_team","season"]].drop_duplicates()
    features=features.drop(columns=["season"]).merge(keys,on=["match_date","home_team","away_team"],how="left",validate="one_to_one")
    if features["season"].isna().any(): raise RuntimeError(f"{league}: failed to restore season labels")
    print(f"{league}: continuous point-in-time rows={len(features)}"); return features

def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-dir",type=Path,default=Path("artifacts/historical_football_signal_work")); p.add_argument("--output-dir",type=Path,default=Path("artifacts/historical_football_signal_lab")); a=p.parse_args()
    combined=pd.concat([download(cfg,league,a.work_dir/"raw"/league.lower()) for league,cfg in LEAGUES.items()],ignore_index=True)
    paths=write_reports(combined,a.output_dir); window,robustness=write_window_reports(combined,a.output_dir)
    print(f"HISTORICAL FOOTBALL SIGNAL LAB COMPLETE rows={len(combined)}")
    for k,v in paths.items(): print(f"{k}: {v}")
    print("WINDOW ABLATION"); print(window.to_string(index=False))
    print("PAIRED WINDOW ROBUSTNESS"); print(robustness.to_string(index=False))
    print("Research only: no training promotion, Supabase writes, Structural changes, or .pkl changes.")
if __name__=="__main__": main()
