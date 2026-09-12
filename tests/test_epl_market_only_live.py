from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import export_epl_upcoming_matches as fixture
import generate_epl_market_shadow as market

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


def fixture_snapshots():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-08-01T10:00:00Z",
                "commence_time_utc":
                    "2030-08-03T15:00:00Z",
                "home_team":
                    "Manchester City",
                "away_team":
                    "Brighton and Hove Albion",
            },
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-08-01T12:00:00Z",
                "commence_time_utc":
                    "2030-08-03T15:00:00Z",
                "home_team":
                    "Manchester City",
                "away_team":
                    "Brighton and Hove Albion",
            },
        ]
    )


def market_snapshots():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-08-01T10:00:00Z",
                "commence_time_utc":
                    "2030-08-03T15:00:00Z",
                "home_team":
                    "Manchester City",
                "away_team":
                    "Brighton and Hove Albion",
                "home_odds": 1.50,
                "draw_odds": 4.50,
                "away_odds": 7.00,
            },
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-08-02T10:00:00Z",
                "commence_time_utc":
                    "2030-08-03T15:00:00Z",
                "home_team":
                    "Manchester City",
                "away_team":
                    "Brighton and Hove Albion",
                "home_odds": 1.60,
                "draw_odds": 4.20,
                "away_odds": 6.50,
            },
            {
                "league": "EPL",
                "event_id": "e1",
                "snapshot_time_utc":
                    "2030-08-03T16:00:00Z",
                "commence_time_utc":
                    "2030-08-03T15:00:00Z",
                "home_team":
                    "Manchester City",
                "away_team":
                    "Brighton and Hove Albion",
                "home_odds": 1.10,
                "draw_odds": 9.00,
                "away_odds": 15.0,
            },
        ]
    )


class SnapshotQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []
        self.order_call = None
        self.limit_value = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self.order_call = (column, bool(desc))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        return SimpleNamespace(data=list(self.rows))


class SnapshotClient:
    def __init__(self, rows):
        self.query = SnapshotQuery(rows)
        self.table_name = None

    def table(self, name):
        self.table_name = name
        return self.query


def test_epl_market_only_config():
    s = EPL_RUNTIME_CONFIG.structural_v2

    assert (
        s.calibration_status
        == "CALIBRATION_REQUIRED"
    )

    assert s.structural_alpha is None
    assert s.edge_threshold is None


def test_fetch_epl_snapshots_requests_newest_rows_first(monkeypatch):
    client = SnapshotClient(
        [
            {
                "league": "EPL",
                "event_id": "newest",
                "snapshot_time_utc": "2030-08-02T10:00:00Z",
            }
        ]
    )
    monkeypatch.setattr(market, "supabase", client)

    fetched = market.fetch_epl_snapshots()

    assert client.table_name == "odds_snapshots"
    assert client.query.filters == [("league", "EPL")]
    assert client.query.order_call == ("snapshot_time_utc", True)
    assert client.query.limit_value == 10000
    assert fetched["event_id"].tolist() == ["newest"]


def test_fixture_export_deduplicates_and_aliases():
    result = (
        fixture.prepare_upcoming_fixtures(
            fixture_snapshots(),
            now=datetime(
                2030,
                8,
                1,
                tzinfo=timezone.utc,
            ),
        )
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert row["event_id"] == "e1"
    assert row["league"] == "EPL"
    assert (
        row["home_team_model"]
        == "Man City"
    )
    assert (
        row["away_team_model"]
        == "Brighton"
    )


def test_fixture_export_rejects_foreign_league():
    bad = fixture_snapshots()

    bad.loc[
        0,
        "league"
    ] = "LA_LIGA"

    with pytest.raises(
        ValueError
    ):
        fixture.prepare_upcoming_fixtures(
            bad,
            now=datetime(
                2030,
                8,
                1,
                tzinfo=timezone.utc,
            ),
        )


def test_market_uses_latest_prekickoff_snapshot():
    upcoming = (
        fixture.prepare_upcoming_fixtures(
            fixture_snapshots(),
            now=datetime(
                2030,
                8,
                1,
                tzinfo=timezone.utc,
            ),
        )
    )

    result = market.build_market_shadow(
        upcoming,
        market_snapshots(),
        previous_history=pd.DataFrame(
            columns=market.OUTPUT_COLUMNS
        ),
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert (
        row["market_shadow_status"]
        == "OK"
    )

    assert bool(
        row["market_only"]
    )

    assert (
        pd.Timestamp(
            row["snapshot_time_utc"]
        )
        == pd.Timestamp(
            "2030-08-02T10:00:00Z"
        )
    )

    assert (
        pd.Timestamp(
            row["snapshot_time_utc"]
        )
        <
        pd.Timestamp(
            row["commence_time_utc"]
        )
    )

    probabilities = np.asarray(
        [
            row[
                "market_home_probability"
            ],
            row[
                "market_draw_probability"
            ],
            row[
                "market_away_probability"
            ],
        ],
        dtype=float,
    )

    assert np.isfinite(
        probabilities
    ).all()

    assert probabilities.sum() == pytest.approx(
        1.0
    )

    assert row["market_argmax"] == "H"


def test_market_snapshot_rejects_foreign_league():
    bad = market_snapshots()

    bad.loc[
        0,
        "league"
    ] = "LA_LIGA"

    with pytest.raises(
        ValueError
    ):
        market.prepare_snapshots(
            bad
        )


def test_epl_wrapper_has_no_structural_runtime_dependency():
    source = open(
        "generate_epl_market_shadow.py",
        encoding="utf-8",
    ).read()

    assert (
        "league_structural_v2_shadow"
        not in source
    )

    assert (
        "football_model_xgboost_elo"
        not in source
    )
