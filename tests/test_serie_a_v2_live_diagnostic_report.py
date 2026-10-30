"""Tests for actual historical-source + stored-market, always research-only."""
from datetime import datetime, timezone, tzinfo

import pandas as pd
import pytest
import serie_a_v2_live_diagnostic_report as report_module

from serie_a_v2_live_diagnostic_report import (
    PUBLIC_BASE, _source_codes, fetch_public_history, make_report,
    MAX_HISTORICAL_CSV_BYTES, MAX_HISTORICAL_TOTAL_BYTES,
)

NOW = datetime(2026,10,13,15,1,tzinfo=timezone.utc)


def history_fixture():
    rows = []
    for date, home, away, home_goals, away_goals, result in [
        ("10/10/2025","Inter Milan","Genoa",2,0,"H"),
        ("11/10/2025","Napoli","Lecce",1,1,"D"),
        ("13/10/2025","Inter Milan","Lecce",4,0,"H"),
    ]:
        rows.append({
            "Date":date, "HomeTeam":home, "AwayTeam":away,
            "FTHG":home_goals,"FTAG":away_goals,"FTR":result,
            "HC":5,"AC":4,"HY":2,"AY":1,"HR":0,"AR":0,
        })
    return pd.DataFrame(rows)


def quote():
    return {
        "league":"SERIE_A","event_id":"real-research-fixture-1",
        "home_team":"Inter Milan","away_team":"Napoli",
        "commence_time_utc":"2026-10-19T19:00:00Z",
        "snapshot_time_utc":"2026-10-13T14:00:00Z",
        "home_odds":1.8,"draw_odds":3.9,"away_odds":5.0,
    }


def source_audit(observed_at="2026-10-13T15:00:00Z"):
    return [{
        "season_code": code,
        "source_url": f"{PUBLIC_BASE}/{code}/I1.csv",
        "archived_source_name": f"serie_a_{code}.csv",
        "source_observed_at_utc": observed_at,
        "csv_sha256": "f" * 64,
        "completed_source_rows": 3,
    } for code in _source_codes()]


def test_historical_source_rejects_oversized_content_length_before_body_read(tmp_path):
    class Response:
        status_code = 200
        headers = {"Content-Length": str(MAX_HISTORICAL_CSV_BYTES + 1)}
        def __init__(self, url):
            self.url = url
            self.closed = False
            self.body_read = False
        def iter_content(self, chunk_size):
            self.body_read = True
            yield b"must-not-be-read"
        def close(self):
            self.closed = True

    response = None
    def fake_get(url, timeout, allow_redirects, stream):
        nonlocal response
        assert stream is True and allow_redirects is False
        response = Response(url)
        return response

    with pytest.raises(RuntimeError, match="exceeds size limit"):
        fetch_public_history(get=fake_get, capture_dir=tmp_path)

    assert response is not None
    assert response.body_read is False
    assert response.closed is True
    assert list(tmp_path.glob("*.csv")) == []


def test_historical_source_stops_on_actual_streamed_byte_limit_and_closes(tmp_path):
    class Response:
        status_code = 200
        headers = {}
        def __init__(self, url):
            self.url = url
            self.closed = False
            self.chunks_yielded = 0
        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            self.chunks_yielded += 1
            yield b"x" * (MAX_HISTORICAL_CSV_BYTES + 1)
            self.chunks_yielded += 1
            yield b"must-not-be-consumed"
        def close(self):
            self.closed = True

    response = None
    def fake_get(url, timeout, allow_redirects, stream):
        nonlocal response
        assert stream is True and allow_redirects is False
        response = Response(url)
        return response

    with pytest.raises(RuntimeError, match="exceeds size limit"):
        fetch_public_history(get=fake_get, capture_dir=tmp_path)

    assert response is not None
    assert response.chunks_yielded == 1
    assert response.closed is True
    assert list(tmp_path.glob("*.csv")) == []







def test_historical_source_collection_stops_stream_at_remaining_aggregate_budget(tmp_path, monkeypatch):
    csv_completed = history_fixture().to_csv(index=False).encode()
    monkeypatch.setattr(
        report_module, "MAX_HISTORICAL_TOTAL_BYTES", len(csv_completed) + 1
    )

    class Response:
        status_code = 200
        headers = {}
        def __init__(self, url, chunks):
            self.url = url
            self.chunks = list(chunks)
            self.chunks_yielded = 0
            self.closed = False
        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            for chunk in self.chunks:
                self.chunks_yielded += 1
                yield chunk
        def close(self):
            self.closed = True

    responses = []
    def fake_get(url, timeout, allow_redirects, stream):
        assert allow_redirects is False and stream is True
        chunks = [csv_completed] if not responses else [b"xx", b"must-not-be-consumed"]
        response = Response(url, chunks)
        responses.append(response)
        return response

    with pytest.raises(RuntimeError, match="total size limit"):
        fetch_public_history(get=fake_get, capture_dir=tmp_path)

    assert len(responses) == 2
    assert responses[0].chunks_yielded == 1
    assert responses[1].chunks_yielded == 1
    assert all(response.closed for response in responses)
    assert len(list(tmp_path.glob("*.csv"))) == 1

def test_historical_source_collection_enforces_total_archive_byte_limit(tmp_path, monkeypatch):
    csv_completed = history_fixture().to_csv(index=False).encode()
    monkeypatch.setattr(
        report_module, "MAX_HISTORICAL_TOTAL_BYTES", len(csv_completed) + 1
    )

    class Response:
        status_code = 200
        headers = {"Content-Length": str(len(csv_completed))}
        def __init__(self, url):
            self.url = url
            self.closed = False
        def iter_content(self, chunk_size):
            yield csv_completed
        def close(self):
            self.closed = True

    responses = []
    def fake_get(url, timeout, allow_redirects, stream):
        assert stream is True and allow_redirects is False
        response = Response(url)
        responses.append(response)
        return response

    with pytest.raises(RuntimeError, match="total size limit"):
        fetch_public_history(get=fake_get, capture_dir=tmp_path)

    assert len(responses) == 2
    assert all(response.closed for response in responses)
    # First CSV is within the total budget; the second would exceed it and is
    # rejected before it can be persisted.
    assert len(list(tmp_path.glob("*.csv"))) == 1



def test_real_frozen_model_diagnostic_never_relabels_later_source_as_prospective():
    report = make_report([quote()], history_fixture(),source_audit(),as_of_utc=NOW)
    assert report["diagnostic_scored"]==1
    assert report["feature_count"]==19
    assert report["quotes_with_source_observed_after_quote"]==1
    assert report["paid_provider_requests"]==report["supabase_writes"]==0
    assert report["independently_attested_feature_availability_at_quote"] is False
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["eligible_for_product_publication"] is False
    assert report["no_bet"] is True
    assert report["protect_2026_27_prospective_outcomes"] is True
    assert report["2026_27_public_results_downloaded"] is False
    assert report["history_stale_without_2026_27_form"] is True
    row = report["diagnostic_previews"][0]
    assert row["market_1x2"]==pytest.approx(row["active_market_fallback_1x2"])
    assert row["model_candidate_sha256"]==report["frozen_candidate_sha256"]


def test_injected_2026_27_results_are_rejected_before_v2_prediction():
    modified = history_fixture()
    modified.loc[2, "Date"] = "13/10/2026"
    with pytest.raises(ValueError, match="protected Serie A 2026/27 outcomes"):
        make_report([quote()], modified, source_audit(), as_of_utc=NOW)


def test_injected_protected_season_audit_rejected_without_source_use():
    bad_audit = source_audit()
    bad_audit[-1] = {**bad_audit[-1], "season_code": "2627",
                     "source_url": f"{PUBLIC_BASE}/2627/I1.csv",
                     "archived_source_name": "serie_a_2627.csv"}
    with pytest.raises(ValueError, match="protected or duplicate season"):
        make_report([quote()], history_fixture(), bad_audit, as_of_utc=NOW)


def test_missing_or_forged_source_audit_fails_closed():
    with pytest.raises(ValueError, match="exact pre-freeze seasons"):
        make_report([quote()], history_fixture(), source_audit()[:-1], as_of_utc=NOW)
    bad = source_audit()
    bad[0]["csv_sha256"] = "bad"
    with pytest.raises(ValueError, match="invalid SHA256"):
        make_report([quote()], history_fixture(), bad, as_of_utc=NOW)
    wrong_url = source_audit()
    wrong_url[0]["source_url"] = "https://example.invalid/1617/I1.csv"
    with pytest.raises(ValueError, match="unexpected URL"):
        make_report([quote()], history_fixture(), wrong_url, as_of_utc=NOW)


def test_future_source_observation_is_not_claimed_as_known():
    with pytest.raises(ValueError, match="observation in the future"):
        make_report([quote()], history_fixture(),
                    source_audit("2026-10-14T15:00:00Z"), as_of_utc=NOW)


def test_first_protected_2026_27_day_is_an_excluded_result():
    modified = history_fixture()
    modified.loc[0, "Date"] = "01/07/2026"
    with pytest.raises(ValueError, match="protected Serie A 2026/27 outcomes"):
        make_report([quote()], modified, source_audit(), as_of_utc=NOW)


def test_missing_source_stats_fail_closed_and_do_not_impute_fake_history():
    with pytest.raises(ValueError,match="required football stats"):
        make_report([quote()],history_fixture().drop(columns=["HC"]),source_audit(),as_of_utc=NOW)


def test_public_free_history_never_downloads_protected_2026_27_outcomes():
    # The current-season CSV includes frozen-prospective outcomes and must
    # NOT be fetched, even if its rows might later be filtered in-memory.
    current = "2627"
    assert current not in _source_codes()
    assert len(_source_codes()) == 10
    csv_completed = history_fixture().to_csv(index=False).encode()
    calls = []
    class Response:
        status_code = 200
        headers = {"Content-Length": str(len(csv_completed))}
        def __init__(self, url):
            self.url = url
            self.closed = False
        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            yield csv_completed
        def close(self):
            self.closed = True
    responses = []
    def fake_get(url, timeout, allow_redirects, stream):
        calls.append((url, timeout, allow_redirects, stream))
        assert url.startswith(PUBLIC_BASE + "/") and url.endswith("/I1.csv")
        assert f"/{current}/" not in url
        assert allow_redirects is False
        assert stream is True
        response = Response(url)
        responses.append(response)
        return response
    history, audit = fetch_public_history(get=fake_get)
    assert len(calls) == 10
    assert all(call[2] is False and call[3] is True for call in calls)
    assert all(response.closed for response in responses)
    assert len(audit) == len(calls)
    assert len(history) == 3*len(calls)
    assert all(x["csv_sha256"] and x["source_observed_at_utc"] for x in audit)


def test_upstream_status_failure_is_not_filled_with_guessed_data():
    class BadResponse:
        status_code = 503
        url = "https://www.football-data.co.uk/mmz4281/1617/I1.csv"
        content = b""
    with pytest.raises(RuntimeError, match="unavailable"):
        fetch_public_history(get=lambda url, timeout, allow_redirects, stream: BadResponse())


def test_public_history_rejects_redirect_before_reading_response_bytes():
    calls = []
    class RedirectResponse:
        status_code = 302
        url = "https://www.football-data.co.uk/mmz4281/1617/I1.csv"
        def iter_content(self, chunk_size):
            raise AssertionError("redirect body must not be read")
        def close(self):
            pass
    def fake_get(url, timeout, allow_redirects, stream):
        calls.append((url, allow_redirects, stream))
        return RedirectResponse()
    with pytest.raises(RuntimeError, match="unavailable"):
        fetch_public_history(get=fake_get)
    assert calls and all(allow_redirects is False and stream is True for _, allow_redirects, stream in calls)


def test_public_history_rejects_unexpected_final_url_before_reading_response_bytes():
    class WrongFinalURL:
        status_code = 200
        url = "https://example.invalid/attacker.csv"
        @property
        def content(self):
            raise AssertionError("unexpected final URL bytes must not be read")
    with pytest.raises(RuntimeError, match="unexpected final URL"):
        fetch_public_history(
            get=lambda url, timeout, allow_redirects, stream: WrongFinalURL()
        )


def test_public_history_rejects_unapproved_source_endpoint_before_network(monkeypatch):
    calls = []
    monkeypatch.setattr(report_module, "PUBLIC_BASE", "http://example.invalid/mmz4281")
    with pytest.raises(ValueError, match="approved HTTPS Football-Data endpoint"):
        fetch_public_history(
            get=lambda url, timeout, allow_redirects, stream: calls.append(url)
        )
    assert calls == []



def test_real_quote_diagnostic_distinguishes_original_v2_partial_imputation():
    report = make_report([quote()], history_fixture(), source_audit(), as_of_utc=NOW)
    assert report["feature_rows_with_missing_values"] == 1
    assert report["feature_rows_all_median_imputed"] == 0
    assert report["feature_rows_with_all_19_observed"] == 0
    coverage = report["per_fixture_feature_coverage"][0]
    assert coverage["event_id"] == quote()["event_id"]
    assert coverage["observed_frozen_feature_count"] > 0
    assert coverage["observed_frozen_feature_count"] < 19
    assert coverage["median_imputed_frozen_feature_count"] + coverage["observed_frozen_feature_count"] == 19
    assert report["diagnostic_previews"][0]["median_imputed_frozen_feature_count"] == coverage["median_imputed_frozen_feature_count"]
    assert report["diagnostic_previews"][0]["no_bet"] is True


def test_real_quote_diagnostic_refuses_both_teams_without_prior_match_history():
    unseen = {**quote(), "home_team": "Unseen Home", "away_team": "Unseen Away"}
    report = make_report([unseen], history_fixture(), source_audit(), as_of_utc=NOW)
    assert report["quoted_fixtures"] == 1
    assert report["feature_rows_with_missing_values"] == 1
    assert report["feature_rows_all_median_imputed"] == 1
    assert report["diagnostic_scored"] == 0
    assert report["diagnostic_blocked"]["ALL_FEATURES_MEDIAN_IMPUTED"] == 1
    assert report["per_fixture_feature_coverage"][0]["observed_frozen_feature_count"] == 0
    assert report["no_bet"] is True
    assert report["supabase_writes"] == report["paid_provider_requests"] == 0

class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "NO_OFFSET"


def test_live_diagnostic_rejects_offsetless_clock_before_feature_build():
    invalid_clock = datetime(2026, 10, 13, 15, 1, tzinfo=_NoOffsetTimezone())
    with pytest.raises(ValueError, match="as-of timestamp needs UTC timezone"):
        make_report([], history_fixture(), [{}], as_of_utc=invalid_clock)

@pytest.mark.parametrize(
    "redirect_kind",
    ["cross_origin", "https_downgrade", "path_change", "query_added", "credentials", "nonstandard_port"],
)
def test_historical_source_final_url_mutations_fail_before_body_read_or_csv_write(tmp_path, redirect_kind):
    """Each source URL mutation must fail before reading bytes or persisting a CSV."""
    body_reads = []

    class MutatedResponse:
        status_code = 200
        headers = {}

        def __init__(self, url):
            self.url = url

        def iter_content(self, chunk_size):
            body_reads.append(self.url)
            raise AssertionError("unapproved final response body must not be read")

        def close(self):
            pass

    def fake_get(url, timeout, allow_redirects, stream):
        assert allow_redirects is False
        assert stream is True
        if redirect_kind == "cross_origin":
            final_url = url.replace("www.football-data.co.uk", "attacker.invalid")
        elif redirect_kind == "https_downgrade":
            final_url = url.replace("https://", "http://", 1)
        elif redirect_kind == "path_change":
            final_url = url.replace("/I1.csv", "/other.csv")
        elif redirect_kind == "query_added":
            final_url = url + "?redirected=1"
        elif redirect_kind == "credentials":
            final_url = url.replace("https://", "https://user@")
        else:
            final_url = url.replace("www.football-data.co.uk", "www.football-data.co.uk:444")
        return MutatedResponse(final_url)

    with pytest.raises(RuntimeError, match="unexpected final URL"):
        fetch_public_history(get=fake_get, capture_dir=tmp_path)
    assert body_reads == []
    assert list(tmp_path.glob("*.csv")) == []

