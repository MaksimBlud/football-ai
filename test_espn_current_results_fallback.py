from datetime import UTC, datetime

import pytest

import espn_current_results_fallback as fallback


class Response:
    def __init__(self, payload, status_code=200, url="https://example.test/scoreboard?dates=x", text=""):
        self._payload = payload
        self.status_code = status_code
        self.url = url
        self.text = text

    def json(self):
        return self._payload


def event(home, away, home_score, away_score, *, completed=True, date="2026-09-06T18:45:00Z"):
    return {
        "date": date,
        "status": {"type": {"completed": completed}},
        "competitions": [
            {
                "competitors": [
                    {"homeAway": "home", "score": str(home_score), "team": {"displayName": home}},
                    {"homeAway": "away", "score": str(away_score), "team": {"displayName": away}},
                ]
            }
        ],
    }


def test_completed_events_become_football_data_like_rows_and_future_is_ignored():
    payload = {
        "events": [
            event("Rayo Vallecano", "Osasuna", 2, 1),
            event("Barcelona", "Real Madrid", 0, 0, completed=False),
        ]
    }
    frame = fallback.build_football_data_like_frame(payload, league="LA_LIGA")
    assert frame.to_dict("records") == [
        {
            "Date": "06/09/2026",
            "HomeTeam": "Vallecano",
            "AwayTeam": "Osasuna",
            "FTHG": 2,
            "FTAG": 1,
            "FTR": "H",
        }
    ]


def test_live_espn_deportivo_name_maps_to_existing_la_liga_identity():
    payload = {"events": [event("Deportivo", "Barcelona", 1, 2)]}
    frame = fallback.build_football_data_like_frame(payload, league="LA_LIGA")
    row = frame.iloc[0]
    assert row["HomeTeam"] == "Dep. A Coruna"
    assert row["AwayTeam"] == "Barcelona"
    assert row["FTR"] == "A"


def test_serie_a_source_names_are_mapped_to_project_compatible_names():
    payload = {"events": [event("Internazionale", "Atalanta", 1, 1)]}
    frame = fallback.build_football_data_like_frame(payload, league="SERIE_A")
    row = frame.iloc[0]
    assert row["HomeTeam"] == "Inter Milan"
    assert row["AwayTeam"] == "Atalanta BC"
    assert row["FTR"] == "D"


def test_completed_event_with_bad_score_fails_closed():
    payload = {"events": [event("Barcelona", "Valencia", "1.5", 0)]}
    with pytest.raises(ValueError, match="invalid home score|non-integer home score"):
        fallback.build_football_data_like_frame(payload, league="LA_LIGA")


def test_conflicting_duplicate_event_fails_closed():
    payload = {
        "events": [
            event("Barcelona", "Valencia", 2, 0),
            event("Barcelona", "Valencia", 3, 0),
        ]
    }
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        fallback.build_football_data_like_frame(payload, league="LA_LIGA")


def test_fetch_is_one_keyless_scoreboard_request_for_current_season_range():
    calls = []

    def get(url, *, params, timeout):
        calls.append((url, params, timeout))
        return Response({"events": [event("Barcelona", "Valencia", 5, 0)]}, url=url + "?dates=" + params["dates"])

    result = fallback.fetch_football_data_like_results(
        league="LA_LIGA",
        now_utc=datetime(2026, 9, 8, 2, 0, tzinfo=UTC),
        get=get,
        sleep=lambda _seconds: None,
    )
    assert result["source_provider"] == "ESPN_SCOREBOARD_FALLBACK"
    assert result["source_competition"] == "esp.1"
    assert result["paid_provider_requests"] == 0
    assert result["public_http_requests"] == 1
    assert result["finished_rows"] == 1
    assert calls == [
        (
            "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
            {"dates": "20260801-20260908"},
            30,
        )
    ]


def test_transient_fallback_http_error_retries_bounded_then_reports_unavailable():
    calls = []

    def get(url, *, params, timeout):
        calls.append((url, params, timeout))
        return Response({}, status_code=503, url=url, text="temporarily unavailable")

    with pytest.raises(fallback.ESPNResultsSourceUnavailable) as caught:
        fallback.fetch_football_data_like_results(
            league="SERIE_A",
            now_utc=datetime(2026, 9, 8, 2, 0, tzinfo=UTC),
            get=get,
            max_attempts=3,
            sleep=lambda _seconds: None,
        )
    assert caught.value.status_code == 503
    assert caught.value.attempts == 3
    assert len(calls) == 3
