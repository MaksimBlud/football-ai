"""Download and build completed Turkey/Portugal offline research history.

Public Football-Data CSV only. No Odds API. No Supabase. No production model use.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from build_configured_offline_foundation import build_configured_offline_foundation
from football_data_history_source import (
    completed_european_season_codes,
    download_configured_history,
)
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


TARGETS = (
    (TURKEY_SUPER_LIG_RUNTIME_CONFIG, "turkey_super_lig"),
    (PRIMEIRA_LIGA_RUNTIME_CONFIG, "primeira_liga"),
)


def run(*, as_of: date, raw_directory: Path, download: bool) -> list[dict[str, object]]:
    summaries = []
    for config, prefix in TARGETS:
        seasons = completed_european_season_codes(config, as_of=as_of)
        if download:
            download_configured_history(
                config=config,
                raw_directory=raw_directory,
                file_prefix=prefix,
                season_codes=seasons,
            )
        summary = build_configured_offline_foundation(
            config=config,
            raw_directory=raw_directory,
            file_prefix=prefix,
            season_codes=seasons,
        )
        summaries.append(summary)
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download validated completed Football-Data seasons before building.",
    )
    parser.add_argument("--raw-directory", default="data/raw")
    parser.add_argument("--as-of", default=date.today().isoformat())
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of)
    summaries = run(
        as_of=as_of,
        raw_directory=Path(args.raw_directory),
        download=args.download,
    )
    for summary in summaries:
        print(summary)


if __name__ == "__main__":
    main()
