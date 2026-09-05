import multi_market_cycle as cycle


def test_cycle_reports_blocked_schema_without_provider_calls(monkeypatch):
    monkeypatch.setattr(cycle, "schema_ready", lambda: False)

    def fail_collect():
        raise AssertionError("collect must not run when schema is missing")

    monkeypatch.setattr(cycle, "collect", fail_collect)
    result = cycle.run_cycle()

    assert result == {
        "status": "BLOCKED_SCHEMA",
        "reason": "schema_not_applied",
        "provider_paid_requests": 0,
    }


def test_cycle_reports_blocked_low_quota_truthfully(monkeypatch):
    monkeypatch.setattr(cycle, "schema_ready", lambda: True)
    monkeypatch.setattr(
        cycle,
        "collect",
        lambda: {
            "quota_blocked": True,
            "quota_before": {"remaining": 215, "last_cost": 0},
            "provider_paid_requests": 0,
            "reason": "remaining<500",
        },
    )

    result = cycle.run_cycle()

    assert result["status"] == "BLOCKED_LOW_QUOTA"
    assert result["provider_paid_requests"] == 0
    assert result["collector"]["quota_before"]["remaining"] == 215


def test_cycle_distinguishes_collection_from_no_eligible_collection(monkeypatch):
    monkeypatch.setattr(cycle, "schema_ready", lambda: True)
    monkeypatch.setattr(
        cycle,
        "collect",
        lambda: {"quota_blocked": False, "eligible_events": 0, "fetched": 0, "inserted": 0},
    )
    assert cycle.run_cycle()["status"] == "NO_ELIGIBLE_COLLECTION"

    monkeypatch.setattr(
        cycle,
        "collect",
        lambda: {"quota_blocked": False, "eligible_events": 1, "fetched": 1, "inserted": 1},
    )
    result = cycle.run_cycle()
    assert result["status"] == "COLLECTED"
    assert result["provider_paid_requests"] == 1
