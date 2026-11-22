from datetime import date, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import sys

import pandas as pd
import pytest

from market_anchor_1x2_v2_shadow import FIRST_OUTCOME_READ_GATE, outcome_read_permitted

import market_anchor_v2_artifact_privacy as artifact_privacy
import market_anchor_v2_direct_access as direct_access
import serie_a_v2_current_form_source_capture as source_capture

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
    validate_current_season_csv,
    validate_preregistered_outcome_read_gate,
)
from serie_a_v2_live_diagnostic_report import _source_codes


def _synthetic_source_capture_access():
    return {
        "access_scope": "SOURCE_CAPTURE_ONLY",
        "rights": {
            "provider": "Football-Data.co.uk",
            "scope_status": "GRANTED",
            "rights_manifest_sha256": "a" * 64,
            "authorization_evidence_sha256": "b" * 64,
        },
        "artifact_privacy": {
            "repository": "MaksimBlud/football-ai",
            "private": True,
            "storage_policy": "PRIVATE_GITHUB_ACTIONS_ARTIFACTS",
        },
    }


class NoOffsetTZ(tzinfo):
    """tzinfo object that is not actually aware because utcoffset is None."""

    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "no-offset"


@pytest.fixture(autouse=True)
def _allow_synthetic_source_capture_rights(monkeypatch):
    """Only offline tests receive a synthetic grant; repository manifest remains HOLD."""
    monkeypatch.setattr(
        source_capture,
        "require_v2_source_capture_access",
        _synthetic_source_capture_access,
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


def test_live_feature_gate_query_selects_only_fixture_metadata_not_scores():
    client = FakeQuery(event_rows(30))
    count = read_completed_primary_event_count(
        client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )
    assert count == 30
    assert client.selected == "match_date,home_team,away_team"


def test_feature_gate_rejects_tzinfo_without_utc_offset_before_supabase_read():
    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            raise AssertionError("Supabase must not be queried with a non-aware gate clock")

    now = datetime(2026, 10, 18, 8, tzinfo=NoOffsetTZ())
    assert now.tzinfo is not None and now.utcoffset() is None
    with pytest.raises(ValueError, match="feature-source gate clock must be timezone-aware"):
        read_completed_primary_event_count(ForbiddenClient(), now=now)


def test_feature_source_gate_is_exactly_the_preregistered_v2_outcome_read_gate():
    protocol_path = Path(__file__).resolve().parents[1] / "experiments" / "market_anchor_1x2_v2_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert FIRST_OUTCOME_READ_GATE == 30
    assert MIN_COMPLETED_FEATURE_SOURCE_EVENTS == FIRST_OUTCOME_READ_GATE
    assert protocol["first_outcome_read_gate"]["completed_primary_events"] == FIRST_OUTCOME_READ_GATE
    assert protocol["first_outcome_read_gate"]["outcome_read_before_gate"] is False
    assert protocol["primary_cohort"]["league"] == "SERIE_A"
    assert protocol["primary_cohort"]["other_leagues_count_toward_gate"] is False
    assert outcome_read_permitted(29) is False
    assert outcome_read_permitted(30) is True
    contract = validate_preregistered_outcome_read_gate()
    assert contract["protocol_blob_sha1"] == source_capture.PREREGISTERED_PROTOCOL_BLOB_SHA1
    assert contract["required_completed_primary_events"] == 30


def test_current_season_csv_rejects_tzinfo_without_utc_offset():
    captured_at = datetime(2026, 10, 18, 8, tzinfo=NoOffsetTZ())
    assert captured_at.tzinfo is not None and captured_at.utcoffset() is None
    with pytest.raises(ValueError, match="current-season source capture clock must be timezone-aware"):
        validate_current_season_csv(current_csv(30), captured_at=captured_at)


def test_changed_preregistered_protocol_fails_before_metadata_or_source_access(tmp_path, monkeypatch):
    bad_protocol = tmp_path / "protocol.json"
    bad_protocol.write_text('{"first_outcome_read_gate":{"completed_primary_events":29}}', encoding="utf-8")
    monkeypatch.setattr(source_capture, "PROTOCOL_PATH", bad_protocol)

    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            raise AssertionError("Supabase metadata must not be read after protocol mismatch")

    def forbidden_history(**_kwargs):
        raise AssertionError("historical source must not be downloaded after protocol mismatch")

    def forbidden_get(*_args, **_kwargs):
        raise AssertionError("current-season outcomes must not be requested after protocol mismatch")

    with pytest.raises(RuntimeError, match="protocol blob changed"):
        capture_source_archive(
            output_dir=tmp_path / "out",
            client=ForbiddenClient(),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )


def test_capture_denies_before_metadata_http_or_archive_creation(monkeypatch, tmp_path):
    calls = []

    def deny():
        raise PermissionError("source-capture scope unresolved")

    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            calls.append("supabase_metadata")
            raise AssertionError("Supabase metadata must not be read before source rights")

    def forbidden_get(*_args, **_kwargs):
        calls.append("current_source_http")
        raise AssertionError("current-season source must not be requested before source rights")

    def forbidden_history(**_kwargs):
        calls.append("historical_source_http")
        raise AssertionError("historical source must not be requested before source rights")

    monkeypatch.setattr(source_capture, "require_v2_source_capture_access", deny)
    output_dir = tmp_path / "must-not-exist"
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        capture_source_archive(
            output_dir=output_dir,
            client=ForbiddenClient(),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )
    assert calls == []
    assert not output_dir.exists()


def test_metadata_helper_denies_before_supabase_client_access(monkeypatch):
    def deny():
        raise PermissionError("source-capture scope unresolved")

    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            pytest.fail("Supabase metadata was accessed before source rights")

    monkeypatch.setattr(source_capture, "require_v2_source_capture_access", deny)
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        read_completed_primary_event_count(
            ForbiddenClient(),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        )


def test_cli_denies_before_supabase_client_creation(monkeypatch, tmp_path):
    def deny():
        raise PermissionError("source-capture scope unresolved")

    monkeypatch.setattr(source_capture, "require_v2_source_capture_access", deny)
    monkeypatch.setattr(
        source_capture,
        "create_client",
        lambda *_args, **_kwargs: pytest.fail("Supabase client created before source rights"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["serie_a_v2_current_form_source_capture.py", "--output-dir", str(tmp_path / "out")],
    )
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        source_capture.main()


def test_repository_source_capture_rights_remain_held_before_private_storage_lookup(monkeypatch):
    calls = []
    monkeypatch.setattr(
        artifact_privacy.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    with pytest.raises(PermissionError, match="automated source capture is not permitted"):
        direct_access.require_v2_source_capture_access()
    assert calls == []


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


def test_csv_identity_digest_matches_metadata_after_v2_alias_normalization():
    metadata = event_rows(30)
    metadata[0] = {
        "match_date": "2026-08-01",
        "home_team": "Atalanta BC",
        "away_team": "Juventus",
    }
    raw = current_csv(n=30).decode().replace(
        "01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
        "01/08/2026,Atalanta,Juventus,1,0,H,5,3,2,1,0,0",
    ).encode()
    metadata_summary = source_capture.summarize_completed_primary_events(
        metadata, before_date=date(2026, 10, 18)
    )
    frame, _ = validate_current_season_csv(
        raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )

    matched = source_capture.validate_current_season_identity_match(metadata_summary, frame)

    assert matched["exact_identity_match"] is True
    assert matched["metadata_canonical_fixture_identities"] == 30
    assert matched["source_canonical_fixture_identities"] == 30
    assert matched["metadata_identity_sha256"] == matched["source_identity_sha256"]


def test_same_count_but_different_fixture_identity_fails_closed():
    metadata_summary = source_capture.summarize_completed_primary_events(
        event_rows(30), before_date=date(2026, 10, 18)
    )
    frame, _ = validate_current_season_csv(
        current_csv(n=30),
        captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
    )
    frame.loc[0, "HomeTeam"] = "Different Home"

    with pytest.raises(RuntimeError, match="do not exactly match Supabase metadata-only gate"):
        source_capture.validate_current_season_identity_match(metadata_summary, frame)


def test_capture_rejects_same_count_different_fixture_identity_before_current_archive(tmp_path):
    raw = current_csv(n=30).decode().replace(
        "01/08/2026,Home 0,Away 0,1,0,H,5,3,2,1,0,0",
        "01/08/2026,Different Home,Away 0,1,0,H,5,3,2,1,0,0",
    ).encode()

    class Response:
        status_code = 200
        url = CURRENT_URL
        content = raw

        def raise_for_status(self):
            return None

    history_audit = [
        {
            "season_code": code,
            "source_url": f"https://www.football-data.co.uk/mmz4281/{code}/I1.csv",
            "archived_source_name": f"serie_a_{code}.csv",
            "csv_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "source_observed_at_utc": "2026-10-18T08:00:00+00:00",
            "completed_source_rows": 1,
        }
        for code in _source_codes()
    ]

    with pytest.raises(RuntimeError, match="do not exactly match Supabase metadata-only gate"):
        capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=lambda *_args, **_kwargs: Response(),
            history_fetch=lambda **_kwargs: (pd.DataFrame([{"historical": 1}]), history_audit),
            clock=lambda: datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        )

    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


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
        get=lambda url, timeout, allow_redirects=False: Response(),
        history_fetch=fake_history,
        clock=lambda: next(source_times),
    )
    assert report["feature_source_gate"]["passed"] is True
    assert report["feature_source_gate"]["observed_completed_primary_events"] == 30
    assert report["feature_source_gate"]["score_or_result_fields_selected_for_gate"] is False
    assert report["feature_source_gate"]["uses_exact_preregistered_outcome_read_gate"] is True
    assert report["preregistered_outcome_read_gate"]["passed"] is True
    assert report["preregistered_outcome_read_gate"]["required_completed_primary_events"] == 30
    assert report["preregistered_outcome_read_gate"]["observed_completed_primary_events"] == 30
    assert report["current_season_completed_match_results_read_for_lagged_features"] is True
    assert report["target_outcomes_read_for_evaluation"] is False
    assert "after the preregistered 30-primary-event gate" in report["target_outcomes_read_scope"]
    assert report["source_capture_access"]["provider_rights_status"] == "GRANTED"
    assert report["source_capture_access"]["artifact_repository_private"] is True
    assert report["source_capture_access"]["artifact_storage_policy"] == "PRIVATE_GITHUB_ACTIONS_ARTIFACTS"
    assert report["historical_old_season_file_count"] == 10
    assert report["source_file_count"] == 11
    assert report["current_season_code"] == CURRENT_CODE == "2627"
    assert report["current_season"] == CURRENT_SEASON == "2026-2027"
    assert report["current_season_completed_prior_day_rows"] == 30
    assert report["current_season_identity_audit"]["exact_identity_match"] is True
    assert report["current_season_identity_audit"]["metadata_canonical_fixture_identities"] == 30
    assert report["feature_source_gate"]["source_identity_audit"]["exact_identity_match"] is True
    assert report["current_season_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / CURRENT_FILENAME).read_bytes() == raw
    assert (tmp_path / MANIFEST_FILENAME).exists()
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["target_outcome_evaluation_gate"]["outcome_gate_open"] is False
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0
    assert report["model_refit_or_promotion"] is False


def test_source_capture_workflow_is_default_deny_and_preserves_existing_schedule():
    """The scheduled workflow may run tests, but cannot fetch or publish source by default."""
    workflow_path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "serie-a-v2-current-form-source-capture.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")

    # Preserve the existing schedule; this regression does not authorize or alter it.
    assert 'cron: "50 5 * * *"' in workflow
    assert "  workflow_dispatch:" in workflow
    assert 'MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED: "false"' in workflow

    private_check = workflow.split("- name: Verify private repository storage before live V2 access", 1)[1]
    capture_step = workflow.split(
        "- name: Capture frozen historical seasons plus gated current-form source", 1
    )[1].split("- name: Archive source bytes and gate manifest for future quotes only", 1)[0]
    upload_step = workflow.split(
        "- name: Archive source bytes and gate manifest for future quotes only", 1
    )[1]

    assert "if: ${{ env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}" in private_check
    assert (
        "if: ${{ env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' "
        "&& steps.private-storage.outputs.is_private == 'true' }}"
    ) in capture_step
    assert "SUPABASE_URL: ${{ secrets.SUPABASE_URL }}" in capture_step
    assert "SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}" in capture_step
    assert (
        "if: ${{ success() && env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' "
        "&& steps.private-storage.outputs.is_private == 'true' }}"
    ) in upload_step

    job_header = workflow.split("  capture-current-form:", 1)[1].split("    steps:", 1)[0]
    assert "SUPABASE_URL" not in job_header
    assert "SUPABASE_KEY" not in job_header

@pytest.mark.parametrize(
    "capture_now",
    [
        datetime(2026, 10, 18, 8, 0),
        datetime(2026, 10, 18, 8, 0, tzinfo=NoOffsetTZ()),
    ],
)
def test_source_archive_rejects_nonaware_entry_clock_before_metadata_or_source_access(
    tmp_path, capture_now
):
    def forbidden(*_args, **_kwargs):
        pytest.fail("no metadata query or source request may run with a non-aware entry clock")

    with pytest.raises(ValueError, match="source capture clock must return a timezone-aware datetime"):
        source_capture._capture_source_archive(
            output_dir=tmp_path,
            client=object(),
            now=capture_now,
            access=_synthetic_source_capture_access(),
            get=forbidden,
            history_fetch=forbidden,
        )

    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


@pytest.mark.parametrize("naive_call", [1, 2])
def test_source_archive_rejects_naive_clock_for_observation_and_archive_time(
    tmp_path, monkeypatch, naive_call
):
    """A local-naive clock must never be silently interpreted as UTC provenance."""
    raw = current_csv(n=30)
    monkeypatch.setattr(
        source_capture,
        "_read_completed_primary_event_summary",
        lambda client, now: source_capture.summarize_completed_primary_events(
            event_rows(30), before_date=now.astimezone(timezone.utc).date()
        ),
    )

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

    naive = datetime(2026, 10, 18, 8, 1)
    aware = datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)
    clock_values = [naive if naive_call == 1 else aware,
                    naive if naive_call == 2 else aware]

    with pytest.raises(ValueError, match="timezone-aware"):
        source_capture._capture_source_archive(
            output_dir=tmp_path,
            client=object(),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=lambda url, timeout, allow_redirects=False: Response(),
            history_fetch=fake_history,
            clock=lambda: clock_values.pop(0),
        )

    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_source_capture_clock_normalizes_explicit_offset_to_utc():
    local = datetime(2026, 10, 18, 11, 1, tzinfo=timezone(timedelta(hours=3)))
    assert source_capture._clock_utc(
        lambda: local, field="test source clock"
    ) == datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)


def test_source_archive_creation_clock_cannot_precede_source_observation():
    observed = datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc)
    earlier = datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="precedes source observation"):
        source_capture._archive_creation_utc(
            lambda: earlier, observed_at=observed
        )
    assert source_capture._archive_creation_utc(
        lambda: observed, observed_at=observed
    ) == observed



def _clock_order_history(*, get, capture_dir):
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
            "source_observed_at_utc": "2026-10-18T07:59:00+00:00",
            "completed_source_rows": 1,
        })
    return pd.DataFrame([{"historical": 1}]), audits


def test_current_source_observation_clock_is_taken_after_successful_http_response(tmp_path):
    events = []
    raw = current_csv(n=30)
    clock_values = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
    ])

    class Response:
        status_code = 200
        url = CURRENT_URL
        content = raw

        def raise_for_status(self):
            events.append("response_complete")

    def fake_get(url, timeout, allow_redirects=False):
        assert url == CURRENT_URL
        assert allow_redirects is False
        assert timeout == 30
        events.append("request_started")
        return Response()

    def clock():
        events.append(f"clock_{sum(event.startswith('clock_') for event in events) + 1}")
        return next(clock_values)

    report = source_capture._capture_source_archive(
        output_dir=tmp_path,
        client=FakeQuery(event_rows(30)),
        now=datetime(2026, 10, 18, 8, 0, tzinfo=timezone.utc),
        access=_synthetic_source_capture_access(),
        get=fake_get,
        history_fetch=_clock_order_history,
        clock=clock,
    )

    assert events == [
        "request_started",
        "response_complete",
        "clock_1",
        "clock_2",
    ]
    assert report["current_season_source_observed_at_utc"] == "2026-10-18T08:01:00+00:00"
    assert report["source_archive_created_at_utc"] == "2026-10-18T08:02:00+00:00"
    assert report["current_season_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / CURRENT_FILENAME).read_bytes() == raw
    assert (tmp_path / MANIFEST_FILENAME).exists()


def test_failed_current_source_http_response_never_gets_observation_timestamp(tmp_path):
    events = []
    clock_calls = []

    class FailedResponse:
        content = current_csv(n=30)

        def raise_for_status(self):
            events.append("response_failed")
            raise RuntimeError("synthetic source HTTP failure")

    def fake_get(url, timeout, allow_redirects=False):
        assert url == CURRENT_URL
        assert allow_redirects is False
        events.append("request_started")
        return FailedResponse()

    def clock():
        clock_calls.append("called")
        return datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)

    with pytest.raises(RuntimeError, match="synthetic source HTTP failure"):
        source_capture._capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, 0, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=fake_get,
            history_fetch=_clock_order_history,
            clock=clock,
        )

    assert events == ["request_started", "response_failed"]
    assert clock_calls == []
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()



def test_current_source_rejects_redirect_response_before_observation_clock_or_write(tmp_path):
    events = []
    clock_calls = []

    class RedirectResponse:
        status_code = 302
        url = "https://redirect.invalid/current-season.csv"

        @property
        def content(self):
            raise AssertionError("redirect response body must not be read")

        def raise_for_status(self):
            events.append("status_checked")

    def fake_get(url, timeout, allow_redirects=True):
        assert url == CURRENT_URL
        assert timeout == 30
        assert allow_redirects is False
        events.append("request")
        return RedirectResponse()

    def clock():
        clock_calls.append("called")
        return datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)

    with pytest.raises(RuntimeError, match="requires HTTP 200 without redirects"):
        source_capture._capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, 0, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=fake_get,
            history_fetch=_clock_order_history,
            clock=clock,
        )

    assert events == ["request", "status_checked"]
    assert clock_calls == []
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_current_source_rejects_unexpected_final_url_before_body_or_observation(tmp_path):
    events = []
    clock_calls = []

    class RedirectedSuccess:
        status_code = 200
        url = "https://redirect.invalid/current-season.csv"

        @property
        def content(self):
            raise AssertionError("unexpected response body must not be read")

        def raise_for_status(self):
            events.append("status_checked")

    def fake_get(url, timeout, allow_redirects=True):
        assert url == CURRENT_URL
        assert allow_redirects is False
        events.append("request")
        return RedirectedSuccess()

    def clock():
        clock_calls.append("called")
        return datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="response URL differs from configured URL"):
        source_capture._capture_source_archive(
            output_dir=tmp_path,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, 0, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=fake_get,
            history_fetch=_clock_order_history,
            clock=clock,
        )

    assert events == ["request", "status_checked"]
    assert clock_calls == []
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()
