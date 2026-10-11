from datetime import datetime, timezone

import pytest

from product_snapshot_store import (
    build_product_view_from_snapshot_rows,
    prediction_identity,
    select_latest_odds_by_event,
    select_latest_prediction_snapshots,
)


def prediction_snapshot(**overrides):
    row = {
        "snapshot_schema_version": "product-prediction.v1",
        "run_id": "run-a",
        "generated_at_utc": "2026-09-12T06:00:00+00:00",
        "league": "EPL",
        "event_id": "event-1",
        "commence_time_utc": "2026-09-13T14:00:00+00:00",
        "match_date": "2026-09-13",
        "match_time": "15:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_team_model": "Arsenal",
        "away_team_model": "Coventry City",
        "prediction": "HOME",
        "prediction_strength": "MEDIUM",
        "model_agreement": True,
        "home_probability": 0.60,
        "draw_probability": 0.24,
        "away_probability": 0.16,
        "expected_home_goals": 1.8,
        "expected_away_goals": 0.9,
        "expected_total_goals": 2.7,
        "over_2_5_probability": 0.58,
        "under_2_5_probability": 0.42,
        "btts_yes_probability": 0.51,
        "btts_no_probability": 0.49,
        "top_score": "2:1",
        "top_score_probability": 0.12,
    }
    row.update(overrides)
    return row


def odds_snapshot(**overrides):
    row = {
        "event_id": "event-1",
        "snapshot_time_utc": "2026-09-12T05:45:00+00:00",
        "commence_time_utc": "2026-09-13T14:00:00+00:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_odds": 1.90,
        "draw_odds": 4.00,
        "away_odds": 7.00,
    }
    row.update(overrides)
    return row


def test_prediction_identity_prefers_provider_event_id():
    assert prediction_identity(prediction_snapshot()) == ("event_id", "event-1")


def test_prediction_identity_has_safe_fixture_fallback():
    identity = prediction_identity(prediction_snapshot(event_id=None))
    assert identity[:4] == ("fixture", "EPL", "Arsenal", "Coventry City")
    assert identity[4] == "2026-09-13T14:00:00+00:00"


def test_latest_prediction_snapshot_wins_without_mutating_history():
    older = prediction_snapshot(home_probability=0.55)
    newer = prediction_snapshot(
        run_id="run-b",
        generated_at_utc="2026-09-12T07:00:00+00:00",
        home_probability=0.61,
    )
    selected = select_latest_prediction_snapshots([older, newer])
    assert len(selected) == 1
    assert selected[0]["run_id"] == "run-b"
    assert selected[0]["home_probability"] == pytest.approx(0.61)


def test_unknown_snapshot_schema_is_not_exposed():
    selected = select_latest_prediction_snapshots(
        [prediction_snapshot(snapshot_schema_version="future.v9")]
    )
    assert selected == []


def test_latest_market_price_is_selected_independently():
    older = odds_snapshot(home_odds=1.80)
    newer = odds_snapshot(
        snapshot_time_utc="2026-09-12T05:55:00+00:00",
        home_odds=1.90,
    )
    selected = select_latest_odds_by_event([older, newer])
    assert selected["event-1"]["home_odds"] == pytest.approx(1.90)


def test_product_view_joins_model_and_market_only_by_event_id():
    payload = build_product_view_from_snapshot_rows(
        [prediction_snapshot()],
        [odds_snapshot()],
    )

    item = payload["matches"][0]
    home = item["markets"]["1x2"]["selections"][0]

    assert home["probability"] == pytest.approx(0.60)
    assert home["bookmaker_odds"] == pytest.approx(1.90)
    assert home["raw_expected_value"] == pytest.approx(0.14)
    assert item["main_forecast"]["status"] == "model_forecast"
    assert item["value_signal"]["status"] == "positive_raw_ev"
    assert payload["data_source"]["join"] == "event_id"


def test_different_event_id_never_cross_matches_same_teams():
    payload = build_product_view_from_snapshot_rows(
        [prediction_snapshot(event_id="model-event")],
        [odds_snapshot(event_id="market-event")],
    )

    item = payload["matches"][0]
    home = item["markets"]["1x2"]["selections"][0]
    assert home["bookmaker_odds"] is None
    assert home["raw_expected_value"] is None
    assert item["main_forecast"]["status"] == "model_forecast"
    assert item["value_signal"]["status"] == "none"


def test_timezone_naive_snapshot_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        select_latest_prediction_snapshots(
            [prediction_snapshot(generated_at_utc="2026-09-12T07:00:00")]
        )


@pytest.mark.parametrize("invalid_quote", [
    {"home_odds": None},
    {"draw_odds": 1.0},
    {"away_odds": float("nan")},
    {"home_odds": "not-a-number"},
    {"away_odds": float("inf")},
])
def test_incomplete_or_invalid_h2h_quote_is_not_counted_as_priced(invalid_quote):
    payload = build_product_view_from_snapshot_rows(
        [prediction_snapshot()], [odds_snapshot(**invalid_quote)],
    )
    assert payload["data_source"]["priced_event_count"] == 0
    item = payload["matches"][0]
    assert item["match"]["market_snapshot_status"] == "no_verified_prekickoff_quote"
    assert item["markets"]["1x2"]["selections"][0]["bookmaker_odds"] is None


def test_older_complete_h2h_quote_survives_newer_incomplete_quote():
    payload = build_product_view_from_snapshot_rows(
        [prediction_snapshot()], [
            odds_snapshot(home_odds=1.85),
            odds_snapshot(snapshot_time_utc="2026-09-12T05:55:00+00:00", draw_odds=None),
        ],
    )
    assert payload["data_source"]["priced_event_count"] == 1
    assert payload["matches"][0]["markets"]["1x2"]["selections"][0]["bookmaker_odds"] == pytest.approx(1.85)


class _FakeSnapshotQuery:
    """Apply database filters, sort, and limit in the same order as PostgREST."""

    def __init__(self, rows):
        self.rows = list(rows)
        self.filters = []
        self.calls = []
        self.sort_key = None
        self.sort_desc = False
        self.row_limit = None

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

    def gte(self, column, value):
        self.calls.append(("gte", column, value))
        self.filters.append(lambda row: str(row[column]) >= value)
        return self

    def gt(self, column, value):
        self.calls.append(("gt", column, value))
        self.filters.append(lambda row: str(row[column]) > value)
        return self

    def lt(self, column, value):
        self.calls.append(("lt", column, value))
        self.filters.append(lambda row: str(row[column]) < value)
        return self

    def lte(self, column, value):
        self.calls.append(("lte", column, value))
        self.filters.append(lambda row: str(row[column]) <= value)
        return self

    def in_(self, column, values):
        allowed = set(values)
        self.calls.append(("in_", column, tuple(values)))
        self.filters.append(lambda row: row[column] in allowed)
        return self

    def order(self, column, desc=False):
        self.calls.append(("order", column, desc))
        self.sort_key = column
        self.sort_desc = desc
        return self

    def limit(self, count):
        self.calls.append(("limit", count))
        self.row_limit = count
        return self

    def execute(self):
        from types import SimpleNamespace

        rows = [row for row in self.rows if all(check(row) for check in self.filters)]
        if self.sort_key:
            rows.sort(key=lambda row: row[self.sort_key], reverse=self.sort_desc)
        return SimpleNamespace(data=rows[: self.row_limit])


class _FakeSnapshotClient:
    def __init__(self, predictions, odds):
        self.datasets = {
            "product_prediction_snapshots": predictions,
            "odds_snapshots": odds,
        }
        self.queries = {}

    def table(self, name):
        query = _FakeSnapshotQuery(self.datasets[name])
        self.queries[name] = query
        return query


def test_database_asof_filters_run_before_page_limits():
    """1000+ future rows must not crowd out a valid pre-kickoff model/price."""
    from product_snapshot_store import load_product_market_view

    now = datetime(2026, 9, 12, 7, tzinfo=timezone.utc)
    future_prediction = prediction_snapshot(
        generated_at_utc="2026-09-12T08:00:00+00:00",
        home_probability=0.91,
    )
    future_quote = odds_snapshot(
        snapshot_time_utc="2026-09-12T08:00:00+00:00",
        home_odds=1.01,
    )
    fake = _FakeSnapshotClient(
        [prediction_snapshot()] + [future_prediction] * 1001,
        [odds_snapshot()] + [future_quote] * 5001,
    )
    result = load_product_market_view(fake, now_utc=now)
    assert result["data_source"]["prediction_snapshot_count"] == 1
    assert result["data_source"]["priced_event_count"] == 1
    item = result["matches"][0]
    assert item["markets"]["1x2"]["selections"][0]["probability"] == pytest.approx(0.60)
    assert item["markets"]["1x2"]["selections"][0]["bookmaker_odds"] == pytest.approx(1.90)

    for name, column in [
        ("product_prediction_snapshots", "generated_at_utc"),
        ("odds_snapshots", "snapshot_time_utc"),
    ]:
        calls = fake.queries[name].calls
        asof_positions = [i for i, call in enumerate(calls) if call[0] == "lte" and call[1] == column]
        assert len(asof_positions) == 1
        assert asof_positions[0] < next(i for i, call in enumerate(calls) if call[0] == "limit")


def test_prediction_snapshot_limit_saturation_fails_closed():
    from product_snapshot_store import load_product_market_view

    fake = _FakeSnapshotClient([prediction_snapshot()] * 1000, [])
    with pytest.raises(ValueError, match="1000-row limit"):
        load_product_market_view(
            fake, now_utc=datetime(2026, 9, 12, 7, tzinfo=timezone.utc),
        )


def test_odds_snapshot_limit_saturation_fails_closed():
    from product_snapshot_store import load_product_market_view

    fake = _FakeSnapshotClient([prediction_snapshot()], [odds_snapshot()] * 5000)
    with pytest.raises(ValueError, match="5000-row limit"):
        load_product_market_view(
            fake, now_utc=datetime(2026, 9, 12, 7, tzinfo=timezone.utc),
        )


def test_exact_kickoff_is_not_upcoming_in_model_or_market_queries():
    """At kickoff the fixture is no longer a future pre-match opportunity."""
    from product_snapshot_store import load_product_market_view

    now = datetime(2026, 9, 13, 14, tzinfo=timezone.utc)
    future_kickoff = "2026-09-13T15:00:00+00:00"
    fake = _FakeSnapshotClient(
        [
            prediction_snapshot(event_id="already-started"),
            prediction_snapshot(event_id="still-upcoming", commence_time_utc=future_kickoff),
        ],
        [
            odds_snapshot(event_id="already-started"),
            odds_snapshot(event_id="still-upcoming", commence_time_utc=future_kickoff),
        ],
    )

    payload = load_product_market_view(fake, now_utc=now)
    assert payload["data_source"]["prediction_snapshot_count"] == 1
    assert payload["data_source"]["priced_event_count"] == 1
    assert [row["match"]["event_id"] for row in payload["matches"]] == ["still-upcoming"]
    for table in ("product_prediction_snapshots", "odds_snapshots"):
        assert ("gt", "commence_time_utc", now.isoformat()) in fake.queries[table].calls
