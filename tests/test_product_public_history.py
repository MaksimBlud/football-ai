"""Public EPL historical statistics: fail-closed provenance and privacy regression."""
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from product_public_history import (
    LIFECYCLE_COLUMNS,
    PUBLIC_SCHEMA,
    build_public_product_history,
    load_public_product_history,
)


NOW = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)
MODEL_A = "a" * 64
MODEL_B = "b" * 64
PROBS = (0.6, 0.25, 0.15)


def lifecycle_pair(snapshot_id=1, *, model=MODEL_A, league="EPL",
                   actual="HOME", kickoff=None, match_id=None):
    kickoff = kickoff or datetime(2026, 9, 20, 14, tzinfo=timezone.utc)
    match_id = match_id or f"epl-event-{snapshot_id}"
    one_hot = [1.0 if index == ["HOME", "DRAW", "AWAY"].index(actual) else 0.0 for index in range(3)]
    brier = sum((p - y) ** 2 for p, y in zip(PROBS, one_hot))
    log_loss = -math.log(PROBS[["HOME", "DRAW", "AWAY"].index(actual)])
    base = {
        "source_prediction_snapshot_id": snapshot_id,
        "event_id": f"secret-provider-id-{snapshot_id}",
        "product_match_id": match_id,
        "league": league,
        "commence_time_utc": kickoff.isoformat(),
        "source_prediction_created_at_utc": (kickoff - timedelta(days=2)).isoformat(),
        "recorded_at_utc": (kickoff + timedelta(hours=3)).isoformat(),
    }
    return [
        {
            **base,
            "id": 1000 + snapshot_id * 2,
            "event_type": "PREDICTION_REGISTERED",
            "payload": {
                "registration_mode": "legacy_source_snapshot_bootstrap",
                "prediction": {
                    "home_probability": PROBS[0],
                    "draw_probability": PROBS[1],
                    "away_probability": PROBS[2],
                    "model_1x2_version": "FROZEN_EPL_1X2",
                    "model_1x2_sha256": model,
                },
            },
        },
        {
            **base,
            "id": 1001 + snapshot_id * 2,
            "event_type": "SETTLED",
            "payload": {
                "settlement_scope": "1x2_model_probability",
                "actual_outcome": actual,
                "model_pick": "HOME",
                "model_pick_probability": PROBS[0],
                "prediction_correct": actual == "HOME",
                "multiclass_brier": brier,
                "log_loss": log_loss,
            },
        },
    ]


def single(*overrides):
    return build_public_product_history(lifecycle_pair(**overrides), now_utc=NOW)


def test_empty_history_is_not_fake_accuracy():
    report = build_public_product_history([], now_utc=NOW)
    assert report["schema_version"] == PUBLIC_SCHEMA
    assert report["settled_unique_fixtures"] == 0
    assert report["model_scopes"] == []
    assert report["events"]["settled"] == 0
    assert report["policy"]["reliability_verdict"] == "INCONCLUSIVE"
    assert report["policy"]["roi"] is None


def test_one_verified_product_settlement_has_reproducible_descriptive_metrics():
    report = single()
    row = report["model_scopes"][0]
    assert report["settled_unique_fixtures"] == 1
    assert report["events"] == {
        "prediction_registered": 1, "market_observed": 0, "settled": 1,
    }
    assert row["model_1x2_sha256"] == MODEL_A
    assert row["settled_unique_fixtures"] == 1
    assert row["correct_picks"] == 1
    assert row["accuracy"] == 1.0
    assert row["multiclass_brier"] == pytest.approx(0.245)
    assert row["log_loss"] == pytest.approx(-math.log(0.6))
    assert row["evidence_state"] == "ACCUMULATING_SAMPLE"
    assert row["reviewable"] is False
    assert row["reliability_status"] == "INCONCLUSIVE"
    assert row["accuracy_wilson_95"]["lower"] < 1


def test_private_rows_never_appear_in_public_json():
    report = single()
    output = json.dumps(report)
    for private_field in (
        "secret-provider-id", "epl-event-1", "source_prediction_snapshot_id",
        "actual_outcome", "prediction_correct", "payload",
        "home_probability", "market_home_prob", "registration_mode",
    ):
        assert private_field not in output
    assert '"betting_action": "NO_BET"' in output
    assert '"roi": null' in output
    assert '"clv": null' in output
    assert '"staking": null' in output
    assert report["policy"]["includes_market_only_research"] is False


def test_market_observed_is_not_counted_as_correct_model_prediction():
    events = lifecycle_pair()
    market_event = dict(events[0])
    market_event.update({
        "id": 9876, "event_type": "MARKET_OBSERVED",
        "payload": {"private_bookmaker_quote": 14.3},
    })
    report = build_public_product_history(events + [market_event], now_utc=NOW)
    assert report["events"]["market_observed"] == 1
    assert report["events"]["settled"] == 1
    assert report["settled_unique_fixtures"] == 1


def test_unknown_future_non_epl_products_are_not_mixed_into_epl_history():
    events = lifecycle_pair()
    # Even if a public product adds Serie A one day, it must not alter EPL.
    events.extend(lifecycle_pair(2, league="Serie A"))
    report = build_public_product_history(events, now_utc=NOW)
    assert report["settled_unique_fixtures"] == 1
    assert len(report["model_scopes"]) == 1
    assert report["league"] == "EPL"


def test_changed_model_sha_is_never_pooled_into_one_scope():
    events = lifecycle_pair()
    events.extend(lifecycle_pair(2, model=MODEL_B))
    report = build_public_product_history(events, now_utc=NOW)
    assert report["settled_unique_fixtures"] == 2
    assert len(report["model_scopes"]) == 2
    assert all(scope["settled_unique_fixtures"] == 1 for scope in report["model_scopes"])
    assert all(scope["evidence_state"] == "ACCUMULATING_SAMPLE" for scope in report["model_scopes"])


def test_frozen_sample_and_time_review_gates_remain_unchanged():
    start = datetime(2026, 1, 1, 14, tzinfo=timezone.utc)
    events = []
    for index in range(100):
        events.extend(lifecycle_pair(index + 1, kickoff=start + timedelta(days=2 * index),
                                     actual="HOME" if index % 2 else "AWAY"))
    report = build_public_product_history(events, now_utc=NOW)
    scope = report["model_scopes"][0]
    assert scope["settled_unique_fixtures"] == 100
    assert scope["reviewable"] is True
    assert scope["evidence_state"] == "REVIEWABLE"
    # REVIEWABLE is an evidence gate, never an automatic proof of accuracy/ROI.
    assert scope["reliability_status"] == "INCONCLUSIVE"
    assert report["policy"]["reliability_verdict"] == "INCONCLUSIVE"


def test_duplicate_fixture_across_two_snapshots_fails_closed():
    events = lifecycle_pair(1, match_id="same-immutable-product-fixture")
    events.extend(lifecycle_pair(2, match_id="same-immutable-product-fixture"))
    with pytest.raises(ValueError, match="duplicate.*fixture"):
        build_public_product_history(events, now_utc=NOW)


def test_duplicate_settlement_fails_closed():
    events = lifecycle_pair()
    extra = dict(events[1], id=5555)
    with pytest.raises(ValueError, match="multiple SETTLED"):
        build_public_product_history(events + [extra], now_utc=NOW)


def test_missing_registration_fails_closed():
    with pytest.raises(ValueError, match="no PREDICTION_REGISTERED"):
        build_public_product_history([lifecycle_pair()[1]], now_utc=NOW)


def test_changed_settlement_metrics_fail_closed():
    events = lifecycle_pair()
    events[1]["payload"]["log_loss"] = 0.001
    with pytest.raises(ValueError, match="disagrees"):
        build_public_product_history(events, now_utc=NOW)


def test_invalid_model_sha_never_published():
    events = lifecycle_pair()
    events[0]["payload"]["prediction"]["model_1x2_sha256"] = "not-the-pinned-model"
    with pytest.raises(ValueError, match="provenance"):
        build_public_product_history(events, now_utc=NOW)


def test_future_source_fact_or_postkickoff_registration_rejected():
    events = lifecycle_pair()
    events[0]["recorded_at_utc"] = (NOW + timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError, match="future lifecycle"):
        build_public_product_history(events, now_utc=NOW)
    events = lifecycle_pair()
    events[0]["source_prediction_created_at_utc"] = events[0]["commence_time_utc"]
    with pytest.raises(ValueError, match="non-prekickoff"):
        build_public_product_history(events, now_utc=NOW)


def test_missing_timestamp_is_a_failure_not_an_empty_history():
    events = lifecycle_pair()
    events[0].pop("recorded_at_utc")
    with pytest.raises((KeyError, ValueError, TypeError)):
        build_public_product_history(events, now_utc=NOW)


def test_duplicate_internal_event_id_fails_closed():
    events = lifecycle_pair()
    events[1]["id"] = events[0]["id"]
    with pytest.raises(ValueError, match="duplicate lifecycle"):
        build_public_product_history(events, now_utc=NOW)


class _FakeQuery:
    def __init__(self, rows, tracker):
        self.rows = rows
        self.tracker = tracker
        self.first = 0
        self.last = len(rows) - 1

    def select(self, columns):
        self.tracker.append(("select", columns))
        return self

    def order(self, column):
        assert column == "id"
        return self

    def range(self, first, last):
        self.tracker.append(("range", first, last))
        self.first = first
        self.last = last
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows[self.first:self.last + 1])


class _FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.tables = []
        self.calls = []

    def table(self, name):
        self.tables.append(name)
        assert name == "product_prediction_lifecycle_events"
        return _FakeQuery(self.rows, self.calls)


def test_loader_reads_only_private_lifecycle_and_never_results_or_research_tables():
    client = _FakeClient(lifecycle_pair())
    report = load_public_product_history(client, now_utc=NOW)
    assert report["settled_unique_fixtures"] == 1
    assert client.tables == ["product_prediction_lifecycle_events"]
    assert client.calls[0] == ("select", LIFECYCLE_COLUMNS)
    assert "*" not in LIFECYCLE_COLUMNS
    assert ("range", 0, 499) in client.calls


def test_loader_uses_bounded_pagination_and_does_not_truncate_records():
    # Simulate >500 source events without changing scoring.
    registrations = []
    for i in range(501):
        registration = lifecycle_pair(i + 1)[0]
        registration["id"] = 5000 + i
        registrations.append(registration)
    client = _FakeClient(registrations)
    report = load_public_product_history(client, now_utc=NOW)
    assert report["events"]["prediction_registered"] == 501
    assert report["events"]["settled"] == 0
    assert client.calls.count(("range", 0, 499)) == 1
    assert ("range", 500, 999) in client.calls


def test_loader_refuses_saturated_10000_event_page_budget():
    records = [dict(lifecycle_pair()[0], id=100000 + i) for i in range(10000)]
    with pytest.raises(ValueError, match="bounded"):
        load_public_product_history(_FakeClient(records), now_utc=NOW)


def test_web_history_requires_private_server_key_and_uses_generic_503():
    app = Path("web_app.py").read_text(encoding="utf-8")
    assert "def _private_lifecycle_client():" in app
    assert "str(SUPABASE_KEY).startswith(\"sb_publishable_\")" in app
    assert "SUPABASE_KEY == SUPABASE_PUBLISHABLE_KEY" in app
    assert "return create_client(SUPABASE_URL, SUPABASE_KEY)" in app
    assert '@app.get("/history")' in app
    assert '@app.get("/product-history")' in app
    assert "return load_public_product_history(_private_lifecycle_client())" in app
    assert "status_code=503" in app


def test_frontend_does_not_claim_roi_or_model_reliability():
    html = Path("static/history.html").read_text(encoding="utf-8")
    index = Path("static/index_v2.html").read_text(encoding="utf-8")
    assert 'href="/history"' in index
    assert "fetch('/product-history',{cache:'no-store'})" in html
    assert "data.policy?.reliability_verdict!=='INCONCLUSIVE'" in html
    assert "data.policy?.betting_action!=='NO_BET'" in html
    assert "data.policy?.roi!==null" in html
    assert 'textContent=' in html
    assert "document.createElement('p')" in html
    assert "Никаких вымышленных ставок" in html
    assert "временно недоступна" in html
    assert "INCONCLUSIVE" in html


def test_history_inline_javascript_parses_with_node_if_available(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("node unavailable")
    html = Path("static/history.html").read_text(encoding="utf-8")
    result = re.search(r"<script>(.*?)</script>", html, re.S)
    assert result
    source = tmp_path / "history.js"
    source.write_text(result.group(1), encoding="utf-8")
    checked = subprocess.run(["node", "--check", str(source)], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
