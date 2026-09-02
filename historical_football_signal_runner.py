"""Download EPL, La Liga and Serie A history and run Historical Football Signal Lab."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import requests
from historical_football_signal_lab import build_point_in_time_features, write_reports
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

LEAGUES={"EPL":EPL_RUNTIME_CONFIG,"LA_LIGA":LA_LIGA_RUNTIME_CONFIG,"SERIE_A":SERIE_A_RUNTIME_CONFIG}
BASE="https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv"

def download(config, league: str, raw_dir: Path):
    frames=[]
    raw_dir.mkdir(parents=True,exist_ok=True)
    for code,season in config.historical_source.season_codes.items():
        url=BASE.format(code=code,comp=config.historical_source.competition_code)
        r=requests.get(url,timeout=60); r.raise_for_status()
        path=raw_dir/f"{league.lower()}_{code}.csv"; path.write_bytes(r.content)
        df=pd.read_csv(path)
        features=build_point_in_time_features(df,league,season)
        frames.append(features)
        print(f"{league} {season}: raw={len(df)} usable={len(features)}")
    return pd.concat(frames,ignore_index=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-dir",type=Path,default=Path("artifacts/historical_football_signal_work")); p.add_argument("--output-dir",type=Path,default=Path("artifacts/historical_football_signal_lab")); a=p.parse_args()
    all_frames=[download(cfg,league,a.work_dir/"raw"/league.lower()) for league,cfg in LEAGUES.items()]
    combined=pd.concat(all_frames,ignore_index=True)
    paths=write_reports(combined,a.output_dir)
    print(f"HISTORICAL FOOTBALL SIGNAL LAB COMPLETE rows={len(combined)}")
    for k,v in paths.items(): print(f"{k}: {v}")
    print("Research only: no training promotion, Supabase writes, Structural changes, or .pkl changes.")
if __name__=="__main__": main()
