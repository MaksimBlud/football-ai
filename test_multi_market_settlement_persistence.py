from copy import deepcopy
from types import SimpleNamespace

import pytest

from multi_market_settlement import UNSETTLED_MISSING_OUTCOME, WIN
from multi_market_settlement_persistence import (
    SettlementConflictError,
    SettlementIdentityError,
    build_settlement_record,
    match_finished_result,
    persist_settlement_records,
    snapshot_local_match_date,
)


def _card():
    return {
        "schema_version": "MULTI_MARKET_V1",
        "research_only": True,
        "handicap": {"home_handicap": -0.5, "away_handicap": 0.5},
        "total_goals": {"point": 2.5},
        "total_corners": {"point": 9.5},
        "team_corners": {
            "home": {"point": 5.5},
            "away": {"point": 3.5},
        },
    }


def _snapshot(**overrides):
    row = {
        "snapshot_key": "snap-1",
        "league": "LA_LIGA",
        "event_id": "event-1",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        # 23:30 UTC is already the next local calendar day in Madrid.
        "kickoff_utc": "2026-09-05T23:30:00+00:00",
        "snapshot_time_utc": "2026-09-05T18:00:00+00:00",
        "payload": {
            "schema_version": "MULTI_MARKET_V1",
            "research_only": True,
            "card": _card(),
        },
    }
    row.update(overrides)
    return row


def _result(**overrides):
    row = {
        "league": "LA_LIGA",
        "season": "2026-2027",
        "match_date": "2026-09-06",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        "home_goals": 2,
        "away_goals": 1,
        "result": "H",
    }
    row.update(overrides)
    return row


def _corners(**overrides):
    row = {
        "league": "LA_LIGA",
        "event_id": "event-1",
        "match_date": "2026-09-06",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        "home_corners": 6,
        "away_corners": 4,
    }
    row.update(overrides)
    return row


def test_snapshot_identity_uses_league_local_date_not_utc_date():
    snapshot = _snapshot()
    assert snapshot_local_match_date(snapshot).isoformat() == "2026-09-06"
    matched = match_finished_result(
        snapshot,
        [
            _result(match_date="2026-09-05", home_goals=9, away_goals=9),
            _result(),
        ],
    )
    assert matched["match_date"] == "2026-09-06"
    assert matched["home_goals"] == 2


def test_snapshot_result_identity_is_exact_and_fail_closed():
    with pytest.raises(SettlementIdentityError, match="no exact finished result"):
        match_finished_result(_snapshot(), [_result(home_team="Real Sociedad")])

    with pytest.raises(SettlementIdentityError, match="ambiguous finished results"):
        match_finished_result(_snapshot(), [_result(), deepcopy(_result())])


def test_post_kickoff_snapshot_is_rejected_even_if_result_matches():
    with pytest.raises(SettlementIdentityError, match="strictly before"):
        build_settlement_record(
            _snapshot(snapshot_time_utc="2026-09-05T23:30:00+00:00"),
            _result(),
        )


def test_goals_only_revision_is_durable_and_corner_markets_remain_unsettled():
    record = build_settlement_record(_snapshot(), _result())
    assert record["outcome_completeness"] == "GOALS_ONLY"
    assert record["result_match_date"] == "2026-09-06"
    assert record["payload"]["research_only"] is True
    settlement = record["payload"]["settlement"]
    assert settlement["handicap"]["home"]["status"] == WIN
    assert settlement["total_goals"]["over"]["status"] == WIN
    assert settlement["total_corners"]["over"]["status"] == UNSETTLED_MISSING_OUTCOME
    assert settlement["team_corners"]["home"]["over"]["status"] == UNSETTLED_MISSING_OUTCOME


def test_later_exact_corner_outcome_creates_new_append_only_revision():
    goals_only = build_settlement_record(_snapshot(), _result())
    complete = build_settlement_record(_snapshot(), _result(), corner_outcome=_corners())

    assert goals_only["settlement_key"] != complete["settlement_key"]
    assert goals_only["outcome_fingerprint"] != complete["outcome_fingerprint"]
    assert goals_only["outcome_completeness"] == "GOALS_ONLY"
    assert complete["outcome_completeness"] == "GOALS_AND_CORNERS"
    assert complete["payload"]["settlement"]["total_corners"]["over"]["status"] == WIN


def test_corner_outcome_requires_exact_fixture_identity():
    with pytest.raises(SettlementIdentityError, match="identity mismatch"):
        build_settlement_record(
            _snapshot(),
            _result(),
            corner_outcome=_corners(away_team="Atletico Madrid"),
        )

    incomplete_identity = {"home_corners": 6, "away_corners": 4}
    with pytest.raises(SettlementIdentityError, match="missing identity"):
        build_settlement_record(
            _snapshot(),
            _result(),
            corner_outcome=incomplete_identity,
        )


def test_outcome_values_must_be_nonnegative_integers():
    with pytest.raises(ValueError, match="home_goals"):
        build_settlement_record(_snapshot(), _result(home_goals=1.5))
    with pytest.raises(ValueError, match="home_corners"):
        build_settlement_record(
            _snapshot(),
            _result(),
            corner_outcome=_corners(home_corners=-1),
        )


class FakeQuery:
    def __init__(self, table):
        self.table = table
        self.keys = None
        self.insert_row = None

    def select(self, _columns):
        return self

    def in_(self, _column, values):
        self.keys = set(values)
        self.table.query_batches.append(list(values))
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
            rows = [row for row in rows if row.get("settlement_key") in self.keys]
        return SimpleNamespace(data=deepcopy(rows))


class FakeTable:
    def __init__(self):
        self.rows = []
        self.query_batches = []

    def query(self):
        return FakeQuery(self)


class FakeClient:
    def __init__(self):
        self.tables = {}

    def table(self, name):
        table = self.tables.setdefault(name, FakeTable())
        return table.query()


def test_persistence_is_insert_only_and_idempotent():
    client = FakeClient()
    first = build_settlement_record(_snapshot(), _result())
    second = build_settlement_record(_snapshot(), _result(), corner_outcome=_corners())

    assert persist_settlement_records(client, [first]) == {
        "inserted": 1,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert persist_settlement_records(client, [first]) == {
        "inserted": 0,
        "unchanged": 1,
        "conflicts": 0,
    }
    assert persist_settlement_records(client, [second]) == {
        "inserted": 1,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert len(client.tables["league_multi_market_settlements"].rows) == 2


def test_persistence_rejects_same_key_with_mutated_payload():
    client = FakeClient()
    record = build_settlement_record(_snapshot(), _result())
    persist_settlement_records(client, [record])

    mutated = deepcopy(record)
    mutated["payload"]["outcome"]["home_goals"] = 99
    with pytest.raises(SettlementConflictError, match="immutable settlement conflict"):
        persist_settlement_records(client, [mutated])


def test_persistence_finds_existing_revision_in_second_key_chunk():
    client = FakeClient()
    records = [
        {"settlement_key": f"k{i:03d}", "payload": {"revision": i}}
        for i in range(101)
    ]
    table = client.tables.setdefault("league_multi_market_settlements", FakeTable())
    table.rows.append(deepcopy(records[100]))

    summary = persist_settlement_records(client, records)

    assert summary == {"inserted": 100, "unchanged": 1, "conflicts": 0}
    assert [len(batch) for batch in table.query_batches] == [100, 1]
    assert len(table.rows) == 101
    assert sum(row["settlement_key"] == "k100" for row in table.rows) == 1
