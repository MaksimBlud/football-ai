from datetime import UTC, datetime

from multi_market_probe_rollover_plan import load_rollover_events, plan_rollover


def event(league, event_id, home, away, kickoff):
    return {
        "league": league,
        "event_id": event_id,
        "home_team": home,
        "away_team": away,
        "commence_time_utc": kickoff,
    }


def test_rollover_is_advisory_zero_cost_and_never_switches_target():
    now = datetime(2026, 9, 6, 5, 15, tzinfo=UTC)
    rows = [event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00")]
    plan = plan_rollover(rows, now_utc=now)
    assert plan["research_only"] is True
    assert plan["read_only"] is True
    assert plan["advisory_only"] is True
    assert plan["writes_performed"] is False
    assert plan["paid_provider_requests"] == 0
    assert plan["paid_provider_credits"] == 0
    assert plan["automatic_target_switching_enabled"] is False
    assert plan["requires_separate_preregistration_pr"] is True
    assert plan["active_target_expired"] is False
    assert plan["rollover_lookahead_hours"] == 168
    assert plan["proposed_candidate"]["event_id"] == "clean"


def test_candidate_requires_at_least_24_hours_lead():
    now = datetime(2026, 9, 6, 5, 15, tzinfo=UTC)
    rows = [
        event("LIGUE_1", "too-soon", "Marseille", "Paris FC", "2026-09-06T18:45:00+00:00"),
        event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00"),
    ]
    plan = plan_rollover(rows, now_utc=now)
    assert plan["minimum_rollover_lead_hours"] == 24
    assert plan["proposed_candidate"]["event_id"] == "clean"


def test_ambiguous_event_identity_is_excluded_fail_closed():
    now = datetime(2026, 9, 6, 5, 15, tzinfo=UTC)
    rows = [
        event("SERIE_A", "dup", "Cagliari", "Lecce", "2026-09-07T16:00:00+00:00"),
        event("SERIE_A", "dup", "Cagliari", "Lecce", "2026-09-07T16:30:00+00:00"),
        event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00"),
    ]
    plan = plan_rollover(rows, now_utc=now)
    assert plan["ambiguous_event_ids_excluded"] == ["dup"]
    assert plan["proposed_candidate"]["event_id"] == "clean"


def test_repeated_snapshots_of_same_identity_are_deduplicated():
    now = datetime(2026, 9, 6, 5, 15, tzinfo=UTC)
    clean = event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00")
    plan = plan_rollover([clean, dict(clean), dict(clean)], now_utc=now)
    assert plan["ambiguous_event_ids_excluded"] == []
    assert plan["eligible_candidate_count"] == 1
    assert plan["proposed_candidate"]["event_id"] == "clean"


def test_prohibited_and_non_source_ready_leagues_are_excluded():
    now = datetime(2026, 9, 6, 5, 15, tzinfo=UTC)
    rows = [
        event("EREDIVISIE", "ered", "A", "B", "2026-09-07T12:00:00+00:00"),
        event("RPL", "rpl", "C", "D", "2026-09-07T13:00:00+00:00"),
        event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00"),
    ]
    plan = plan_rollover(rows, now_utc=now)
    assert plan["proposed_candidate"]["event_id"] == "clean"


def test_expired_active_target_does_not_auto_promote_candidate():
    now = datetime(2026, 9, 6, 13, 1, tzinfo=UTC)
    rows = [event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00")]
    plan = plan_rollover(rows, now_utc=now)
    assert plan["active_target_expired"] is True
    assert plan["active_target_seconds_remaining"] == 0
    assert plan["proposed_candidate"]["event_id"] == "clean"
    assert plan["automatic_target_switching_enabled"] is False


class Response:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

    def gte(self, column, value):
        self.calls.append(("gte", column, value))
        return self

    def lte(self, column, value):
        self.calls.append(("lte", column, value))
        return self

    def order(self, column, desc=False):
        self.calls.append(("order", column, desc))
        return self

    def range(self, start, end):
        self.calls.append(("range", start, end))
        self.start, self.end = start, end
        return self

    def execute(self):
        return Response(self.rows[self.start : self.end + 1])


class Client:
    def __init__(self, rows):
        self.query = Query(rows)
        self.table_name = None

    def table(self, name):
        self.table_name = name
        return self.query


def test_live_loader_is_supabase_only_and_uses_seven_day_window():
    now = datetime(2026, 9, 6, 5, 15, tzinfo=UTC)
    rows = [event("LA_LIGA", "clean", "Getafe", "Celta Vigo", "2026-09-07T17:00:00+00:00")]
    client = Client(rows)
    loaded = load_rollover_events(client, now_utc=now)
    assert client.table_name == "odds_snapshots"
    assert loaded == rows
    assert any(call[0] == "gte" and call[1] == "commence_time_utc" for call in client.query.calls)
    lte_calls = [call for call in client.query.calls if call[0] == "lte" and call[1] == "commence_time_utc"]
    assert len(lte_calls) == 1
    assert lte_calls[0][2] == "2026-09-13T05:15:00+00:00"
