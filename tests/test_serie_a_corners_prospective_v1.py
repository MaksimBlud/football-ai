import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pandas as pd

import serie_a_corners_prospective_v1 as s


def _fixture(
    fixture_id: int,
    kickoff: str,
    *,
    status: str = "scheduled",
    home: str = "Inter",
    away: str = "Milan",
):
    return {
        "id": fixture_id,
        "league": {"id": int(s.LEAGUE_ID), "name": "Serie A"},
        "teams": {
            "home": {"name": home},
            "away": {"name": away},
        },
        "kickoff_utc": kickoff,
        "status": status,
    }


def test_frozen_contract_constants():
    assert s.EXPERIMENT_ID == "SERIE_A_CORNERS_PROSPECTIVE_V1"
    assert s.TARGET_ELIGIBLE_ROWS == 30
    assert s.BLEND_WEIGHT_FOOTBALL == 0.25
    assert s.MAX_PROVIDER_REQUESTS == 20
    assert s.REQUEST_INTERVAL_SECONDS >= 3.0
    assert s.MIN_PREMATCH_LEAD_HOURS == 6
    assert str(s.PROSPECTIVE_START_UTC) == "2026-09-19 00:00:00+00:00"


def test_select_scheduled_enforces_start_lead_and_horizon():
    captured = pd.Timestamp("2026-09-18T12:00:00Z")
    payload = {
        "success": 1,
        "data": [
            _fixture(1, "2026-09-18T16:00:00Z"),  # < 6h lead and pre-start
            _fixture(2, "2026-09-19T00:00:00Z"),  # valid
            _fixture(3, "2026-10-04T00:00:00Z"),  # beyond 14d
            _fixture(4, "2026-09-20T00:00:00Z", status="finished"),
        ],
    }
    rows = s.select_scheduled(payload, captured_at=captured)
    assert [row["fixture_id"] for row in rows] == ["2"]


def test_opening_corner_row_is_prematch_and_bet365_only():
    captured = pd.Timestamp("2026-09-18T12:00:00Z")
    fixture = {
        "fixture_id": "10",
        "league": s.LEAGUE,
        "league_id": s.LEAGUE_ID,
        "kickoff_utc": "2026-09-20T12:00:00Z",
        "home_team": "Inter",
        "away_team": "Milan",
    }
    payload = {
        "success": 1,
        "data": {
            "bookmakers": [
                {
                    "slug": "bet365",
                    "odds": {
                        "corner_line": {
                            "opening": {"line": 9.5, "over": 1.91, "under": 1.89}
                        }
                    },
                }
            ]
        },
    }
    row = s.opening_corner_row(payload, fixture, captured_at=captured)
    assert row is not None
    assert row["opening_line"] == 9.5
    assert row["capture_lead_hours"] == 48.0
    assert row["finished"] is False


def test_opening_corner_row_rejects_too_late_capture():
    fixture = {
        "fixture_id": "11",
        "league": s.LEAGUE,
        "league_id": s.LEAGUE_ID,
        "kickoff_utc": "2026-09-20T12:00:00Z",
        "home_team": "Inter",
        "away_team": "Milan",
    }
    payload = {
        "success": 1,
        "data": {
            "bookmakers": [
                {
                    "slug": "bet365",
                    "odds": {
                        "corner_line": {
                            "opening": {"line": 10.0, "over": 1.9, "under": 1.9}
                        }
                    },
                }
            ]
        },
    }
    assert (
        s.opening_corner_row(
            payload,
            fixture,
            captured_at=pd.Timestamp("2026-09-20T08:00:00Z"),
        )
        is None
    )


def test_merge_results_never_replaces_opening_market():
    ledger = [
        {
            "fixture_id": "12",
            "kickoff_utc": "2026-09-20T12:00:00Z",
            "opening_line": 9.5,
            "opening_over": 1.91,
            "opening_under": 1.89,
            "finished": False,
        }
    ]
    merged = s.merge_results(
        ledger,
        {
            "12": {
                "fixture_id": "12",
                "home_corners": 6.0,
                "away_corners": 5.0,
                "total_corners": 11.0,
            }
        },
    )
    assert merged[0]["opening_line"] == 9.5
    assert merged[0]["opening_over"] == 1.91
    assert merged[0]["finished"] is True
    assert merged[0]["total_corners"] == 11.0


def test_sealed_state_makes_zero_provider_requests(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        json.dumps(
            {
                "fixture_id": "13",
                "kickoff_utc": "2026-09-20T12:00:00Z",
                "finished": True,
            }
        )
        + "\n"
    )
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"sealed": True, "sealed_verdict": "NOT_REPLICATED"}))

    monkeypatch.delenv(s.KEY_ENV, raising=False)
    report = s.collect(
        output_dir=tmp_path / "out",
        ledger_in=ledger,
        state_in=state,
        now=datetime(2026, 9, 21, tzinfo=UTC),
    )
    assert report["status"] == "SEALED"
    assert report["provider_requests"] == 0


def test_verdict_gate_is_frozen():
    assert (
        s._decide_verdict(
            market_brier=0.25,
            blend_brier=0.24,
            market_logloss=0.69,
            blend_logloss=0.68,
            alignment=0.02,
            ci_low=0.001,
        )
        == "REPLICATED_SIGNAL_SCREEN"
    )
    assert (
        s._decide_verdict(
            market_brier=0.25,
            blend_brier=0.24,
            market_logloss=0.69,
            blend_logloss=0.68,
            alignment=0.02,
            ci_low=-0.003,
        )
        == "INDICATIVE_NOT_CONFIRMED"
    )
    assert (
        s._decide_verdict(
            market_brier=0.25,
            blend_brier=0.251,
            market_logloss=0.69,
            blend_logloss=0.68,
            alignment=0.02,
            ci_low=0.001,
        )
        == "NOT_REPLICATED"
    )


def test_evaluate_keeps_metrics_sealed_before_30(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger_path.write_text(
        json.dumps(
            {
                "fixture_id": "99",
                "league": s.LEAGUE,
                "league_id": s.LEAGUE_ID,
                "kickoff_utc": "2026-09-20T12:00:00Z",
                "home_team": "Inter",
                "away_team": "Milan",
                "opening_line": 9.5,
                "opening_over": 1.9,
                "opening_under": 1.9,
                "captured_at_utc": "2026-09-19T00:00:00Z",
                "finished": True,
                "home_corners": 6,
                "away_corners": 5,
                "total_corners": 11,
            }
        )
        + "\n"
    )
    current = tmp_path / "finished.json"
    current.write_text(json.dumps({"success": 1, "data": [{"id": 99}]}))

    synthetic_features = pd.DataFrame(
        [
            {
                "season": s.CURRENT_SEASON,
                "fixture_id": "99",
                "home_prior_matches": 20,
                "away_prior_matches": 20,
                "total_corners": 11,
            }
        ]
    )
    monkeypatch.setattr(s, "_current_fixture_row", lambda raw: {"fixture_id": "99"})
    monkeypatch.setattr(s, "load_serie_a_history", lambda _: pd.DataFrame())
    monkeypatch.setattr(
        s.frozen,
        "_build_features",
        lambda history, current_rows, league: synthetic_features,
    )
    monkeypatch.setattr(
        s.frozen,
        "_fit_models",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("model metrics must remain sealed before gate")
        ),
    )

    report = s.evaluate(
        output_dir=tmp_path / "out",
        ledger_path=ledger_path,
        history_dir=tmp_path,
        current_fixtures_json=current,
    )
    assert report["status"] == "COLLECTING"
    assert report["eligible_finished_rows"] == 1
    assert report["confirmatory_metrics_opened"] is False
    assert "market" not in report
    assert "blend25" not in report
