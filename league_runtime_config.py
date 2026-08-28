"""Immutable runtime configuration for league-aware research pipelines.

This module contains configuration only.

It does not:
- collect odds;
- write Supabase;
- train models;
- promote artifacts;
- activate a league automatically.

Operational activation remains separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class LeagueIdentity:
    identifier: str
    display_name: str
    timezone: str
    odds_sport_key: str


@dataclass(frozen=True)
class HistoricalSourceConfig:
    provider: str
    competition_code: str
    season_codes: Mapping[str, str]


@dataclass(frozen=True)
class FinishedResultsSourceConfig:
    provider: str
    competition_code: str
    season: str
    season_code: str


@dataclass(frozen=True)
class LeaguePaths:
    historical_raw: Path
    historical_normalized: Path
    temporal_features: Path
    trainable_features: Path
    upcoming_fixtures: Path
    market_shadow: Path
    market_history: Path
    structural_shadow: Path
    structural_history: Path
    current_results: Path


@dataclass(frozen=True)
class TemporalConfig:
    min_prior_matches: int


@dataclass(frozen=True)
class EloConfig:
    initial_rating: float
    k_factor: float
    home_advantage: float


@dataclass(frozen=True)
class StructuralV2Config:
    league_id: str
    structural_alpha: float | None
    edge_threshold: float | None
    min_prior_matches: int
    prediction_source: str
    calibration_status: str = "CALIBRATED"

    def validate_for(
        self,
        league_id: str,
    ) -> None:
        if self.league_id != league_id:
            raise ValueError(
                "Structural V2 calibration league mismatch: "
                f"{self.league_id!r} != {league_id!r}"
            )

        if self.calibration_status not in {
            "CALIBRATED",
            "CALIBRATION_REQUIRED",
        }:
            raise ValueError(
                "Unknown Structural V2 calibration status"
            )

        if self.calibration_status == "CALIBRATION_REQUIRED":
            if (
                self.structural_alpha is not None
                or self.edge_threshold is not None
            ):
                raise ValueError(
                    "Calibration-required Structural V2 "
                    "must not contain guessed parameters"
                )
        else:
            if (
                self.structural_alpha is None
                or self.edge_threshold is None
            ):
                raise ValueError(
                    "Calibrated Structural V2 requires parameters"
                )

            if not (
                0.0
                <= self.structural_alpha
                <= 1.0
            ):
                raise ValueError(
                    "structural_alpha must be in [0, 1]"
                )

            if self.edge_threshold < 0:
                raise ValueError(
                    "edge_threshold must be non-negative"
                )

        if self.min_prior_matches < 0:
            raise ValueError(
                "min_prior_matches must be non-negative"
            )


@dataclass(frozen=True)
class LeagueRuntimeConfig:
    identity: LeagueIdentity
    historical_source: HistoricalSourceConfig
    finished_results_source: FinishedResultsSourceConfig
    paths: LeaguePaths
    aliases: Mapping[str, str]
    allowed_cold_starts: frozenset[str]
    temporal: TemporalConfig
    elo: EloConfig
    structural_v2: StructuralV2Config

    def validate(self) -> None:
        self.structural_v2.validate_for(
            self.identity.identifier
        )

        if (
            self.temporal.min_prior_matches
            != self.structural_v2.min_prior_matches
        ):
            raise ValueError(
                "Temporal and Structural V2 minimum-history "
                "contracts disagree"
            )


LA_LIGA_ALIASES = {
    "Ath Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atlético Madrid",
    "Atl. Madrid": "Atlético Madrid",
    "Osasuna": "CA Osasuna",
    "Celta": "Celta Vigo",
    "La Coruna": "Deportivo La Coruña",
    "Dep. A Coruna": "Deportivo La Coruña",
    "Elche": "Elche CF",
    "Malaga": "Málaga",
    "Betis": "Real Betis",
    "Sociedad": "Real Sociedad",
    "Santander": "Real Racing Club de Santander",
    "Rayo Vallecano": "Vallecano",
}


LA_LIGA_RUNTIME_CONFIG = LeagueRuntimeConfig(
    identity=LeagueIdentity(
        identifier="LA_LIGA",
        display_name="La Liga",
        timezone="Europe/Madrid",
        odds_sport_key="soccer_spain_la_liga",
    ),
    historical_source=HistoricalSourceConfig(
        provider="FOOTBALL_DATA_CSV",
        competition_code="SP1",
        season_codes={
            "1617": "2016-2017",
            "1718": "2017-2018",
            "1819": "2018-2019",
            "1920": "2019-2020",
            "2021": "2020-2021",
            "2122": "2021-2022",
            "2223": "2022-2023",
            "2324": "2023-2024",
            "2425": "2024-2025",
            "2526": "2025-2026",
        },
    ),
    finished_results_source=FinishedResultsSourceConfig(
        provider="FOOTBALL_DATA_CSV",
        competition_code="SP1",
        season="2026-2027",
        season_code="2627",
    ),
    paths=LeaguePaths(
        historical_raw=(
            ROOT
            / "data"
            / "la_liga_official_history_2016_2026.csv"
        ),
        historical_normalized=(
            ROOT
            / "data"
            / "la_liga_official_history_2016_2026_normalized.csv"
        ),
        temporal_features=(
            ROOT
            / "data"
            / "la_liga_features_temporal.csv"
        ),
        trainable_features=(
            ROOT
            / "data"
            / "la_liga_features_with_elo_trainable.csv"
        ),
        upcoming_fixtures=(
            ROOT
            / "data"
            / "upcoming_matches_la_liga.csv"
        ),
        market_shadow=(
            ROOT
            / "experiments"
            / "la_liga_market_shadow.csv"
        ),
        market_history=(
            ROOT
            / "experiments"
            / "la_liga_market_shadow_history.csv"
        ),
        structural_shadow=(
            ROOT
            / "experiments"
            / "la_liga_structural_v2_shadow.csv"
        ),
        structural_history=(
            ROOT
            / "experiments"
            / "la_liga_structural_v2_shadow_history.csv"
        ),
        current_results=(
            ROOT
            / "data"
            / "la_liga_2026_2027_results.csv"
        ),
    ),
    aliases=LA_LIGA_ALIASES,
    allowed_cold_starts=frozenset(
        {
            "Real Racing Club de Santander",
        }
    ),
    temporal=TemporalConfig(
        min_prior_matches=5,
    ),
    elo=EloConfig(
        initial_rating=1500.0,
        k_factor=20.0,
        home_advantage=65.0,
    ),
    structural_v2=StructuralV2Config(
        league_id="LA_LIGA",
        structural_alpha=0.10,
        edge_threshold=0.75,
        min_prior_matches=5,
        prediction_source="STRUCTURAL_EDGE_V2_SHADOW",
    ),
)

LA_LIGA_RUNTIME_CONFIG.validate()


EPL_ALIASES = {
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Tottenham Hotspur": "Tottenham",
    "Brighton and Hove Albion": "Brighton",
    "Brighton & Hove Albion": "Brighton",
    "Nottingham Forest": "Nott'm Forest",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Hull City": "Hull",
    "AFC Bournemouth": "Bournemouth",
}


EPL_RUNTIME_CONFIG = LeagueRuntimeConfig(
    identity=LeagueIdentity(
        identifier="EPL",
        display_name="Premier League",
        timezone="Europe/London",
        odds_sport_key="soccer_epl",
    ),
    historical_source=HistoricalSourceConfig(
        provider="FOOTBALL_DATA_CSV",
        competition_code="E0",
        season_codes={
            "1617": "2016-2017",
            "1718": "2017-2018",
            "1819": "2018-2019",
            "1920": "2019-2020",
            "2021": "2020-2021",
            "2122": "2021-2022",
            "2223": "2022-2023",
            "2324": "2023-2024",
            "2425": "2024-2025",
            "2526": "2025-2026",
        },
    ),
    finished_results_source=FinishedResultsSourceConfig(
        provider="FOOTBALL_DATA_ORG",
        competition_code="PL",
        season="2026-2027",
        season_code="2026",
    ),
    paths=LeaguePaths(
        historical_raw=(
            ROOT
            / "data"
            / "epl_history_2016_2026_raw.csv"
        ),
        historical_normalized=(
            ROOT
            / "data"
            / "epl_history_2016_2026_normalized.csv"
        ),
        temporal_features=(
            ROOT
            / "data"
            / "epl_features_temporal.csv"
        ),
        trainable_features=(
            ROOT
            / "data"
            / "epl_features_with_elo_trainable.csv"
        ),
        upcoming_fixtures=(
            ROOT
            / "data"
            / "upcoming_matches_epl.csv"
        ),
        market_shadow=(
            ROOT
            / "experiments"
            / "epl_market_shadow.csv"
        ),
        market_history=(
            ROOT
            / "experiments"
            / "epl_market_shadow_history.csv"
        ),
        structural_shadow=(
            ROOT
            / "experiments"
            / "epl_structural_v2_shadow.csv"
        ),
        structural_history=(
            ROOT
            / "experiments"
            / "epl_structural_v2_shadow_history.csv"
        ),
        current_results=(
            ROOT
            / "data"
            / "epl_2026_2027_results.csv"
        ),
    ),
    aliases=EPL_ALIASES,
    allowed_cold_starts=frozenset(),
    temporal=TemporalConfig(
        min_prior_matches=5,
    ),
    elo=EloConfig(
        initial_rating=1500.0,
        k_factor=20.0,
        home_advantage=65.0,
    ),
    structural_v2=StructuralV2Config(
        league_id="EPL",
        structural_alpha=None,
        edge_threshold=None,
        min_prior_matches=5,
        prediction_source="STRUCTURAL_EDGE_V2_SHADOW",
        calibration_status="CALIBRATION_REQUIRED",
    ),
)


EPL_RUNTIME_CONFIG.validate()
