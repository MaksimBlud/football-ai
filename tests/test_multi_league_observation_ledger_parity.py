from types import SimpleNamespace

import pandas as pd
import pytest

import audit_multi_league_observation_ledger_parity as audit


def observations(league="EPL"):
    return pd.DataFrame([
        {
            "league": league,
            "event_id": "e1",
            "snapshot_time_utc": "2030-01-01T10:00:00Z",
            "commence_time_utc": "2030-01-01T15:00:00Z",
        },
        {
            "league": league,
            "event_id": "e1",
            "snapshot_time_utc": "2030-01-01T11:00:00Z",
            "commence_time_utc": "2030-01-01T15:00:00Z",
        },
    ])


def ledger(league="EPL"):
    return pd.DataFrame([
        {
            "league": league,
            "event_id": "e1",
            "snapshot_time_utc": "2030-01-01T10:00:00Z",
        }
    ])


def test_snapshot_gap_on_covered_event_is_warning_only():
    report = audit.audit_frames(
        "EPL",
        observations(),
        ledger(),
        audited_at_utc="2030-01-01T12:00:00Z",
    )
    assert report.observation_rows == 2
    assert report.ledger_rows == 1
    assert report.orphan_snapshot_rows == 1
    assert report.orphan_snapshot_events == 1
    assert report.orphan_snapshots_on_covered_events == 1
    assert report.post_ledger_events_without_any_ledger == 0
    assert report.critical_failures == 0
    assert report.future_orphan_snapshot_rows == 1


def test_post_ledger_event_without_any_ledger_is_critical():
    obs = observations()
    obs.loc[len(obs)] = {
        "league": "EPL",
        "event_id": "e2",
        "snapshot_time_utc": "2030-01-01T12:00:00Z",
        "commence_time_utc": "2030-01-01T16:00:00Z",
    }
    report = audit.audit_frames(
        "EPL", obs, ledger(), audited_at_utc="2030-01-01T13:00:00Z"
    )
    assert report.post_ledger_events_without_any_ledger == 1
    assert report.post_ledger_orphan_snapshots_without_any_ledger == 1
    assert report.critical_failures == 1


def test_no_ledger_era_is_diagnostic_not_critical():
    report = audit.audit_frames(
        "RPL",
        observations("RPL"),
        pd.DataFrame(),
        audited_at_utc="2030-01-01T12:00:00Z",
    )
    assert report.orphan_snapshot_rows == 2
    assert report.orphan_snapshot_events == 1
    assert report.critical_failures == 0


def test_rejects_foreign_league_rows():
    with pytest.raises(ValueError, match="foreign league"):
        audit.audit_frames(
            "EPL",
            observations("RPL"),
            ledger(),
            audited_at_utc="2030-01-01T12:00:00Z",
        )


def test_la_liga_uses_legacy_observation_table():
    assert audit._observation_table("LA_LIGA") == "la_liga_structural_v2_observations"
    assert audit._observation_table("EPL") == "league_structural_v2_observations"


def test_all_current_live_leagues_are_in_scope():
    assert audit.LEAGUES == (
        "EPL",
        "LA_LIGA",
        "BUNDESLIGA",
        "SERIE_A",
        "LIGUE_1",
        "EREDIVISIE",
        "RPL",
    )


class PagedQuery:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.filters = {}
        self.orders = []
        self.bounds = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def order(self, field, desc=False):
        self.orders.append((field, desc))
        return self

    def range(self, start, end):
        self.bounds = (start, end)
        return self

    def execute(self):
        rows = [
            dict(row)
            for row in self.client.tables[self.table]
            if all(row.get(key) == value for key, value in self.filters.items())
        ]
        for field, desc in reversed(self.orders):
            rows.sort(key=lambda row: str(row.get(field)), reverse=desc)
        start, end = self.bounds or (0, len(rows) - 1)
        self.client.ranges.append((self.table, start, end))
        return SimpleNamespace(data=rows[start : end + 1])


class PagedClient:
    def __init__(self, tables):
        self.tables = tables
        self.ranges = []

    def table(self, name):
        return PagedQuery(self, name)


def test_live_frame_loader_reads_beyond_postgrest_page_cap():
    observation_rows = []
    ledger_rows = []
    for index in range(1005):
        event_id = f"event-{index:04d}"
        timestamp = f"2030-01-{1 + index // 500:02d}T10:{index % 60:02d}:00+00:00"
        observation_rows.append({
            "observation_key": f"EPL:o-{index:04d}",
            "league": "EPL",
            "event_id": event_id,
            "snapshot_time_utc": timestamp,
            "commence_time_utc": "2030-02-01T10:00:00+00:00",
        })
        ledger_rows.append({
            "prediction_key": f"EPL:p-{index:04d}",
            "league": "EPL",
            "event_id": event_id,
            "snapshot_time_utc": timestamp,
        })

    client = PagedClient({
        audit.GENERIC_OBSERVATION_TABLE: observation_rows,
        audit.LEDGER_TABLE: ledger_rows,
    })
    loaded_observations, loaded_ledger = audit.load_frames(client, "EPL")

    assert len(loaded_observations) == 1005
    assert len(loaded_ledger) == 1005
    assert (audit.GENERIC_OBSERVATION_TABLE, 0, 999) in client.ranges
    assert (audit.GENERIC_OBSERVATION_TABLE, 1000, 1999) in client.ranges
    assert (audit.LEDGER_TABLE, 0, 999) in client.ranges
    assert (audit.LEDGER_TABLE, 1000, 1999) in client.ranges
