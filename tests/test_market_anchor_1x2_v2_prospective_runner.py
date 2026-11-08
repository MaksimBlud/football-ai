"""Integration regressions for the original V2 live prospective runner."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

import market_anchor_1x2_v2_prospective_evaluator as evaluator
import market_anchor_1x2_v2_prospective_runner as runner


@pytest.fixture(autouse=True)
def _allow_synthetic_inference_scope(monkeypatch):
    monkeypatch.setattr(
        runner,
        "require_personal_research_inference_scope",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )


def _forecast_rows(count: int = 30) -> list[dict]:
    rows = []
    first_day = date(2026, 10, 19)
    for index in range(count):
        match_day = (first_day + timedelta(days=index % 13)).isoformat()
        home = f"Gate Home {index}"
        away = f"Gate Away {index}"
        kickoff = f"{match_day}T18:00:00Z"
        rows.append({
            "experiment_id": evaluator.EXPERIMENT_ID,
            "evidence_class": "PROSPECTIVE_SHADOW",
            "league": "SERIE_A",
            "event_id": f"provider-event-{index}",
            "match_date": match_day,
            "home_team": home,
            "away_team": away,
            "candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
            "active_lambda": 0.0,
            "shadow_residual_lambda": 1.0,
            "no_bet": True,
            "eligible_for_current_form_forward_shadow": True,
            "eligible_for_product_publication": False,
            "shadow_evidence_status": "SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE",
            "source_artifact_id": 20001,
            "source_archive_sha256": "a" * 64,
            "source_observed_at_utc": f"{match_day}T08:45:00Z",
            "source_archive_created_at_utc": f"{match_day}T08:50:00Z",
            "source_parent_run_id": 30001,
            "source_parent_run_sha": "b" * 40,
            "source_parent_run_completed_at_utc": f"{match_day}T09:00:00Z",
            "quote_time_utc": f"{match_day}T09:10:00Z",
            "forecast_captured_at_utc": f"{match_day}T09:11:00Z",
            "kickoff_utc": kickoff,
            "market_1x2": [0.50, 0.30, 0.20],
            "active_market_fallback_1x2": [0.50, 0.30, 0.20],
            "incumbent_1x2": [0.52, 0.28, 0.20],
            "incumbent_evidence": {
                "model_version": "synthetic-nonlegacy-incumbent-v1",
                "artifact_sha256": "c" * 64,
                "source_record_id": f"incumbent-record-{index}",
                "generated_at_utc": f"{match_day}T09:05:00Z",
                "history_cutoff_utc": f"{match_day}T08:45:00Z",
                "league": "SERIE_A",
                "match_date": match_day,
                "home_team": home,
                "away_team": away,
                "kickoff_utc": kickoff,
            },
            "shadow_v2_residual_1x2": [0.51, 0.29, 0.20],
        })
    return rows


def _persisted_after_kickoff(row: dict, *, hours: int = 2) -> str:
    kickoff = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
    return (kickoff + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def _gate_attestation(identities: set[tuple[str, str, str]]) -> dict:
    return {
        "schema_version": evaluator.COMPLETED_FIXTURE_GATE_SCHEMA,
        "source_table": evaluator.COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
        "selected_columns": list(evaluator.COMPLETED_FIXTURE_GATE_COLUMNS),
        "league": evaluator.PRIMARY_LEAGUE,
        "season": "2026-2027",
        "query_contract_id": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID,
        "query_contract_sha256": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
        "captured_at_utc": "2026-11-01T08:00:00Z",
        "cutoff_date_exclusive_utc": "2026-11-01",
        "completed_fixture_identity_count": len(identities),
        "completed_fixture_identity_sha256": evaluator._sha_fixture_set(identities),
        "outcome_columns_selected": False,
        "target_outcomes_read": False,
    }


def test_live_runner_reads_identity_gate_and_keeps_outcomes_lazy_when_incumbent_unpinned(monkeypatch):
    rows = _forecast_rows()
    # Mirror the current-form forward artifact: it contains no incumbent
    # vector/evidence while the frozen same-league incumbent is unresolved.
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    attestation = _gate_attestation(identities)
    client = object()
    gate_calls = []

    def read_gate(received_client):
        gate_calls.append(received_client)
        return identities, attestation

    monkeypatch.setattr(runner, "read_completed_fixture_gate", read_gate)
    outcome_calls = []

    def load_outcomes(keys):
        outcome_calls.append(keys)
        return {key: "H" for key in keys}

    report = runner.evaluate_live_prospective_cohort(client, rows, load_outcomes)

    assert gate_calls == [client]
    assert report["eligible_completed_forecasts"] == 30
    assert report["completed_fixture_gate_attestation_verified"] is True
    assert report["frozen_incumbent_reference_pinned"] is False
    assert report["status"] == "EVALUATION_BLOCKED_UNPINNED_INCUMBENT"
    assert report["outcome_read_gate_open"] is False
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert outcome_calls == []


def test_live_runner_stops_if_identity_gate_fails_before_evaluator_or_outcomes(monkeypatch):
    outcome_calls = []

    def fail_gate(_client):
        raise RuntimeError("identity-only gate unavailable")

    def forbidden_evaluator(*_args, **_kwargs):
        pytest.fail("evaluator must not run after a failed metadata gate")

    monkeypatch.setattr(runner, "read_completed_fixture_gate", fail_gate)
    monkeypatch.setattr(runner, "evaluate_after_gate", forbidden_evaluator)

    with pytest.raises(RuntimeError, match="identity-only gate unavailable"):
        runner.evaluate_live_prospective_cohort(
            object(),
            [],
            lambda keys: outcome_calls.append(keys) or {},
        )

    assert outcome_calls == []

def test_live_market_only_runner_uses_identity_gate_and_scores_only_after_30(monkeypatch):
    rows = _forecast_rows()
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    attestation = _gate_attestation(identities)
    client = object()
    gate_calls = []

    def read_gate(received_client):
        gate_calls.append(received_client)
        return identities, attestation

    monkeypatch.setattr(runner, "read_completed_fixture_gate", read_gate)
    outcome_calls = []

    def load_outcomes(keys):
        outcome_calls.append(keys)
        return {key: "H" for key in keys}

    report = runner.evaluate_live_market_only_prospective_cohort(
        client, rows, load_outcomes
    )

    assert gate_calls == [client]
    assert len(outcome_calls) == 1
    assert outcome_calls[0] == frozenset(identities)
    assert report["status"] == "EVALUATED_MARKET_ONLY_DIAGNOSTIC"
    assert report["scored_forecasts"] == 30
    assert report["review_signal"] is False
    assert report["no_bet"] is True

class _ExactOutcomeResponse:
    def __init__(self, data):
        self.data = data


class _ExactOutcomeQuery:
    def __init__(self, client):
        self.client = client
        self.columns = None
        self.filters = {}
        self.membership = {}

    def select(self, columns):
        self.columns = columns
        self.client.select_calls.append(columns)
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def in_(self, field, values):
        self.membership[field] = list(values)
        return self

    def execute(self):
        self.client.result_query_count += 1
        selected = self.columns.split(",")
        matches = []
        for row in self.client.rows:
            if any(row.get(key) != value for key, value in self.filters.items()):
                continue
            if any(row.get(key) not in values for key, values in self.membership.items()):
                continue
            matches.append({key: row[key] for key in selected})
        return _ExactOutcomeResponse(matches)


class _ExactOutcomeClient:
    def __init__(self, rows):
        self.rows = list(rows)
        self.select_calls = []
        self.result_query_count = 0

    def table(self, name):
        assert name == "league_finished_results"
        return _ExactOutcomeQuery(self)


def test_live_supabase_market_only_runner_does_not_read_results_below_30(monkeypatch):
    rows = _forecast_rows(29)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    client = _ExactOutcomeClient([])

    report = runner.evaluate_live_market_only_from_supabase(client, rows)

    assert report["status"] == "OUTCOME_READ_GATE_CLOSED"
    assert report["eligible_completed_forecasts"] == 29
    assert report["target_outcomes_read"] is False
    assert client.result_query_count == 0
    assert client.select_calls == []


def test_live_supabase_market_only_runner_reads_only_exact_identity_and_result_after_30(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    rows[0]["home_team"] = "Atalanta BC"
    rows[0]["away_team"] = "Sassuolo"
    identities = {
        (
            row["match_date"],
            "Atalanta" if row["home_team"] == "Atalanta BC" else row["home_team"],
            row["away_team"],
        )
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    outcome_rows = []
    for index, row in enumerate(rows):
        home = "Atalanta" if row["home_team"] == "Atalanta BC" else row["home_team"]
        outcome_rows.append({
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": row["match_date"],
            "home_team": home,
            "away_team": row["away_team"],
            "result": "H",
            "persisted_at_utc": _persisted_after_kickoff(row),
        })
        if index == 0:
            # The real metadata table contains this known duplicate raw alias.
            outcome_rows.append({
                "league": "SERIE_A",
                "season": "2026-2027",
                "match_date": row["match_date"],
                "home_team": "Atalanta BC",
                "away_team": "Sassuolo",
                "result": "H",
                "persisted_at_utc": _persisted_after_kickoff(row),
            })
    client = _ExactOutcomeClient(outcome_rows)

    report = runner.evaluate_live_market_only_from_supabase(client, rows)

    assert report["status"] == "EVALUATED_MARKET_ONLY_DIAGNOSTIC"
    assert report["scored_forecasts"] == 30
    assert report["target_outcomes_read"] is True
    assert report["review_signal"] is False
    assert client.result_query_count == 30
    assert client.select_calls == ["match_date,home_team,away_team,result,persisted_at_utc"] * 30



@pytest.mark.parametrize("hours", [-1, 0])
def test_live_supabase_market_only_runner_rejects_outcome_persisted_at_or_before_kickoff(monkeypatch, hours):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    outcome_rows = [
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": row["match_date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "result": "H",
            "persisted_at_utc": _persisted_after_kickoff(row, hours=hours),
        }
        for row in rows
    ]
    client = _ExactOutcomeClient(outcome_rows)

    with pytest.raises(ValueError, match="persisted_at_utc must be strictly after kickoff_utc"):
        runner.evaluate_live_market_only_from_supabase(client, rows)

    assert client.result_query_count == 1
    assert client.select_calls == ["match_date,home_team,away_team,result,persisted_at_utc"]



def test_live_supabase_market_only_runner_rejects_outcome_persisted_after_evaluation_observation_time(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    outcome_rows = [
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": row["match_date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "result": "H",
            "persisted_at_utc": _persisted_after_kickoff(row),
        }
        for row in rows
    ]
    # This timestamp is after kickoff but after the evaluator's frozen
    # observation clock; it must not be treated as already persisted evidence.
    outcome_rows[0]["persisted_at_utc"] = "2026-12-01T20:00:00Z"
    client = _ExactOutcomeClient(outcome_rows)

    with pytest.raises(ValueError, match="cannot be later than evaluation observation time"):
        runner.evaluate_live_market_only_from_supabase(
            client, rows, observed_at_utc="2026-12-01T19:00:00Z"
        )

    assert client.result_query_count == 1
    assert client.select_calls == ["match_date,home_team,away_team,result,persisted_at_utc"]


def test_live_supabase_market_only_runner_rejects_offsetless_evaluation_observation_clock(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    gate_calls = []
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: gate_calls.append(True) or (identities, _gate_attestation(identities)),
    )
    client = _ExactOutcomeClient([])

    with pytest.raises(ValueError, match="evaluation observed_at_utc must have a real UTC offset"):
        runner.evaluate_live_market_only_from_supabase(
            client, rows, observed_at_utc="2026-11-06T12:00:00"
        )

    assert gate_calls == []
    assert client.result_query_count == 0
    assert client.select_calls == []


def test_live_supabase_market_only_runner_rejects_offsetless_outcome_persistence_timestamp(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    outcome_rows = [
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": row["match_date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "result": "H",
            "persisted_at_utc": row["kickoff_utc"].replace("Z", ""),
        }
        for row in rows
    ]
    client = _ExactOutcomeClient(outcome_rows)

    with pytest.raises(ValueError, match="persisted_at_utc must have a real UTC offset"):
        runner.evaluate_live_market_only_from_supabase(client, rows)

    assert client.result_query_count == 1
    assert client.select_calls == ["match_date,home_team,away_team,result,persisted_at_utc"]



def test_live_supabase_market_only_runner_rejects_missing_persistence_timestamp_field(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    outcome_rows = [
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": row["match_date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "result": "H",
            "persisted_at_utc": _persisted_after_kickoff(row),
        }
        for row in rows
    ]

    class _MissingPersistenceTimestampClient(_ExactOutcomeClient):
        def table(self, name):
            query = super().table(name)
            execute = query.execute

            def execute_without_persistence_timestamp():
                response = execute()
                response.data = [
                    {key: value for key, value in item.items() if key != "persisted_at_utc"}
                    for item in response.data
                ]
                return response

            query.execute = execute_without_persistence_timestamp
            return query

    client = _MissingPersistenceTimestampClient(outcome_rows)

    with pytest.raises(ValueError, match="outcome query returned fields outside the exact identity\\+result allowlist"):
        runner.evaluate_live_market_only_from_supabase(client, rows)

    assert client.result_query_count == 1
    assert client.select_calls == ["match_date,home_team,away_team,result,persisted_at_utc"]

def test_live_supabase_market_only_runner_rejects_conflicting_duplicate_alias_results(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    rows[0]["home_team"] = "Atalanta BC"
    rows[0]["away_team"] = "Sassuolo"
    identities = {
        (
            row["match_date"],
            "Atalanta" if row["home_team"] == "Atalanta BC" else row["home_team"],
            row["away_team"],
        )
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    outcome_rows = [
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": rows[0]["match_date"],
            "home_team": "Atalanta",
            "away_team": "Sassuolo",
            "result": "H",
            "persisted_at_utc": _persisted_after_kickoff(rows[0]),
        },
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": rows[0]["match_date"],
            "home_team": "Atalanta BC",
            "away_team": "Sassuolo",
            "result": "A",
            "persisted_at_utc": _persisted_after_kickoff(rows[0]),
        },
    ]
    client = _ExactOutcomeClient(outcome_rows)

    with pytest.raises(ValueError, match="duplicate raw aliases disagree"):
        runner.evaluate_live_market_only_from_supabase(client, rows)

    assert client.result_query_count == 1
    assert client.select_calls == ["match_date,home_team,away_team,result,persisted_at_utc"]



def test_market_only_preflight_and_evaluator_share_one_immutable_gate_snapshot(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    attestation = _gate_attestation(identities)
    client = object()
    gate_calls = []
    call_order = []
    preflight_seen = []
    evaluator_seen = []
    outcome_calls = []

    def read_gate(received_client):
        gate_calls.append(received_client)
        return set(identities), attestation

    def preflight(received_identities, received_attestation):
        call_order.append("preflight")
        preflight_seen.append((received_identities, received_attestation))
        assert isinstance(received_identities, frozenset)
        assert received_identities == frozenset(identities)
        # Mutating this detached nested list must not alter the attestation
        # later supplied to the evaluator.
        received_attestation["selected_columns"].append("result")

    def fake_evaluate(received_rows, received_identities, outcome_loader, *, completed_fixture_gate_attestation):
        call_order.append("evaluate")
        evaluator_seen.append((received_identities, completed_fixture_gate_attestation))
        assert list(completed_fixture_gate_attestation["selected_columns"]) == [
            "match_date", "home_team", "away_team"
        ]
        assert received_identities == frozenset(identities)
        assert len(list(received_rows)) == 30
        return {"status": "GATE_SNAPSHOT_REUSED"}

    def outcome_loader(_identities):
        outcome_calls.append(_identities)
        raise AssertionError("stub evaluator must not request outcomes")

    monkeypatch.setattr(runner, "read_completed_fixture_gate", read_gate)
    monkeypatch.setattr(runner, "evaluate_market_only_after_gate", fake_evaluate)

    report = runner.evaluate_live_market_only_prospective_cohort(
        client, rows, outcome_loader, preflight=preflight
    )

    assert gate_calls == [client]
    assert call_order == ["preflight", "evaluate"]
    assert preflight_seen[0][0] is evaluator_seen[0][0]
    assert preflight_seen[0][0] == evaluator_seen[0][0]
    assert preflight_seen[0][1]["selected_columns"] == [
        "match_date", "home_team", "away_team", "result"
    ]
    assert outcome_calls == []
    assert report["status"] == "GATE_SNAPSHOT_REUSED"


def test_market_only_preflight_failure_stops_before_evaluator_or_outcomes(monkeypatch):
    rows = _forecast_rows(30)
    for row in rows:
        row.pop("incumbent_1x2")
        row.pop("incumbent_evidence")
    identities = {
        (row["match_date"], row["home_team"], row["away_team"])
        for row in rows
    }
    monkeypatch.setattr(
        runner, "read_completed_fixture_gate",
        lambda _client: (identities, _gate_attestation(identities)),
    )
    evaluator_calls = []
    outcome_calls = []

    def preflight(_identities, _attestation):
        raise RuntimeError("source identity SHA mismatch")

    def fake_evaluate(*args, **kwargs):
        evaluator_calls.append((args, kwargs))
        return {"status": "SHOULD_NOT_RUN"}

    def outcome_loader(_identities):
        outcome_calls.append(_identities)
        return {}

    monkeypatch.setattr(runner, "evaluate_market_only_after_gate", fake_evaluate)

    with pytest.raises(RuntimeError, match="source identity SHA mismatch"):
        runner.evaluate_live_market_only_prospective_cohort(
            object(), rows, outcome_loader, preflight=preflight
        )

    assert evaluator_calls == []
    assert outcome_calls == []



@pytest.mark.parametrize(
    "entrypoint",
    ["incumbent_cohort", "market_only_cohort", "supabase_wrapper"],
)
def test_every_live_runner_blocks_before_identity_gate_without_inference_rights(monkeypatch, entrypoint):
    rows = _forecast_rows(30)
    calls = []

    def deny_rights():
        calls.append("rights")
        raise PermissionError("frozen-inference scope remains unresolved")

    def forbidden_gate(_client):
        calls.append("gate")
        pytest.fail("the Supabase identity gate must not run without inference rights")

    monkeypatch.setattr(runner, "require_personal_research_inference_scope", deny_rights)
    monkeypatch.setattr(runner, "read_completed_fixture_gate", forbidden_gate)

    with pytest.raises(PermissionError, match="frozen-inference scope remains unresolved"):
        if entrypoint == "incumbent_cohort":
            runner.evaluate_live_prospective_cohort(
                object(), rows, lambda _keys: pytest.fail("outcome loader must remain lazy")
            )
        elif entrypoint == "market_only_cohort":
            runner.evaluate_live_market_only_prospective_cohort(
                object(), rows, lambda _keys: pytest.fail("outcome loader must remain lazy")
            )
        else:
            runner.evaluate_live_market_only_from_supabase(object(), rows)

    assert calls == ["rights"]
