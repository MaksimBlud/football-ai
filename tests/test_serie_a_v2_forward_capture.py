"""Original frozen V2 forward-only capture, using only synthetic pre-2026/27 scores."""
import hashlib
from io import BytesIO
import json
from datetime import datetime, timedelta, timezone
import zipfile
import sys

import serie_a_v2_forward_capture as forward_capture
import market_anchor_v2_direct_access as direct_access

_REAL_REQUIRE_SOURCE_CAPTURE_ACCESS = direct_access.require_v2_source_capture_access
import serie_a_v2_frozen_shadow_preview as frozen_preview
import serie_a_v2_live_diagnostic_report as live_diagnostic
import pytest


@pytest.fixture(autouse=True)
def _allow_synthetic_provider_rights_for_offline_tests(monkeypatch):
    monkeypatch.setattr(
        direct_access, "require_v2_source_capture_rights",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(
        direct_access, "require_v2_inference_access",
        lambda: {"access_scope": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(
        direct_access, "require_v2_source_capture_access",
        lambda: {"access_scope": "SYNTHETIC_TEST_ONLY"},
    )
    monkeypatch.setattr(frozen_preview, "require_v2_source_capture_rights", lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"})
    monkeypatch.setattr(frozen_preview, "require_v2_inference_access", lambda: {"access_scope": "SYNTHETIC_TEST_ONLY"})
    monkeypatch.setattr(live_diagnostic, "require_v2_inference_access", lambda: {"access_scope": "SYNTHETIC_TEST_ONLY"})


def _allow_private_repository_for_test(monkeypatch):
    monkeypatch.setattr(
        forward_capture,
        "require_private_repository",
        lambda *, token, get=None: {"repository": "MaksimBlud/football-ai", "private": True},
    )


from serie_a_v2_frozen_shadow_preview import parse_utc

from serie_a_v2_live_diagnostic_report import _source_codes, PUBLIC_BASE
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_forward_capture import (
    ARTIFACT_NAME, ARCHIVE_REPORT, SOURCE_DIR,
    capture_forward_with_source_preflight, discover_archives,
    prepare_forward_capture, verify_source_run, SOURCE_WORKFLOW_PATH,
    get_archive, require_private_repository,
)

NOW = datetime(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
AFTER_CAPTURE = datetime(2026, 10, 14, 6, 0, tzinfo=timezone.utc)


def quote(ts="2026-10-14T06:00:00Z"):
    return {
        "league": "SERIE_A", "event_id": "new-fixture-original-v2",
        "home_team": "Juventus", "away_team": "Napoli",
        "snapshot_time_utc": ts,
        "created_at": "2026-10-14T06:00:01Z",
        "commence_time_utc": "2026-10-20T18:00:00Z",
        "home_odds": 1.92, "draw_odds": 3.45, "away_odds": 4.22,
    }


def make_source_archive():
    payloads = {}
    source_audits = []
    for code in _source_codes():
        year = 2000 + int(code[:2])
        body = (
            "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
            f"01/10/{year},Juventus,Napoli,2,1,H,7,3,2,1,0,0\n"
        ).encode()
        filename = f"serie_a_{code}.csv"
        payloads[SOURCE_DIR + filename] = body
        source_audits.append({
            "season_code": code,
            "source_url": f"{PUBLIC_BASE}/{code}/I1.csv",
            "archived_source_name": filename,
            "csv_sha256": hashlib.sha256(body).hexdigest(),
            "source_observed_at_utc": "2026-10-13T14:50:00Z",
            "completed_source_rows": 1,
        })
    report = {
        "frozen_candidate_sha256": FROZEN_SHA,
        "2026_27_public_results_downloaded": False,
        "protect_2026_27_prospective_outcomes": True,
        "public_source_files": source_audits,
    }
    bio = BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        z.writestr(ARCHIVE_REPORT, json.dumps(report))
        for path, payload in payloads.items():
            z.writestr(path, payload)
    raw = bio.getvalue()
    metadata = [{
        "artifact_id": 123,
        "run_id": 456,
        "head_sha": "a" * 40,
        "created_at": datetime(2026, 10, 13, 15, 0, tzinfo=timezone.utc),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }]
    return raw, metadata


def fake_verified_parent_run(archive, quote_time):
    assert archive["run_id"] == 456
    assert archive["head_sha"] == "a" * 40
    assert quote_time.tzinfo is not None
    return {
        "run_id": 456,
        "run_head_sha": "a" * 40,
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "head_branch": "main",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "run_created_at_utc": "2026-10-13T14:40:00Z",
        "run_completed_at_utc": "2026-10-13T15:01:00Z",
    }



def test_forward_v2_scores_only_after_real_prior_archive_and_never_promotes():
    raw, metadata = make_source_archive()
    calls = []
    report = prepare_forward_capture(
        [quote()], metadata, as_of_utc=NOW,
        load_archive=lambda artifact_id: calls.append(artifact_id) or raw,
        verify_parent_run=fake_verified_parent_run,
    )
    assert calls == [123]
    assert report["quotes_seen"] == report["future_quotes_checked"] == 1
    assert report["v2_diagnostic_previews_captured"] == 1
    assert report["uses_2026_27_results"] is False
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["rows"][0]["source_provenance"]["archive_sha256_verified"] is True
    assert report["rows"][0]["source_provenance"]["parent_run"]["run_completed_at_utc"] == "2026-10-13T15:01:00+00:00"
    assert report["eligible_for_product_publication"] is False
    assert report["no_bet"] is True
    row = report["rows"][0]
    assert row["quote_row_created_at_utc"] == "2026-10-14T06:00:01+00:00"
    assert row["source_artifact_sha256"] == metadata[0]["sha256"]
    assert row["status"] == "SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY"
    assert row["v2_preview"]["model_candidate_sha256"] == FROZEN_SHA
    assert row["v2_preview"]["market_1x2"] == pytest.approx(
        row["v2_preview"]["active_market_fallback_1x2"]
    )
    assert row["v2_preview"]["eligible_for_frozen_prospective_cohort"] is False


@pytest.mark.parametrize(
    ("created_at", "kickoff", "message"),
    [
        ("2026-10-14T05:59:59Z", "2026-10-20T18:00:00Z", "persisted before declared snapshot time"),
        ("2026-10-14T07:00:01Z", "2026-10-20T18:00:00Z", "persisted after capture clock"),
        ("2026-10-14T06:30:00Z", "2026-10-14T06:30:00Z", "persisted at or after kickoff"),
    ],
)
def test_forward_capture_rejects_invalid_quote_persistence_time_before_archive_io(
    created_at, kickoff, message
):
    raw, metadata = make_source_archive()
    calls = []
    with pytest.raises(ValueError, match=message):
        prepare_forward_capture(
            [{**quote(), "created_at": created_at, "commence_time_utc": kickoff}],
            metadata,
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: calls.append("archive") or raw,
            verify_parent_run=lambda archive, quote_time: (
                calls.append("parent") or fake_verified_parent_run(archive, quote_time)
            ),
        )
    assert calls == []


def test_forward_capture_requires_database_persistence_timestamp_before_archive_io():
    raw, metadata = make_source_archive()
    calls = []
    missing = quote()
    del missing["created_at"]
    with pytest.raises(ValueError, match="saved quote row is missing created_at"):
        prepare_forward_capture(
            [missing],
            metadata,
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: calls.append("archive") or raw,
            verify_parent_run=lambda archive, quote_time: (
                calls.append("parent") or fake_verified_parent_run(archive, quote_time)
            ),
        )
    assert calls == []


def test_original_october_13_quote_is_not_backfilled_from_later_archive():
    raw, metadata = make_source_archive()
    def cannot_download(_artifact_id):
        raise AssertionError("do not use archive after source quote")
    report = prepare_forward_capture(
        [quote("2026-10-13T14:48:53Z")], metadata,
        as_of_utc=NOW, load_archive=cannot_download,
        verify_parent_run=fake_verified_parent_run,
    )
    assert report["v2_diagnostic_previews_captured"] == 0
    assert report["blocked_no_prior_source"] == 1
    assert report["rows"][0]["v2_preview"] is None


def test_wrong_archive_bytes_fail_sha_gate():
    raw, metadata = make_source_archive()
    with pytest.raises(ValueError, match="digest mismatch"):
        prepare_forward_capture(
            [quote()], metadata, as_of_utc=NOW,
            load_archive=lambda _: raw+b"tampered",
            verify_parent_run=fake_verified_parent_run,
        )


def test_source_capture_refuses_protected_result_fields_before_any_download():
    raw, metadata = make_source_archive()
    with pytest.raises(ValueError, match="outcomes or settlement fields forbidden"):
        prepare_forward_capture(
            [{**quote(), "result": "H"}], metadata, as_of_utc=NOW,
            load_archive=lambda _: raw,
            verify_parent_run=fake_verified_parent_run,
        )


def test_future_quote_clock_rejected_without_external_requests():
    raw, metadata = make_source_archive()
    with pytest.raises(ValueError, match="invalid stored quote timing"):
        prepare_forward_capture(
            [quote("2026-10-15T06:00:00Z")], metadata, as_of_utc=NOW,
            load_archive=lambda _: raw,
            verify_parent_run=fake_verified_parent_run,
        )


def test_github_source_catalog_requires_main_sha_and_does_not_trust_missing_digest(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    class Response:
        def __init__(self, data):
            self.data=data
        def raise_for_status(self): pass
        def json(self): return self.data
    calls=[]
    def get(url,headers,timeout):
        calls.append(url)
        return Response({"artifacts": [
            {"id": 123, "name": ARTIFACT_NAME,"expired":False,
             "workflow_run":{"head_branch":"main", "id":456,"head_sha":"a"*40},
             "digest":"sha256:"+"a"*64,
             "created_at":"2026-10-13T15:00:00Z"},
            {"id": 124,"name":ARTIFACT_NAME,"expired":False,
             "workflow_run":{"head_branch":"research-tampered", "id":457,"head_sha":"b"*40},
             "digest":"sha256:"+"b"*64,
             "created_at":"2026-10-13T14:00:00Z"},
        ]})
    rows=discover_archives(token="test-token",get=get)
    assert [x["artifact_id"] for x in rows] == [123]
    assert len(calls) == 1

    def invalid(url,headers,timeout):
        return Response({"artifacts": [
            {"id": 125, "name": ARTIFACT_NAME,"expired":False,
             "workflow_run":{"head_branch":"main", "id":456,"head_sha":"a"*40},
             "digest":None, "created_at":"2026-10-13T15:00:00Z"},
        ]})
    with pytest.raises(ValueError,match="missing GitHub source archive SHA256 digest"):
        discover_archives(token="test-token",get=invalid)


def test_successful_exact_source_workflow_and_prequote_completion_required(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    _, artifacts = make_source_archive()
    meta = artifacts[0]
    class Response:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data
    valid = {
        "id": 456, "path": SOURCE_WORKFLOW_PATH,
        "head_branch": "main", "head_sha": "a"*40,
        "status": "completed", "conclusion": "success",
        "event": "push",
        "created_at": "2026-10-13T14:40:00Z",
        "updated_at": "2026-10-13T15:01:00Z",
    }
    hits = []
    def get(url, headers, timeout):
        hits.append(url)
        return Response(valid)
    result = verify_source_run(meta, quote_time=parse_utc("2026-10-14T06:00:00Z"),
                               token="test-token", get=get)
    assert hits == ["https://api.github.com/repos/MaksimBlud/football-ai/actions/runs/456"]
    assert result["workflow_path"] == SOURCE_WORKFLOW_PATH
    assert result["run_completed_at_utc"] == "2026-10-13T15:01:00+00:00"
    for altered, expected in [
        ({"path":".github/workflows/other.yml"}, "verified original V2 collector"),
        ({"head_sha":"b"*40}, "verified original V2 collector"),
        ({"conclusion":"failure"}, "verified original V2 collector"),
        ({"status":"in_progress"}, "verified original V2 collector"),
        ({"event":"workflow_run"}, "verified original V2 collector"),
        ({"updated_at":"2026-10-14T06:01:00Z"}, "not successfully finished before quote"),
    ]:
        def bad_get(url,headers,timeout):
            return Response({**valid,**altered})
        with pytest.raises(ValueError, match=expected):
            verify_source_run(meta, quote_time=parse_utc("2026-10-14T06:00:00Z"),
                              token="test-token", get=bad_get)


def test_forward_v2_refuses_unknown_or_late_parent_workflow_before_zip_download():
    raw, metadata = make_source_archive()
    download = []
    with pytest.raises(ValueError, match="verified source workflow provenance"):
        prepare_forward_capture(
            [quote()], metadata, as_of_utc=NOW,
            load_archive=lambda _: download.append(True) or raw,
            verify_parent_run=lambda a, qt: None,
        )
    assert download == []
    with pytest.raises(ValueError, match="source workflow finished after another quote"):
        prepare_forward_capture(
            [quote()], metadata, as_of_utc=NOW,
            load_archive=lambda _: download.append(True) or raw,
            verify_parent_run=lambda a, qt:
                {"run_completed_at_utc":"2026-10-14T06:01:00Z"},
        )
    assert download == []


def test_catalog_rejects_missing_parent_run_identity_even_with_valid_digest(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"artifacts":[
                {"id": 234,"name":ARTIFACT_NAME,"expired":False,
                 "workflow_run":{"head_branch":"main"},
                 "digest":"sha256:"+"a"*64,
                 "created_at":"2026-10-13T15:00:00Z"},
            ]}
    with pytest.raises(ValueError,match="missing GitHub parent run identity"):
        discover_archives(token="test-token",
                          get=lambda url,headers,timeout:Response())


def _fully_verified_parent(archive, quote_time, completed="2026-10-13T15:01:00Z"):
    return {
        "run_id": archive["run_id"],
        "run_head_sha": archive["head_sha"],
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "head_branch": "main",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "run_created_at_utc": "2026-10-13T14:40:00Z",
        "run_completed_at_utc": completed,
    }


def test_original_forward_live_access_defaults_to_denied_before_any_callback(monkeypatch):
    monkeypatch.delenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", raising=False)
    monkeypatch.setattr(
        direct_access, "require_v2_source_capture_access",
        _REAL_REQUIRE_SOURCE_CAPTURE_ACCESS,
    )
    calls = []
    with pytest.raises(PermissionError, match="MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=true"):
        capture_forward_with_source_preflight(
            [],
            as_of_utc=NOW,
            token="test-token",
            fetch_quotes=lambda: calls.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: calls.append("archive"),
            verify_parent_run=lambda *_args: calls.append("parent"),
        )
    assert calls == []


def test_original_forward_verifies_parent_and_zip_sha_before_saved_quote_reader(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    raw, metadata = make_source_archive()
    events = []

    def verify_parent(archive, quote_time):
        events.append("parent")
        return _fully_verified_parent(archive, quote_time)

    def load_archive(artifact_id):
        events.append("archive")
        assert artifact_id == metadata[0]["artifact_id"]
        return raw

    def fetch_quotes():
        events.append("quotes")
        return [quote()]

    report = capture_forward_with_source_preflight(
        metadata,
        as_of_utc=NOW,
            token="test-token",
        fetch_quotes=fetch_quotes,
        load_archive=load_archive,
        verify_parent_run=verify_parent,
    )

    assert events == ["parent", "archive", "quotes"]
    assert report["source_preflight"]["verified"] is True
    assert report["source_preflight"]["source_artifact_sha256"] == metadata[0]["sha256"]
    assert report["source_preflight"]["original_candidate_sha256"] == FROZEN_SHA
    assert report["source_preflight"]["quotes_read_after_source_preflight"] is True
    assert report["v2_diagnostic_previews_captured"] == 1
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["no_bet"] is True
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0


def test_original_forward_does_not_read_quotes_when_source_parent_is_invalid(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    raw, metadata = make_source_archive()
    calls = []

    def reject_parent(_archive, _quote_time):
        calls.append("parent")
        raise ValueError("source artifact parent run is not the verified original V2 collector")

    with pytest.raises(ValueError, match="verified original V2 collector"):
        capture_forward_with_source_preflight(
            metadata,
            as_of_utc=NOW,
            token="test-token",
            fetch_quotes=lambda: calls.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: calls.append("archive") or raw,
            verify_parent_run=reject_parent,
        )
    assert calls == ["parent"]


def test_original_forward_does_not_read_quotes_when_source_zip_sha_fails(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    raw, metadata = make_source_archive()
    calls = []

    with pytest.raises(ValueError, match="archive digest mismatch"):
        capture_forward_with_source_preflight(
            metadata,
            as_of_utc=NOW,
            token="test-token",
            fetch_quotes=lambda: calls.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: calls.append("archive") or raw + b"tampered",
            verify_parent_run=lambda archive, quote_time: (
                calls.append("parent") or _fully_verified_parent(archive, quote_time)
            ),
        )
    assert calls == ["parent", "archive"]


def test_original_forward_blocks_quote_when_parent_completed_after_quote(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    raw, metadata = make_source_archive()
    parent = _fully_verified_parent(
        metadata[0], NOW, completed="2026-10-14T06:30:00Z"
    )
    report = capture_forward_with_source_preflight(
        metadata,
        as_of_utc=NOW,
            token="test-token",
        fetch_quotes=lambda: [quote("2026-10-14T06:00:00Z")],
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=lambda _archive, _quote_time: parent,
    )
    assert report["source_preflight"]["verified"] is True
    assert report["v2_diagnostic_previews_captured"] == 0
    assert report["blocked_no_prior_source"] == 1
    assert report["rows"][0]["status"] == "NO_EARLIER_SOURCE_ARCHIVE"
    assert report["rows"][0]["v2_preview"] is None


def test_original_forward_does_not_fallback_to_older_archive_when_newest_sha_is_invalid(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    _allow_private_repository_for_test(monkeypatch)
    raw, metadata = make_source_archive()
    older = metadata[0]
    newer = {
        **older,
        "artifact_id": 124,
        "created_at": NOW - timedelta(minutes=1),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    calls = []

    def verify_parent(archive, quote_time):
        calls.append(("parent", archive["artifact_id"]))
        return _fully_verified_parent(archive, quote_time)

    def load_archive(artifact_id):
        calls.append(("archive", artifact_id))
        return raw + b"tampered" if artifact_id == 124 else raw

    with pytest.raises(ValueError, match="archive digest mismatch"):
        capture_forward_with_source_preflight(
            [older, newer],
            as_of_utc=NOW,
            token="test-token",
            fetch_quotes=lambda: calls.append(("quotes", None)) or [quote()],
            load_archive=load_archive,
            verify_parent_run=verify_parent,
        )

    # The newest source is authoritative for this attempt. Its failed digest
    # must stop the pipeline rather than silently falling back to older bytes.
    assert calls == [("parent", 124), ("archive", 124)]



def test_original_forward_cli_default_denies_before_archive_discovery_or_database_import(
    monkeypatch, tmp_path
):
    """Exercise main(), not only its helper: a default-deny CLI must touch no live boundary."""
    import builtins
    import sys
    import types
    import serie_a_v2_forward_capture as forward_module

    events = []
    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    monkeypatch.delenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(
        forward_module,
        "discover_archives",
        lambda **_kwargs: events.append("archive_discovery") or [],
    )
    monkeypatch.setitem(sys.modules, "database", types.SimpleNamespace(supabase=object()))

    real_import = builtins.__import__

    def tracked_import(name, *args, **kwargs):
        if name == "database":
            events.append("database_import")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "serie_a_v2_forward_capture.py",
            "--output", str(tmp_path / "report.json"),
            "--sources-output-dir", str(tmp_path / "sources"),
        ],
    )

    with pytest.raises(PermissionError, match="MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=true"):
        forward_module.main()

    assert events == []
    assert not (tmp_path / "report.json").exists()


def test_original_forward_cli_verifies_parent_and_zip_before_lazy_database_import(
    monkeypatch, tmp_path
):
    """Pin the real CLI wiring: source provenance and ZIP SHA precede DB import and quote read."""
    import builtins
    import sys
    import types
    import serie_a_v2_forward_capture as forward_module

    class FrozenNow(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is timezone.utc
            return cls(2026, 10, 14, 7, 0, tzinfo=timezone.utc)

    raw, metadata = make_source_archive()
    metadata[0]["created_at"] = FrozenNow(2026, 10, 13, 15, 0, tzinfo=timezone.utc)
    events = []
    fake_supabase = object()

    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(forward_module, "datetime", FrozenNow)

    def allow_private_repository(*, token):
        events.append("private_repository_check")
        assert token == "synthetic-token"
        return {"repository": "MaksimBlud/football-ai", "private": True}

    monkeypatch.setattr(forward_module, "require_private_repository", allow_private_repository)

    def discover_archives(*, token):
        events.append("archive_discovery")
        assert token == "synthetic-token"
        return metadata

    def verify_parent(archive, *, quote_time, token):
        events.append("parent_verification")
        assert archive["artifact_id"] == 123
        assert token == "synthetic-token"
        assert quote_time == FrozenNow(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
        return {
            "run_id": archive["run_id"],
            "run_head_sha": archive["head_sha"],
            "workflow_path": SOURCE_WORKFLOW_PATH,
            "head_branch": "main",
            "event": "push",
            "status": "completed",
            "conclusion": "success",
            "run_created_at_utc": "2026-10-13T14:40:00Z",
            "run_completed_at_utc": "2026-10-13T15:01:00Z",
        }

    def download_archive(artifact_id, *, token):
        events.append("archive_download_and_sha_input")
        assert artifact_id == 123
        assert token == "synthetic-token"
        return raw

    def read_quotes(client, *, now):
        events.append("saved_quote_reader")
        assert client is fake_supabase
        assert now == FrozenNow(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
        return [quote()]

    monkeypatch.setattr(forward_module, "_discover_archives_unchecked", discover_archives)
    monkeypatch.setattr(forward_module, "_verify_source_run_unchecked", verify_parent)
    monkeypatch.setattr(forward_module, "get_archive", download_archive)
    monkeypatch.setattr(forward_module, "fetch_saved_upcoming_serie_a_quotes", read_quotes)
    monkeypatch.setitem(sys.modules, "database", types.SimpleNamespace(supabase=fake_supabase))

    real_import = builtins.__import__

    def tracked_import(name, *args, **kwargs):
        if name == "database":
            events.append("database_import")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "serie_a_v2_forward_capture.py",
            "--output", str(tmp_path / "report.json"),
            "--sources-output-dir", str(tmp_path / "sources"),
        ],
    )

    forward_module.main()

    assert events == [
        "private_repository_check",
        "archive_discovery",
        "parent_verification",
        "archive_download_and_sha_input",
        "database_import",
        "saved_quote_reader",
    ]
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["source_preflight"]["verified"] is True
    assert report["source_preflight"]["source_artifact_sha256"] == metadata[0]["sha256"]
    assert report["quotes_seen"] == 1
    assert report["v2_diagnostic_previews_captured"] == 1
    assert report["eligible_for_frozen_prospective_cohort"] is False
    assert report["no_bet"] is True
    assert report["paid_provider_calls"] == 0
    assert report["supabase_writes"] == 0


def test_original_forward_cli_invalid_archive_sha_blocks_database_import_and_quote_read(
    monkeypatch, tmp_path
):
    """Exercise main(): a bad source ZIP digest must stop before DB import or quotes."""
    import builtins
    import sys
    import serie_a_v2_forward_capture as forward_module

    class FrozenNow(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is timezone.utc
            return cls(2026, 10, 14, 7, 0, tzinfo=timezone.utc)

    raw, metadata = make_source_archive()
    metadata[0]["created_at"] = FrozenNow(2026, 10, 13, 15, 0, tzinfo=timezone.utc)
    events = []

    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(forward_module, "datetime", FrozenNow)

    def allow_private_repository(*, token):
        events.append("private_repository_check")
        assert token == "synthetic-token"
        return {"repository": "MaksimBlud/football-ai", "private": True}

    monkeypatch.setattr(forward_module, "require_private_repository", allow_private_repository)

    def discover_archives(*, token):
        events.append("archive_discovery")
        assert token == "synthetic-token"
        return metadata

    def verify_parent(archive, quote_time, token):
        events.append("parent_verification")
        assert token == "synthetic-token"
        return _fully_verified_parent(
            archive, quote_time, completed="2026-10-13T15:01:00Z"
        )

    def tampered_archive(artifact_id, *, token):
        events.append("archive_download_and_sha_input")
        assert artifact_id == metadata[0]["artifact_id"]
        assert token == "synthetic-token"
        return raw + b"tampered"

    def forbidden_quote_read(*_args, **_kwargs):
        raise AssertionError("invalid source ZIP SHA must block saved quote access")

    monkeypatch.setattr(forward_module, "_discover_archives_unchecked", discover_archives)
    monkeypatch.setattr(forward_module, "_verify_source_run_unchecked", verify_parent)
    monkeypatch.setattr(forward_module, "get_archive", tampered_archive)
    monkeypatch.setattr(
        forward_module, "fetch_saved_upcoming_serie_a_quotes", forbidden_quote_read
    )

    real_import = builtins.__import__

    def tracked_import(name, *args, **kwargs):
        if name == "database":
            events.append("database_import")
            raise AssertionError("invalid source ZIP SHA must block database import")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    output = tmp_path / "report.json"
    sources = tmp_path / "sources"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "serie_a_v2_forward_capture.py",
            "--output",
            str(output),
            "--sources-output-dir",
            str(sources),
        ],
    )

    with pytest.raises(ValueError, match="archive digest mismatch"):
        forward_module.main()

    assert events == [
        "private_repository_check",
        "archive_discovery",
        "parent_verification",
        "archive_download_and_sha_input",
    ]
    assert not output.exists()
    assert not sources.exists()


class _FakeArtifactResponse:
    def __init__(self, status_code, url, *, headers=None, content=b"", history=()):
        self.status_code = status_code
        self.url = url
        self.headers = headers or {}
        self.content = content
        self.history = list(history)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

class _FakeRepositoryResponse:
    def __init__(self, url, *, private=True, full_name="MaksimBlud/football-ai"):
        self.url = url
        self.status_code = 200
        self.data = {"full_name": full_name, "private": private}

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


REPOSITORY_API_URL = "https://api.github.com/repos/MaksimBlud/football-ai"

def _with_private_repository(fake_get, *, private=True, full_name="MaksimBlud/football-ai"):
    def get(url, **kwargs):
        if url == REPOSITORY_API_URL:
            assert kwargs.get("allow_redirects") is False
            return _FakeRepositoryResponse(url, private=private, full_name=full_name)
        return fake_get(url, **kwargs)
    return get

def test_get_archive_requires_private_repository_before_source_zip_download(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []

    def public_repository_get(url, **kwargs):
        calls.append((url, kwargs))
        if url == REPOSITORY_API_URL:
            return _FakeRepositoryResponse(url, private=False)
        raise AssertionError("source ZIP must not be requested for a public repository")

    with pytest.raises(PermissionError, match="requires the exact GitHub repository to be private"):
        get_archive(123, token="synthetic-token", get=public_repository_get)

    assert len(calls) == 1
    assert calls[0][0] == REPOSITORY_API_URL
    assert calls[0][1]["allow_redirects"] is False

def test_get_archive_fetches_signed_storage_url_without_forwarding_github_token(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = "https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/123/zip"
    signed_url = (
        "https://productionresultssa0.blob.core.windows.net/"
        "actions-results/container/archive.zip?sig=synthetic"
    )
    archive_bytes = bytes.fromhex("504b0304") + b"synthetic-zip"
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if len(calls) == 1:
            return _FakeArtifactResponse(
                302, api_url, headers={"Location": signed_url}
            )
        return _FakeArtifactResponse(200, signed_url, content=archive_bytes)

    assert get_archive(123, token="synthetic-token", get=_with_private_repository(fake_get)) == archive_bytes
    assert len(calls) == 2
    assert calls[0][0] == api_url
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][1]["headers"]["Authorization"] == "Bearer synthetic-token"
    assert calls[1][0] == signed_url
    assert calls[1][1]["allow_redirects"] is False
    assert "headers" not in calls[1][1]


@pytest.mark.parametrize(
    "location",
    [
        "http://productionresultssa0.blob.core.windows.net/actions-results/a.zip?sig=x",
        "https://evil.example/actions-results/a.zip?sig=x",
        "https://productionresults.evil.blob.core.windows.net/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net/other/a.zip?sig=x",
        "https://user@productionresultssa0.blob.core.windows.net/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net:444/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net/actions-results/a.zip",
        "https://productionresultssa0.blob.core.windows.net/actions-results/../a.zip?sig=x",
    ],
)

def test_get_archive_rejects_untrusted_or_malformed_redirect_without_following(
    monkeypatch, location
):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = "https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/123/zip"
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _FakeArtifactResponse(302, api_url, headers={"Location": location})

    with pytest.raises(ValueError, match="redirect"):
        get_archive(123, token="synthetic-token", get=_with_private_repository(fake_get))
    assert len(calls) == 1
    assert calls[0][1]["allow_redirects"] is False

def test_get_archive_rejects_missing_location_before_storage_request(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = "https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/123/zip"
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeArtifactResponse(302, api_url)

    with pytest.raises(ValueError, match="Location"):
        get_archive(123, token="synthetic-token", get=_with_private_repository(fake_get))
    assert calls == [api_url]

def test_get_archive_rejects_api_200_instead_of_documented_redirect(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = "https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/123/zip"
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeArtifactResponse(200, api_url, content=b"not-a-redirect")

    with pytest.raises(ValueError, match="HTTP 302"):
        get_archive(123, token="synthetic-token", get=_with_private_repository(fake_get))
    assert calls == [api_url]

def test_get_archive_rejects_second_redirect_without_following_or_token(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = "https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/123/zip"
    signed_url = (
        "https://productionresultssa0.blob.core.windows.net/"
        "actions-results/container/archive.zip?sig=synthetic"
    )
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if len(calls) == 1:
            return _FakeArtifactResponse(302, api_url, headers={"Location": signed_url})
        return _FakeArtifactResponse(
            302, signed_url, headers={"Location": "https://evil.example/next"}
        )

    with pytest.raises(ValueError, match="HTTP 200"):
        get_archive(123, token="synthetic-token", get=_with_private_repository(fake_get))
    assert len(calls) == 2
    assert "headers" not in calls[1][1]
    assert calls[1][1]["allow_redirects"] is False

def test_private_repository_guard_accepts_only_exact_private_repository(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    url_value = "https://api.github.com/repos/MaksimBlud/football-ai"
    calls = []

    class Response:
        status_code = 200
        def __init__(self, data):
            self.url = url_value
            self.data = data
        def json(self):
            return self.data

    def get(requested_url, headers, timeout, allow_redirects):
        calls.append((requested_url, headers, timeout, allow_redirects))
        assert headers["Authorization"] == "Bearer test-token"
        return Response({"full_name": "MaksimBlud/football-ai", "private": True})

    assert require_private_repository(token="test-token", get=get) == {
        "repository": "MaksimBlud/football-ai", "private": True
    }
    assert len(calls) == 1
    assert calls[0][0] == url_value
    assert calls[0][3] is False

def test_private_repository_guard_rejects_public_repository_before_source_access(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    url_value = "https://api.github.com/repos/MaksimBlud/football-ai"

    class Response:
        status_code = 200
        url = url_value
        def json(self):
            return {"full_name": "MaksimBlud/football-ai", "private": False}

    with pytest.raises(PermissionError, match="requires the exact GitHub repository to be private"):
        require_private_repository(
            token="test-token",
            get=lambda requested_url, headers, timeout, allow_redirects: Response(),
        )

def test_private_repository_guard_rejects_wrong_repository_identity(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    url_value = "https://api.github.com/repos/MaksimBlud/football-ai"

    class Response:
        status_code = 200
        url = url_value
        def json(self):
            return {"full_name": "attacker/other-repo", "private": True}

    with pytest.raises(ValueError, match="identity mismatch"):
        require_private_repository(
            token="test-token",
            get=lambda requested_url, headers, timeout, allow_redirects: Response(),
        )

def test_private_repository_guard_rejects_redirect_without_parsing_body(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    url_value = "https://api.github.com/repos/MaksimBlud/football-ai"

    class Response:
        status_code = 302
        url = url_value
        def json(self):
            raise AssertionError("redirect body must not be parsed")

    with pytest.raises(ValueError, match="HTTP 302"):
        require_private_repository(
            token="test-token",
            get=lambda requested_url, headers, timeout, allow_redirects: Response(),
        )

def test_private_repository_guard_rejects_unexpected_final_url(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")

    class Response:
        status_code = 200
        url = "https://evil.example/repos/MaksimBlud/football-ai"
        def json(self):
            raise AssertionError("unexpected response URL must be rejected before parsing")

    with pytest.raises(ValueError, match="response URL"):
        require_private_repository(
            token="test-token",
            get=lambda requested_url, headers, timeout, allow_redirects: Response(),
        )

def test_original_forward_cli_checks_private_repository_before_archive_discovery(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    output = tmp_path / "output" / "forward.json"
    sources = tmp_path / "sources"
    monkeypatch.setattr(sys, "argv", [
        "serie_a_v2_forward_capture.py",
        "--output", str(output),
        "--sources-output-dir", str(sources),
    ])
    calls = []

    def reject_public_repository(*, token):
        calls.append(("privacy", token))
        raise PermissionError("repository is public")

    def forbidden_discovery(*, token):
        calls.append(("archives", token))
        raise AssertionError("archive discovery must not run for a public repository")

    monkeypatch.setattr(forward_capture, "require_private_repository", reject_public_repository)
    monkeypatch.setattr(forward_capture, "_discover_archives_unchecked", forbidden_discovery)

    with pytest.raises(PermissionError, match="repository is public"):
        forward_capture.main()

    assert calls == [("privacy", "test-token")]
    assert not output.parent.exists()
    assert not sources.exists()

def test_original_forward_cli_keeps_live_access_gate_before_private_metadata(monkeypatch, tmp_path):
    monkeypatch.delenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    output = tmp_path / "output" / "forward.json"
    sources = tmp_path / "sources"
    monkeypatch.setattr(sys, "argv", [
        "serie_a_v2_forward_capture.py",
        "--output", str(output),
        "--sources-output-dir", str(sources),
    ])
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("no metadata or archive access before live-access approval")

    monkeypatch.setattr(forward_capture, "require_private_repository", forbidden)
    monkeypatch.setattr(forward_capture, "_discover_archives_unchecked", forbidden)

    with pytest.raises(PermissionError, match="MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=true"):
        forward_capture.main()

    assert calls == []
    assert not output.parent.exists()
    assert not sources.exists()

def test_direct_github_metadata_helpers_require_private_repository_before_http(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []

    def reject_public_repository(*, token, get):
        calls.append(("private", token))
        raise PermissionError("private repository required")

    def forbidden_http(*args, **kwargs):
        calls.append(("http", args[0] if args else None))
        raise AssertionError("GitHub metadata request must not run for a public repository")

    monkeypatch.setattr(forward_capture, "require_private_repository", reject_public_repository)
    with pytest.raises(PermissionError, match="private repository required"):
        forward_capture._github_json(
            "https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts",
            token="test-token", get=forbidden_http,
        )
    with pytest.raises(PermissionError, match="private repository required"):
        discover_archives(token="test-token", get=forbidden_http)
    _, metadata = make_source_archive()
    with pytest.raises(PermissionError, match="private repository required"):
        verify_source_run(
            metadata[0], quote_time=parse_utc("2026-10-14T06:00:00Z"),
            token="test-token", get=forbidden_http,
        )
    assert calls == [
        ("private", "test-token"),
        ("private", "test-token"),
        ("private", "test-token"),
    ]


def test_direct_callback_forward_preflight_requires_private_repository_before_callbacks(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []

    def reject_public_repository(*, token, get):
        calls.append(("private", token))
        raise PermissionError("private repository required")

    monkeypatch.setattr(forward_capture, "require_private_repository", reject_public_repository)
    with pytest.raises(PermissionError, match="private repository required"):
        capture_forward_with_source_preflight(
            [],
            as_of_utc=NOW,
            token="test-token",
            fetch_quotes=lambda: calls.append(("quotes", None)),
            load_archive=lambda _artifact_id: calls.append(("archive", None)),
            verify_parent_run=lambda *_args: calls.append(("parent", None)),
        )
    assert calls == [("private", "test-token")]

