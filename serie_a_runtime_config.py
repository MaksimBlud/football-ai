"""Serie A runtime configuration for the generic research infrastructure."""

from __future__ import annotations

from league_runtime_config import (
    ROOT,
    EloConfig,
    FinishedResultsSourceConfig,
    HistoricalSourceConfig,
    LeagueIdentity,
    LeaguePaths,
    LeagueRuntimeConfig,
    StructuralV2Config,
    TemporalConfig,
)

SERIE_A_ALIASES = {
    "Inter": "Inter Milan",
    "Milan": "AC Milan",
    "Roma": "AS Roma",
    "Verona": "Hellas Verona",
}

SERIE_A_RUNTIME_CONFIG = LeagueRuntimeConfig(
    identity=LeagueIdentity(
        identifier="SERIE_A",
        display_name="Serie A",
        timezone="Europe/Rome",
        odds_sport_key="soccer_italy_serie_a",
    ),
    historical_source=HistoricalSourceConfig(
        provider="FOOTBALL_DATA_CSV",
        competition_code="I1",
        season_codes={
            "1617": "2016-2017", "1718": "2017-2018", "1819": "2018-2019",
            "1920": "2019-2020", "2021": "2020-2021", "2122": "2021-2022",
            "2223": "2022-2023", "2324": "2023-2024", "2425": "2024-2025",
            "2526": "2025-2026",
        },
    ),
    finished_results_source=FinishedResultsSourceConfig(
        provider="FOOTBALL_DATA_CSV",
        competition_code="I1",
        season="2026-2027",
        season_code="2627",
    ),
    paths=LeaguePaths(
        historical_raw=ROOT / "data" / "serie_a_history_2016_2026_raw.csv",
        historical_normalized=ROOT / "data" / "serie_a_history_2016_2026_normalized.csv",
        temporal_features=ROOT / "data" / "serie_a_features_temporal.csv",
        trainable_features=ROOT / "data" / "serie_a_features_with_elo_trainable.csv",
        upcoming_fixtures=ROOT / "data" / "upcoming_matches_serie_a.csv",
        market_shadow=ROOT / "experiments" / "serie_a_market_shadow.csv",
        market_history=ROOT / "experiments" / "serie_a_market_shadow_history.csv",
        structural_shadow=ROOT / "experiments" / "serie_a_structural_v2_shadow.csv",
        structural_history=ROOT / "experiments" / "serie_a_structural_v2_shadow_history.csv",
        current_results=ROOT / "data" / "serie_a_2026_2027_results.csv",
    ),
    aliases=SERIE_A_ALIASES,
    allowed_cold_starts=frozenset(),
    temporal=TemporalConfig(min_prior_matches=5),
    elo=EloConfig(initial_rating=1500.0, k_factor=20.0, home_advantage=65.0),
    structural_v2=StructuralV2Config(
        league_id="SERIE_A",
        structural_alpha=None,
        edge_threshold=None,
        min_prior_matches=5,
        prediction_source="STRUCTURAL_EDGE_V2_SHADOW",
        calibration_status="CALIBRATION_REQUIRED",
    ),
)

SERIE_A_RUNTIME_CONFIG.validate()
