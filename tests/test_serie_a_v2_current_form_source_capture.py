from datetime import date, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from types import SimpleNamespace
import hashlib

import pandas as pd
import pytest
import serie_a_v2_current_form_source_capture as source_capture

from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE,
    CURRENT_FILENAME,
    CURRENT_SEASON,
    CURRENT_URL,
    MANIFEST_FILENAME,
    MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
    MAX_CURRENT_CSV_BYTES,
    REQUIRED_COLUMNS,
    capture_source_archive,
    count_unique_completed_primary_events,
    read_completed_primary_event_count,
    read_completed_primary_event_identities,
    validate_current_season_csv,
    _current_source_fixture_identities,
    _fixture_identity_sha256,
)
from serie_a_v2_live_diagnostic_report import _source_codes


@pytest.fixture(autouse=True)
def allow_synthetic_source_capture_scope(monkeypatch):
    """Offline fixtures explicitly stub source rights and private storage only."""
    import market_anchor_v2_source_capture_rights as capture_rights
    import market_anchor_v2_artifact_privacy as privacy

    monkeypatch.setattr(
        capture_rights,
        "require_personal_research_source_capture_scope",
        lambda: {"source_capture_only": True, "scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(
        privacy,
        "require_private_repository_for_source_artifacts",
        lambda: {"private": True, "storage_policy": "SYNTHETIC_TEST_ONLY"},
    )


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


class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "NO_OFFSET"


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


def current_csv(n=30, *, same_day=False, future_unplayed=False, future_completed=False, old_season_completed=False, post_season_completed=False, invalid_past_result=False, missing_date_with_stats=False):
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
    if old_season_completed:
        rows.append("01/05/2026,Old Season Home,Old Season Away,1,0,H,5,3,2,1,0,0")
    if post_season_completed:
        rows.append("01/07/2027,Post Season Home,Post Season Away,1,0,H,5,3,2,1,0,0")
    if invalid_past_result:
        rows.append("15/09/2026,Malformed Home,Malformed Away,1,0,X,5,3,2,1,0,0")
    if missing_date_with_stats:
        rows.append(",Missing Date Home,Missing Date Away,1,0,H,5,3,2,1,0,0")
    return (header + "\n" + "\n".join(rows) + "\n").encode()

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



def test_gate_count_rejects_preseason_metadata_rows():
    with pytest.raises(ValueError, match="pre-season fixture identity"):
        count_unique_completed_primary_events(
            [{"match_date": "2026-06-30", "home_team": "Home", "away_team": "Away"}],
            before_date=date(2026, 10, 18),
        )


def test_gate_count_rejects_postseason_metadata_rows():
    with pytest.raises(ValueError, match="post-season fixture identity"):
        count_unique_completed_primary_events(
            [{"match_date": "2027-07-01", "home_team": "Home", "away_team": "Away"}],
            before_date=date(2027, 8, 1),
        )


def test_gate_count_rejects_reversed_duplicate_after_alias_normalization():
    rows = [
        {"match_date": "2026-08-22", "home_team": "Atalanta BC", "away_team": "Juventus"},
        {"match_date": "2026-08-22", "home_team": "Juventus", "away_team": "Atalanta"},
    ]
    with pytest.raises(ValueError, match="reversed duplicate fixture identity"):
        count_unique_completed_primary_events(rows, before_date=date(2026, 10, 18))


@pytest.mark.parametrize("bad_date", ["2026-10-01T00:00:00Z", "2026-10-01suffix", "20261001"])
def test_gate_count_rejects_noncanonical_metadata_date_strings(bad_date):
    rows = [{
        "match_date": bad_date,
        "home_team": "Home",
        "away_team": "Away",
    }]
    with pytest.raises(ValueError, match="invalid primary event date"):
        count_unique_completed_primary_events(rows, before_date=date(2026, 10, 18))


@pytest.mark.parametrize("bad_date", ["2026-10-01T00:00:00Z", "2026-10-01suffix", "20261001"])
def test_gate_identity_reader_rejects_noncanonical_metadata_date_strings(bad_date):
    client = FakeQuery([{
        "match_date": bad_date,
        "home_team": "Home",
        "away_team": "Away",
    }])
    with pytest.raises(ValueError, match="invalid primary event date"):
        read_completed_primary_event_identities(
            client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


@pytest.mark.parametrize("extra_field", ["result", "home_goals", "score"])
def test_gate_count_rejects_outcome_fields_in_identity_metadata(extra_field):
    row = {
        "match_date": "2026-10-01",
        "home_team": "Home",
        "away_team": "Away",
    }
    row[extra_field] = "H"
    with pytest.raises(ValueError, match="identity-only allowlist"):
        count_unique_completed_primary_events([row], before_date=date(2026, 10, 18))


@pytest.mark.parametrize("extra_field", ["result", "home_goals", "score"])
def test_gate_identity_reader_rejects_outcome_fields_in_supabase_response(extra_field):
    row = {
        "match_date": "2026-10-01",
        "home_team": "Home",
        "away_team": "Away",
    }
    row[extra_field] = "H"
    client = FakeQuery([row])
    with pytest.raises(ValueError, match="identity-only allowlist"):
        read_completed_primary_event_identities(
            client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )

@pytest.mark.parametrize("bad_team", ["Atalanta\tBC", "Atalanta\nBC", "Atalanta\rBC"])
def test_gate_rejects_control_characters_in_team_identity(bad_team):
    rows = [{
        "match_date": "2026-10-01",
        "home_team": bad_team,
        "away_team": "Juventus",
    }]
    with pytest.raises(ValueError, match="control characters"):
        count_unique_completed_primary_events(
            rows, before_date=date(2026, 10, 18)
        )


@pytest.mark.parametrize("bad_team", ["Atalanta\tBC", "Atalanta\nBC", "Atalanta\rBC"])
def test_fixture_identity_sha256_rejects_control_characters_and_preserves_valid_digest(bad_team):
    valid = {("2026-10-01", "Atalanta", "Juventus")}
    expected = hashlib.sha256(b"2026-10-01\tAtalanta\tJuventus").hexdigest()
    assert _fixture_identity_sha256(valid) == expected
    with pytest.raises(ValueError, match="control characters"):
        _fixture_identity_sha256({("2026-10-01", bad_team, "Juventus")})


def test_live_feature_gate_query_selects_only_fixture_metadata_not_scores():
    client = FakeQuery(event_rows(30))
    count = read_completed_primary_event_count(
        client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )
    assert count == 30
    assert client.selected == "match_date,home_team,away_team"


def test_gate_identity_reader_returns_canonical_metadata_only():
    client = FakeQuery([
        {"match_date": "2026-10-01", "home_team": "Atalanta BC", "away_team": "Juventus"},
    ])
    identities = read_completed_primary_event_identities(
        client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )
    assert identities == {("2026-10-01", "Atalanta", "Juventus")}
    assert client.selected == "match_date,home_team,away_team"



def test_gate_identity_reader_rejects_preseason_metadata_rows():
    client = FakeQuery([
        {"match_date": "2026-06-30", "home_team": "Home", "away_team": "Away"},
    ])
    with pytest.raises(ValueError, match="pre-season fixture identity"):
        read_completed_primary_event_identities(
            client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_gate_identity_reader_rejects_postseason_metadata_rows():
    client = FakeQuery([
        {"match_date": "2027-07-01", "home_team": "Home", "away_team": "Away"},
    ])
    with pytest.raises(ValueError, match="post-season fixture identity"):
        read_completed_primary_event_identities(
            client, now=datetime(2027, 8, 1, 8, tzinfo=timezone.utc)
        )


def test_gate_identity_reader_rejects_reversed_duplicate_after_alias_normalization():
    client = FakeQuery([
        {"match_date": "2026-08-22", "home_team": "Atalanta BC", "away_team": "Juventus"},
        {"match_date": "2026-08-22", "home_team": "Juventus", "away_team": "Atalanta"},
    ])
    with pytest.raises(ValueError, match="reversed duplicate fixture identity"):
        read_completed_primary_event_identities(
            client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )

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


@pytest.mark.parametrize(
    "timestamp_date",
    [
        "01/08/2026 00:00:00",
        "01/08/2026 12:30:00",
        "2026-08-01T00:00:00Z",
        "2026-08-01 12:30:00+00:00",
    ],
)
def test_current_csv_rejects_timestamp_dates_before_pandas_normalization(timestamp_date):
    raw = current_csv().decode().replace(
        "01/08/2026,Home 0", f"{timestamp_date},Home 0", 1
    ).encode()
    with pytest.raises(ValueError, match="date-only"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_reversed_duplicate_fixture_identity():
    raw = (
        ",".join(REQUIRED_COLUMNS) + "\n"
        "01/08/2026,Atalanta BC,Juventus,1,0,H,5,3,2,1,0,0\n"
        "01/08/2026,Juventus,Atalanta,0,1,A,4,6,1,2,0,0\n"
    ).encode()
    with pytest.raises(ValueError, match="reversed duplicate fixture identity"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_completed_postseason_row():
    with pytest.raises(ValueError, match="completed row after season end"):
        validate_current_season_csv(
            current_csv(n=30, post_season_completed=True),
            captured_at=datetime(2027, 8, 1, 8, tzinfo=timezone.utc),
        )


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


def test_gate_open_rejects_csv_missing_a_gate_fixture_before_current_source_write(tmp_path):
    raw = current_csv(n=30).replace(
        b"01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
        b"01/08/2026,Other Home,Other Away,1,0,H,5,3,2,1,0,0",
    )
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

    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {"Content-Length": str(len(raw))}

        def __init__(self):
            self.closed = False

        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            yield raw

        def raise_for_status(self):
            return None

        def close(self):
            self.closed = True

    with pytest.raises(RuntimeError, match="omits 1 completed fixture identities"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, timeout, allow_redirects=False, stream=False: Response(),
            history_fetch=fake_history,
            clock=lambda: next(source_times),
        )
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


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

    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {"Content-Length": str(len(raw))}

        def __init__(self):
            self.closed = False

        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            yield raw

        def raise_for_status(self):
            return None

        def close(self):
            self.closed = True

    report = capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(30)),
        now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        get=lambda url, timeout, allow_redirects=False, stream=False: Response(),
        history_fetch=fake_history,
        clock=lambda: next(source_times),
    )
    assert report["feature_source_gate"]["passed"] is True
    assert report["feature_source_gate"]["observed_completed_primary_events"] == 30
    assert report["feature_source_gate"]["score_or_result_fields_selected_for_gate"] is False
    assert report["feature_source_gate"]["gate_fixture_identity_count"] == 30
    assert report["feature_source_gate"]["gate_fixture_identities_covered_by_current_source"] == 30
    assert report["feature_source_gate"]["gate_fixture_identities_missing_from_current_source"] == 0
    assert len(report["feature_source_gate"]["gate_fixture_identity_sha256"]) == 64
    gate_identities = {
        tuple(identity) for identity in report["feature_source_gate"]["gate_fixture_identities"]
    }
    assert len(gate_identities) == 30
    assert report["feature_source_gate"]["gate_fixture_identities"] == [
        list(identity) for identity in sorted(gate_identities)
    ]
    assert _fixture_identity_sha256(gate_identities) == report["feature_source_gate"]["gate_fixture_identity_sha256"]
    assert len(report["feature_source_gate"]["current_source_fixture_identity_sha256"]) == 64
    assert report["historical_old_season_file_count"] == 10
    assert report["source_file_count"] == 11
    assert report["current_season_code"] == CURRENT_CODE == "2627"
    assert report["current_season"] == CURRENT_SEASON == "2026-2027"
    assert report["current_season_completed_prior_day_rows"] == 30
    assert report["current_season_latest_completed_fixture_date"] == "2026-08-30"
    current_audit = next(
        item for item in report["source_files"] if item["season_code"] == CURRENT_CODE
    )
    assert current_audit["latest_completed_fixture_date"] == "2026-08-30"
    assert report["current_season_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / CURRENT_FILENAME).read_bytes() == raw
    assert (tmp_path / MANIFEST_FILENAME).exists()
    assert report["target_outcomes_read"] is False
    assert report["source_capture_only"] is True
    assert report["research_inference_permitted"] is False
    assert report["model_inference_executed"] is False
    assert report["model_training_executed"] is False
    assert report["target_outcomes_scored"] is False
    assert report["target_outcome_evaluation_gate"]["outcome_gate_open"] is False
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0
    assert report["model_refit_or_promotion"] is False


def test_gate_and_current_csv_share_all_configured_team_aliases():
    """Real Serie A source short names must equal canonical metadata identities."""
    metadata = [
        {"match_date": "2026-08-22", "home_team": "Inter Milan", "away_team": "Monza"},
        {"match_date": "2026-08-23", "home_team": "Torino", "away_team": "AC Milan"},
        {"match_date": "2026-08-24", "home_team": "AS Roma", "away_team": "Fiorentina"},
        {"match_date": "2026-08-25", "home_team": "Atalanta", "away_team": "Sassuolo"},
        # Supabase also contains this provider alias for the same canonical event.
        {"match_date": "2026-08-25", "home_team": "Atalanta BC", "away_team": "Sassuolo"},
    ]
    client = FakeQuery(metadata)
    as_of = datetime(2026, 10, 25, 19, 0, tzinfo=timezone.utc)
    gate_identities = read_completed_primary_event_identities(client, now=as_of)
    assert client.selected == "match_date,home_team,away_team"

    raw = (
        ",".join(REQUIRED_COLUMNS) + "\n"
        "22/08/2026,Inter,Monza,1,0,H,5,3,2,1,0,0\n"
        "23/08/2026,Torino,Milan,1,1,D,4,4,1,1,0,0\n"
        "24/08/2026,Roma,Fiorentina,0,2,A,2,5,2,1,0,0\n"
        "25/08/2026,Atalanta,Sassuolo,2,0,H,5,3,2,1,0,0\n"
    ).encode()
    frame, _ = validate_current_season_csv(raw, captured_at=as_of)
    source_identities = _current_source_fixture_identities(frame)

    assert len(gate_identities) == 4
    assert source_identities == gate_identities


def test_gate_count_rejects_timezone_without_real_offset_before_supabase_read():
    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            pytest.fail("Supabase must not be queried with an offsetless gate clock")

    with pytest.raises(ValueError, match="real UTC offset"):
        read_completed_primary_event_count(
            ForbiddenClient(),
            now=datetime(2026, 10, 18, 8, tzinfo=_NoOffsetTimezone()),
        )


def test_current_csv_validator_rejects_timezone_without_real_offset():
    with pytest.raises(ValueError, match="real UTC offset"):
        validate_current_season_csv(
            current_csv(n=MIN_COMPLETED_FEATURE_SOURCE_EVENTS),
            captured_at=datetime(2026, 10, 18, 8, tzinfo=_NoOffsetTimezone()),
        )


def test_source_capture_rejects_timezone_without_real_offset_before_any_io(tmp_path):
    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            pytest.fail("Supabase must not be queried with an offsetless capture clock")

    def forbidden_history(**_kwargs):
        pytest.fail("historical CSVs must not be downloaded with an offsetless capture clock")

    def forbidden_get(*_args, **_kwargs):
        pytest.fail("current-season CSV must not be requested with an offsetless capture clock")

    with pytest.raises(ValueError, match="real UTC offset"):
        capture_source_archive(
            output_dir=tmp_path,
            client=ForbiddenClient(),
            now=datetime(2026, 10, 18, 8, tzinfo=_NoOffsetTimezone()),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )

    assert list(tmp_path.iterdir()) == []


def _valid_fake_history_for_clock_tests():
    audits = [
        {"season_code": code, "csv_sha256": "0" * 64}
        for code in _source_codes()
    ]
    return pd.DataFrame([{"historical": 1}]), audits


def test_source_observation_clock_without_offset_fails_after_body_read_before_write(tmp_path):
    body_read = False

    class Response:
        status_code = 200
        url = CURRENT_URL

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            nonlocal body_read
            assert chunk_size == 64 * 1024
            body_read = True
            yield current_csv(n=MIN_COMPLETED_FEATURE_SOURCE_EVENTS)

        def close(self):
            self.closed = True

    def invalid_clock():
        assert body_read, "observation clock must follow complete response-body consumption"
        return datetime(2026, 10, 18, 8, tzinfo=_NoOffsetTimezone())

    with pytest.raises(ValueError, match="source observation clock must have a real UTC offset"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda *_args, **_kwargs: Response(),
            history_fetch=lambda **_kwargs: _valid_fake_history_for_clock_tests(),
            clock=invalid_clock,
        )

    assert body_read
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_source_observation_timestamp_and_date_cutoff_follow_body_completion(tmp_path):
    raw = current_csv(n=MIN_COMPLETED_FEATURE_SOURCE_EVENTS, same_day=True)
    body_read = False
    source_times = iter([
        datetime(2026, 10, 19, 0, 0, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 19, 0, 0, 2, tzinfo=timezone.utc),
    ])

    class Response:
        status_code = 200
        url = CURRENT_URL

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            nonlocal body_read
            assert chunk_size == 64 * 1024
            body_read = True
            yield raw

        def close(self):
            self.closed = True

    def clock_after_body():
        assert body_read, "source clock must be sampled after the response body is complete"
        return next(source_times)

    report = capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
        now=datetime(2026, 10, 18, 23, 59, 59, tzinfo=timezone.utc),
        get=lambda *_args, **_kwargs: Response(),
        history_fetch=lambda **_kwargs: _valid_fake_history_for_clock_tests(),
        clock=clock_after_body,
    )

    assert body_read
    assert report["current_season_source_observed_at_utc"] == "2026-10-19T00:00:01+00:00"
    assert report["source_archive_created_at_utc"] == "2026-10-19T00:00:02+00:00"
    # The response completed after midnight, so the prior UTC day is available
    # to the source validator; the gate itself remains the earlier metadata-only snapshot.
    assert report["current_season_completed_prior_day_rows"] == MIN_COMPLETED_FEATURE_SOURCE_EVENTS + 1
    assert (tmp_path / MANIFEST_FILENAME).exists()


def test_archive_creation_clock_without_offset_fails_before_current_source_write(tmp_path):
    clocks = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=_NoOffsetTimezone()),
    ])

    class Response:
        status_code = 200
        url = CURRENT_URL
        body = current_csv(n=MIN_COMPLETED_FEATURE_SOURCE_EVENTS)
        headers = {"Content-Length": str(len(body))}

        def __init__(self):
            self.closed = False

        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            yield self.body

        def raise_for_status(self):
            return None

        def close(self):
            self.closed = True

    with pytest.raises(ValueError, match="source archive creation clock must have a real UTC offset"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda *_args, **_kwargs: Response(),
            history_fetch=lambda **_kwargs: _valid_fake_history_for_clock_tests(),
            clock=lambda: next(clocks),
        )

    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_frozen_candidate_is_verified_before_gate_reads_or_source_requests(monkeypatch, tmp_path):
    calls = []
    client = FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS))

    def reject_candidate():
        calls.append("candidate")
        raise ValueError("frozen V2 candidate integrity failure")

    def forbidden_history(**_kwargs):
        calls.append("history")
        raise AssertionError("historical sources must not be downloaded for an invalid candidate")

    def forbidden_get(*_args, **_kwargs):
        calls.append("http")
        raise AssertionError("current-season source must not be requested for an invalid candidate")

    monkeypatch.setattr(source_capture, "_verify_frozen_candidate_contract_pin", reject_candidate)
    with pytest.raises(ValueError, match="frozen V2 candidate integrity failure"):
        capture_source_archive(
            output_dir=tmp_path,
            client=client,
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )

    assert calls == ["candidate"]
    assert client.selected is None
    assert list(tmp_path.iterdir()) == []


def _fake_history_for_redirect_test(capture_dir):
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


def test_current_source_url_must_be_exact_approved_https_before_gate_reads(monkeypatch, tmp_path):
    monkeypatch.setattr(source_capture, "CURRENT_URL", "https://evil.example/2627/I1.csv")
    client = FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS))

    def forbidden_history(**_kwargs):
        raise AssertionError("unapproved current URL must be rejected before historical downloads")

    def forbidden_get(*_args, **_kwargs):
        raise AssertionError("unapproved current URL must be rejected before HTTP request")

    with pytest.raises(ValueError, match="approved HTTPS Football-Data URL"):
        capture_source_archive(
            output_dir=tmp_path,
            client=client,
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )

    assert client.selected is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("status_code", "final_url", "message"),
    [
        (302, CURRENT_URL, "direct HTTP 200"),
        (200, "https://evil.example/2627/I1.csv", "response URL differs"),
    ],
)
def test_current_source_redirect_or_final_url_mismatch_fails_before_body_access(
    tmp_path, status_code, final_url, message
):
    class Response:
        url = final_url
        headers = {}

        def __init__(self):
            self.status_code = status_code
            self.closed = False
            self.iter_content_called = False

        def iter_content(self, chunk_size):
            self.iter_content_called = True
            raise AssertionError("unapproved response body must never be read")

        def raise_for_status(self):
            raise AssertionError("response must be rejected before raise_for_status")

        def close(self):
            self.closed = True

    requests_seen = []

    def fake_get(url, *, timeout, allow_redirects, stream):
        requests_seen.append((url, timeout, allow_redirects, stream))
        return Response()

    with pytest.raises(ValueError, match=message):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=fake_get,
            history_fetch=lambda **kwargs: _fake_history_for_redirect_test(kwargs["capture_dir"]),
        )

    assert requests_seen == [(CURRENT_URL, 30, False, True)]
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()



def test_current_source_rejects_oversized_content_length_before_reading_body(tmp_path):
    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {"Content-Length": str(MAX_CURRENT_CSV_BYTES + 1)}

        def __init__(self):
            self.closed = False
            self.iter_content_called = False

        def iter_content(self, chunk_size):
            self.iter_content_called = True
            yield b"must-not-be-read"

        def raise_for_status(self):
            return None

        def close(self):
            self.closed = True

    response = Response()
    requests_seen = []

    def fake_get(url, *, timeout, allow_redirects, stream):
        requests_seen.append((url, timeout, allow_redirects, stream))
        return response

    with pytest.raises(ValueError, match="exceeds size limit"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=fake_get,
            history_fetch=lambda **kwargs: _fake_history_for_redirect_test(kwargs["capture_dir"]),
            clock=lambda: pytest.fail("clock must not be sampled before body completion"),
        )

    assert requests_seen == [(CURRENT_URL, 30, False, True)]
    assert response.iter_content_called is False
    assert response.closed is True
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


@pytest.mark.parametrize(
    "declared_length",
    ["+1", "1.0", "١", "-1", "", "1e0"],
)
def test_current_source_rejects_non_ascii_or_non_decimal_content_length_before_body_read(
    tmp_path, declared_length
):
    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {"Content-Length": declared_length}

        def __init__(self):
            self.closed = False
            self.iter_content_called = False

        def iter_content(self, chunk_size):
            self.iter_content_called = True
            yield b"must-not-be-read"

        def raise_for_status(self):
            return None

        def close(self):
            self.closed = True

    response = Response()

    with pytest.raises(ValueError, match="invalid Content-Length"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, timeout, allow_redirects=False, stream=False: response,
            history_fetch=lambda **kwargs: _fake_history_for_redirect_test(kwargs["capture_dir"]),
            clock=lambda: pytest.fail("clock must not be sampled before body completion"),
        )

    assert response.iter_content_called is False
    assert response.closed is True
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_current_source_stream_enforces_actual_byte_limit_and_closes_early(tmp_path):
    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {}

        def __init__(self):
            self.closed = False
            self.chunks_yielded = 0

        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            self.chunks_yielded += 1
            yield b"x" * (MAX_CURRENT_CSV_BYTES + 1)
            self.chunks_yielded += 1
            yield b"must-not-be-consumed"

        def raise_for_status(self):
            return None

        def close(self):
            self.closed = True

    response = Response()
    with pytest.raises(ValueError, match="exceeds size limit"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, timeout, allow_redirects=False, stream=False: response,
            history_fetch=lambda **kwargs: _fake_history_for_redirect_test(kwargs["capture_dir"]),
        )

    assert response.chunks_yielded == 1
    assert response.closed is True
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()



def test_current_csv_rejects_completed_row_before_current_season_start():
    with pytest.raises(ValueError, match="before season start"):
        validate_current_season_csv(
            current_csv(n=30, old_season_completed=True),
            captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        )


@pytest.mark.parametrize(
    ("original", "replacement", "field"),
    [
        (
            "01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
            "01/08/2026,Home 0,Away 0,1.5,0,H,5,3,2,1,0,0",
            "FTHG",
        ),
        (
            "01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
            "01/08/2026,Home 0,Away 0,1,0,H,5.5,3,2,1,0,0",
            "HC",
        ),
    ],
)
def test_current_csv_rejects_non_integer_goal_and_stat_counts(original, replacement, field):
    raw = current_csv(n=30).decode().replace(original, replacement, 1).encode()
    with pytest.raises(ValueError, match=f"non-integer {field}"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_past_statistics_with_invalid_result_marker():
    with pytest.raises(ValueError, match="statistics but invalid full-time result marker"):
        validate_current_season_csv(
            current_csv(n=30, invalid_past_result=True),
            captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        )


def test_current_csv_rejects_populated_row_without_fixture_date():
    with pytest.raises(ValueError, match="populated fixture row without date"):
        validate_current_season_csv(
            current_csv(n=30, missing_date_with_stats=True),
            captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        )

@pytest.mark.parametrize(
    ("clock_values", "expected_error"),
    [
        (
            [
                datetime(2026, 10, 18, 7, 59, tzinfo=timezone.utc),
                datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
            ],
            "source observation timestamp precedes feature-source gate check",
        ),
        (
            [
                datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
                datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
            ],
            "source archive creation timestamp precedes source observation",
        ),
    ],
)
def test_capture_rejects_reversed_gate_source_archive_clock_order(tmp_path, clock_values, expected_error):
    """Clock rollback must not produce a manifest with false source chronology."""
    raw = current_csv(n=MIN_COMPLETED_FEATURE_SOURCE_EVENTS)
    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {}
        def __init__(self):
            self.closed = False
            self.body_complete = False
        def raise_for_status(self):
            return None
        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            self.body_complete = True
            yield raw
        def close(self):
            self.closed = True
    response = Response()
    clocks = iter(clock_values)
    with pytest.raises(ValueError, match=expected_error):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(MIN_COMPLETED_FEATURE_SOURCE_EVENTS)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda *_args, **_kwargs: response,
            history_fetch=lambda **_kwargs: _valid_fake_history_for_clock_tests(),
            clock=lambda: next(clocks),
        )
    assert response.body_complete is True
    assert response.closed is True
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_source_gate_allows_extra_current_csv_identities_when_every_gate_identity_is_covered(tmp_path):
    """The CSV may contain fixtures persisted after the identity-only gate snapshot."""
    raw = current_csv(n=31)

    def fake_history(*, get, capture_dir):
        audits = []
        for code in _source_codes():
            filename = f"serie_a_{code}.csv"
            body = (
                "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\\n"
                f"01/10/{2000 + int(code[:2])},Juventus,Napoli,1,0,H,5,3,2,1,0,0\\n"
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

    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {"Content-Length": str(len(raw))}

        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            yield raw

        def raise_for_status(self):
            return None

        def close(self):
            return None

    source_times = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
    ])
    report = capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(30)),
        now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        get=lambda *_args, **_kwargs: Response(),
        history_fetch=fake_history,
        clock=lambda: next(source_times),
    )

    gate = report["feature_source_gate"]
    assert gate["gate_fixture_identity_count"] == 30
    assert gate["gate_fixture_identities_covered_by_current_source"] == 30
    assert gate["gate_fixture_identities_missing_from_current_source"] == 0
    assert gate["current_source_fixture_identity_count"] == 31
    assert gate["passed"] is True
    assert report["current_season_completed_prior_day_rows"] == 31
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False


def test_source_capture_push_runs_offline_validation_without_download_job():
    workflow_path = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/serie-a-v2-current-form-source-capture.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")
    assert "validate-source-capture:" in workflow
    assert "if: github.event_name == 'push'" in workflow
    assert "capture-current-form:" in workflow
    capture_job = workflow.split("  capture-current-form:\n", 1)[1].split("\n    runs-on:", 1)[0]
    assert "github.event_name != 'push'" in capture_job
    assert "github.ref == 'refs/heads/main'" in capture_job
    validator_job = workflow.split("  validate-source-capture:\n", 1)[1].split("\n  capture-current-form:\n", 1)[0]
    assert "SUPABASE_URL" not in validator_job
    assert "SUPABASE_KEY" not in validator_job
    assert "GITHUB_TOKEN" not in validator_job
    assert "Check shared public-source download budget" in workflow
    assert "Capture frozen historical seasons plus gated current-form source" in workflow



def _atomic_source_capture_inputs(raw):
    def fake_history(*, get, capture_dir):
        audits = []
        for code in _source_codes():
            filename = f"serie_a_{code}.csv"
            body = (
                "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\\n"
                f"01/10/{2000 + int(code[:2])},Juventus,Napoli,1,0,H,5,3,2,1,0,0\\n"
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

    class Response:
        status_code = 200
        url = CURRENT_URL
        headers = {"Content-Length": str(len(raw))}

        def iter_content(self, chunk_size):
            assert chunk_size == 64 * 1024
            yield raw

        def raise_for_status(self):
            return None

        def close(self):
            return None

    return (
        FakeQuery(event_rows(30)),
        lambda _url, timeout, allow_redirects, stream: Response(),
        fake_history,
    )


@pytest.mark.parametrize(
    ("clock_values", "message"),
    [
        (
            [
                datetime(2026, 10, 18, 8, 1),
                datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
            ],
            "source observation clock must have a real UTC offset",
        ),
        (
            [
                datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
                datetime(2026, 10, 18, 8, 2),
            ],
            "source archive creation clock must have a real UTC offset",
        ),
        (
            [
                datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
                datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
            ],
            "source archive creation timestamp precedes source observation",
        ),
    ],
)
def test_atomic_source_capture_rejects_ambiguous_or_reversed_clocks_without_partial_archive(
    tmp_path, clock_values, message
):
    raw = current_csv(n=30)
    client, get, history_fetch = _atomic_source_capture_inputs(raw)
    values = iter(clock_values)
    output_dir = tmp_path / "current-form-source"

    with pytest.raises(ValueError, match=message):
        capture_source_archive(
            output_dir=output_dir,
            client=client,
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=get,
            history_fetch=history_fetch,
            clock=lambda: next(values),
        )

    assert not output_dir.exists()
    assert not list(tmp_path.glob(".current-form-source.staging-*"))


def test_atomic_source_capture_refuses_nonempty_output_before_metadata_or_source_reads(tmp_path):
    output_dir = tmp_path / "existing-source"
    output_dir.mkdir()
    sentinel = output_dir / "preserve.txt"
    sentinel.write_text("prior evidence", encoding="utf-8")
    calls = []

    def forbidden_history(**_kwargs):
        calls.append("history")
        raise AssertionError("history must not be read for an occupied output directory")

    def forbidden_get(*_args, **_kwargs):
        calls.append("http")
        raise AssertionError("HTTP must not run for an occupied output directory")

    client = FakeQuery(event_rows(30))
    with pytest.raises(FileExistsError, match="absent or empty"):
        capture_source_archive(
            output_dir=output_dir,
            client=client,
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )

    assert sentinel.read_text(encoding="utf-8") == "prior evidence"
    assert client.selected is None
    assert calls == []


def test_atomic_source_capture_publishes_complete_archive_as_one_directory(tmp_path):
    raw = current_csv(n=30)
    client, get, history_fetch = _atomic_source_capture_inputs(raw)
    output_dir = tmp_path / "complete-source"
    source_times = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
    ])

    report = capture_source_archive(
        output_dir=output_dir,
        client=client,
        now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        get=get,
        history_fetch=history_fetch,
        clock=lambda: next(source_times),
    )

    assert report["source_file_count"] == 11
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["supabase_writes"] == 0
    assert len(list(output_dir.glob("serie_a_*.csv"))) == 11
    assert (output_dir / MANIFEST_FILENAME).is_file()
    assert len(list(output_dir.iterdir())) == 12
    assert not list(tmp_path.glob(".complete-source.staging-*"))

def test_source_only_candidate_contract_pin_does_not_load_model_weights(monkeypatch):
    import serie_a_v2_frozen_shadow_preview as frozen

    monkeypatch.setattr(
        frozen,
        "load_verified_original",
        lambda: pytest.fail("source-only capture must not load model weights or run inference validation"),
    )
    assert source_capture._verify_frozen_candidate_contract_pin() == source_capture.FROZEN_SHA
