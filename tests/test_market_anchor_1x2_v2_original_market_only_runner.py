from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

import market_anchor_1x2_v2_original_market_only_runner as runner


def test_rights_gate_blocks_before_any_github_or_supabase_request(tmp_path, monkeypatch):
    calls = []

    def denied():
        calls.append("rights")
        raise PermissionError("no research inference scope")

    def forbidden_get(*args, **kwargs):
        calls.append("github")
        raise AssertionError("GitHub must not be called before rights pass")

    def forbidden_client():
        calls.append("supabase")
        raise AssertionError("Supabase must not be called before rights pass")

    monkeypatch.setattr(
        runner, "write_research_scope_blocked_report",
        lambda *args, **kwargs: {"mode": "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE"},
    )
    report = runner.run_live(
        token="token",
        current_sha="a" * 40,
        client_factory=forbidden_client,
        now=datetime(2026, 11, 6, 4, 0, tzinfo=timezone.utc),
        get=forbidden_get,
        rights_check=denied,
    )
    assert calls == ["rights"]
    assert report["status"] == "SOURCE_RIGHTS_BLOCKED_NO_EXTERNAL_READ"
    assert report["target_outcomes_read"] is False
    assert report["supabase_writes"] == 0
    assert report["paid_provider_calls"] == 0


def test_forward_artifact_extractor_accepts_exact_report_and_attestation():
    buffer = BytesIO()
    report = {
        "schema_version": "SERIE_A_ORIGINAL_V2_FORWARD_SOURCE_BEFORE_QUOTE_V1",
        "rows": [],
        "archived_sources_used": {},
        "uses_2026_27_results": False,
    }
    with ZipFile(buffer, "w") as archive:
        archive.writestr("artifacts/serie_a_v2_forward_source_checked.json", json.dumps(report))
        archive.writestr("artifacts/serie_a_v2_real_source_attestation.json", "{}")
    extracted = runner._extract_forward_report(buffer.getvalue())
    assert extracted["rows"] == []
    assert extracted["archived_sources_used"] == {}


@pytest.mark.parametrize("member", ["../escape.json", "/absolute.json", "folder\\bad.json"])
def test_forward_artifact_extractor_rejects_unsafe_member_paths(member):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(member, "{}")
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        runner._extract_forward_report(buffer.getvalue())


def test_forward_artifact_extractor_rejects_duplicate_report():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("a/serie_a_v2_forward_source_checked.json", "{}")
        archive.writestr("b/serie_a_v2_forward_source_checked.json", "{}")
    with pytest.raises(ValueError, match="exactly one"):
        runner._extract_forward_report(buffer.getvalue())


def test_completed_fixture_gate_selects_only_identity_columns_and_attests_sha():
    class Response:
        data = [{
            "match_date": "2026-08-22",
            "home_team": "Atalanta BC",
            "away_team": "Pisa",
        }]

    class Query:
        def __init__(self):
            self.selected = None
            self.filters = []
            self.range_value = None

        def select(self, value):
            self.selected = value
            return self

        def eq(self, key, value):
            self.filters.append(("eq", key, value))
            return self

        def lt(self, key, value):
            self.filters.append(("lt", key, value))
            return self

        def range(self, start, end):
            self.range_value = (start, end)
            return self

        def execute(self):
            return Response()

    class Client:
        def __init__(self):
            self.query = Query()

        def table(self, name):
            assert name == "league_finished_results"
            return self.query

    client = Client()
    identities, attestation = runner.read_completed_fixture_gate(
        client, now=datetime(2026, 11, 6, 4, 0, tzinfo=timezone.utc)
    )
    assert client.query.selected == "match_date,home_team,away_team"
    assert ("lt", "match_date", "2026-11-06") in client.query.filters
    assert identities == {("2026-08-22", "Atalanta", "Pisa")}
    assert attestation["selected_columns"] == ["match_date", "home_team", "away_team"]
    assert attestation["target_outcomes_read"] is False
    assert attestation["completed_fixture_identity_count"] == 1


def test_no_post_freeze_forward_artifacts_returns_without_supabase(monkeypatch):
    monkeypatch.setattr(runner, "verify_current_main_contract", lambda *a, **k: None)
    monkeypatch.setattr(runner, "discover_forward_artifacts", lambda *a, **k: [])
    report = runner.run_live(
        token="token",
        current_sha="a" * 40,
        client_factory=lambda: (_ for _ in ()).throw(AssertionError("Supabase must not be created")),
        now=datetime(2026, 11, 6, 4, 0, tzinfo=timezone.utc),
        get=lambda *a, **k: (_ for _ in ()).throw(AssertionError("GitHub fetch must be stubbed")),
        rights_check=lambda: {"scope_status": "CONDITIONAL_RESEARCH_ONLY"},
    )
    assert report["status"] == "NO_POST_FREEZE_FORWARD_ARTIFACTS"
    assert report["eligible_forecast_count"] == 0
    assert report["target_outcomes_read"] is False
    assert report["outcomes_scored"] is False


def test_outcome_loader_queries_only_exact_fixture_and_post_kickoff_fields():
    identity = ("2026-08-22", "Atalanta", "Pisa")
    kickoff = "2026-08-22T18:30:00+00:00"

    class Response:
        data = [{
            "match_date": "2026-08-22",
            "home_team": "Atalanta",
            "away_team": "Pisa",
            "result": "H",
            "persisted_at_utc": "2026-08-22T20:35:00+00:00",
        }]

    class Query:
        def __init__(self):
            self.selected = None
            self.filters = []

        def select(self, value):
            self.selected = value
            return self

        def eq(self, key, value):
            self.filters.append(("eq", key, value))
            return self

        def in_(self, key, value):
            self.filters.append(("in", key, tuple(value)))
            return self

        def execute(self):
            return Response()

    class Client:
        def __init__(self):
            self.query = Query()

        def table(self, name):
            assert name == "league_finished_results"
            return self.query

    client = Client()
    loaded = runner._read_exact_outcomes(client, (identity,), {identity: kickoff})
    assert client.query.selected == "match_date,home_team,away_team,result,persisted_at_utc"
    assert ("eq", "match_date", "2026-08-22") in client.query.filters
    assert loaded[identity]["result"] == "H"
    assert loaded[identity]["persisted_at_utc"] == "2026-08-22T20:35:00+00:00"


def test_outcome_loader_rejects_persistence_at_or_before_kickoff():
    identity = ("2026-08-22", "Atalanta", "Pisa")

    class Response:
        data = [{
            "match_date": "2026-08-22",
            "home_team": "Atalanta",
            "away_team": "Pisa",
            "result": "H",
            "persisted_at_utc": "2026-08-22T18:30:00+00:00",
        }]

    class Query:
        def select(self, value): return self
        def eq(self, key, value): return self
        def in_(self, key, value): return self
        def execute(self): return Response()

    class Client:
        def table(self, name): return Query()

    with pytest.raises(ValueError, match="strictly later than kickoff"):
        runner._read_exact_outcomes(
            Client(), (identity,), {identity: "2026-08-22T18:30:00+00:00"}
        )
