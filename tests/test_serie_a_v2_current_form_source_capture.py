from datetime import date, datetime, timedelta, timezone, tzinfo
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
    MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
    REQUIRED_COLUMNS,
    capture_source_archive,
    count_unique_completed_primary_events,
    read_completed_primary_event_count,
    read_completed_primary_event_identities,
    validate_current_season_csv,
    _current_source_fixture_identities,
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


def test_gate_count_rejects_reversed_duplicate_after_alias_normalization():
    rows = [
        {"match_date": "2026-08-22", "home_team": "Atalanta BC", "away_team": "Juventus"},
        {"match_date": "2026-08-22", "home_team": "Juventus", "away_team": "Atalanta"},
    ]
    with pytest.raises(ValueError, match="reversed duplicate fixture identity"):
        count_unique_completed_primary_events(rows, before_date=date(2026, 10, 18))

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


def test_current_csv_rejects_reversed_duplicate_fixture_identity():
    raw = (
        ",".join(REQUIRED_COLUMNS) + "\n"
        "01/08/2026,Atalanta BC,Juventus,1,0,H,5,3,2,1,0,0\n"
        "01/08/2026,Juventus,Atalanta,0,1,A,4,6,1,2,0,0\n"
    ).encode()
    with pytest.raises(ValueError, match="reversed duplicate fixture identities"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
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
        content = raw
        def raise_for_status(self):
            return None

    with pytest.raises(RuntimeError, match="omits 1 completed fixture identities"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda url, timeout: Response(),
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
        content = raw
        def raise_for_status(self):
            return None

    report = capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(30)),
        now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        get=lambda url, timeout: Response(),
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
    assert len(report["feature_source_gate"]["current_source_fixture_identity_sha256"]) == 64
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
