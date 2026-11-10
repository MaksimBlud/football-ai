"""Original frozen V2 forward-only capture, using only synthetic pre-2026/27 scores."""
import hashlib
from io import BytesIO
import json
from datetime import datetime, timedelta, timezone, tzinfo
import zipfile

import pytest
import serie_a_v2_forward_capture as forward_capture_module

from serie_a_v2_frozen_shadow_preview import MAX_QUOTE_AGE, parse_utc

from serie_a_v2_live_diagnostic_report import _source_codes, PUBLIC_BASE
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_forward_capture import (
    ARTIFACT_NAME, ARCHIVE_REPORT, SOURCE_DIR,
    discover_archives, get_archive, prepare_forward_capture, verify_source_run,
    SOURCE_WORKFLOW_PATH, SOURCE_LOADER_PATH, EXPECTED_SOURCE_LOADER_BLOB_SHA1,
    SOURCE_RIGHTS_HELPER_PATH, EXPECTED_SOURCE_RIGHTS_HELPER_BLOB_SHA1,
    SOURCE_RIGHTS_MANIFEST_PATH, EXPECTED_SOURCE_RIGHTS_MANIFEST_BLOB_SHA1,
)

NOW = datetime(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
AFTER_CAPTURE = datetime(2026, 10, 14, 6, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def allow_synthetic_v2_inference_scope(monkeypatch):
    """Offline fixtures use synthetic inputs; this is not provider authorization."""
    import market_anchor_v2_source_rights as rights

    monkeypatch.setattr(
        rights,
        "require_personal_research_inference_scope",
        lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )

    import market_anchor_v2_artifact_privacy as privacy
    monkeypatch.setattr(
        privacy,
        "require_private_repository_for_source_artifacts",
        lambda: {"private": True, "storage_policy": "SYNTHETIC_TEST_ONLY"},
    )


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
    return {"run_completed_at_utc": "2026-10-13T15:01:00Z",
            "workflow_path": SOURCE_WORKFLOW_PATH, "run_id": 456}



@pytest.mark.parametrize("conflict", ["home_team", "kickoff"])
def test_prepare_forward_capture_denies_unresolved_inference_before_inputs_or_callbacks(monkeypatch, tmp_path):
    import market_anchor_v2_source_rights as rights

    def deny_scope():
        raise PermissionError("V2 frozen inference scope remains unresolved")

    monkeypatch.setattr(rights, "require_personal_research_inference_scope", deny_scope)

    class ForbiddenRows:
        def __iter__(self):
            pytest.fail("quotes and archive metadata must not be inspected before inference rights")

    output_dir = tmp_path / "must-not-be-created"
    with pytest.raises(PermissionError, match="V2 frozen inference scope remains unresolved"):
        prepare_forward_capture(
            ForbiddenRows(),
            ForbiddenRows(),
            as_of_utc=NOW,
            load_archive=lambda *_args, **_kwargs: pytest.fail("archive must not be loaded"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent run must not be read"),
            write_archives_to=output_dir,
        )
    assert not output_dir.exists()


def test_prepare_forward_capture_denies_public_artifact_storage_before_inputs(monkeypatch, tmp_path):
    import market_anchor_v2_artifact_privacy as privacy

    def deny_public_storage():
        raise PermissionError("source archives require a private GitHub repository")

    monkeypatch.setattr(privacy, "require_private_repository_for_source_artifacts", deny_public_storage)

    class ForbiddenRows:
        def __iter__(self):
            pytest.fail("quotes and archive metadata must not be inspected before private storage")

    output_dir = tmp_path / "must-not-be-created"
    with pytest.raises(PermissionError, match="private GitHub repository"):
        prepare_forward_capture(
            ForbiddenRows(),
            ForbiddenRows(),
            as_of_utc=NOW,
            load_archive=lambda *_args, **_kwargs: pytest.fail("archive must not be loaded"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent run must not be read"),
            write_archives_to=output_dir,
        )
    assert not output_dir.exists()


def test_same_original_event_id_cannot_change_fixture_identity(conflict):
    raw, metadata = make_source_archive()
    first = quote(ts="2026-10-14T06:00:00Z")
    second = quote(ts="2026-10-14T06:01:00Z")
    if conflict == "home_team":
        second["home_team"] = "Inter"
    else:
        second["commence_time_utc"] = "2026-10-21T18:00:00Z"

    calls = []

    def load_archive(artifact_id):
        calls.append(("load_archive", artifact_id))
        return raw

    def verify_parent_run(archive, quote_time):
        calls.append(("verify_parent_run", archive["artifact_id"]))
        return fake_verified_parent_run(archive, quote_time)

    with pytest.raises(ValueError, match="conflicting fixture identity for same original V2 event_id"):
        prepare_forward_capture(
            [first, second],
            metadata,
            as_of_utc=NOW,
            load_archive=load_archive,
            verify_parent_run=verify_parent_run,
        )

    assert calls == []


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



def test_stale_original_quote_is_blocked_before_source_parent_or_archive_access():
    raw, metadata = make_source_archive()
    stale_time = (NOW - MAX_QUOTE_AGE - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    metadata[0]["created_at"] = parse_utc(stale_time) - timedelta(hours=1)
    calls = []

    report = prepare_forward_capture(
        [quote(stale_time)],
        metadata,
        as_of_utc=NOW,
        load_archive=lambda artifact_id: calls.append(("archive", artifact_id)) or raw,
        verify_parent_run=lambda archive, quote_time: (
            calls.append(("parent", archive["artifact_id"]))
            or fake_verified_parent_run(archive, quote_time)
        ),
    )

    assert calls == []
    assert report["quotes_seen"] == report["future_quotes_checked"] == 1
    assert report["v2_diagnostic_previews_captured"] == 0
    assert report["blocked_stale_market_quote"] == 1
    assert report["blocked_no_prior_source"] == 0
    assert report["rows"][0]["status"] == "STALE_MARKET_QUOTE"
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
        def __init__(self, data, url):
            self.data = data
            self.url = url
            self.status_code = 200
        def raise_for_status(self): pass
        def json(self): return self.data
    calls=[]
    def get(url,headers,timeout,allow_redirects):
        assert allow_redirects is False
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
        ]}, url)
    rows=discover_archives(token="test-token",get=get)
    assert [x["artifact_id"] for x in rows] == [123]
    assert len(calls) == 1

    def invalid(url,headers,timeout,allow_redirects):
        assert allow_redirects is False
        return Response({"artifacts": [
            {"id": 125, "name": ARTIFACT_NAME,"expired":False,
             "workflow_run":{"head_branch":"main", "id":456,"head_sha":"a"*40},
             "digest":None, "created_at":"2026-10-13T15:00:00Z"},
        ]}, url)
    with pytest.raises(ValueError,match="missing GitHub source archive SHA256 digest"):
        discover_archives(token="test-token",get=invalid)


def test_successful_exact_source_workflow_and_prequote_completion_required():
    _, artifacts = make_source_archive()
    meta = artifacts[0]
    class Response:
        def __init__(self, data, url):
            self.data = data
            self.url = url
            self.status_code = 200
        def raise_for_status(self): pass
        def json(self): return self.data
    valid = {
        "id": 456, "path": SOURCE_WORKFLOW_PATH,
        "head_branch": "main", "head_sha": "a"*40,
        "status": "completed", "conclusion": "success",
        "event": "schedule",
        "created_at": "2026-10-13T14:40:00Z",
        "updated_at": "2026-10-13T15:01:00Z",
    }
    run_url = f"{forward_capture_module.GITHUB_API}/actions/runs/456"
    approved = {
        SOURCE_LOADER_PATH: EXPECTED_SOURCE_LOADER_BLOB_SHA1,
        SOURCE_RIGHTS_HELPER_PATH: EXPECTED_SOURCE_RIGHTS_HELPER_BLOB_SHA1,
        SOURCE_RIGHTS_MANIFEST_PATH: EXPECTED_SOURCE_RIGHTS_MANIFEST_BLOB_SHA1,
    }
    approved_urls = {
        path: f"{forward_capture_module.GITHUB_API}/contents/{path}?ref={'a'*40}"
        for path in approved
    }
    hits = []
    def get(url, headers, timeout, allow_redirects):
        assert allow_redirects is False
        hits.append(url)
        if url == run_url:
            return Response(valid, url)
        for path, expected_sha in approved.items():
            if url == approved_urls[path]:
                return Response({"path": path, "type": "file", "sha": expected_sha}, url)
        raise AssertionError(f"unexpected GitHub API URL: {url}")
    result = verify_source_run(
        meta, quote_time=parse_utc("2026-10-14T06:00:00Z"),
        token="test-token", get=get,
    )
    assert hits == [run_url, *approved_urls.values()]
    assert result["workflow_path"] == SOURCE_WORKFLOW_PATH
    assert result["run_completed_at_utc"] == "2026-10-13T15:01:00+00:00"
    assert result["source_loader_blob_sha1"] == EXPECTED_SOURCE_LOADER_BLOB_SHA1
    assert result["source_rights_helper_blob_sha1"] == EXPECTED_SOURCE_RIGHTS_HELPER_BLOB_SHA1
    assert result["source_rights_manifest_blob_sha1"] == EXPECTED_SOURCE_RIGHTS_MANIFEST_BLOB_SHA1
    for altered, expected in [
        ({"path":".github/workflows/other.yml"}, "verified original V2 collector"),
        ({"head_sha":"b"*40}, "verified original V2 collector"),
        ({"conclusion":"failure"}, "verified original V2 collector"),
        ({"status":"in_progress"}, "verified original V2 collector"),
        ({"event":"workflow_run"}, "verified original V2 collector"),
        ({"event":"push"}, "verified original V2 collector"),
        ({"updated_at":"2026-10-14T06:00:00Z"}, "not successfully finished before quote"),
        ({"updated_at":"2026-10-14T06:01:00Z"}, "not successfully finished before quote"),
        ({"updated_at":"2026-10-14T06:00:00Z"}, "not successfully finished before quote"),
    ]:
        def bad_get(url, headers, timeout, allow_redirects):
            assert allow_redirects is False
            if url == run_url:
                return Response({**valid, **altered}, url)
            for path, expected_sha in approved.items():
                if url == approved_urls[path]:
                    return Response({"path": path, "type": "file", "sha": expected_sha}, url)
            raise AssertionError(f"unexpected GitHub API URL: {url}")
        with pytest.raises(ValueError, match=expected):
            verify_source_run(
                meta, quote_time=parse_utc("2026-10-14T06:00:00Z"),
                token="test-token", get=bad_get,
            )


def test_legacy_source_loader_blob_is_rejected_before_forward_archive_download():
    raw, metadata = make_source_archive()
    meta = metadata[0]
    valid = {
        "id": 456, "path": SOURCE_WORKFLOW_PATH,
        "head_branch": "main", "head_sha": "a"*40,
        "status": "completed", "conclusion": "success",
        "event": "schedule",
        "created_at": "2026-10-13T14:40:00Z",
        "updated_at": "2026-10-13T15:01:00Z",
    }
    downloads = []
    def get(url, headers, timeout, allow_redirects):
        assert allow_redirects is False
        if url.endswith("/actions/runs/456"):
            return type("Response", (), {
                "url": url, "status_code": 200, "json": lambda self: valid
            })()
        if "/contents/" + SOURCE_LOADER_PATH + "?ref=" in url:
            return type("Response", (), {
                "url": url, "status_code": 200,
                "json": lambda self: {
                    "path": SOURCE_LOADER_PATH, "type": "file",
                    "sha": "fae3698769f857fbcb6c8d3ea7826eb81135fec4",
                }
            })()
        raise AssertionError(f"unexpected GitHub API URL: {url}")
    with pytest.raises(ValueError, match="approved redirect-guarded V2 source/rights file"):
        prepare_forward_capture(
            [quote()], [meta], as_of_utc=NOW,
            load_archive=lambda artifact_id: downloads.append(artifact_id) or raw,
            verify_parent_run=lambda archive, quote_time: verify_source_run(
                archive, quote_time=quote_time, token="test-token", get=get
            ),
        )
    assert downloads == []


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
        def __init__(self, url):
            self.url = url
            self.status_code = 200
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
                          get=lambda url,headers,timeout,allow_redirects:Response(url))



class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "NO_OFFSET"


def test_original_forward_clock_rejects_tzinfo_without_offset_before_archive_access():
    invalid_clock = datetime(2026, 10, 14, 7, 0, tzinfo=_NoOffsetTimezone())
    with pytest.raises(ValueError, match="as_of_utc must be timezone-aware"):
        prepare_forward_capture(
            [], [],
            as_of_utc=invalid_clock,
            load_archive=lambda _artifact_id: pytest.fail("archive must not be loaded"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent must not be checked"),
        )

class _StreamingArtifactResponse:
    def __init__(self, chunks, headers=None, error=None):
        self.chunks = list(chunks)
        self.headers = headers or {}
        self.error = error
        self.iterated = 0
        self.chunk_size = None
        self.closed = False

    def raise_for_status(self):
        if self.error is not None:
            raise self.error

    def iter_content(self, chunk_size):
        self.chunk_size = chunk_size
        for chunk in self.chunks:
            self.iterated += 1
            yield chunk

    def close(self):
        self.closed = True


def test_original_artifact_zip_download_streams_and_closes_response():
    raw = b"PK\\x03\\x04bounded-original-v2"
    response = _StreamingArtifactResponse(
        [raw[:4], b"", raw[4:]],
        headers={"Content-Length": str(len(raw))},
    )
    request = {}

    def fake_get(url, **kwargs):
        request["url"] = url
        request.update(kwargs)
        return response

    assert get_archive(123, token="test-token", get=fake_get) == raw
    assert request["url"].endswith("/actions/artifacts/123/zip")
    assert request["stream"] is True
    assert response.chunk_size == 64 * 1024
    assert response.closed is True


def test_original_artifact_zip_declared_oversize_fails_before_body_read(monkeypatch):
    monkeypatch.setattr(forward_capture_module, "MAX_ZIP_BYTES", 5)
    response = _StreamingArtifactResponse(
        [b"must-not-read"],
        headers={"Content-Length": "6"},
    )

    with pytest.raises(ValueError, match="missing or oversized source archive"):
        get_archive(
            123,
            token="test-token",
            get=lambda _url, **_kwargs: response,
        )

    assert response.iterated == 0
    assert response.closed is True


def test_original_artifact_zip_stream_oversize_stops_at_first_excess_chunk(monkeypatch):
    monkeypatch.setattr(forward_capture_module, "MAX_ZIP_BYTES", 5)
    response = _StreamingArtifactResponse([b"12345", b"6", b"never-read"])

    with pytest.raises(ValueError, match="missing or oversized source archive"):
        get_archive(
            123,
            token="test-token",
            get=lambda _url, **_kwargs: response,
        )

    assert response.iterated == 2
    assert response.closed is True


def test_original_artifact_zip_requires_read_token_before_request():
    calls = []
    with pytest.raises(ValueError, match="GitHub token required"):
        get_archive(
            123,
            token="",
            get=lambda *args, **kwargs: calls.append((args, kwargs)),
        )
    assert calls == []


def test_original_artifact_zip_rejects_malformed_content_length_before_read():
    response = _StreamingArtifactResponse(
        [b"must-not-read"], headers={"Content-Length": "unknown"}
    )
    with pytest.raises(ValueError, match="Content-Length"):
        get_archive(123, token="test-token", get=lambda _url, **_kwargs: response)
    assert response.iterated == 0
    assert response.closed is True


@pytest.mark.parametrize("declared_length", ["+1", "١", "1.0"])
def test_original_artifact_zip_rejects_non_ascii_or_non_decimal_content_length(
    declared_length
):
    response = _StreamingArtifactResponse(
        [b"must-not-read"], headers={"Content-Length": declared_length}
    )
    with pytest.raises(ValueError, match="Content-Length"):
        get_archive(123, token="test-token", get=lambda _url, **_kwargs: response)
    assert response.iterated == 0
    assert response.closed is True


def test_original_artifact_zip_rejects_non_bytes_chunk_and_closes():
    response = _StreamingArtifactResponse([bytearray(b"not-immutable-bytes")])
    with pytest.raises(ValueError, match="non-bytes chunk"):
        get_archive(123, token="test-token", get=lambda _url, **_kwargs: response)
    assert response.iterated == 1
    assert response.closed is True


def test_original_artifact_zip_rejects_empty_stream_and_closes():
    response = _StreamingArtifactResponse([])
    with pytest.raises(ValueError, match="missing or oversized source archive"):
        get_archive(123, token="test-token", get=lambda _url, **_kwargs: response)
    assert response.closed is True


def test_original_artifact_zip_closes_response_after_http_error():
    response = _StreamingArtifactResponse([], error=RuntimeError("http failure"))
    with pytest.raises(RuntimeError, match="http failure"):
        get_archive(123, token="test-token", get=lambda _url, **_kwargs: response)
    assert response.closed is True



class _GithubJsonGuardResponse:
    def __init__(self, url, status_code, payload=None):
        self.url = url
        self.status_code = status_code
        self.payload = payload
        self.json_called = False

    def json(self):
        self.json_called = True
        return self.payload


def test_original_forward_github_api_json_disables_redirects_and_rejects_302_before_body_read():
    url = forward_capture_module.GITHUB_API + "/actions/artifacts?per_page=1"
    response = _GithubJsonGuardResponse(url, 302, {"artifacts": []})
    request = {}

    def fake_get(request_url, **kwargs):
        request["url"] = request_url
        request.update(kwargs)
        return response

    with pytest.raises(RuntimeError, match="HTTP 302"):
        forward_capture_module._github_json(url, token="read-only-test-token", get=fake_get)

    assert request["url"] == url
    assert request["allow_redirects"] is False
    assert response.json_called is False


def test_original_forward_github_api_json_rejects_unexpected_response_url():
    url = forward_capture_module.GITHUB_API + "/actions/runs/123"
    response = _GithubJsonGuardResponse("https://attacker.example/forged", 200, {"id": 123})
    request = {}

    def fake_get(request_url, **kwargs):
        request["allow_redirects"] = kwargs.get("allow_redirects")
        return response

    with pytest.raises(ValueError, match="response URL mismatch"):
        forward_capture_module._github_json(url, token="read-only-test-token", get=fake_get)

    assert request["allow_redirects"] is False
    assert response.json_called is False


def test_original_forward_github_api_json_accepts_exact_http_200_without_redirects():
    url = forward_capture_module.GITHUB_API + "/actions/artifacts?per_page=1"
    response = _GithubJsonGuardResponse(url, 200, {"artifacts": []})
    request = {}

    def fake_get(request_url, **kwargs):
        request["allow_redirects"] = kwargs.get("allow_redirects")
        return response

    assert forward_capture_module._github_json(url, token="read-only-test-token", get=fake_get) == {"artifacts": []}
    assert request["allow_redirects"] is False
    assert response.json_called is True


def _repository_git_blob_sha1(path):
    from pathlib import Path
    raw = Path(path).read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def test_original_forward_rights_blob_pins_match_exact_repository_bytes():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert EXPECTED_SOURCE_RIGHTS_HELPER_BLOB_SHA1 == _repository_git_blob_sha1(
        root / SOURCE_RIGHTS_HELPER_PATH
    )
    assert EXPECTED_SOURCE_RIGHTS_MANIFEST_BLOB_SHA1 == _repository_git_blob_sha1(
        root / SOURCE_RIGHTS_MANIFEST_PATH
    )
    assert EXPECTED_SOURCE_LOADER_BLOB_SHA1 == _repository_git_blob_sha1(
        root / SOURCE_LOADER_PATH
    )

def test_source_archive_created_at_equal_to_quote_is_not_prequote_source():
    _, metadata = make_source_archive()
    quote_time = "2026-10-14T06:00:00Z"
    metadata[0]["created_at"] = parse_utc(quote_time)
    calls = []

    report = prepare_forward_capture(
        [quote(quote_time)],
        metadata,
        as_of_utc=NOW,
        load_archive=lambda artifact_id: calls.append(("archive", artifact_id)),
        verify_parent_run=lambda archive, at: calls.append(("parent", archive["artifact_id"])),
    )

    assert calls == []
    assert report["v2_diagnostic_previews_captured"] == 0
    assert report["blocked_no_prior_source"] == 1
    assert report["rows"][0]["status"] == "NO_EARLIER_SOURCE_ARCHIVE"
    assert report["rows"][0]["v2_preview"] is None
