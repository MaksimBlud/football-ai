"""Original frozen V2 forward-only capture, using only synthetic pre-2026/27 scores."""
import hashlib
from io import BytesIO
import json
from datetime import datetime, timezone
import zipfile

import pytest

from serie_a_v2_frozen_shadow_preview import parse_utc

from serie_a_v2_live_diagnostic_report import _source_codes, PUBLIC_BASE
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_forward_capture import (
    ARTIFACT_NAME, ARCHIVE_REPORT, SOURCE_DIR,
    discover_archives, prepare_forward_capture, verify_source_run,
    capture_forward_with_source_preflight, SOURCE_WORKFLOW_PATH,
)

NOW = datetime(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
AFTER_CAPTURE = datetime(2026, 10, 14, 6, 0, tzinfo=timezone.utc)


def quote(ts="2026-10-14T06:00:00Z"):
    return {
        "league": "SERIE_A", "event_id": "new-fixture-original-v2",
        "home_team": "Juventus", "away_team": "Napoli",
        "snapshot_time_utc": ts,
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
        "run_completed_at_utc": "2026-10-13T15:01:00Z",
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_id": 456,
        "run_head_sha": "a" * 40,
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
    assert report["eligible_for_product_publication"] is False
    assert report["no_bet"] is True
    row = report["rows"][0]
    assert row["source_artifact_sha256"] == metadata[0]["sha256"]
    assert row["status"] == "SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY"
    assert row["v2_preview"]["model_candidate_sha256"] == FROZEN_SHA
    assert row["v2_preview"]["market_1x2"] == pytest.approx(
        row["v2_preview"]["active_market_fallback_1x2"]
    )
    assert row["v2_preview"]["eligible_for_frozen_prospective_cohort"] is False


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


def test_github_source_catalog_requires_main_sha_and_does_not_trust_missing_digest():
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


def test_successful_exact_source_workflow_and_prequote_completion_required():
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


def test_catalog_rejects_missing_parent_run_identity_even_with_valid_digest():
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

def test_verified_forward_source_archives_are_published_atomically(tmp_path):
    raw, metadata = make_source_archive()
    target = tmp_path / "source-archives"
    report = prepare_forward_capture(
        [quote()],
        metadata,
        as_of_utc=NOW,
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=fake_verified_parent_run,
        write_archives_to=target,
    )
    published = list(target.glob("source_artifact_*.zip"))
    assert report["v2_diagnostic_previews_captured"] == 1
    assert len(published) == 1
    assert published[0].read_bytes() == raw
    assert not list(tmp_path.glob(".source-archives.staging-*"))


def test_unverified_forward_source_archive_is_never_published(tmp_path):
    raw, metadata = make_source_archive()
    target = tmp_path / "source-archives"
    with pytest.raises(ValueError, match="digest mismatch"):
        prepare_forward_capture(
            [quote()],
            metadata,
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: raw + b"tampered",
            verify_parent_run=fake_verified_parent_run,
            write_archives_to=target,
        )
    assert not target.exists()
    assert not list(tmp_path.glob(".source-archives.staging-*"))


def test_later_quote_failure_discards_earlier_verified_source_archives(tmp_path):
    raw, metadata = make_source_archive()
    target = tmp_path / "source-archives"
    later_bad_quote = {**quote("2026-10-14T06:05:00Z"), "result": "H"}
    with pytest.raises(ValueError, match="outcomes or settlement fields forbidden"):
        prepare_forward_capture(
            [quote(), later_bad_quote],
            metadata,
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: raw,
            verify_parent_run=fake_verified_parent_run,
            write_archives_to=target,
        )
    assert not target.exists()
    assert not list(tmp_path.glob(".source-archives.staging-*"))


def test_nonempty_forward_source_output_is_preserved_without_callbacks(tmp_path):
    _, metadata = make_source_archive()
    target = tmp_path / "source-archives"
    target.mkdir()
    marker = target / "owner-evidence.txt"
    marker.write_text("preserve", encoding="utf-8")
    calls = []
    with pytest.raises(FileExistsError, match="must be absent or empty"):
        prepare_forward_capture(
            [quote()],
            metadata,
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: calls.append("load"),
            verify_parent_run=lambda *_args, **_kwargs: calls.append("verify"),
            write_archives_to=target,
        )
    assert calls == []
    assert marker.read_text(encoding="utf-8") == "preserve"




def test_original_forward_source_sha_and_parent_are_verified_before_saved_quote_reader():
    raw, metadata = make_source_archive()
    events = []

    def verify_parent(archive, quote_time):
        events.append(("parent", quote_time))
        return fake_verified_parent_run(archive, quote_time)

    def load_archive(artifact_id):
        events.append(("archive", artifact_id))
        return raw

    def fetch_quotes():
        events.append(("quotes", None))
        return [quote()]

    report = capture_forward_with_source_preflight(
        metadata,
        as_of_utc=NOW,
        require_access_fn=lambda: None,
        fetch_quotes=fetch_quotes,
        load_archive=load_archive,
        verify_parent_run=verify_parent,
    )

    assert [name for name, _ in events] == ["parent", "archive", "quotes"]
    assert report["source_preflight"]["verified"] is True
    assert report["source_preflight"]["source_artifact_sha256"] == metadata[0]["sha256"]
    assert report["source_preflight"]["quotes_read_after_source_preflight"] is True
    assert report["v2_diagnostic_previews_captured"] == 1
    assert report["rows"][0]["source_artifact_sha256"] == metadata[0]["sha256"]


def test_original_forward_does_not_read_quotes_without_any_prior_source_archive():
    calls = []

    with pytest.raises(RuntimeError, match="no original V2 source archive before quote read"):
        capture_forward_with_source_preflight(
            [],
            as_of_utc=NOW,
            require_access_fn=lambda: None,
            fetch_quotes=lambda: calls.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: calls.append("archive"),
            verify_parent_run=lambda *_args: calls.append("parent"),
        )

    assert calls == []


def test_original_forward_does_not_read_quotes_when_parent_workflow_is_unverified():
    raw, metadata = make_source_archive()
    calls = []

    def reject_parent(_archive, _quote_time):
        calls.append("parent")
        raise ValueError("source artifact parent run is not the verified original V2 collector")

    with pytest.raises(ValueError, match="verified original V2 collector"):
        capture_forward_with_source_preflight(
            metadata,
            as_of_utc=NOW,
            require_access_fn=lambda: None,
            fetch_quotes=lambda: calls.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: calls.append("archive") or raw,
            verify_parent_run=reject_parent,
        )

    assert calls == ["parent"]


def test_original_forward_does_not_read_quotes_when_source_archive_sha_fails():
    raw, metadata = make_source_archive()
    calls = []

    with pytest.raises(ValueError, match="archive digest mismatch"):
        capture_forward_with_source_preflight(
            metadata,
            as_of_utc=NOW,
            require_access_fn=lambda: None,
            fetch_quotes=lambda: calls.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: calls.append("archive") or raw + b"tampered",
            verify_parent_run=fake_verified_parent_run,
        )

    assert calls == ["archive"]


def test_original_forward_source_preflight_does_not_backfill_quote_older_than_archive():
    raw, metadata = make_source_archive()
    calls = []

    report = capture_forward_with_source_preflight(
        metadata,
        as_of_utc=NOW,
        require_access_fn=lambda: None,
        fetch_quotes=lambda: calls.append("quotes") or [quote("2026-10-13T14:48:53Z")],
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=fake_verified_parent_run,
    )

    assert calls == ["quotes"]
    assert report["source_preflight"]["verified"] is True
    assert report["v2_diagnostic_previews_captured"] == 0
    assert report["blocked_no_prior_source"] == 1
    assert report["rows"][0]["v2_preview"] is None



def test_original_forward_source_preflight_runs_direct_access_gate_before_parent_archive_and_quotes(monkeypatch):
    import sys
    from types import ModuleType

    raw, metadata = make_source_archive()
    events = []
    access_module = ModuleType("market_anchor_v2_direct_access")
    access_module.require_v2_inference_access = lambda: events.append("access")
    monkeypatch.setitem(sys.modules, "market_anchor_v2_direct_access", access_module)

    def verify_parent(archive, quote_time):
        events.append("parent")
        return fake_verified_parent_run(archive, quote_time)

    def load_archive(artifact_id):
        events.append("archive")
        return raw

    def fetch_quotes():
        events.append("quotes")
        return [quote()]

    report = capture_forward_with_source_preflight(
        metadata,
        as_of_utc=NOW,
        fetch_quotes=fetch_quotes,
        load_archive=load_archive,
        verify_parent_run=verify_parent,
    )

    assert events == ["access", "parent", "archive", "quotes"]
    assert report["source_preflight"]["verified"] is True
    assert report["quotes_read_after_source_preflight"] if "quotes_read_after_source_preflight" in report else report["source_preflight"]["quotes_read_after_source_preflight"]


def test_original_forward_source_preflight_denies_before_parent_archive_or_quote_callbacks(monkeypatch):
    import sys
    from types import ModuleType

    events = []

    def deny_access():
        events.append("access")
        raise PermissionError("provider/private-storage access is not cleared")

    access_module = ModuleType("market_anchor_v2_direct_access")
    access_module.require_v2_inference_access = deny_access
    monkeypatch.setitem(sys.modules, "market_anchor_v2_direct_access", access_module)

    with pytest.raises(PermissionError, match="provider/private-storage access is not cleared"):
        capture_forward_with_source_preflight(
            [],
            as_of_utc=NOW,
            fetch_quotes=lambda: events.append("quotes") or [quote()],
            load_archive=lambda _artifact_id: events.append("archive"),
            verify_parent_run=lambda *_args: events.append("parent"),
        )

    assert events == ["access"]
