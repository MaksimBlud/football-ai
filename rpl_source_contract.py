"""Verified external source facts for Russian Premier League research.

This module records source identifiers that have been verified externally.
It deliberately does not activate live persistence, fetch secrets, train
models, or enable Structural V2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RPLSourceContract:
    odds_sport_key: str
    historical_provider: str
    historical_competition_code: str
    historical_current_csv_url: str
    historical_last_supported_season: str
    finished_results_provider: str
    finished_results_competition_code: str
    finished_results_access_status: str


RPL_SOURCE_CONTRACT = RPLSourceContract(
    odds_sport_key="soccer_russia_premier_league",
    historical_provider="FOOTBALL_DATA_CO_UK",
    historical_competition_code="RUS",
    historical_current_csv_url="https://www.football-data.co.uk/new/RUS.csv",
    historical_last_supported_season="2025-2026",
    finished_results_provider="FOOTBALL_DATA_ORG",
    finished_results_competition_code="RFPL",
    finished_results_access_status="TOKEN_ACCESS_REQUIRES_LIVE_VERIFICATION",
)


def validate_rpl_source_contract() -> None:
    contract = RPL_SOURCE_CONTRACT

    if contract.odds_sport_key != "soccer_russia_premier_league":
        raise ValueError("Unexpected RPL odds sport key")

    if contract.historical_competition_code != "RUS":
        raise ValueError("Unexpected Football-Data.co.uk RPL code")

    if not contract.historical_current_csv_url.endswith("/new/RUS.csv"):
        raise ValueError("Unexpected RPL historical CSV URL")

    if contract.historical_last_supported_season != "2025-2026":
        raise ValueError("Unexpected RPL historical terminal season")

    if contract.finished_results_competition_code != "RFPL":
        raise ValueError("Unexpected football-data.org RPL code")

    if contract.finished_results_access_status != (
        "TOKEN_ACCESS_REQUIRES_LIVE_VERIFICATION"
    ):
        raise ValueError("RPL live result access must remain unverified")


validate_rpl_source_contract()
