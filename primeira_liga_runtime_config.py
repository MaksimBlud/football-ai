"""Primeira Liga runtime configuration for generic research infrastructure."""
from league_runtime_config import ROOT,EloConfig,FinishedResultsSourceConfig,HistoricalSourceConfig,LeagueIdentity,LeaguePaths,LeagueRuntimeConfig,StructuralV2Config,TemporalConfig

PRIMEIRA_LIGA_RUNTIME_CONFIG=LeagueRuntimeConfig(
    identity=LeagueIdentity(identifier="PRIMEIRA_LIGA",display_name="Primeira Liga",timezone="Europe/Lisbon",odds_sport_key="soccer_portugal_primeira_liga"),
    historical_source=HistoricalSourceConfig(provider="FOOTBALL_DATA_CSV",competition_code="P1",season_codes={"1617":"2016-2017","1718":"2017-2018","1819":"2018-2019","1920":"2019-2020","2021":"2020-2021","2122":"2021-2022","2223":"2022-2023","2324":"2023-2024","2425":"2024-2025","2526":"2025-2026","2627":"2026-2027"}),
    finished_results_source=FinishedResultsSourceConfig(provider="FOOTBALL_DATA_CSV",competition_code="P1",season="2026-2027",season_code="2627"),
    paths=LeaguePaths(
        historical_raw=ROOT/"data"/"primeira_liga_history_2016_2027_raw.csv",
        historical_normalized=ROOT/"data"/"primeira_liga_history_2016_2027_normalized.csv",
        temporal_features=ROOT/"data"/"primeira_liga_features_temporal.csv",
        trainable_features=ROOT/"data"/"primeira_liga_features_with_elo_trainable.csv",
        upcoming_fixtures=ROOT/"data"/"upcoming_matches_primeira_liga.csv",
        market_shadow=ROOT/"experiments"/"primeira_liga_market_shadow.csv",
        market_history=ROOT/"experiments"/"primeira_liga_market_shadow_history.csv",
        structural_shadow=ROOT/"experiments"/"primeira_liga_structural_v2_shadow.csv",
        structural_history=ROOT/"experiments"/"primeira_liga_structural_v2_shadow_history.csv",
        current_results=ROOT/"data"/"primeira_liga_2026_2027_results.csv"),
    aliases={},allowed_cold_starts=frozenset(),temporal=TemporalConfig(min_prior_matches=5),
    elo=EloConfig(initial_rating=1500.0,k_factor=20.0,home_advantage=65.0),
    structural_v2=StructuralV2Config(league_id="PRIMEIRA_LIGA",structural_alpha=None,edge_threshold=None,min_prior_matches=5,prediction_source="STRUCTURAL_EDGE_V2_SHADOW",calibration_status="CALIBRATION_REQUIRED"),
)
PRIMEIRA_LIGA_RUNTIME_CONFIG.validate()
