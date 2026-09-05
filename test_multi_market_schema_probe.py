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
        # A zero-row schema probe must never expose configured data rows.
        data = [] if self.limit_value == 0 else self.client.rows.get(self.table_name, [])[: self.limit_value]
        return Response(self.client.counts.get(self.table_name, 0), data)


class Client:
    def __init__(self, *, failures=None, counts=None, rows=None):
        self.failures = failures or {}
        self.counts = counts or {}
        self.rows = rows or {}
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return Query(self, name)


def test_probe_uses_exact_required_columns_and_zero_row_select_only():
    client = Client()
    result = probe_schema(client)
    assert result["all_ready"] is True
    assert result["zero_row_probe"] is True
    assert result["blocked_tables"] == []
    assert set(result["ready_tables"]) == set(TABLE_COLUMNS)

    for table, columns in TABLE_COLUMNS.items():
        assert ("table", table) in client.calls
        assert ("select", table, ",".join(columns), "exact") in client.calls
        assert ("limit", table, 0) in client.calls
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
    assert row["zero_row_probe"] is True


def test_nonzero_count_is_reported_without_returning_any_payload_or_outcome_row():
    client = Client(
        counts={"league_multi_market_settlements": 42},
        rows={
            "league_multi_market_settlements": [
                {"settlement_key": "secret-row", "payload": {"outcome": {"home_goals": 9}}}
            ]
        },
    )
    row = probe_table(
        client,
        "league_multi_market_settlements",
        TABLE_COLUMNS["league_multi_market_settlements"],
    )
    assert row["status"] == "READY"
    assert row["row_count"] == 42
    assert row["sample_rows_returned"] == 0
    assert row["zero_row_probe"] is True
    assert ("limit", "league_multi_market_settlements", 0) in client.calls
