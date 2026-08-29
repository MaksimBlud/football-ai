from league_runtime_config import RPL_RUNTIME_CONFIG


def test_rpl_structural_v2_remains_disabled():
    config = RPL_RUNTIME_CONFIG.structural_v2
    assert config.calibration_status == "CALIBRATION_REQUIRED"
    assert config.structural_alpha is None
    assert config.edge_threshold is None
