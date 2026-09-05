from types import SimpleNamespace

import pandas as pd

from multi_market_backfill import load_paginated_rows, run_backfill


READY_SCHEMA = {"all_ready": True, "blocked_tables": [], "tables": []}
BLOCKED_SCHEMA = {
    "all_ready": False,
    "blocked_tables": ["league_multi_market_snapshots"],
    "tables": [],
}


def card():
    return {
        "schema_version": "MULTI_MARKET_V1",
        "research_only": True,
        "handicap": None,
        "total_goals": {
            "point": 2.5,
            "over_probability": 0.52,
            "under_probability": 0.48,
        },
        "total_corners": {
            "point": 9.5,
            "over_probability": 0.51,
            "under_probability": 0.49,
        },
        "team_corners": {"home": None, "away": None},
    }


def snapshot(league="EPL", home="Arsenal", away="Chelsea"):
    return {
        "snapshot_key": f"snap-{league}",
        "league": league,
        "event_id": f"event-{league}",
        "home_team": home,
        "away_team": away,
        "kickoff_utc": "2026-09-05T14:00:00+00:00",
        "snapshot_time_utc": "2026-09-05T10:00:00+00:00",
        "payload": {
            "schema_version": "MULTI_MARKET_V1",
            "research_only": True,
            "card": card(),
        },
    }


def result(league="EPL", home="Arsenal", away="Chelsea", hg=2, ag=1):
    return {
        "league": league,
        "season": "2026-2027",
        "match_date": "2026-09-05",
        "home_team": home,
        "away_team": away,
        "home_goals": hg,
        "away_goals": ag,
    }


def test_schema_blocked_short_circuits_every_data_and_write_path():
    calls = {name: 0 for name in ("snapshots", "corners", "results", "fetch", "cp", "sp")}

    def called(name, value):
        def fn(*args, **kwargs):
            calls[name] += 1
            return value
        return fn

    out = run_backfill(
        object(),
        write=True,
        probe_fn=lambda client: BLOCKED_SCHEMA,
        snapshot_loader=called("snapshots", []),
        corner_loader=called("corners", []),
        results_loader=called("results", pd.DataFrame()),
        corner_fetcher=called("fetch", None),
        corner_persist=called("cp", {}),
        settlement_persist=called("sp", {}),
    )
    assert out["status"] == "NOOP_SCHEMA_BLOCKED"
    assert out["writes_performed"] == 0
    assert out["football_data_fetches"] == 0
    assert out["the_odds_api_requests"] == 0
    assert out["oos_evaluation_invoked"] is False
    assert calls == {name: 0 for name in calls}


def test_source_unconfigured_league_never_constructs_or_fetches_corner_url():
    fetch_calls = 0

    def forbidden_fetch(*args, **kwargs):
        nonlocal fetch_calls
        fetch_calls += 1
        raise AssertionError("unconfigured league must not fetch Football-Data")

    out = run_backfill(
        object(),
        probe_fn=lambda client: READY_SCHEMA,
        snapshot_loader=lambda client: [snapshot()],
        corner_loader=lambda client: [],
        results_loader=lambda client, config: pd.DataFrame([result()]),
        corner_fetcher=forbidden_fetch,
    )
    assert fetch_calls == 0
    assert out["corner_status"]["EPL"]["status"] == "SOURCE_NOT_CONFIGURED"
    assert out["settlement_rows_built"] == 1
    assert out["status"] == "DRY_RUN_READY"
    assert out["writes_performed"] == 0


def test_supported_corner_source_reconciles_and_builds_complete_settlement():
    snap = snapshot("LA_LIGA", "Real Madrid", "Barcelona")
    res = result("LA_LIGA", "Real Madrid", "Barcelona", 3, 2)
    source = pd.DataFrame(
        [
            {
                "Date": "05/09/2026",
                "HomeTeam": "Real Madrid",
                "AwayTeam": "Barcelona",
                "FTHG": 3,
                "FTAG": 2,
                "FTR": "H",
                "HC": 7,
                "AC": 4,
            }
        ]
    )
    corner_batches = []
    settlement_batches = []

    def persist_corners(client, records):
        records = list(records)
        corner_batches.extend(records)
        return {"inserted": len(records), "unchanged": 0, "conflicts": 0}

    def persist_settlements(client, records):
        records = list(records)
        settlement_batches.extend(records)
        return {"inserted": len(records), "unchanged": 0, "conflicts": 0}

    out = run_backfill(
        object(),
        write=True,
        probe_fn=lambda client: READY_SCHEMA,
        snapshot_loader=lambda client: [snap],
        corner_loader=lambda client: [],
        results_loader=lambda client, config: pd.DataFrame([res]),
        corner_fetcher=lambda config, session: (source, "https://configured.example/SP1.csv"),
        corner_persist=persist_corners,
        settlement_persist=persist_settlements,
    )
    assert out["football_data_fetches"] == 1
    assert out["generated_corner_rows"] == 1
    assert out["settlement_rows_built"] == 1
    assert out["writes_performed"] == 2
    assert len(corner_batches) == 1
    assert len(settlement_batches) == 1
    payload = settlement_batches[0]["payload"]
    assert payload["outcome_completeness"] == "GOALS_AND_CORNERS"
    assert payload["outcome"]["home_corners"] == 7
    assert payload["outcome"]["away_corners"] == 4
    assert out["oos_evaluation_invoked"] is False


class PagingQuery:
    def __init__(self, pages):
        self.pages = pages
        self.current = None
        self.ranges = []

    def select(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, start, end):
        self.current = (start, end)
        self.ranges.append(self.current)
        return self

    def execute(self):
        return SimpleNamespace(data=self.pages.get(self.current, []))


class PagingClient:
    def __init__(self, query):
        self.query = query

    def table(self, name):
        return self.query


def test_paginated_loader_reads_until_short_page_without_default_limit_loss():
    query = PagingQuery(
        {
            (0, 1): [{"id": 1}, {"id": 2}],
            (2, 3): [{"id": 3}, {"id": 4}],
            (4, 5): [{"id": 5}],
        }
    )
    rows = load_paginated_rows(PagingClient(query), "x", order_by="id", page_size=2)
    assert [row["id"] for row in rows] == [1, 2, 3, 4, 5]
    assert query.ranges == [(0, 1), (2, 3), (4, 5)]
