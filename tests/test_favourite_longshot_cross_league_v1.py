import favourite_longshot_cross_league_v1 as mod


def _horizon():
    return {
        "residual_slope": {"slope": 0.1, "ci95_low": 0.01},
        "regions": {
            "longshot_p_lt_0_30": {"gap": -0.01},
            "favourite_p_ge_0_60": {"gap": 0.02},
        },
        "by_league": {
            "BUNDESLIGA": {"residual_slope": 0.1},
            "LIGUE_1": {"residual_slope": 0.08},
        },
        "by_bookmaker": {
            "BET365": {"residual_slope": 0.1},
            "PINNACLE": {"residual_slope": 0.05},
        },
    }


def _report():
    return {
        "decision": "NO_STABLE_FAVOURITE_LONGSHOT_BIAS",
        "validation": {"closing": _horizon()},
        "test": {"closing": _horizon()},
    }


def test_favourite_longshot_transport_passes_all_frozen_gates(monkeypatch):
    monkeypatch.setattr(mod.parent, "evaluate", _report)
    result = mod.evaluate()
    assert result["decision"] == "SUPPORTED_CROSS_LEAGUE_FAVOURITE_LONGSHOT_PATTERN"
    assert result["transfer_gate"]["supported"] is True


def test_favourite_longshot_transport_fails_crossing_ci(monkeypatch):
    report = _report()
    report["test"]["closing"]["residual_slope"]["ci95_low"] = -0.01
    monkeypatch.setattr(mod.parent, "evaluate", lambda: report)
    result = mod.evaluate()
    assert result["decision"] == "NO_CROSS_LEAGUE_FAVOURITE_LONGSHOT_CONFIRMATION"
