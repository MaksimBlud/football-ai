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
    read_completed_primary_event_summary,
    summarize_completed_primary_events,
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
    # Reach the provider-rights gate while retaining the real owner flag guard.
    # The committed manifest still denies capture, so private-repository lookup
    # and all network access must remain untouched.
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
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
    assert report["feature_source_gate"]["identity_audit"]["canonical_unique_fixture_identities"] == 30
    assert report["preregistered_outcome_read_gate"]["identity_audit"]["canonical_unique_fixture_identities"] == 30
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
    assert '"serie_a_v2_current_form_source_capture.py"' in workflow
    assert '"tests/test_serie_a_v2_current_form_source_capture.py"' in workflow


def test_current_form_capture_scopes_github_token_only_to_private_storage_check():
    workflow_path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "serie-a-v2-current-form-source-capture.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")
    private_check = workflow.split(
        "- name: Verify private repository storage before live V2 access", 1
    )[1].split("- name: Capture frozen historical seasons plus gated current-form source", 1)[0]
    capture_step = workflow.split(
        "- name: Capture frozen historical seasons plus gated current-form source", 1
    )[1].split("- name: Archive source bytes and gate manifest for future quotes only", 1)[0]
    job_header = workflow.split("  capture-current-form:", 1)[1].split("    steps:", 1)[0]
    assert "GH_TOKEN: ${{ github.token }}" in private_check
    assert workflow.count("GH_TOKEN:") == 1
    assert "GH_TOKEN" not in job_header
    assert "GITHUB_TOKEN" not in workflow
    assert "GH_TOKEN" not in capture_step
    assert "SUPABASE_URL" not in job_header and "SUPABASE_KEY" not in job_header
    assert "MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true'" in capture_step
    assert "steps.private-storage.outputs.is_private == 'true'" in capture_step



def test_current_form_source_capture_rights_validation_is_covered_by_source_first_ci():
    workflow_path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "market-anchor-v2-original-forward-source-first-validation.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")
    assert "research/v2-current-form-identity-restack-on-991-20261128-run11" in workflow
    assert '"serie_a_v2_current_form_source_capture.py"' in workflow
    assert '"tests/test_serie_a_v2_current_form_source_capture.py"' in workflow
    assert '"serie_a_v2_live_diagnostic_report.py"' in workflow
    assert '"tests/test_serie_a_v2_live_diagnostic_report.py"' in workflow
    assert "serie_a_v2_live_diagnostic_report.py" in workflow.split(
        "name: Compile original V2 source-first modules", 1
    )[1].split("      - name: Run original V2 source-first and frozen-contract regressions", 1)[0]
    assert "serie_a_v2_current_form_source_capture.py" in workflow.split(
        "name: Compile original V2 source-first modules", 1
    )[1].split("      - name: Run original V2 source-first and frozen-contract regressions", 1)[0]
    assert "tests/test_serie_a_v2_live_diagnostic_report.py" in workflow.split(
        "      - name: Run original V2 source-first and frozen-contract regressions", 1
    )[1].split("      - name: Guard production model binaries", 1)[0]
    assert "tests/test_serie_a_v2_current_form_source_capture.py" in workflow.split(
        "      - name: Run original V2 source-first and frozen-contract regressions", 1
    )[1].split("      - name: Guard production model binaries", 1)[0]
    assert "persist-credentials: false" in workflow
    assert "contents: read" in workflow
    assert "secrets." not in workflow
    assert "SUPABASE_" not in workflow
    assert "GITHUB_TOKEN" not in workflow
    assert "actions/upload-artifact" not in workflow
    assert "actions/download-artifact" not in workflow
    assert "git diff --exit-code origin/main...HEAD -- '*.pkl'" in workflow


def _write_historical_capture_sources(*, get, capture_dir):
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


def test_source_capture_clock_rejects_naive_or_offsetless_datetime():
    class NoOffset(tzinfo):
        def utcoffset(self, _dt):
            return None

        def dst(self, _dt):
            return None

    values = [
        datetime(2026, 10, 18, 8, 1),
        datetime(2026, 10, 18, 8, 1, tzinfo=NoOffset()),
    ]
    for value in values:
        with pytest.raises(ValueError, match="timezone-aware"):
            source_capture._clock_utc(lambda value=value: value, field="test source clock")


def test_source_capture_clock_normalizes_explicit_offset_to_utc():
    local = datetime(2026, 10, 18, 11, 1, tzinfo=timezone(timedelta(hours=3)))
    assert source_capture._clock_utc(
        lambda: local, field="test source clock"
    ) == datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)


def test_source_archive_creation_clock_cannot_precede_source_observation():
    observed = datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc)
    earlier = datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="precedes source observation"):
        source_capture._archive_creation_utc(lambda: earlier, observed_at=observed)
    assert source_capture._archive_creation_utc(
        lambda: observed, observed_at=observed
    ) == observed


def test_source_archive_rejects_naive_entry_clock_before_metadata_or_io(tmp_path):
    def forbidden(*_args, **_kwargs):
        pytest.fail("invalid source clock must fail before metadata or source access")

    with pytest.raises(ValueError, match="timezone-aware"):
        source_capture._capture_source_archive(
            output_dir=tmp_path / "published",
            client=object(),
            now=datetime(2026, 10, 18, 8),
            access=_synthetic_source_capture_access(),
            get=forbidden,
            history_fetch=forbidden,
        )
    assert not (tmp_path / "published").exists()


def test_source_archive_refuses_symlink_or_occupied_output_before_metadata_or_io(tmp_path):
    def forbidden(*_args, **_kwargs):
        pytest.fail("unsafe output destination must fail before metadata or source access")

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    sentinel = occupied / "preserve.txt"
    sentinel.write_text("previous evidence", encoding="utf-8")
    with pytest.raises(FileExistsError, match="must be absent or empty"):
        source_capture._capture_source_archive(
            output_dir=occupied,
            client=object(),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=forbidden,
            history_fetch=forbidden,
        )
    assert sentinel.read_text(encoding="utf-8") == "previous evidence"
    assert list(occupied.iterdir()) == [sentinel]

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "symlink-destination"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="cannot be a symlink"):
        source_capture._capture_source_archive(
            output_dir=link,
            client=object(),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=forbidden,
            history_fetch=forbidden,
        )
    assert list(target.iterdir()) == []


def test_source_archive_discards_partial_history_after_current_source_redirect(tmp_path):
    output_dir = tmp_path / "published"
    events = []

    class RedirectResponse:
        status_code = 302
        url = "https://redirect.invalid/current-season.csv"

        @property
        def content(self):
            raise AssertionError("redirect body must not be read")

        def raise_for_status(self):
            events.append("response_checked")

    def fake_get(url, timeout, allow_redirects=False):
        assert url == CURRENT_URL
        assert timeout == 30
        assert allow_redirects is False
        events.append("request")
        return RedirectResponse()

    with pytest.raises(RuntimeError, match="requires HTTP 200 without redirects"):
        source_capture._capture_source_archive(
            output_dir=output_dir,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=fake_get,
            history_fetch=_write_historical_capture_sources,
            clock=lambda: pytest.fail("observation clock must not be read after redirect"),
        )

    assert events == ["request", "response_checked"]
    assert not output_dir.exists()
    assert not list(tmp_path.glob(".published.staging-*"))


def test_source_archive_rejects_unexpected_current_final_url_before_body_or_clock(tmp_path):
    output_dir = tmp_path / "published"

    class RedirectedSuccess:
        status_code = 200
        url = "https://redirect.invalid/current-season.csv"

        @property
        def content(self):
            raise AssertionError("unexpected response body must not be read")

        def raise_for_status(self):
            return None

    def fake_get(url, timeout, allow_redirects=False):
        assert url == CURRENT_URL
        assert allow_redirects is False
        return RedirectedSuccess()

    with pytest.raises(ValueError, match="response URL differs from configured URL"):
        source_capture._capture_source_archive(
            output_dir=output_dir,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=fake_get,
            history_fetch=_write_historical_capture_sources,
            clock=lambda: pytest.fail("observation clock must not be read after unexpected URL"),
        )
    assert not output_dir.exists()
    assert not list(tmp_path.glob(".published.staging-*"))


def test_source_archive_publishes_complete_source_set_atomically(tmp_path):
    output_dir = tmp_path / "published"
    raw = current_csv(n=30)
    events = []
    clock_values = iter([
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
    ])

    class Response:
        status_code = 200
        url = CURRENT_URL

        @property
        def content(self):
            events.append("body_read")
            return raw

        def raise_for_status(self):
            events.append("response_checked")

    def fake_get(url, timeout, allow_redirects=False):
        assert url == CURRENT_URL
        assert timeout == 30
        assert allow_redirects is False
        events.append("request")
        return Response()

    def clock():
        events.append(f"clock_{len([item for item in events if item.startswith('clock_')]) + 1}")
        return next(clock_values)

    report = source_capture._capture_source_archive(
        output_dir=output_dir,
        client=FakeQuery(event_rows(30)),
        now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
        access=_synthetic_source_capture_access(),
        get=fake_get,
        history_fetch=_write_historical_capture_sources,
        clock=clock,
    )

    expected = {f"serie_a_{code}.csv" for code in _source_codes()}
    expected.update({CURRENT_FILENAME, MANIFEST_FILENAME})
    assert output_dir.is_dir()
    assert {path.name for path in output_dir.iterdir()} == expected
    assert report["source_file_count"] == 11
    assert report["current_season_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["source_archive_created_at_utc"] == "2026-10-18T08:02:00+00:00"
    assert events[-5:] == ["request", "response_checked", "body_read", "clock_1", "clock_2"]
    assert not list(tmp_path.glob(".published.staging-*"))


def test_source_archive_rejects_backwards_archive_clock_without_publication(tmp_path):
    output_dir = tmp_path / "published"
    raw = current_csv(n=30)
    clock_values = iter([
        datetime(2026, 10, 18, 8, 2, tzinfo=timezone.utc),
        datetime(2026, 10, 18, 8, 1, tzinfo=timezone.utc),
    ])

    class Response:
        status_code = 200
        url = CURRENT_URL
        content = raw

        def raise_for_status(self):
            return None

    with pytest.raises(ValueError, match="precedes source observation"):
        source_capture._capture_source_archive(
            output_dir=output_dir,
            client=FakeQuery(event_rows(30)),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            access=_synthetic_source_capture_access(),
            get=lambda url, timeout, allow_redirects=False: Response(),
            history_fetch=_write_historical_capture_sources,
            clock=lambda: next(clock_values),
        )
    assert not output_dir.exists()
    assert not list(tmp_path.glob(".published.staging-*"))



def test_gate_identity_audit_reconciles_aliases_and_rejects_reversed_duplicates():
    rows = [
        {"match_date": "2026-10-01", "home_team": "Atalanta", "away_team": "Juventus"},
        {"match_date": "2026-10-01", "home_team": "Atalanta BC", "away_team": "Juventus"},
        {"match_date": "2026-10-02", "home_team": "Milan", "away_team": "Inter"},
        {"match_date": "2026-10-19", "home_team": "Roma", "away_team": "Napoli"},
    ]
    audit = summarize_completed_primary_events(rows, before_date=date(2026, 10, 18))
    assert audit["raw_metadata_rows"] == 4
    assert audit["eligible_metadata_rows_before_cutoff"] == 3
    assert audit["raw_unique_fixture_identities"] == 3
    assert audit["canonical_unique_fixture_identities"] == 2
    assert audit["exact_duplicate_metadata_rows"] == 0
    assert audit["alias_collapsed_duplicate_identities"] == 1
    assert audit["alias_collision_count"] == 1

    reversed_rows = [
        {"match_date": "2026-08-23", "home_team": "Atalanta", "away_team": "Juventus"},
        {"match_date": "2026-08-23", "home_team": "Juventus", "away_team": "Atalanta BC"},
    ]
    with pytest.raises(ValueError, match="reversed duplicate"):
        summarize_completed_primary_events(reversed_rows, before_date=date(2026, 10, 18))


@pytest.mark.parametrize(
    "bad_date",
    ["2026-10-01T12:00:00Z", "2026-10-01suffix", "2026-1-1", "20261001"],
)
def test_gate_rejects_noncanonical_or_timestamp_fixture_dates(bad_date):
    with pytest.raises(ValueError, match="canonical YYYY-MM-DD"):
        summarize_completed_primary_events(
            [{"match_date": bad_date, "home_team": "Atalanta", "away_team": "Juventus"}],
            before_date=date(2026, 10, 18),
        )


def test_gate_rejects_datetime_objects_as_fixture_dates():
    with pytest.raises(ValueError, match="date-only"):
        summarize_completed_primary_events(
            [{"match_date": datetime(2026, 10, 1, 12), "home_team": "Atalanta", "away_team": "Juventus"}],
            before_date=date(2026, 10, 18),
        )


def test_live_feature_gate_summary_reads_only_fixture_metadata():
    client = FakeQuery(event_rows(30))
    audit = read_completed_primary_event_summary(
        client, now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
    )
    assert audit["canonical_unique_fixture_identities"] == 30
    assert audit["raw_metadata_rows"] == 30
    assert client.selected == "match_date,home_team,away_team"


def test_reversed_duplicate_gate_identity_fails_before_any_source_download(tmp_path):
    rows = event_rows(30)
    rows[0] = {"match_date": "2026-08-23", "home_team": "Atalanta", "away_team": "Juventus"}
    rows[1] = {"match_date": "2026-08-23", "home_team": "Juventus", "away_team": "Atalanta BC"}
    calls = []

    def forbidden_get(*_args, **_kwargs):
        calls.append("current-source")
        raise AssertionError("current source must not be requested after an ambiguous gate identity")

    def forbidden_history(**_kwargs):
        calls.append("historical-source")
        raise AssertionError("historical source must not be requested after an ambiguous gate identity")

    output_dir = tmp_path / "archive"
    with pytest.raises(ValueError, match="reversed duplicate"):
        capture_source_archive(
            output_dir=output_dir,
            client=FakeQuery(rows),
            now=datetime(2026, 10, 18, 8, tzinfo=timezone.utc),
            get=forbidden_get,
            history_fetch=forbidden_history,
        )
    assert calls == []
    assert not output_dir.exists()

def test_current_csv_rejects_timestamp_or_noncanonical_date_values():
    raw = current_csv(n=30).decode().replace(
        "01/08/2026", "01/08/2026 12:00", 1
    ).encode()
    with pytest.raises(ValueError, match="strict DD/MM/YYYY"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_non_integer_feature_counts():
    raw = current_csv(n=30).decode().replace(
        "1,0,H,5,3,2,1,0,0", "1,0,H,5.5,3,2,1,0,0", 1
    ).encode()
    with pytest.raises(ValueError, match="non-integer HC"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_non_finite_feature_counts():
    raw = current_csv(n=30).decode().replace(
        "1,0,H,5,3,2,1,0,0", "1,0,H,inf,3,2,1,0,0", 1
    ).encode()
    with pytest.raises(ValueError, match="missing/invalid HC"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_invalid_full_time_result_markers():
    raw = current_csv(n=30).decode().replace(
        "1,0,H,5,3,2,1,0,0", "1,0,X,5,3,2,1,0,0", 1
    ).encode()
    with pytest.raises(ValueError, match="invalid full-time result marker"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_past_partial_statistics_without_result():
    raw = current_csv(n=30).decode().replace(
        "1,0,H,5,3,2,1,0,0", "1,0,,5,3,2,1,0,0", 1
    ).encode()
    with pytest.raises(ValueError, match="partial statistics"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_future_statistics_even_without_result():
    future_stats = ",".join([
        "20/10/2026", "Future Home", "Future Away",
        "", "", "", "1", "", "", "", "", "",
    ])
    raw = (current_csv(n=30).decode().rstrip() + "\n" + future_stats + "\n").encode()
    with pytest.raises(ValueError, match="future statistics data"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_rejects_result_or_statistics_without_fixture_date():
    missing_date = ",".join([
        "", "Missing Date Home", "Missing Date Away",
        "1", "0", "H", "5", "3", "2", "1", "0", "0",
    ])
    raw = (current_csv(n=30).decode().rstrip() + "\n" + missing_date + "\n").encode()
    with pytest.raises(ValueError, match="without a fixture date"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


def test_current_csv_requires_a_real_utc_offset():
    class NoOffset(tzinfo):
        def utcoffset(self, _dt):
            return None

        def dst(self, _dt):
            return None

    with pytest.raises(ValueError, match="timezone-aware"):
        validate_current_season_csv(
            current_csv(n=30),
            captured_at=datetime(2026, 10, 18, 8, tzinfo=NoOffset()),
        )


def test_current_csv_requires_full_time_result_to_match_exact_goal_comparison():
    raw = current_csv(n=30).decode().replace(
        "1,0,H,5,3,2,1,0,0", "1,0,D,5,3,2,1,0,0", 1
    ).encode()
    with pytest.raises(ValueError, match="does not match full-time goals"):
        validate_current_season_csv(
            raw, captured_at=datetime(2026, 10, 18, 8, tzinfo=timezone.utc)
        )


class _ForbiddenSourceCaptureInput:
    def __bool__(self):
        raise AssertionError("source-capture input inspected before rights gate")

    def __iter__(self):
        raise AssertionError("source-capture input iterated before rights gate")

    def __len__(self):
        raise AssertionError("source-capture input length inspected before rights gate")

    def __getitem__(self, _key):
        raise AssertionError("source-capture input indexed before rights gate")

    def get(self, *_args, **_kwargs):
        raise AssertionError("source-capture mapping inspected before rights gate")

    def __fspath__(self):
        raise AssertionError("source-capture path inspected before rights gate")


def test_direct_internal_metadata_reader_denies_before_supabase_access(monkeypatch):
    def deny():
        raise PermissionError("source-capture scope unresolved")

    class ForbiddenClient:
        def table(self, *_args, **_kwargs):
            pytest.fail("Supabase metadata was accessed before source-capture rights")

    monkeypatch.setattr(source_capture, "require_v2_source_capture_access", deny)
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        source_capture._read_completed_primary_event_summary(
            ForbiddenClient(), now=_ForbiddenSourceCaptureInput()
        )


def test_direct_internal_archive_builder_denies_before_input_paths_or_callbacks(monkeypatch):
    def deny():
        raise PermissionError("source-capture scope unresolved")

    def forbidden(*_args, **_kwargs):
        pytest.fail("source archive callback ran before source-capture rights")

    monkeypatch.setattr(source_capture, "require_v2_source_capture_access", deny)
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        source_capture._capture_source_archive(
            output_dir=_ForbiddenSourceCaptureInput(),
            client=_ForbiddenSourceCaptureInput(),
            now=_ForbiddenSourceCaptureInput(),
            access=_ForbiddenSourceCaptureInput(),
            get=forbidden,
            history_fetch=forbidden,
        )


def test_direct_internal_archive_contents_builder_denies_before_path_or_callbacks(monkeypatch):
    def deny():
        raise PermissionError("source-capture scope unresolved")

    def forbidden(*_args, **_kwargs):
        pytest.fail("source archive contents callback ran before source-capture rights")

    monkeypatch.setattr(source_capture, "require_v2_source_capture_access", deny)
    with pytest.raises(PermissionError, match="source-capture scope unresolved"):
        source_capture._capture_source_archive_contents(
            output_dir=_ForbiddenSourceCaptureInput(),
            at=_ForbiddenSourceCaptureInput(),
            preregistered_gate=_ForbiddenSourceCaptureInput(),
            gate_count=_ForbiddenSourceCaptureInput(),
            gate_identity_audit=_ForbiddenSourceCaptureInput(),
            access=_ForbiddenSourceCaptureInput(),
            get=forbidden,
            history_fetch=forbidden,
        )
