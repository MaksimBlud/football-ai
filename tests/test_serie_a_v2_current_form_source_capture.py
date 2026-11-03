from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import hashlib

import pandas as pd
import pytest

from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE,
    CURRENT_FILENAME,
    CURRENT_SEASON,
    CURRENT_URL,
    MANIFEST_FILENAME,
    MAX_CURRENT_CSV_BYTES,
    MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
    REQUIRED_COLUMNS,
    capture_source_archive,
    count_unique_completed_primary_events,
    read_completed_primary_event_count,
    read_completed_primary_event_identities,
    validate_current_season_csv,
)
from serie_a_v2_live_diagnostic_report import _source_codes


def event_rows(n=30):
    start = date(2026, 8, 1)
    return [
        {
            "match_date": (start + timedelta(days=i)).isoformat(),
            "home_team": f"Home {i}",
            "away_team": f"Away {i}",
        }
        for i in range(n)
    ]


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.selected = None

    def table(self, _name):
        return self

    def select(self, columns):
        self.selected = columns
        return self

    def eq(self, *_args):
        return self

    def gte(self, *_args):
        return self

    def lt(self, *_args):
        return self

    def range(self, *_args):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


def current_csv(n=30, *, same_day=False, future_unplayed=False, future_completed=False):
    header = ",".join(REQUIRED_COLUMNS)
    rows = []
    start = date(2026, 8, 1)
    for i in range(n):
        day = start + timedelta(days=i)
        rows.append(
            f"{day.strftime('%d/%m/%Y')},Home {i},Away {i},1,0,H,5,3,2,1,0,0"
        )
    if same_day:
        rows.append("18/10/2026,Same Day Home,Same Day Away,1,1,D,4,4,1,1,0,0")
    if future_unplayed:
        rows.append("20/10/2026,Future Home,Future Away,,,,,,,,,")
    if future_completed:
        rows.append("20/10/2026,Future Home,Future Away,1,0,H,4,2,1,0,0,0")
    return (header + "\n" + "\n".join(rows) + "\n").encode()


class StreamResponse:
    def __init__(self, body, *, status_code=200, url=CURRENT_URL, headers=None, chunks=None):
        self.status_code = status_code
        self.url = url
        self.headers = headers if headers is not None else {"Content-Length": str(len(body))}
        self._chunks = list(chunks) if chunks is not None else [body]
        self.iterated = False
        self.closed = False

    def iter_content(self, chunk_size):
        assert chunk_size == 65536
        self.iterated = True
        yield from self._chunks

    def close(self):
        self.closed = True


def test_gate_counts_unique_primary_fixture_metadata_only_and_normalizes_aliases():
    rows = [
        {"match_date": "2026-10-01", "home_team": "Atalanta", "away_team": "Juventus"},
        {"match_date": "2026-10-01", "home_team": "Atalanta BC", "away_team": "Juventus"},
        {"match_date": "2026-10-02", "home_team": "Milan", "away_team": "Inter"},
        {"match_date": "2026-10-19", "home_team": "Roma", "away_team": "Napoli"},
    ]
    assert count_unique_completed_primary_events(
        rows, before_date=date(2026, 10, 18)
    ) == 2


def test_live_feature_gate_query_selects_only_fixture_metadata_not_scores():
    client = FakeQuery(event_rows(30))
    count = read_completed_primary_event_count(
        client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )
    assert count == 30
    assert client.selected == "match_date,home_team,away_team"


def test_current_csv_uses_only_completed_rows_strictly_before_capture_day():
    raw = current_csv(n=30, same_day=True, future_unplayed=True)
    frame, excluded = validate_current_season_csv(
        raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )
    assert len(frame) == 30
    assert set(frame.columns) == set(REQUIRED_COLUMNS)
    assert excluded == 2
    assert not frame["Date"].str.contains("18/10/2026").any()
    assert not frame["Date"].str.contains("20/10/2026").any()


def test_current_csv_rejects_completed_future_result_and_missing_stats():
    with pytest.raises(ValueError, match="completed result after capture date"):
        validate_current_season_csv(
            current_csv(n=30, future_completed=True),
            captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        )
    broken = current_csv(n=30).decode().replace(
        "01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
        "01/08/2026,Home 0,Away 0,1,0,H,,,,,,",
    ).encode()
    with pytest.raises(ValueError, match="missing/invalid HC"):
        validate_current_season_csv(
            broken, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_closed_feature_source_gate_stops_before_any_public_download(tmp_path):
    calls = []
    def forbidden_history(**_kwargs):
        calls.append("old-history")
        raise AssertionError("history must not be downloaded before gate")
    def forbidden_get(*_args, **_kwargs):
        calls.append("current-season")
        raise AssertionError("current source must not be requested before gate")
    with pytest.raises(RuntimeError, match="feature-source gate closed"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS - 1)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )
    assert calls == []


def test_gate_open_captures_11_sources_and_keeps_target_evaluation_closed(tmp_path):
    raw = current_csv(n=30)
    source_times = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
    ])
    def fake_history(*, get, capture_dir):
        audits = []
        for code in _source_codes():
            filename = f"serie_a_{code}.csv"
            body = (
                "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
                f"01/10/{2000 + int(code[:2])},Juventus,Napoli,1,0,H,5,3,2,1,0,0\n"
            ).encode()
            (capture_dir / filename).write_bytes(body)
            audits.append({
                "season_code": code,
                "source_url": f"https://www.football-data.co.uk/mmz4281/{code}/I1.csv",
                "archived_source_name": filename,
                "csv_sha256": hashlib.sha256(body).hexdigest(),
                "source_observed_at_utc": "2026-10-18T08:00:00+00:00",
                "completed_source_rows": 1,
            })
        return pd.DataFrame([{"historical": 1}]), audits

    response = StreamResponse(raw)

    def fake_get(url, **kwargs):
        assert url == CURRENT_URL
        assert kwargs == {"timeout": 30, "stream": True, "allow_redirects": False}
        return response

    report = capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(30)),
        now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        get=fake_get,
        history_fetch=fake_history,
        clock=lambda: next(source_times),
    )
    assert report["feature_source_gate"]["passed"] is True
    assert report["feature_source_gate"]["observed_completed_primary_events"] == 30
    assert report["feature_source_gate"]["score_or_result_fields_selected_for_gate"] is False
    assert report["historical_old_season_file_count"] == 10
    assert report["source_file_count"] == 11
    assert report["current_season_code"] == CURRENT_CODE == "2627"
    assert report["current_season"] == CURRENT_SEASON == "2026-2027"
    assert report["current_season_completed_prior_day_rows"] == 30
    assert report["current_season_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / CURRENT_FILENAME).read_bytes() == raw
    assert (tmp_path / MANIFEST_FILENAME).exists()
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["target_outcome_evaluation_gate"]["outcome_gate_open"] is False
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0
    assert report["model_refit_or_promotion"] is False
    assert response.iterated is True
    assert response.closed is True


def test_production_capture_fails_closed_without_actions_read_token(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = []

    def forbidden_get(*_args, **_kwargs):
        calls.append("public-source")
        raise AssertionError("public CSV requests must not occur without actions:read")

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN with actions:read"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
        )
    assert calls == []


def _injected_history_for_source_capture(*, get, capture_dir):
    audits = []
    for code in _source_codes():
        filename = f"serie_a_{code}.csv"
        body = (
            "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
            f"01/10/{2000 + int(code[:2])},Juventus,Napoli,1,0,H,5,3,2,1,0,0\n"
        ).encode()
        (capture_dir / filename).write_bytes(body)
        audits.append({
            "season_code": code,
            "source_url": f"https://www.football-data.co.uk/mmz4281/{code}/I1.csv",
            "archived_source_name": filename,
            "csv_sha256": hashlib.sha256(body).hexdigest(),
            "source_observed_at_utc": "2026-10-18T08:00:00+00:00",
            "completed_source_rows": 1,
        })
    return pd.DataFrame([{"historical": 1}]), audits


def test_current_source_capture_rejects_redirect_before_reading_body(tmp_path):
    response = StreamResponse(b"unused", status_code=302, headers={"Location": "https://example.invalid/redirect"})

    with pytest.raises(ValueError, match="redirect rejected"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, **kwargs: response,
            history_fetch=_injected_history_for_source_capture,
        )
    assert response.iterated is False
    assert response.closed is True


def test_current_source_capture_rejects_oversized_declared_length_before_body_read(tmp_path):
    response = StreamResponse(b"small", headers={"Content-Length": str(MAX_CURRENT_CSV_BYTES + 1)})

    with pytest.raises(ValueError, match="declared size exceeds"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, **kwargs: response,
            history_fetch=_injected_history_for_source_capture,
        )
    assert response.iterated is False
    assert response.closed is True


def test_current_source_capture_enforces_actual_streamed_byte_limit(tmp_path):
    response = StreamResponse(
        b"x" * (MAX_CURRENT_CSV_BYTES + 1),
        headers={"Content-Length": "1"},
    )

    with pytest.raises(ValueError, match="streamed current-season source exceeds"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, **kwargs: response,
            history_fetch=_injected_history_for_source_capture,
        )
    assert response.iterated is True
    assert response.closed is True


def test_current_form_capture_reuses_verified_historical_archive_when_actions_token_exists(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    raw = current_csv(n=30)
    now = datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    reuse_calls = []
    public_calls = []
    source_times = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
    ])

    def fake_reuse(**kwargs):
        reuse_calls.append(kwargs)
        audits = []
        frames = []
        capture_dir = kwargs["capture_dir"]
        for code in _source_codes():
            year = 2000 + int(code[:2])
            body = (
                "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
                f"01/10/{year},Juventus,Napoli,1,0,H,5,3,2,1,0,0\n"
            ).encode()
            filename = f"serie_a_{code}.csv"
            (capture_dir / filename).write_bytes(body)
            frames.append(pd.read_csv(BytesIO(body)))
            audits.append({
                "season_code": code,
                "source_url": f"https://www.football-data.co.uk/mmz4281/{code}/I1.csv",
                "archived_source_name": filename,
                "csv_sha256": hashlib.sha256(body).hexdigest(),
                "source_observed_at_utc": "2026-10-18T08:00:00+00:00",
                "completed_source_rows": 1,
            })
        provenance = {
            "mode": "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY",
            "source_artifact_id": 123,
            "historical_files_reused": 10,
            "public_historical_csv_requests": 0,
            "current_season_file_reused": False,
            "prior_feature_gate_reused": False,
            "protected_2026_27_source_file_read": False,
            "target_outcomes_read": False,
            "supabase_writes": 0,
            "paid_provider_calls": 0,
        }
        return pd.concat(frames, ignore_index=True), audits, provenance

    response = StreamResponse(raw)

    def fake_current_get(url, **kwargs):
        public_calls.append((url, kwargs))
        assert url == CURRENT_URL
        assert kwargs == {"timeout": 30, "stream": True, "allow_redirects": False}
        return response

    report = capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(30)),
        now=now,
        get=fake_current_get,
        history_fetch_with_provenance=fake_reuse,
        clock=lambda: next(source_times),
    )

    assert len(reuse_calls) == 1
    assert reuse_calls[0]["token"] == "test-token"
    assert reuse_calls[0]["now"] == now
    assert public_calls == [(CURRENT_URL, {"timeout": 30, "stream": True, "allow_redirects": False})]
    assert response.iterated is True
    assert response.closed is True
    assert report["historical_source_reuse"]["mode"] == "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY"
    assert report["historical_source_reuse"]["historical_files_reused"] == 10
    assert report["historical_source_reuse"]["public_historical_csv_requests"] == 0
    assert report["historical_source_reuse"]["current_season_file_reused"] is False
    assert report["source_file_count"] == 11
    assert report["historical_old_season_file_count"] == 10
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False

def test_capture_rejects_current_csv_missing_a_gate_identity_before_archiving_current_member(tmp_path):
    raw = current_csv(n=30).replace(
        b"01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
        b"01/08/2026,Other Home,Away 0,1,0,H,5,3,2,1,0,0",
    )
    response = StreamResponse(raw)
    with pytest.raises(RuntimeError, match="omits 1 completed fixture identities"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda _url, **_kwargs: response,
            history_fetch=_injected_history_for_source_capture,
            clock=lambda: datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        )
    assert response.closed is True
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()

def test_identity_gate_rejects_unrequested_outcome_fields_and_noncanonical_dates():
    outcome_client = FakeQuery([{
        "match_date": "2026-10-01",
        "home_team": "Atalanta",
        "away_team": "Juventus",
        "result": "H",
    }])
    with pytest.raises(ValueError, match="identity-only allowlist"):
        read_completed_primary_event_identities(
            outcome_client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )

    malformed_date_client = FakeQuery([{
        "match_date": "2026-10-01T00:00:00Z",
        "home_team": "Atalanta",
        "away_team": "Juventus",
    }])
    with pytest.raises(ValueError, match="invalid primary event date"):
        read_completed_primary_event_identities(
            malformed_date_client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )

