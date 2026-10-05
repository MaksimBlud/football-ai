import bookmaker_price_formation_v1 as mod


def _test_report(common_mean=-0.01, common_high=-0.001, share=0.20, residual=0.80):
    book = {"decomposition": {"specific_variance_share": share}}
    return {
        "common_information": {
            "log_loss": {"mean": common_mean, "ci95_high": common_high},
            "by_league_log_loss": {"EPL": -0.01, "LA_LIGA": -0.02, "SERIE_A": 0.01},
        },
        "pooled_decomposition": {
            "specific_variance_share": share,
            "variance_after_margin_fraction": residual,
        },
        "by_bookmaker": {"BET365": book, "PINNACLE": book},
    }


def test_price_formation_gate_passes_complete_frozen_contract():
    gate = mod._formal_gate(_test_report(), True)
    assert gate["supported"] is True


def test_price_formation_gate_rejects_common_ci_crossing_zero():
    gate = mod._formal_gate(_test_report(common_high=0.001), True)
    assert gate["supported"] is False
    assert gate["gates"]["common_move_ci95_upper_below_zero"] is False


def test_price_formation_gate_rejects_margin_only_specific_move():
    gate = mod._formal_gate(_test_report(residual=0.10), True)
    assert gate["supported"] is False
    assert gate["gates"]["specific_variance_not_explained_by_margin"] is False
