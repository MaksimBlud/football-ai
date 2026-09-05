from types import SimpleNamespace

from multi_market_cycle import run_cycle


class FakeQuery:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def select(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        if self.error is not None:
            raise self.error
        return self.response or SimpleNamespace(data=[], count=0)


class FakeClient:
    def __init__(self, table_errors=None):
        self.table_errors = table_errors or {}
        self.tables = []

    def table(self, name):
        self.tables.append(name)
        return FakeQuery(error=self.table_errors.get(name))


def test_cycle_does_not_call_collect_when_schema_blocked():
    client = FakeClient({"league_multi_market_snapshots": RuntimeError("PGRST205")})
    calls = {"collect": 0, "quota": 0}

    def quota():
        calls["quota"] += 1
        return {"remaining": "999", "last_cost": "0"}

    def collect():
        calls["collect"] += 1
        return {"fetched": 1}

    result = run_cycle(client, quota, collect, collection_enabled=True)
    assert result["action"] == "NOOP_BLOCKED"
    assert result["collection_called"] is False
    assert result["paid_provider_requests"] == 0
    assert result["prospective_oos_evaluation_active"] is False
    assert calls == {"collect": 0, "quota": 1}


def test_cycle_does_not_call_collect_when_quota_below_threshold():
    client = FakeClient()
    calls = {"collect": 0}

    result = run_cycle(
        client,
        lambda: {"remaining": "207", "last_cost": "0"},
        lambda: calls.__setitem__("collect", calls["collect"] + 1) or {"fetched": 1},
        collection_enabled=True,
    )
    assert result["action"] == "NOOP_BLOCKED"
    assert result["readiness"]["quota_ready"] is False
    assert result["collection_called"] is False
    assert result["paid_provider_requests"] == 0
    assert calls["collect"] == 0


def test_ready_infrastructure_still_requires_explicit_activation():
    client = FakeClient()
    calls = {"collect": 0}

    result = run_cycle(
        client,
        lambda: {"remaining": "700", "last_cost": "0"},
        lambda: calls.__setitem__("collect", calls["collect"] + 1) or {"fetched": 1},
    )
    assert result["action"] == "NOOP_ACTIVATION_REQUIRED"
    assert result["collection_activation_enabled"] is False
    assert result["collection_called"] is False
    assert result["paid_provider_requests"] == 0
    assert calls["collect"] == 0


def test_cycle_calls_collect_only_when_all_gates_and_activation_ready():
    client = FakeClient()
    calls = {"collect": 0}

    def collect():
        calls["collect"] += 1
        return {"fetched": 2, "inserted": 2}

    result = run_cycle(
        client,
        lambda: {"remaining": "700", "last_cost": "0"},
        collect,
        collection_enabled=True,
    )
    assert result["action"] == "COLLECTION_ATTEMPTED"
    assert result["collection_activation_enabled"] is True
    assert result["collection_called"] is True
    assert result["paid_provider_requests"] == 2
    assert calls["collect"] == 1
    assert result["prospective_oos_evaluation_active"] is False
