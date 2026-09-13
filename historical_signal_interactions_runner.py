"""Run the fixed trajectory/shot-quality interaction extension of Historical Signal Lab."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from historical_football_signal_runner import LEAGUES, download
from historical_signal_interactions import write_interaction_reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("artifacts/historical_signal_interactions_work"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical_signal_interactions"),
    )
    args = parser.parse_args()
    combined = pd.concat(
        [
            download(config, league, args.work_dir / "raw" / league.lower())
            for league, config in LEAGUES.items()
        ],
        ignore_index=True,
    )
    summary = write_interaction_reports(combined, args.output_dir)
    print("FIXED TRAJECTORY-SHOT INTERACTIONS")
    print(summary.to_string(index=False))
    print("Research only; existing point-in-time Historical Signal Lab inputs reused.")


if __name__ == "__main__":
    main()
