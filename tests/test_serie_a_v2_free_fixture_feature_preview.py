from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from historical_football_signal_lab import FEATURE_SETS
from serie_a_v2_free_fixture_feature_preview import (
    EVENTS_URL,
    FROZEN_SHA,
    SPORT_KEY,
    _validated_future_events,
    build_feature_readiness_preview,
    capture_free_fixture_preview,
)

UTC = timezone.utc
STARTED = datetime(2026, 10, 28, 10, 2, tzinfo=UTC)
RECEIVED = datetime(2026, 10, 28, 10, 3, tzinfo=UTC)
API_KEY = "test-secret-must-never-be-serialized"


def source_attestation(**overrides):
    result = {
        "verified": True,
        "fresh_for_new_quote": True,
        "candidate_sha256": FROZEN_SHA,
        "artifact_id": 12345,
        "artifact_sha256": "a" * 64,
        "source_archive_created_at_utc": "2026-10-28T10:00:00Z",
        "latest_source_observed_at_utc": "2026-10-28T09:59:00Z",
        "parent_run": {
            "run_id": 54321,
            "run_head_sha": "b" * 40,
            "run_completed_at_utc": "2026-10-28T10:01:00Z",
        },
    }
    result.update(overrides)
    return result


def history_frame():
    rows = []
    first = datetime(2026, 8, 1)
    for index in range(40):
        day = first + timedelta(days=index)
        if index % 2 == 0:
            home, away, hg, ag, result = "Home FC", f"Opponent {index}", 2, 1, "H"
        else:
            home, away, hg, ag, result = f"Opponent {index}", "Away FC", 0, 1, "A"
        rows.append({
            "Date": day.strftime("%d/%m/%Y"),
            "HomeTeam": home,
            "AwayTeam": away,
            "FTHG": hg,
            "FTAG": ag,
            "FTR": result,
            "HC": 4 + index % 3,
            "AC": 2 + index % 2,
            "HY": index % 2,
            "AY": (index + 1) % 2,
            "HR": 0,
            "AR": 0,
        })
    # Same-day history must be excluded because the historical source is date-only.
    rows.append({
        "Date": "28/10/2026",
        "HomeTeam": "Home FC",
        "AwayTeam": "Same Day Opponent",
        "FTHG": 1,
        "FTAG": 0,
        "FTR": "H",
        "HC": 8,
        "AC": 0,
        "HY": 0,
        "AY": 0,
        "HR": 0,
        "AR": 0,
    })
    return pd.DataFrame(rows)


def event(event_id="serie-a-event-1", **overrides):
    item = {
        "id": event_id,
        "sport_key": SPORT_KEY,
        "sport_title": "Serie A",
        "commence_time": "2026-10-30T18:45:00Z",
        "home_team": "Home FC",
        "away_team": "Away FC",
    }
    item.update(overrides)
    return item


def response_for(payload, *, cost="0", status=200, history=()):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    url = EVENTS_URL + "?apiKey=REDACTED&dateFormat=iso"
    return SimpleNamespace(
        status_code=status,
        headers={"x-requests-last": cost} if cost is not None else {},
        content=raw,
        url=url,
        history=history,
        json=lambda: payload,
    )


def test_source_gate_and_order_fail_before_provider_request():
    calls = []
    with pytest.raises(ValueError, match="stale"):
        capture_free_fixture_preview(
            api_key=API_KEY,
            source_attestation=source_attestation(fresh_for_new_quote=False),
            history=history_frame(),
            request_started_at=STARTED,
            get=lambda *a, **k: calls.append((a, k)),
            clock=lambda: RECEIVED,
        )
    assert calls == []

    bad = source_attestation(
        source_archive_created_at_utc="2026-10-28T10:04:00Z"
    )
    with pytest.raises(ValueError, match="finish before"):
        capture_free_fixture_preview(
            api_key=API_KEY,
            source_attestation=bad,
            history=history_frame(),
            request_started_at=STARTED,
            get=lambda *a, **k: calls.append((a, k)),
            clock=lambda: RECEIVED,
        )
    assert calls == []


def test_exactly_one_zero_credit_events_request_and_original_19_features_only():
    payload = [event()]
    response = response_for(payload)
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return response

    report = capture_free_fixture_preview(
        api_key=API_KEY,
        source_attestation=source_attestation(),
        history=history_frame(),
        request_started_at=STARTED,
        get=fake_get,
        clock=lambda: RECEIVED,
    )

    assert len(calls) == 1
    assert calls[0][0] == EVENTS_URL
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][1]["timeout"] == 20
    assert calls[0][1]["params"]["apiKey"] == API_KEY
    assert calls[0][1]["params"]["dateFormat"] == "iso"
    assert report["status"] == "CAPTURED"
    assert report["provider_last_request_cost_credits"] == 0
    assert report["provider_response_sha256"] == hashlib.sha256(response.content).hexdigest()
    assert report["future_fixture_count"] == 1
    assert report["feature_count"] == 19
    assert report["candidate_sha256"] == FROZEN_SHA
    assert report["feature_builder_git_blob_sha1"] == "401b3a0893371bfa4a488ec92a4a54af2678c8f7"
    assert report["model_probabilities_emitted"] is False
    assert report["market_quotes_read"] is False
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["production_pkl_touched"] is False
    assert report["supabase_writes"] == 0
    manifest = report["feature_manifests"][0]
    assert set(manifest["features"]) == set(FEATURE_SETS["ALL_FOOTBALL"])
    assert len(manifest["features"]) == 19
    assert manifest["history_coverage"]["home"]["prior_matches_in_frozen_30_match_window"] == 20
    assert manifest["median_imputed_frozen_feature_count"] + manifest["observed_frozen_feature_count"] == 19
    assert API_KEY not in json.dumps(report)


@pytest.mark.parametrize("cost", ["1", "2", None, "not-a-number"])
def test_nonzero_or_unattested_provider_cost_fails_closed(cost):
    calls = []
    response = response_for([event()], cost=cost)
    with pytest.raises(ValueError, match="quota cost|zero-credit"):
        capture_free_fixture_preview(
            api_key=API_KEY,
            source_attestation=source_attestation(),
            history=history_frame(),
            request_started_at=STARTED,
            get=lambda *a, **k: (calls.append((a, k)) or response),
            clock=lambda: RECEIVED,
        )
    assert len(calls) == 1


def test_redirect_or_non_200_response_fails_closed():
    redirected = response_for([event()], history=(object(),))
    with pytest.raises(ValueError, match="redirect"):
        capture_free_fixture_preview(
            api_key=API_KEY,
            source_attestation=source_attestation(),
            history=history_frame(),
            request_started_at=STARTED,
            get=lambda *a, **k: redirected,
            clock=lambda: RECEIVED,
        )
    not_ok = response_for([], status=302)
    with pytest.raises(RuntimeError, match="HTTP 302"):
        capture_free_fixture_preview(
            api_key=API_KEY,
            source_attestation=source_attestation(),
            history=history_frame(),
            request_started_at=STARTED,
            get=lambda *a, **k: not_ok,
            clock=lambda: RECEIVED,
        )


def test_provider_odds_or_outcome_fields_are_rejected():
    with pytest.raises(ValueError, match="non-metadata"):
        _validated_future_events([event(home_score=2)], observed_at=RECEIVED)
    with pytest.raises(ValueError, match="non-metadata"):
        _validated_future_events([event(bookmakers=[])], observed_at=RECEIVED)


def test_duplicate_canonical_fixture_identity_is_rejected_even_with_different_ids():
    second = event(event_id="different-provider-id")
    with pytest.raises(ValueError, match="duplicate future event identity"):
        _validated_future_events([event(), second], observed_at=RECEIVED)


def test_in_play_events_are_excluded_and_empty_future_list_is_valid():
    live = event(event_id="live", commence_time="2026-10-28T10:02:30Z")
    future = event()
    selected = _validated_future_events([live, future], observed_at=RECEIVED)
    assert [row["event_id"] for row in selected] == ["serie-a-event-1"]
    assert _validated_future_events([live], observed_at=RECEIVED) == []


def test_feature_readiness_uses_date_only_cutoff_and_never_emits_probabilities():
    report = build_feature_readiness_preview(
        history_frame(),
        [{
            "event_id": "serie-a-event-1",
            "home_team": "Home FC",
            "away_team": "Away FC",
            "commence_time_utc": "2026-10-30T18:45:00Z",
        }],
        as_of_utc=STARTED,
    )
    row = report["feature_manifests"][0]
    assert row["feature_history_cutoff_utc"] == "2026-10-28T00:00:00+00:00"
    assert row["history_coverage"]["home"]["prior_matches_in_frozen_30_match_window"] == 20
    assert report["feature_count"] == 19
    assert report["model_probabilities_emitted"] is False
    assert "brier_score" not in json.dumps(report).lower()
    assert "log_loss" not in json.dumps(report).lower()
