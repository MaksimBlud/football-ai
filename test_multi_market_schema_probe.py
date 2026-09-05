from multi_market_schema_probe import TABLE_COLUMNS, probe_schema, probe_table


class Response:
    def __init__(self, count=0, data=None):
        self.count = count
        self.data = data or []


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.selected = None
        self.count_mode = None
        self.limit_value = None

    def select(self, columns, count=None):
        self.selected = columns
        self.count_mode = count
        self.client.calls.append(("select", self.table_name, columns, count))
        return self

    def limit(self, value):
        self.limit_value = value
        self.client.calls.append(("limit", self.table_name, value))
        return self

    def execute(self):
        self.client.calls.append(("execute", self.table_name))
        failure = self.client.failures.get(self.table_name)
        if failure:
            raise RuntimeError(failure)
        return Response(self.client.counts.get(self.table_name, 0), [])


class Client:
    def __init__(self, *, failures=None, counts=None):
        self.failures = failures or {}
        self.counts = counts or {}
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return Query(self, name)


def test_probe_uses_exact_required_columns_and_bounded_select_only():
    client = Client()
    result = probe_schema(client)
    assert result["all_ready"] is True
    assert result["blocked_tables"] == []
    assert set(result["ready_tables"]) == set(TABLE_COLUMNS)

    for table, columns in TABLE_COLUMNS.items():
        assert ("table", table) in client.calls
        assert ("select", table, ",".join(columns), "exact") in client.calls
        assert ("limit", table, 1) in client.calls
        assert ("execute", table) in client.calls

    assert all(call[0] in {"table", "select", "limit", "execute"} for call in client.calls)


def test_missing_or_incompatible_table_is_reported_not_raised():
    client = Client(failures={"league_corner_results": "relation does not exist"})
    result = probe_schema(client)
    assert result["all_ready"] is False
    assert result["blocked_tables"] == ["league_corner_results"]
    row = next(row for row in result["tables"] if row["table"] == "league_corner_results")
    assert row["status"] == "MISSING_OR_INCOMPATIBLE"
    assert row["error"]["type"] == "RuntimeError"
    assert "relation does not exist" in row["error"]["message"]


def test_empty_table_is_schema_ready_and_count_is_preserved():
    client = Client(counts={"league_multi_market_snapshots": 0})
    row = probe_table(
        client,
        "league_multi_market_snapshots",
        TABLE_COLUMNS["league_multi_market_snapshots"],
    )
    assert row["status"] == "READY"
    assert row["row_count"] == 0
    assert row["sample_rows_returned"] == 0


def test_nonzero_count_is_reported_without_fetching_more_than_one_row():
    client = Client(counts={"league_multi_market_settlements": 42})
    row = probe_table(
        client,
        "league_multi_market_settlements",
        TABLE_COLUMNS["league_multi_market_settlements"],
    )
    assert row["status"] == "READY"
    assert row["row_count"] == 42
    assert ("limit", "league_multi_market_settlements", 1) in client.calls
