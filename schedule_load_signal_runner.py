"""Download three-league history and run the preregistered Schedule Load Signal Lab."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from schedule_load_signal_lab import build_schedule_features, write_reports
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

LEAGUES = {
    "EPL": EPL_RUNTIME_CONFIG,
    "LA_LIGA": LA_LIGA_RUNTIME_CONFIG,
    "SERIE_A": SERIE_A_RUNTIME_CONFIG,
}
BASE = "https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv"


def download_history(config, league: str, raw_dir: Path) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for code, season in config.historical_source.season_codes.items():
        url = BASE.format(code=code, comp=config.historical_source.competition_code)
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        path = raw_dir / f"{league.lower()}_{code}.csv"
        path.write_bytes(response.content)
        frame = pd.read_csv(path)
        frame["_season"] = season
        frames.append(frame)
        print(f"{league} {season}: raw={len(frame)}")
    raw = pd.concat(frames, ignore_index=True)
    features = build_schedule_features(raw, league)
    print(f"{league}: continuous schedule rows={len(features)}")
    return features


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("artifacts/schedule_load_signal_work"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/schedule_load_signal_lab"),
    )
    args = parser.parse_args()

    combined = pd.concat(
        [
            download_history(config, league, args.work_dir / "raw" / league.lower())
            for league, config in LEAGUES.items()
        ],
        ignore_index=True,
    )
    summary, paired = write_reports(combined, args.output_dir)
    print(f"SCHEDULE LOAD SIGNAL LAB COMPLETE rows={len(combined)}")
    print("AGGREGATE SUMMARY")
    print(summary.to_string(index=False))
    print("PAIRED MARKET INCREMENTAL")
    print(paired.to_string(index=False))
    print("Research only: no production promotion, Supabase writes, or .pkl changes.")


if __name__ == "__main__":
    main()
