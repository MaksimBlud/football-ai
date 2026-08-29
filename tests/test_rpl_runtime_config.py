from league_runtime_config import RPL_RUNTIME_CONFIG


def test_rpl_identity_and_market_source_contract():
    config = RPL_RUNTIME_CONFIG

    assert config.identity.identifier == "RPL"
    assert config.identity.display_name == "Russian Premier League"
    assert config.identity.timezone == "Europe/Moscow"
    assert (
        config.identity.odds_sport_key
        == "soccer_russia_premier_league"
    )


def test_rpl_starts_market_only_and_uncalibrated():
    structural = RPL_RUNTIME_CONFIG.structural_v2

    assert structural.league_id == "RPL"
    assert structural.calibration_status == "CALIBRATION_REQUIRED"
    assert structural.structural_alpha is None
    assert structural.edge_threshold is None
    assert structural.min_prior_matches == 5


def test_rpl_does_not_guess_historical_or_results_provider_ids():
    config = RPL_RUNTIME_CONFIG

    assert config.historical_source.provider == "SOURCE_REQUIRED"
    assert config.historical_source.competition_code == "UNRESOLVED"
    assert dict(config.historical_source.season_codes) == {}

    assert config.finished_results_source.provider == "SOURCE_REQUIRED"
    assert config.finished_results_source.competition_code == "UNRESOLVED"
    assert config.finished_results_source.season == "2026-2027"


def test_rpl_paths_are_isolated_from_existing_leagues():
    config = RPL_RUNTIME_CONFIG
    paths = config.paths

    expected_fragments = {
        "historical_raw": "rpl_history_raw.csv",
        "historical_normalized": "rpl_history_normalized.csv",
        "temporal_features": "rpl_features_temporal.csv",
        "trainable_features": "rpl_features_with_elo_trainable.csv",
        "upcoming_fixtures": "upcoming_matches_rpl.csv",
        "market_shadow": "rpl_market_shadow.csv",
        "market_history": "rpl_market_shadow_history.csv",
        "structural_shadow": "rpl_structural_v2_shadow.csv",
        "structural_history": "rpl_structural_v2_shadow_history.csv",
        "current_results": "rpl_2026_2027_results.csv",
    }

    for field, filename in expected_fragments.items():
        value = getattr(paths, field)
        assert value.name == filename


def test_rpl_runtime_validates_without_structural_activation():
    RPL_RUNTIME_CONFIG.validate()
