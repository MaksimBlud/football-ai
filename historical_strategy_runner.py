"""Download and run the read-only multi-league Historical Strategy Lab.

Research only. No model training, no Supabase writes, no live activation, no .pkl changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

from historical_strategy_lab import write_reports
from league_historical_market import load_historical_market
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG

LEAGUES = {
    "EPL": (EPL_RUNTIME_CONFIG, "epl"),
    "LA_LIGA": (LA_LIGA_RUNTIME_CONFIG, "la_liga"),
}
BASE_URL = "https://www.football-data.co.uk/mmz4281/{season_code}/{competition_code}.csv"


def download_league_history(config, prefix: str, raw_dir: Path, timeout: int = 60) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for season_code, season in config.historical_source.season_codes.items():
        start_year = int(season.split("-")[0])
        path = raw_dir / f"{prefix}_{start_year}_{start_year + 1}.csv"
        url = BASE_URL.format(
            season_code=season_code,
            competition_code=config.historical_source.competition_code,
        )
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        if not response.content:
            raise RuntimeError(f"Empty historical response: {url}")
        path.write_bytes(response.content)
        paths.append(path)
    return paths


def build_inputs(selected_leagues: list[str], work_dir: Path) -> list[Path]:
    normalized_dir = work_dir / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for league_id in selected_leagues:
        if league_id not in LEAGUES:
            raise ValueError(f"Unsupported historical league: {league_id}")
        config, prefix = LEAGUES[league_id]
        raw_dir = work_dir / "raw" / league_id.lower()
        download_league_history(config, prefix, raw_dir)
        frame, triplet = load_historical_market(
            config=config,
            raw_directory=raw_dir,
            file_prefix=prefix,
        )
        output = normalized_dir / f"{league_id.lower()}_historical_market.csv"
        frame.to_csv(output, index=False)
        outputs.append(output)
        print(
            f"{league_id}: rows={len(frame)} source={triplet.source} "
            f"columns={triplet.home}/{triplet.draw}/{triplet.away}"
        )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run historical MARKET_ONLY research without Codespaces")
    parser.add_argument(
        "--leagues",
        nargs="+",
        default=["EPL", "LA_LIGA"],
        choices=sorted(LEAGUES),
    )
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/historical_strategy_work"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/historical_strategy_lab"))
    args = parser.parse_args()

    inputs = build_inputs(args.leagues, args.work_dir)
    combined = pd.concat([pd.read_csv(path) for path in inputs], ignore_index=True)
    reports = write_reports(combined, args.output_dir)

    print("HISTORICAL STRATEGY RUN COMPLETE")
    print(f"leagues={','.join(args.leagues)} rows={len(combined)}")
    for name, path in reports.items():
        print(f"{name}: {path}")
    print("No training, Supabase writes, live activation, or .pkl changes performed.")


if __name__ == "__main__":
    main()
