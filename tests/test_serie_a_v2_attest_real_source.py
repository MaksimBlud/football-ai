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
def allow_synthetic_v2_access_scopes(monkeypatch):
    """Offline fixtures use synthetic permissions; this is not provider authorization."""
    import market_anchor_v2_source_rights as inference_rights
    import market_anchor_v2_source_capture_rights as capture_rights
    import market_anchor_v2_artifact_privacy as privacy

    monkeypatch.setattr(
        inference_rights,
        "require_personal_research_inference_scope",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )
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
            "workflow_path":SOURCE_WORKFLOW_PATH,
            "run_id":meta["run_id"], "run_head_sha":meta["head_sha"]}


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


def test_main_blocks_before_github_archive_discovery_when_research_scope_is_denied(monkeypatch, tmp_path):
    output = tmp_path / "blocked.json"
    monkeypatch.setenv("GITHUB_REPOSITORY", attestor.REPOSITORY)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        sys, "argv",
        ["serie_a_v2_attest_real_source.py", "--output", str(output)],
    )
    import market_anchor_v2_direct_access as direct_access
    monkeypatch.setattr(
        direct_access,
        "require_v2_source_capture_access",
        lambda: (_ for _ in ()).throw(PermissionError("research scope not confirmed")),
    )
    monkeypatch.setattr(
        attestor,
        "attest_latest_source",
        lambda **kwargs: pytest.fail("archive discovery/download must not run before rights approval"),
    )

    attestor.main()

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["operation"] == "SERIE_A_ORIGINAL_V2_SOURCE_ATTESTATION"
    assert report["block_reason"] == "research scope not confirmed"
    assert report["public_http_requests"] == 0
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["quotes_read"] == 0
    assert report["forecasts_created"] == 0


def test_attestation_skips_newer_failed_parent_and_uses_older_verified_archive():
    raw, meta = source_fixture()
    older = meta[0]
    newer = {
        **older,
        "artifact_id": 766,
        "run_id": 433,
        "head_sha": "b" * 40,
        "created_at": datetime(2026, 10, 13, 15, 6, tzinfo=timezone.utc),
    }
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        if candidate["artifact_id"] == 766:
            raise ValueError("source artifact parent run is not the verified original V2 collector")
        return valid_parent(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return raw

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [("verify", 766), ("verify", 765), ("load", 765)]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    assert proof["source_candidates_examined"] == 2
    assert proof["rejected_source_artifacts"][0]["artifact_id"] == 766
    assert proof["quotes_read"] == proof["forecasts_created"] == 0


def test_attestation_skips_newer_bad_digest_and_uses_older_verified_archive():
    raw, meta = source_fixture()
    older = meta[0]
    newer = {
        **older,
        "artifact_id": 766,
        "run_id": 433,
        "head_sha": "b" * 40,
        "created_at": datetime(2026, 10, 13, 15, 6, tzinfo=timezone.utc),
    }
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        if candidate["artifact_id"] == 766:
            return {
                "run_completed_at_utc": "2026-10-13T15:06:30Z",
                "workflow_path": SOURCE_WORKFLOW_PATH,
                "run_id": 433,
                "run_head_sha": "b" * 40,
            }
        return valid_parent(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return raw + b"tampered" if artifact_id == 766 else raw

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [
        ("verify", 766), ("load", 766),
        ("verify", 765), ("load", 765),
    ]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    assert proof["rejected_source_artifacts"][0]["reason"].endswith("digest mismatch")
    assert proof["source_archive_sha256_verified"] is True


def test_attestation_rejects_parent_that_completed_after_archive_or_after_check_time():
    raw, meta = source_fixture()

    def late_parent(candidate, quote_time, token):
        return {
            "run_completed_at_utc": "2026-10-14T16:00:01Z",
            "workflow_path": SOURCE_WORKFLOW_PATH,
            "run_id": candidate["run_id"],
            "run_head_sha": candidate["head_sha"],
        }

    with pytest.raises(ValueError, match="no fully verified.*completion time"):
        attest_latest_source(
            token="test-token",
            now=NOW,
            discover=lambda **kwargs: meta,
            load=lambda artifact_id, token: raw,
            verify_run=late_parent,
        )

def _http_error_with_status(status_code):
    from requests import HTTPError
    from types import SimpleNamespace

    error = HTTPError(f"HTTP {status_code}")
    error.response = SimpleNamespace(status_code=status_code)
    return error


def _valid_parent_for_candidate(candidate, quote_time, token):
    from datetime import timedelta

    assert token == "test-token"
    assert quote_time == NOW
    completed = candidate["created_at"] + timedelta(seconds=30)
    return {
        "run_completed_at_utc": completed.isoformat(),
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_id": candidate["run_id"],
        "run_head_sha": candidate["head_sha"],
    }


def _newer_candidate(older, *, digest=None):
    return {
        **older,
        "artifact_id": 766,
        "run_id": 433,
        "head_sha": "b" * 40,
        "sha256": digest or older["sha256"],
        "created_at": datetime(2026, 10, 13, 15, 6, tzinfo=timezone.utc),
    }


def test_attestation_skips_missing_newer_artifact_404_and_uses_older_verified_archive():
    raw, meta = source_fixture()
    older = meta[0]
    newer = _newer_candidate(older)
    events = []

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        if artifact_id == 766:
            raise _http_error_with_status(404)
        return raw

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        return _valid_parent_for_candidate(candidate, quote_time, token)

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [
        ("verify", 766), ("load", 766),
        ("verify", 765), ("load", 765),
    ]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    assert proof["rejected_source_artifacts"][0]["artifact_id"] == 766
    assert proof["rejected_source_artifacts"][0]["error_type"] == "HTTPError"
    assert proof["quotes_read"] == proof["forecasts_created"] == 0


def test_attestation_does_not_fallback_on_newer_artifact_http_503():
    raw, meta = source_fixture()
    older = meta[0]
    newer = _newer_candidate(older)
    events = []

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        if artifact_id == 766:
            raise _http_error_with_status(503)
        return raw

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        return _valid_parent_for_candidate(candidate, quote_time, token)

    with pytest.raises(Exception) as error:
        attest_latest_source(
            token="test-token",
            now=NOW,
            discover=lambda **kwargs: [older, newer],
            load=load,
            verify_run=verify,
        )

    from requests import HTTPError
    assert isinstance(error.value, HTTPError)
    assert events == [("verify", 766), ("load", 766)]


def test_attestation_skips_corrupt_newer_zip_with_matching_digest_and_uses_older():
    raw, meta = source_fixture()
    older = meta[0]
    corrupt = b"not-a-valid-zip-archive"
    newer = _newer_candidate(older, digest=hashlib.sha256(corrupt).hexdigest())
    events = []

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return corrupt if artifact_id == 766 else raw

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        return _valid_parent_for_candidate(candidate, quote_time, token)

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [
        ("verify", 766), ("load", 766),
        ("verify", 765), ("load", 765),
    ]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    assert proof["rejected_source_artifacts"][0]["error_type"] == "BadZipFile"
    assert proof["source_archive_sha256_verified"] is True

@pytest.mark.parametrize("status_code", [404, 503])
def test_attestation_handles_parent_run_http_errors_before_archive_download(status_code):
    raw, meta = source_fixture()
    older = meta[0]
    newer = _newer_candidate(older)
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        if candidate["artifact_id"] == 766:
            raise _http_error_with_status(status_code)
        return _valid_parent_for_candidate(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return raw

    if status_code == 404:
        proof = attest_latest_source(
            token="test-token",
            now=NOW,
            discover=lambda **kwargs: [older, newer],
            load=load,
            verify_run=verify,
        )
        assert events == [
            ("verify", 766),
            ("verify", 765),
            ("load", 765),
        ]
        assert proof["source_artifact_id"] == 765
        assert proof["source_candidate_fallback_used"] is True
        assert proof["rejected_source_artifacts"][0]["artifact_id"] == 766
        assert proof["rejected_source_artifacts"][0]["error_type"] == "HTTPError"
        assert proof["quotes_read"] == proof["forecasts_created"] == 0
    else:
        from requests import HTTPError

        with pytest.raises(HTTPError) as error:
            attest_latest_source(
                token="test-token",
                now=NOW,
                discover=lambda **kwargs: [older, newer],
                load=load,
                verify_run=verify,
            )
        assert error.value.response.status_code == 503
        assert events == [("verify", 766)]

@pytest.mark.parametrize(
    "malformation",
    ["root_not_object", "non_object_audit_entry", "missing_observation_time"],
)
def test_attestation_skips_malformed_manifest_and_uses_older_verified_archive(malformation):
    raw, meta = source_fixture()
    older = meta[0]
    with zipfile.ZipFile(BytesIO(raw), "r") as source:
        members = {
            name: source.read(name)
            for name in source.namelist()
        }
    report = json.loads(members[ARCHIVE_REPORT])
    if malformation == "root_not_object":
        replacement = []
    elif malformation == "non_object_audit_entry":
        report["public_source_files"][0] = None
        replacement = report
    else:
        del report["public_source_files"][0]["source_observed_at_utc"]
        replacement = report
    members[ARCHIVE_REPORT] = json.dumps(replacement).encode("utf-8")

    malformed_buffer = BytesIO()
    with zipfile.ZipFile(malformed_buffer, "w") as target:
        for name, content in members.items():
            target.writestr(name, content)
    malformed_raw = malformed_buffer.getvalue()
    newer = _newer_candidate(
        older,
        digest=hashlib.sha256(malformed_raw).hexdigest(),
    )
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        return _valid_parent_for_candidate(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return malformed_raw if artifact_id == 766 else raw

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [
        ("verify", 766), ("load", 766),
        ("verify", 765), ("load", 765),
    ]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    assert proof["rejected_source_artifacts"][0]["artifact_id"] == 766
    assert proof["rejected_source_artifacts"][0]["error_type"] == "ValueError"
    assert proof["quotes_read"] == proof["forecasts_created"] == 0


# Uses the exact RuntimeError emitted by the original guarded GitHub JSON boundary.

def test_attestation_skips_guarded_runtime_http_404_parent_and_uses_older_verified_archive():
    raw, meta = source_fixture()
    older = meta[0]
    newer = _newer_candidate(older)
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        if candidate["artifact_id"] == 766:
            raise RuntimeError("GitHub API request failed with HTTP 404")
        return _valid_parent_for_candidate(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return raw

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [("verify", 766), ("verify", 765), ("load", 765)]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    assert proof["rejected_source_artifacts"][0]["artifact_id"] == 766
    assert proof["rejected_source_artifacts"][0]["error_type"] == "RuntimeError"
    assert proof["quotes_read"] == proof["forecasts_created"] == 0


def test_attestation_does_not_fallback_on_guarded_runtime_http_503_parent():
    raw, meta = source_fixture()
    older = meta[0]
    newer = _newer_candidate(older)
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        if candidate["artifact_id"] == 766:
            raise RuntimeError("GitHub API request failed with HTTP 503")
        return _valid_parent_for_candidate(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return raw

    with pytest.raises(RuntimeError, match="HTTP 503"):
        attest_latest_source(
            token="test-token",
            now=NOW,
            discover=lambda **kwargs: [older, newer],
            load=load,
            verify_run=verify,
        )

    assert events == [("verify", 766)]



def _deflate_corrupt_member(raw, member_name):
    with zipfile.ZipFile(BytesIO(raw), "r") as source:
        members = {name: source.read(name) for name in source.namelist()}
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, payload in members.items():
            target.writestr(name, payload, compress_type=zipfile.ZIP_DEFLATED)
    damaged = bytearray(buffer.getvalue())
    cursor = 0
    while True:
        header = damaged.find(b"PK\x03\x04", cursor)
        if header < 0:
            raise AssertionError(f"ZIP member not found: {member_name}")
        filename_length = int.from_bytes(damaged[header + 26:header + 28], "little")
        extra_length = int.from_bytes(damaged[header + 28:header + 30], "little")
        compressed_size = int.from_bytes(damaged[header + 18:header + 22], "little")
        filename = bytes(damaged[header + 30:header + 30 + filename_length]).decode("utf-8")
        data_start = header + 30 + filename_length + extra_length
        if filename == member_name:
            method = int.from_bytes(damaged[header + 8:header + 10], "little")
            assert method == zipfile.ZIP_DEFLATED
            damaged[data_start] ^= 0xFF
            return bytes(damaged)
        cursor = data_start + compressed_size


def test_attestation_skips_deflate_corrupt_newer_archive_with_matching_sha():
    raw, meta = source_fixture()
    older = meta[0]
    damaged = _deflate_corrupt_member(raw, ARCHIVE_REPORT)
    newer = _newer_candidate(older, digest=hashlib.sha256(damaged).hexdigest())
    events = []

    def verify(candidate, quote_time, token):
        events.append(("verify", candidate["artifact_id"]))
        return _valid_parent_for_candidate(candidate, quote_time, token)

    def load(artifact_id, token):
        events.append(("load", artifact_id))
        return damaged if artifact_id == 766 else raw

    proof = attest_latest_source(
        token="test-token",
        now=NOW,
        discover=lambda **kwargs: [older, newer],
        load=load,
        verify_run=verify,
    )

    assert events == [
        ("verify", 766), ("load", 766),
        ("verify", 765), ("load", 765),
    ]
    assert proof["source_artifact_id"] == 765
    assert proof["source_candidate_fallback_used"] is True
    rejected = proof["rejected_source_artifacts"][0]
    assert rejected["artifact_id"] == 766
    assert "decompress" in rejected["reason"].lower()
    assert proof["quotes_read"] == proof["forecasts_created"] == 0
