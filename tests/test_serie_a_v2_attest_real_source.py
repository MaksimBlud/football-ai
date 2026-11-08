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


NOW = datetime(2026, 10, 14, 16, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _allow_private_source_only_scope_for_synthetic_attestation(monkeypatch):
    """Keep synthetic ZIP tests offline; denial/order cases override these gates."""
    monkeypatch.setattr(
        attestor,
        "require_personal_research_source_capture_scope",
        lambda: {
            "source_capture_scope": "PRIVATE_NONCOMMERCIAL_RESEARCH_ARCHIVE_ONLY",
            "rights_manifest_sha256": "a" * 64,
            "policy_url": "https://football-data.co.uk/contact.php",
            "policy_checked_at_utc": "2026-11-07T01:56:17+00:00",
            "policy_page_updated_date": "2026-11-06",
        },
    )
    monkeypatch.setattr(
        attestor,
        "require_private_repository_for_source_artifacts",
        lambda repository, token: {
            "repository": repository,
            "private": True,
            "storage_policy": "PRIVATE_GITHUB_ACTIONS_ARTIFACTS",
        },
    )


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
    assert proof["source_rights_manifest_sha256"] == "a" * 64
    assert proof["source_policy_url"] == "https://football-data.co.uk/contact.php"
    assert proof["source_policy_checked_at_utc"] == "2026-11-07T01:56:17+00:00"
    assert proof["source_policy_page_updated_date"] == "2026-11-06"
    assert proof["source_artifact_storage_policy"] == "PRIVATE_GITHUB_ACTIONS_ARTIFACTS"
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
    monkeypatch.setattr(
        attestor,
        "require_personal_research_source_capture_scope",
        lambda: (_ for _ in ()).throw(PermissionError("source-only scope not confirmed")),
    )
    monkeypatch.setattr(
        attestor,
        "require_private_repository_for_source_artifacts",
        lambda *args, **kwargs: pytest.fail("privacy lookup must not run after source-rights denial"),
    )

    attestor.main()

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "SOURCE_CAPTURE_SCOPE_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["operation"] == "SERIE_A_ORIGINAL_V2_SOURCE_ATTESTATION"
    assert report["block_reason"] == "source-only scope not confirmed"
    assert report["public_http_requests"] == 0
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["quotes_read"] == 0
    assert report["forecasts_created"] == 0



def test_direct_attestation_checks_rights_and_private_storage_before_archive_io(monkeypatch):
    data, meta = source_fixture()
    calls = []

    def allow_rights():
        calls.append("rights")
        return {
            "rights_manifest_sha256": "b" * 64,
            "policy_url": "https://football-data.co.uk/contact.php",
            "policy_checked_at_utc": "2026-11-07T01:56:17+00:00",
            "policy_page_updated_date": "2026-11-06",
        }

    def allow_private(repository, token):
        calls.append("privacy")
        assert repository == attestor.REPOSITORY
        assert token == "test-token"
        return {"private": True, "storage_policy": "PRIVATE_GITHUB_ACTIONS_ARTIFACTS"}

    def discover(**kwargs):
        calls.append("discover")
        return meta

    def verify(m, quote_time, token):
        calls.append("verify")
        return valid_parent(m, quote_time, token)

    def load(artifact_id, token):
        calls.append("load")
        return data

    monkeypatch.setattr(attestor, "require_personal_research_source_capture_scope", allow_rights)
    monkeypatch.setattr(attestor, "require_private_repository_for_source_artifacts", allow_private)
    proof = attest_latest_source(
        token="test-token", now=NOW, discover=discover, load=load, verify_run=verify,
    )

    assert calls == ["rights", "privacy", "discover", "verify", "load"]
    assert proof["source_rights_manifest_sha256"] == "b" * 64
    assert proof["source_artifact_storage_policy"] == "PRIVATE_GITHUB_ACTIONS_ARTIFACTS"


def test_direct_attestation_blocks_rights_denial_before_privacy_or_archive_discovery(monkeypatch):
    calls = []

    def deny_rights():
        calls.append("rights")
        raise PermissionError("source-only rights denied")

    monkeypatch.setattr(attestor, "require_personal_research_source_capture_scope", deny_rights)
    monkeypatch.setattr(
        attestor, "require_private_repository_for_source_artifacts",
        lambda *args, **kwargs: pytest.fail("privacy check must not run after rights denial"),
    )

    with pytest.raises(PermissionError, match="source-only rights denied"):
        attest_latest_source(
            token="test-token", now=NOW,
            discover=lambda **kwargs: pytest.fail("archive discovery must remain blocked"),
            load=lambda *args, **kwargs: pytest.fail("archive download must remain blocked"),
            verify_run=lambda *args, **kwargs: pytest.fail("parent verification must remain blocked"),
        )

    assert calls == ["rights"]


def test_direct_attestation_blocks_public_storage_before_archive_discovery(monkeypatch):
    calls = []

    def allow_rights():
        calls.append("rights")
        return {"rights_manifest_sha256": "c" * 64}

    def deny_privacy(repository, token):
        calls.append("privacy")
        raise PermissionError("private repository required")

    monkeypatch.setattr(attestor, "require_personal_research_source_capture_scope", allow_rights)
    monkeypatch.setattr(attestor, "require_private_repository_for_source_artifacts", deny_privacy)

    with pytest.raises(PermissionError, match="private repository required"):
        attest_latest_source(
            token="test-token", now=NOW,
            discover=lambda **kwargs: pytest.fail("public-storage denial must precede archive discovery"),
            load=lambda *args, **kwargs: pytest.fail("public-storage denial must precede archive download"),
            verify_run=lambda *args, **kwargs: pytest.fail("public-storage denial must precede parent verification"),
        )

    assert calls == ["rights", "privacy"]
