import pytest

import scheduled_turkey_portugal_odds as scheduler


def _stub_common(monkeypatch, *, remaining, last_cost=0):
    collect_calls=[]
    monkeypatch.setattr(scheduler,"config_for",lambda _league: object())
    monkeypatch.setattr(
        scheduler,
        "zero_cost_quota",
        lambda: {"remaining":remaining,"last_cost":last_cost},
    )
    monkeypatch.setattr(scheduler,"recent_rows",lambda _league: [])

    def collect(league, *, persist):
        collect_calls.append((league,persist))
        return {
            "rows":9,
            "persisted":9,
            "quota":{"remaining":remaining-1,"last_cost":1},
        }

    monkeypatch.setattr(scheduler,"collect_snapshot",collect)
    return collect_calls


def test_shared_reserve_allows_collection_with_current_quota(monkeypatch):
    calls=_stub_common(monkeypatch,remaining=187)

    out=scheduler.run("PRIMEIRA_LIGA")

    assert out["status"]=="COLLECTED"
    assert calls==[("PRIMEIRA_LIGA",True)]


def test_two_credit_cycle_envelope_protects_hard_reserve(monkeypatch):
    calls=_stub_common(monkeypatch,remaining=101)

    out=scheduler.run("TURKEY_SUPER_LIG")

    assert out["status"]=="BLOCKED_LOW_QUOTA"
    assert calls==[]


def test_zero_cost_preflight_must_report_zero_last_cost(monkeypatch):
    calls=_stub_common(monkeypatch,remaining=187,last_cost=1)

    with pytest.raises(RuntimeError,match="Expected zero-cost sports quota preflight"):
        scheduler.run("TURKEY_SUPER_LIG")

    assert calls==[]
