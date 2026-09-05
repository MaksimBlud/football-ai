from pathlib import Path

from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_runtime_config_modules_are_absent():
    assert not (ROOT / "turkey_runtime_config.py").exists()
    assert not (ROOT / "primeira_runtime_config.py").exists()


def test_canonical_runtime_configs_keep_canonical_data_paths():
    turkey = TURKEY_SUPER_LIG_RUNTIME_CONFIG
    portugal = PRIMEIRA_LIGA_RUNTIME_CONFIG

    assert turkey.identity.identifier == "TURKEY_SUPER_LIG"
    assert portugal.identity.identifier == "PRIMEIRA_LIGA"

    assert "turkey_super_lig" in turkey.paths.historical_raw.name
    assert "turkey_super_lig" in turkey.paths.upcoming_fixtures.name
    assert "primeira_liga" in portugal.paths.historical_raw.name
    assert "primeira_liga" in portugal.paths.upcoming_fixtures.name
