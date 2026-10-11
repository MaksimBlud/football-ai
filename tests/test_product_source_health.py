"""Contract tests for the no-cost, read-only website source-health endpoint."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from product_source_health import load_website_source_health


NOW = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)
KICKOFF = "2026-10-17T14:00:00+00:00"
CREATED = "2026-10-09T15:29:33+00:00"
QUOTED = "2026-10-09T15:25:57+00:00"


def prediction(**overrides):
    row = {
        "snapshot_schema_version": "product-prediction.v1",
        "generated_at_utc": CREATED,
        "league": "EPL",
        "event_id": "event-1",
        "commence_time_utc": KICKOFF,
        "match_date": "2026-10-17",
        "match_time": "15:00",
        "home_team": "Home",
        "away_team": "Away",
        "home_team_model": "Home",
        "away_team_model": "Away",
        "prediction": "HOME",
        "prediction_strength": "MEDIUM",
        "model_agreement": True,
        "home_probability": 0.60,
        "draw_probability": 0.25,
        "away_probability": 0.15,
        "expected_home_goals": 1.8,
        "expected_away_goals": 1.2,
        "expected_total_goals": 3.0,
        "over_2_5_probability": 0.60,
        "under_2_5_probability": 0.40,
        "btts_yes_probability": 0.55,
        "btts_no_probability": 0.45,
        "top_score": "2:1",
        "top_score_probability": 0.12,
    }
    row.update(overrides)
    return row


def price(**overrides):
    row = {
        "event_id": "event-1",
        "snapshot_time_utc": QUOTED,
        "commence_time_utc": KICKOFF,
        "home_team": "Home",
        "away_team": "Away",
        "home_odds": 1.90,
        "draw_odds": 3.50,
        "away_odds": 4.20,
    }
    row.update(overrides)
    return row


class Query:
    def __init__(self, rows, calls):
        self.rows = list(rows)
        self.calls = calls
        self.filters = []
        self.sort_key = None
        self.desc = False
        self.page_limit = 5000

    def select(self, fields):
        self.calls.append(("select", fields))
        return self

    def gt(self, field, bound):
        self.calls.append(("gt", field, bound))
        self.filters.append(lambda row: row[field] > bound)
        return self

    def lt(self, field, bound):
        self.calls.append(("lt", field, bound))
        self.filters.append(lambda row: row[field] < bound)
        return self

    def lte(self, field, bound):
        self.calls.append(("lte", field, bound))
        self.filters.append(lambda row: row[field] <= bound)
        return self

    def order(self, field, desc=False):
        self.calls.append(("order", field, desc))
        self.sort_key = field
        self.desc = desc
        return self

    def limit(self, limit):
        self.calls.append(("limit", limit))
        self.page_limit = limit
        return self

    def execute(self):
        rows = [row for row in self.rows if all(eligible(row) for eligible in self.filters)]
        rows.sort(key=lambda row: row[self.sort_key], reverse=self.desc)
        return SimpleNamespace(data=rows[: self.page_limit])


class FakeClient:
    def __init__(self, predictions=(), odds=()):
        self.data = {
            "product_prediction_snapshots": list(predictions),
            "odds_snapshots": list(odds),
        }
        self.calls = {}

    def table(self, name):
        assert name in self.data, "unexpected table or private lifecycle access"
        calls = self.calls.setdefault(name, [])
        return Query(self.data[name], calls)


def check(client):
    return load_website_source_health(client, now_utc=NOW)


def test_verified_future_ai_market_coverage():
    client = FakeClient([prediction()], [price()])
    health = check(client)
    assert health["state"] == "COVERED"
    assert health["future_ai_events"] == 1
    assert health["future_provider_odds_events"] == 1
    assert health["verified_prediction_market_pairs"] == 1
    assert health["provider_events_waiting_for_ai"] == 0
    assert health["ai_events_without_verified_price"] == 0
    assert health["safety"]["read_only"] is True
    assert health["safety"]["provider_calls"] is False
    assert "event-1" not in str(health)
    assert "model_1x2_sha256" not in str(health)
    assert health["latest_model_generated_at_utc"] == CREATED
    for table, as_of_column in (
        ("product_prediction_snapshots", "generated_at_utc"),
        ("odds_snapshots", "snapshot_time_utc"),
    ):
        calls = client.calls[table]
        assert ("gt", "commence_time_utc", NOW.isoformat()) in calls
        assert ("lte", as_of_column, NOW.isoformat()) in calls
        assert next(i for i, call in enumerate(calls) if call[0] == "lte") < next(
            i for i, call in enumerate(calls) if call[0] == "limit"
        )


def test_no_source_events_is_not_misreported_as_existing_forecasts():
    health = check(FakeClient())
    assert health["state"] == "NO_FUTURE_EVENTS"
    assert health["future_ai_events"] == 0
    assert health["future_provider_odds_events"] == 0


def test_future_provider_event_waits_for_genuine_ai_prediction():
    health = check(FakeClient(odds=[price()]))
    assert health["state"] == "WAITING_FOR_PREDICTION_SOURCE"
    assert health["provider_events_waiting_for_ai"] == 1
    assert health["verified_prediction_market_pairs"] == 0


def test_model_only_future_event_has_no_verified_market_quote():
    health = check(FakeClient(predictions=[prediction()]))
    assert health["state"] == "NO_PROVIDER_SNAPSHOTS"
    assert health["ai_events_without_verified_price"] == 1


@pytest.mark.parametrize("bad_price", [
    {"event_id": "other-event"},
    {"commence_time_utc": "2026-10-18T14:00:00+00:00"},
    {"home_team": "Other"},
    {"draw_odds": 1.00},
])
def test_bad_market_binding_never_produces_covered_state(bad_price):
    health = check(FakeClient([prediction()], [price(**bad_price)]))
    assert health["verified_prediction_market_pairs"] == 0
    assert health["state"] != "COVERED"


def test_future_provider_event_without_matching_model_causes_waiting():
    client = FakeClient([prediction()], [price(), price(event_id="other-event")])
    health = check(client)
    assert health["state"] == "WAITING_FOR_PREDICTION_SOURCE"
    assert health["provider_events_waiting_for_ai"] == 1
    assert health["verified_prediction_market_pairs"] == 1


def test_current_kickoff_and_future_generated_rows_are_excluded_before_limit():
    old = prediction(event_id="started", commence_time_utc=NOW.isoformat())
    invalid = prediction(event_id="not-yet-predicted",
                         generated_at_utc="2026-10-12T10:00:00+00:00")
    future_quote = price(event_id="future-quote",
                         snapshot_time_utc="2026-10-12T10:00:00+00:00")
    health = check(FakeClient([old, invalid, prediction()], [future_quote, price()]))
    assert health["state"] == "COVERED"
    assert health["future_ai_events"] == 1
    assert health["future_provider_odds_events"] == 1


def test_prediction_and_odds_saturation_are_fail_closed():
    with pytest.raises(ValueError, match="1000-row limit"):
        check(FakeClient([prediction()] * 1000, [price()]))
    with pytest.raises(ValueError, match="5000-row limit"):
        check(FakeClient([prediction()], [price()] * 5000))


def test_rejects_naive_clock_and_invalid_horizon():
    with pytest.raises(ValueError, match="timezone-aware"):
        load_website_source_health(FakeClient(), now_utc=datetime(2026, 10, 11))
    with pytest.raises(ValueError, match="horizon_days"):
        load_website_source_health(FakeClient(), now_utc=NOW, horizon_days=31)


def test_endpoint_is_read_only_and_does_not_expose_internal_rows():
    web = Path("web_app.py").read_text(encoding="utf-8")
    assert '@app.get("/source-health")' in web
    assert "return load_website_source_health(_supabase_client())" in web
