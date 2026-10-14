"""Free actual-source attestation behavior with synthetic pre-2026 history only."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import zipfile

import pytest

from serie_a_v2_attest_real_source import attest_latest_source
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_forward_capture import SOURCE_WORKFLOW_PATH
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes
from serie_a_v2_prequote_source_archive_gate import ARCHIVE_REPORT, SOURCE_DIR


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
