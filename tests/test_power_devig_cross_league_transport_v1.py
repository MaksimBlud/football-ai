import power_devig_cross_league_transport_v1 as mod


def _report():
    return {
        "decision": "NO_STABLE_DEVIG_WINNER",
        "validation": {"closing": {"pooled": {
            "power": {"log_loss": 0.99},
            "multiplicative": {"log_loss": 1.00},
        }}},
        "test": {"closing": {}},
        "confirmation": {
            "closing_deltas_vs_multiplicative": {"log_loss": -0.01, "brier": -0.01, "rps": -0.01},
            "opening_log_loss_delta_vs_multiplicative": -0.01,
            "paired_fixture_cluster_bootstrap": {"ci95_high": -0.001},
            "stability": {
                "by_league": {"BUNDESLIGA": -0.01, "LIGUE_1": -0.02},
                "by_bookmaker": {"BET365": -0.01, "PINNACLE": -0.01},
            },
        },
    }


def test_power_transport_passes_only_all_frozen_gates(monkeypatch):
    monkeypatch.setattr(mod.parent, "evaluate", _report)
    result = mod.evaluate()
    assert result["decision"] == "POWER_CROSS_LEAGUE_TRANSPORT_SUPPORTED"
    assert result["transfer_gate"]["supported"] is True


def test_power_transport_fails_on_one_league(monkeypatch):
    report = _report()
    report["confirmation"]["stability"]["by_league"]["LIGUE_1"] = 0.001
    monkeypatch.setattr(mod.parent, "evaluate", lambda: report)
    result = mod.evaluate()
    assert result["decision"] == "POWER_CROSS_LEAGUE_TRANSPORT_NOT_SUPPORTED"

