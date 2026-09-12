from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import all_leagues_market_only_v1_1_status as status
from all_leagues_market_only_v1_1_gate import V1_1_FREEZE_UTC, load_seed_keys


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "all-leagues-v1-1-sample-health.yml"


def _iso(value):
    return value.isoformat()


def _row(prediction_key, *, event_id=None, created_at=None, kickoff=None):
    created_at = created_at or V1_1_FREEZE_UTC - timedelta(hours=1)
    kickoff = kickoff or V1_1_FREEZE_UTC + timedelta(days=7)
    league = prediction_key.split(":", 1)[0]
    return {
        "prediction_key": prediction_key,
        "league": league,
        "event_id": event_id or prediction_key.split(":", 1)[1],
        "kickoff_utc": _iso(kickoff),
        "prediction_time_utc": _iso(created_at - timedelta(minutes=2)),
        "snapshot_time_utc": _iso(created_at - timedelta(minutes=3)),
        "market_home_prob": 0.4,
        "market_draw_prob": 0.3,
        "market_away_prob": 0.3,
        "structural_applied": False,
        "prediction_mode": "MARKET_ONLY",
        "created_at_utc": _iso(created_at),
    }


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.filters = []
        self.orders = []
        self.bounds = None

    def select(self, columns):
        self.client.selected_columns.add(columns)
        return self

    def in_(self, field, values):
        self.filters.append(("in", field, set(values)))
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def gt(self, field, value):
        self.filters.append(("gt", field, value))
        return self

    def order(self, field, desc=False):
        self.orders.append((field, desc))
        return self

    def range(self, start, end):
        self.bounds = (start, end)
        return self

    def execute(self):
        rows = [dict(row) for row in self.client.rows]
        for operation, field, value in self.filters:
            if operation == "in":
                rows = [row for row in rows if row.get(field) in value]
            elif operation == "eq":
                rows = [row for row in rows if row.get(field) == value]
            elif operation == "gt":
                rows = [row for row in rows if str(row.get(field)) > str(value)]
        for field, desc in reversed(self.orders):
            rows.sort(key=lambda row: str(row.get(field)), reverse=desc)
        if self.bounds is not None:
            start, end = self.bounds
            self.client.ranges.append((start, end))
            rows = rows[start : end + 1]
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.selected_columns = set()
        self.ranges = []

    def table(self, table):
        assert table == status.LEDGER_TABLE
        return FakeQuery(self, table)


def _seed_rows():
    return [_row(key) for key in sorted(load_seed_keys())]


def test_live_monitor_reads_only_frozen_metadata_and_stays_sample_closed():
    client = FakeClient(_seed_rows())

    report = status.run_live(
        client,
        now_utc=V1_1_FREEZE_UTC + timedelta(hours=1),
    )

    assert report["source"]["seed_keys_expected"] == 127
    assert report["source"]["seed_keys_matched"] == 127
    assert report["source"]["post_freeze_candidate_rows"] == 0
    assert report["gate"]["status"] == "SAMPLE_CLOSED"
    assert report["gate"]["outcome_read_allowed"] is False
    assert report["safety"] == {
        "outcome_sources_read": False,
        "provider_requests": 0,
        "supabase_writes": 0,
        "production_artifact_changes": 0,
        "stricter_gates_assumed_clear": False,
    }
    selected = next(iter(client.selected_columns)).split(",")
    assert set(selected) == set(status.METADATA_COLUMNS)
    assert set(selected).isdisjoint(
        {"result", "score", "winner", "settlement", "home_goals", "away_goals"}
    )


def test_monitor_fails_closed_when_any_frozen_seed_key_is_missing():
    with pytest.raises(status.SampleHealthInputError, match=r"1 key\(s\) missing"):
        status.build_sample_health(
            _seed_rows()[1:],
            now_utc=V1_1_FREEZE_UTC + timedelta(hours=1),
        )


def test_future_loader_pages_deterministically_beyond_postgrest_cap():
    future_created = V1_1_FREEZE_UTC + timedelta(hours=1)
    future_kickoff = V1_1_FREEZE_UTC + timedelta(days=30)
    future = [
        _row(
            f"EPL:future-{index:04d}",
            created_at=future_created + timedelta(seconds=index),
            kickoff=future_kickoff + timedelta(seconds=index),
        )
        for index in range(1001)
    ]
    client = FakeClient(_seed_rows() + future)

    rows = status.fetch_metadata_rows(client)

    assert len(rows) == 127 + 1001
    assert (0, 999) in client.ranges
    assert (1000, 1999) in client.ranges


def test_future_duplicate_event_is_reduced_by_frozen_earliest_row_rule():
    created = V1_1_FREEZE_UTC + timedelta(hours=1)
    kickoff = V1_1_FREEZE_UTC + timedelta(days=8)
    early = _row("EPL:future-early", event_id="future", created_at=created, kickoff=kickoff)
    late = _row(
        "EPL:future-late",
        event_id="future",
        created_at=created + timedelta(minutes=1),
        kickoff=kickoff,
    )
    report = status.build_sample_health(
        _seed_rows() + [late, early],
        now_utc=V1_1_FREEZE_UTC + timedelta(hours=2),
    )

    assert report["source"]["post_freeze_candidate_rows"] == 2
    assert report["source"]["post_freeze_selected_events"] == 1
    assert report["gate"]["per_league"]["EPL"]["selected_events"] == 21


def test_pre_freeze_nonseed_is_not_reported_as_future_candidate():
    old = _row("EPL:excluded-old-row")

    report = status.build_sample_health(
        _seed_rows() + [old],
        now_utc=V1_1_FREEZE_UTC + timedelta(hours=2),
    )

    assert report["source"]["post_freeze_candidate_rows"] == 0
    assert report["source"]["post_freeze_selected_events"] == 0
    assert report["gate"]["per_league"]["EPL"]["selected_events"] == 20


def test_workflow_is_read_only_and_runs_live_after_main_merge():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in source
    assert "schedule:" in source
    assert "push:" in source and "branches: [main]" in source
    assert "SUPABASE_URL: ${{ secrets.SUPABASE_URL }}" in source
    assert "SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}" in source
    assert "python all_leagues_market_only_v1_1_status.py" in source
    assert "ODDS_API_KEY" not in source
    assert "permissions:\n  contents: read" in source
