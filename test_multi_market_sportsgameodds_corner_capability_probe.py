from datetime import UTC, datetime

import pytest

import multi_market_sportsgameodds_corner_capability_probe as probe

NOW = datetime(2026, 9, 8, 16, 30, tzinfo=UTC)


def _event(*, home="Union Berlin", away="FC Schalke 04", kickoff=None, odds=None, event_id="sgo-target-1"):
    return {
        "eventID": event_id,
        "leagueID": "BUNDESLIGA",
        "startTime": kickoff or probe.TARGET["commence_time_utc"],
        "teams": {
            "home": {"name": home},
            "away": {"name": away},
        },
        "odds": odds or {},
    }


def _payload(*events):
    return {"success": True, "data": list(events)}


def _paired_odds(*, line="9.5", over_odds="-110", under_odds="-105", available=True):
    return {
        probe.CORNER_ODD_IDS[0]: {
            "oddID": probe.CORNER_ODD_IDS[0],
            "bookOddsAvailable": True,
            "bookOverUnder": line,
            "bookOdds": over_odds,
            "byBookmaker": {
                "bet365": {
                    "available": available,
                    "odds": over_odds,
                    "overUnder": line,
                    "lastUpdatedAt": "2026-09-08T16:00:00Z",
                }
            },
        },
        probe.CORNER_ODD_IDS[1]: {
            "oddID": probe.CORNER_ODD_IDS[1],
            "bookOddsAvailable": True,
            "bookOverUnder": line,
            "bookOdds": under_odds,
            "byBookmaker": {
                "bet365": {
                    "available": available,
                    "odds": under_odds,
                    "overUnder": line,
                    "lastUpdatedAt": "2026-09-08T16:00:01Z",
                }
            },
        },
    }


def test_request_is_minimal_fixed_bundesliga_total_corner_query():
    assert probe.PROVIDER == "SPORTSGAMEODDS"
    assert probe.TARGET == {
        "league": "BUNDESLIGA",
        "home_team": "Union Berlin",
        "away_team": "FC Schalke 04",
        "commence_time_utc": "2026-09-11T18:30:00+00:00",
    }
    assert probe.CORNER_ODD_IDS == (
        "cornerKicks-all-game-ou-over",
        "cornerKicks-all-game-ou-under",
    )
    assert probe.build_request_params() == {
        "leagueID": "BUNDESLIGA",
        "oddsAvailable": "true",
        "started": "false",
        "oddID": "cornerKicks-all-game-ou-over,cornerKicks-all-game-ou-under",
        "includeOpposingOdds": "false",
        "includeAltLines": "false",
        "limit": "100",
    }
    assert "apiKey" not in probe.build_request_params()


def test_expired_target_blocks_before_provider_request():
    calls = []
    result = probe.run_probe(
        lambda params: calls.append(params),
        now_utc=datetime(2026, 9, 11, 18, 30, tzinfo=UTC),
    )
    assert result["status"] == "BLOCKED"
    assert result["blocker"] == "PREREGISTERED_TARGET_NOT_PROSPECTIVE"
    assert result["provider_request_attempted"] is False
    assert result["provider_requests"] == 0
    assert result["writes_performed"] is False
    assert calls == []


def test_exact_target_with_paired_available_bookmaker_line_and_prices_confirms_capability():
    calls = []

    def fetch(params):
        calls.append(dict(params))
        return _payload(_event(odds=_paired_odds()))

    result = probe.run_probe(fetch, now_utc=NOW)
    assert result["status"] == "CAPABILITY_CONFIRMED"
    assert result["target_verified"] is True
    assert result["provider_event_id"] == "sgo-target-1"
    assert result["provider_request_attempted"] is True
    assert result["provider_requests"] == 1
    assert result["paired_bookmaker_count"] == 1
    assert result["corner_bookmaker_ids"] == ["bet365"]
    assert result["paired_bookmaker_evidence"] == [{
        "bookmaker_id": "bet365",
        "line": "9.5",
        "over_odds": "-110",
        "under_odds": "-105",
        "over_last_updated_at": "2026-09-08T16:00:00Z",
        "under_last_updated_at": "2026-09-08T16:00:01Z",
    }]
    assert result["writes_performed"] is False
    assert result["external_account_action_performed"] is False
    assert result["subscription_change_performed"] is False
    assert len(calls) == 1


def test_consensus_corner_line_without_bookmaker_evidence_is_not_capability():
    odds = {
        probe.CORNER_ODD_IDS[0]: {
            "oddID": probe.CORNER_ODD_IDS[0],
            "bookOddsAvailable": True,
            "bookOverUnder": "9.5",
            "bookOdds": "-110",
            "byBookmaker": {},
        },
        probe.CORNER_ODD_IDS[1]: {
            "oddID": probe.CORNER_ODD_IDS[1],
            "bookOddsAvailable": True,
            "bookOverUnder": "9.5",
            "bookOdds": "-110",
            "byBookmaker": {},
        },
    }
    result = probe.run_probe(lambda _params: _payload(_event(odds=odds)), now_utc=NOW)
    assert result["status"] == "CAPABILITY_MISS"
    assert result["blocker"] == "BOOKMAKER_CORNER_LINE_PRICE_NOT_FOUND"
    assert result["target_verified"] is True
    assert result["paired_bookmaker_count"] == 0


def test_one_sided_bookmaker_market_is_not_capability():
    odds = _paired_odds()
    odds.pop(probe.CORNER_ODD_IDS[1])
    result = probe.run_probe(lambda _params: _payload(_event(odds=odds)), now_utc=NOW)
    assert result["status"] == "CAPABILITY_MISS"
    assert result["paired_bookmaker_count"] == 0


def test_mismatched_over_under_lines_fail_closed_as_capability_miss():
    odds = _paired_odds()
    odds[probe.CORNER_ODD_IDS[1]]["byBookmaker"]["bet365"]["overUnder"] = "10.5"
    result = probe.run_probe(lambda _params: _payload(_event(odds=odds)), now_utc=NOW)
    assert result["status"] == "CAPABILITY_MISS"
    assert result["paired_bookmaker_count"] == 0


def test_unavailable_bookmaker_is_not_counted():
    result = probe.run_probe(
        lambda _params: _payload(_event(odds=_paired_odds(available=False))),
        now_utc=NOW,
    )
    assert result["status"] == "CAPABILITY_MISS"
    assert result["paired_bookmaker_count"] == 0


def test_exact_target_not_found_is_clean_capability_miss_after_one_request():
    result = probe.run_probe(
        lambda _params: _payload(_event(home="Different Club", odds=_paired_odds())),
        now_utc=NOW,
    )
    assert result["status"] == "CAPABILITY_MISS"
    assert result["blocker"] == "EXACT_TARGET_NOT_FOUND"
    assert result["target_verified"] is False
    assert result["provider_request_attempted"] is True
    assert result["provider_requests"] == 1


def test_provider_team_aliases_are_explicitly_supported_without_fuzzy_matching():
    result = probe.run_probe(
        lambda _params: _payload(_event(home="1. FC Union Berlin", away="Schalke 04", odds=_paired_odds())),
        now_utc=NOW,
    )
    assert result["status"] == "CAPABILITY_CONFIRMED"
    assert result["target_verified"] is True


def test_duplicate_exact_target_identity_fails_closed_and_preserves_attempt_accounting():
    with pytest.raises(probe.ProviderRequestAttemptedError, match="ambiguous") as caught:
        probe.run_probe(
            lambda _params: _payload(
                _event(event_id="sgo-1", odds=_paired_odds()),
                _event(event_id="sgo-2", odds=_paired_odds()),
            ),
            now_utc=NOW,
        )
    assert caught.value.result["provider_request_attempted"] is True
    assert caught.value.result["provider_requests"] == 1
    assert caught.value.result["writes_performed"] is False


def test_provider_error_response_fails_closed_after_one_attempt():
    with pytest.raises(probe.ProviderRequestAttemptedError, match="not entitled") as caught:
        probe.run_probe(
            lambda _params: {"success": False, "error": "not entitled"},
            now_utc=NOW,
        )
    assert caught.value.result["provider_request_attempted"] is True
    assert caught.value.result["provider_requests"] == 1


def test_transport_exception_is_conservatively_accounted_as_one_attempt():
    def fail(_params):
        raise RuntimeError("transport failed")

    with pytest.raises(probe.ProviderRequestAttemptedError, match="transport failed") as caught:
        probe.run_probe(fail, now_utc=NOW)
    assert caught.value.result["provider_request_attempted"] is True
    assert caught.value.result["provider_requests"] == 1


def test_http_fetch_uses_secret_header_not_query_parameter(monkeypatch):
    seen = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": True, "data": []}

    def fake_get(url, *, headers, params, timeout):
        seen.update(url=url, headers=dict(headers), params=dict(params), timeout=timeout)
        return Response()

    monkeypatch.setattr(probe.requests, "get", fake_get)
    params = probe.build_request_params()
    payload = probe.fetch_events("super-secret", params)
    assert payload == {"success": True, "data": []}
    assert seen["url"] == "https://api.sportsgameodds.com/v2/events"
    assert seen["headers"] == {"x-api-key": "super-secret"}
    assert "apiKey" not in seen["params"]
    assert seen["timeout"] == 20
