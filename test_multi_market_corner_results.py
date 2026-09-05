from copy import deepcopy
from types import SimpleNamespace

import pandas as pd
import pytest

from league_runtime_config import LA_LIGA_RUNTIME_CONFIG, EPL_RUNTIME_CONFIG
from multi_market_corner_results import (
    CornerResultConflictError,
    CornerResultIdentityError,
    normalize_corner_source_frame,
    persist_corner_results,
    reconcile_with_finished_results,
    settlement_corner_outcome,
)


def _frame():
    return pd.DataFrame(
        {
            "Date": ["05/09/2026", "06/09/2026"],
            "HomeTeam": ["Ath Madrid", "Real Madrid"],
            "AwayTeam": ["Barcelona", "Valencia"],
            "FTHG": [2, None],
            "FTAG": [1, None],
            "FTR": ["H", ""],
            "HC": [7, None],
            "AC": [3, None],
        }
    )


def test_normalization_uses_configured_contract_aliases_and_finished_rows_only():
    rows = normalize_corner_source_frame(
        LA_LIGA_RUNTIME_CONFIG,
        _frame(),
        source_url="https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
        fetched_at_utc="2026-09-05T12:00:00+00:00",
    )
    assert len(rows) == 1
    row = rows.iloc[0]
    assert row["league"] == "LA_LIGA"
    assert row["season"] == "2026-2027"
    assert row["home_team"] == "Atlético Madrid"
    assert row["away_team"] == "Barcelona"
    assert row["home_corners"] == 7
    assert row["away_corners"] == 3
    assert row["source_competition_code"] == "SP1"
    assert row["source_season_code"] == "2627"


def test_unconfigured_current_csv_source_is_rejected():
    with pytest.raises(ValueError, match="no configured"):
        normalize_corner_source_frame(EPL_RUNTIME_CONFIG, _frame(), source_url="x")


def _finished(**overrides):
    row = {
        "league": "LA_LIGA",
        "season": "2026-2027",
        "match_date": "2026-09-05",
        "home_team": "Atlético Madrid",
        "away_team": "Barcelona",
        "home_goals": 2,
        "away_goals": 1,
        "result": "H",
    }
    row.update(overrides)
    return row


def _normalized():
    return normalize_corner_source_frame(
        LA_LIGA_RUNTIME_CONFIG,
        _frame(),
        source_url="https://www.football-data.co.uk/mmz4281/2627/SP1.csv",
        fetched_at_utc="2026-09-05T12:00:00+00:00",
    )


def test_reconciliation_requires_unique_exact_finished_result_and_equal_goals():
    records = reconcile_with_finished_results(_normalized(), [_finished()])
    assert len(records) == 1
    record = records[0]
    assert record["payload"]["identity_reconciled"] is True
    assert record["payload"]["goals_reconciled"] is True
    assert record["home_corners"] == 7

    with pytest.raises(CornerResultIdentityError, match="no canonical"):
        reconcile_with_finished_results(_normalized(), [_finished(away_team="Sevilla")])

    with pytest.raises(CornerResultIdentityError, match="ambiguous"):
        reconcile_with_finished_results(_normalized(), [_finished(), deepcopy(_finished())])

    with pytest.raises(CornerResultIdentityError, match="goal reconciliation mismatch"):
        reconcile_with_finished_results(_normalized(), [_finished(home_goals=3)])


def test_settlement_projection_contains_exact_fixture_identity_and_corners():
    record = reconcile_with_finished_results(_normalized(), [_finished()])[0]
    projected = settlement_corner_outcome(record)
    assert projected == {
        "league": "LA_LIGA",
        "match_date": "2026-09-05",
        "home_team": "Atlético Madrid",
        "away_team": "Barcelona",
        "home_corners": 7,
        "away_corners": 3,
    }


class FakeQuery:
    def __init__(self, table):
        self.table = table
        self.keys = None
        self.insert_row = None

    def select(self, _columns):
        return self

    def in_(self, _column, values):
        self.keys = set(values)
        return self

    def insert(self, row):
        self.insert_row = deepcopy(row)
        return self

    def execute(self):
        if self.insert_row is not None:
            self.table.rows.append(self.insert_row)
            return SimpleNamespace(data=[deepcopy(self.insert_row)])
        rows = self.table.rows
        if self.keys is not None:
            rows = [row for row in rows if row.get("corner_result_key") in self.keys]
        return SimpleNamespace(data=deepcopy(rows))


class FakeTable:
    def __init__(self):
        self.rows = []

    def query(self):
        return FakeQuery(self)


class FakeClient:
    def __init__(self):
        self.tables = {}

    def table(self, name):
        return self.tables.setdefault(name, FakeTable()).query()


def test_corner_persistence_is_append_only_idempotent_and_conflict_safe():
    record = reconcile_with_finished_results(_normalized(), [_finished()])[0]
    client = FakeClient()
    assert persist_corner_results(client, [record]) == {"inserted": 1, "unchanged": 0, "conflicts": 0}
    assert persist_corner_results(client, [record]) == {"inserted": 0, "unchanged": 1, "conflicts": 0}

    mutated = deepcopy(record)
    mutated["home_corners"] = 99
    with pytest.raises(CornerResultConflictError, match="immutable corner-result conflict"):
        persist_corner_results(client, [mutated])
