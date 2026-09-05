from primeira_runtime_config import PRIMEIRA_RUNTIME_CONFIG
from turkey_runtime_config import TURKEY_RUNTIME_CONFIG
from audit_turkey_portugal_bootstrap import audit


def test_runtime_configs_are_market_only_and_correct():
    assert TURKEY_RUNTIME_CONFIG.identity.odds_sport_key == "soccer_turkey_super_league"
    assert PRIMEIRA_RUNTIME_CONFIG.identity.odds_sport_key == "soccer_portugal_primeira_liga"
    for cfg in (TURKEY_RUNTIME_CONFIG, PRIMEIRA_RUNTIME_CONFIG):
        assert cfg.structural_v2.calibration_status == "CALIBRATION_REQUIRED"
        assert cfg.structural_v2.structural_alpha is None
        assert cfg.structural_v2.edge_threshold is None


def test_catalog_audit_matches_exact_keys():
    rows=[{"key":"soccer_turkey_super_league","active":True},{"key":"soccer_portugal_primeira_liga","active":True}]
    report=audit(rows)
    assert [r["league"] for r in report] == ["TURKEY_SUPER_LIG","PRIMEIRA_LIGA"]
    assert all(r["catalog_present"] for r in report)
    assert all(r["active"] for r in report)
