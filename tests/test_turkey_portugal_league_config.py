from league_config import (
    PRIMEIRA_LIGA,
    TURKEY_SUPER_LIG,
    configured_leagues,
    is_collection_ready,
    is_operational_collection_ready,
)


def test_turkey_super_lig_uses_dedicated_operational_collection_only():
    assert TURKEY_SUPER_LIG.identifier == "TURKEY_SUPER_LIG"
    assert TURKEY_SUPER_LIG.odds_api_sport_key == "soccer_turkey_super_league"
    assert TURKEY_SUPER_LIG.timezone == "Europe/Istanbul"
    assert not is_collection_ready("TURKEY_SUPER_LIG")
    assert is_operational_collection_ready("TURKEY_SUPER_LIG")


def test_primeira_liga_uses_dedicated_operational_collection_only():
    assert PRIMEIRA_LIGA.identifier == "PRIMEIRA_LIGA"
    assert PRIMEIRA_LIGA.odds_api_sport_key == "soccer_portugal_primeira_liga"
    assert PRIMEIRA_LIGA.timezone == "Europe/Lisbon"
    assert not is_collection_ready("PRIMEIRA_LIGA")
    assert is_operational_collection_ready("PRIMEIRA_LIGA")


def test_configured_leagues_contains_nine_unique_identifiers():
    identifiers = [league.identifier for league in configured_leagues()]
    assert len(identifiers) == 9
    assert len(set(identifiers)) == 9
    assert "TURKEY_SUPER_LIG" in identifiers
    assert "PRIMEIRA_LIGA" in identifiers
