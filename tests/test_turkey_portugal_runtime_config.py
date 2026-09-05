from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


def test_turkey_runtime_config_is_market_only():
    c=TURKEY_SUPER_LIG_RUNTIME_CONFIG
    assert c.identity.identifier=="TURKEY_SUPER_LIG"
    assert c.identity.odds_sport_key=="soccer_turkey_super_league"
    assert c.historical_source.competition_code=="T1"
    assert c.finished_results_source.provider=="THE_ODDS_API"
    assert c.structural_v2.calibration_status=="CALIBRATION_REQUIRED"
    assert c.structural_v2.structural_alpha is None
    assert c.structural_v2.edge_threshold is None


def test_portugal_runtime_config_is_market_only():
    c=PRIMEIRA_LIGA_RUNTIME_CONFIG
    assert c.identity.identifier=="PRIMEIRA_LIGA"
    assert c.identity.odds_sport_key=="soccer_portugal_primeira_liga"
    assert c.historical_source.competition_code=="P1"
    assert c.finished_results_source.provider=="THE_ODDS_API"
    assert c.structural_v2.calibration_status=="CALIBRATION_REQUIRED"
    assert c.structural_v2.structural_alpha is None
    assert c.structural_v2.edge_threshold is None
