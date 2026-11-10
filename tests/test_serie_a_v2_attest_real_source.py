"""Free actual-source attestation behavior with synthetic pre-2026 history only."""
from datetime import datetime, timezone, tzinfo
import hashlib
from io import BytesIO
import json
import sys

import serie_a_v2_attest_real_source as attestor
import zipfile

import pytest

from serie_a_v2_attest_real_source import attest_latest_source
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_forward_capture import SOURCE_WORKFLOW_PATH
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes
from serie_a_v2_prequote_source_archive_gate import ARCHIVE_REPORT, SOURCE_DIR



@pytest.fixture(autouse=True)
def allow_synthetic_private_archive_read_scope(monkeypatch):
    monkeypatch.setattr(
        attestor,
        "_require_private_source_archive_read_scope",
        lambda: {"access_scope": "SYNTHETIC_TEST_ONLY", "artifact_privacy": {"private": True}},
    )


NOW = datetime(2026, 10, 14, 16, tzinfo=timezone.utc)


def source_fixture():
    sources = {}
    manifest = []
    for code in _source_codes():
        year = 2000 + int(code[:2])
        raw = (
            "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
            f"01/10/{year},Juventus,Napoli,2,1,H,3,4,2,1,0,0\n"
        ).encode("ascii")
        name = f"serie_a_{code}.csv"
        sources[SOURCE_DIR+name] = raw
        manifest.append({
            "season_code":code,
            "source_url":f"{PUBLIC_BASE}/{code}/I1.csv",
            "archived_source_name":name,
            "source_observed_at_utc":"2026-10-13T15:00:00Z",
            "csv_sha256":hashlib.sha256(raw).hexdigest(),
            "completed_source_rows":1,
        })
    report = {
        "frozen_candidate_sha256":FROZEN_SHA,
        "2026_27_public_results_downloaded":False,
        "protect_2026_27_prospective_outcomes":True,
        "public_source_files":manifest,
    }
    buffer = BytesIO()
    with zipfile.ZipFile(buffer,"w") as zipfile_writer:
        zipfile_writer.writestr(ARCHIVE_REPORT,json.dumps(report))
        for path,raw in sources.items():
            zipfile_writer.writestr(path,raw)
    data = buffer.getvalue()
    meta = [{
        "artifact_id":765,
        "run_id":432,
        "head_sha":"a"*40,
        "sha256":hashlib.sha256(data).hexdigest(),
        "created_at":datetime(2026,10,13,15,5,tzinfo=timezone.utc),
    }]
    return data, meta


def valid_parent(meta, quote_time, token):
    assert token=="test-token"
    assert meta["run_id"]==432
    assert quote_time==NOW
    return {"run_completed_at_utc":"2026-10-13T15:05:30+00:00",
            "workflow_path":SOURCE_WORKFLOW_PATH}


def test_complete_attestation_proves_actual_zip_contents_without_any_quotes():
    data, meta = source_fixture()
    calls = []
    proof = attest_latest_source(
        token="test-token", now=NOW,
        discover=lambda **kwargs: meta,
        load=lambda artifact_id,token:
            calls.append(artifact_id) or data,
        verify_run=valid_parent,
    )
    assert calls==[765]
    assert proof["verified_pre_prospective_source_files"]==10
    assert proof["verified_historical_results"]==10
    assert proof["verified_original_v2_sha256"]==FROZEN_SHA
    assert proof["source_run_provenance"]["workflow_path"]==SOURCE_WORKFLOW_PATH
    assert proof["source_archive_sha256_verified"] is True
    assert proof["quotes_read"]==proof["forecasts_created"]==0
    assert proof["paid_provider_calls"]==0
    assert proof["supabase_reads"]==proof["supabase_writes"]==0
    assert proof["eligible_for_frozen_prospective_cohort"] is False
    assert proof["no_bet"] is True


def test_attestation_fails_closed_without_earlier_verified_source():
    raw, meta = source_fixture()
    with pytest.raises(RuntimeError, match="no original historical"):
        attest_latest_source(
            token="test-token", now=NOW,
            discover=lambda **kwargs: [],
            load=lambda *args,**kwargs: raw,
            verify_run=valid_parent,
        )
    with pytest.raises(RuntimeError, match="no original historical"):
        attest_latest_source(
            token="test-token",
            now=datetime(2026,10,13,14,tzinfo=timezone.utc),
            discover=lambda **kwargs: meta,
            load=lambda *args,**kwargs: raw,
            verify_run=valid_parent,
        )


def test_attestation_does_not_publish_tampered_or_unverified_archive():
    raw, meta = source_fixture()
    calls=[]
    with pytest.raises(ValueError, match="source workflow parent attestation missing"):
        attest_latest_source(
            token="test-token", now=NOW, discover=lambda **kwargs:meta,
            load=lambda artifact_id,token:calls.append(artifact_id) or raw,
            verify_run=lambda m,quote_time,token: {},
        )
    assert calls==[]
    with pytest.raises(ValueError, match="digest mismatch"):
        attest_latest_source(
            token="test-token", now=NOW, discover=lambda **kwargs:meta,
            load=lambda artifact_id,token: raw+b"tampered",
            verify_run=valid_parent,
        )


def test_invalid_datetime_is_not_silently_assumed_utc():
    raw, meta=source_fixture()
    with pytest.raises(ValueError,match="aware UTC clock"):
        attest_latest_source(
            token="test-token",now=datetime(2026,10,14,16),
            discover=lambda **kwargs:meta,
            load=lambda *a,**kw:raw,verify_run=valid_parent,
        )



class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "NO_OFFSET"


def test_no_offset_timezone_is_not_silently_assumed_utc():
    invalid_clock = datetime(2026, 10, 14, 16, tzinfo=_NoOffsetTimezone())
    with pytest.raises(ValueError, match="aware UTC clock"):
        attest_latest_source(
            token="test-token",
            now=invalid_clock,
            discover=lambda **kwargs: pytest.fail("archive discovery must not run"),
            load=lambda *args, **kwargs: pytest.fail("archive must not load"),
            verify_run=lambda *args, **kwargs: pytest.fail("parent verification must not run"),
        )


def test_main_blocks_before_github_archive_discovery_when_private_source_scope_is_denied(monkeypatch, tmp_path):
    output = tmp_path / "blocked.json"
    monkeypatch.setenv("GITHUB_REPOSITORY", attestor.REPOSITORY)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        sys, "argv",
        ["serie_a_v2_attest_real_source.py", "--output", str(output)],
    )
    monkeypatch.setattr(
        attestor,
        "_require_private_source_archive_read_scope",
        lambda: (_ for _ in ()).throw(PermissionError("private source archive scope not confirmed")),
    )
    monkeypatch.setattr(
        attestor,
        "discover_archives",
        lambda **kwargs: pytest.fail("archive discovery must not run before source/privacy approval"),
    )

    attestor.main()

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "SOURCE_CAPTURE_SCOPE_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["operation"] == "SERIE_A_ORIGINAL_V2_SOURCE_ATTESTATION"
    assert report["block_reason"] == "private source archive scope not confirmed"
    assert report["public_http_requests"] == 0
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["quotes_read"] == 0
    assert report["forecasts_created"] == 0


def test_attestation_checks_source_archive_scope_before_injected_discovery_or_load(monkeypatch):
    calls = []

    def deny():
        calls.append("source_privacy")
        raise PermissionError("source archive scope denied")

    monkeypatch.setattr(attestor, "_require_private_source_archive_read_scope", deny)
    with pytest.raises(PermissionError, match="source archive scope denied"):
        attest_latest_source(
            token="test-token",
            now=NOW,
            discover=lambda **kwargs: pytest.fail("discovery must follow source/privacy gate"),
            load=lambda *args, **kwargs: pytest.fail("archive download must follow source/privacy gate"),
            verify_run=lambda *args, **kwargs: pytest.fail("parent verification must follow source/privacy gate"),
        )
    assert calls == ["source_privacy"]


def test_attestation_can_use_source_only_archive_scope_without_frozen_inference(monkeypatch):
    from serie_a_v2_forward_capture import _require_private_source_archive_read_scope
    import market_anchor_v2_source_rights as inference_rights
    monkeypatch.setattr(attestor, "_require_private_source_archive_read_scope", _require_private_source_archive_read_scope)
    import market_anchor_v2_source_capture_rights as source_rights
    import market_anchor_v2_artifact_privacy as privacy

    calls = []

    def deny_inference():
        calls.append("inference")
        raise PermissionError("inference scope intentionally unresolved")

    def allow_source_only():
        calls.append("source_only")
        return {"source_capture_scope": "SYNTHETIC_TEST_ONLY"}

    monkeypatch.setattr(inference_rights, "require_personal_research_inference_scope", deny_inference)
    monkeypatch.setattr(source_rights, "require_personal_research_source_capture_scope", allow_source_only)
    monkeypatch.setattr(
        privacy,
        "require_private_repository_for_source_artifacts",
        lambda: calls.append("private") or {"private": True},
    )

    with pytest.raises(RuntimeError, match="no original historical"):
        attest_latest_source(
            token="test-token",
            now=NOW,
            discover=lambda **kwargs: calls.append("discover") or [],
            load=lambda *args, **kwargs: pytest.fail("no archive should be loaded"),
            verify_run=lambda *args, **kwargs: pytest.fail("no parent should be verified"),
        )
    assert calls == ["inference", "source_only", "private", "discover"]
