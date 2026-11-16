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
    capture_forward_with_source_preflight,
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
    return {
        "run_completed_at_utc": "2026-10-13T15:01:00Z",
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_id": 456,
        "run_head_sha": "a" * 40,
    }



@pytest.mark.parametrize("conflict", ["home_team", "kickoff"])
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


@pytest.mark.parametrize(
    ("first_home", "first_away", "second_home", "second_away"),
    [
        ("Juventus", "Napoli", "Juventus", "Napoli"),
        ("Atalanta", "Fiorentina", "Atalanta BC", " FIORENTINA "),
        ("Juventus", "Napoli", "Napoli", "Juventus"),
    ],
)
def test_same_original_fixture_cannot_be_split_across_provider_event_ids(
    first_home, first_away, second_home, second_away
):
    first = {
        **quote(ts="2026-10-14T06:00:00Z"),
        "home_team": first_home,
        "away_team": first_away,
    }
    second = {
        **quote(ts="2026-10-14T06:01:00Z"),
        "event_id": "another-provider-event-id",
        "home_team": second_home,
        "away_team": second_away,
    }
    with pytest.raises(ValueError, match="conflicting event IDs or orientation"):
        prepare_forward_capture(
            [first, second],
            [],
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: pytest.fail(
                "duplicate fixture identity must fail before archive access"
            ),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail(
                "duplicate fixture identity must fail before parent verification"
            ),
        )


def test_original_event_id_with_surrounding_whitespace_is_rejected_before_archive_access():
    first = quote(ts="2026-10-14T06:00:00Z")
    second = {
        **quote(ts="2026-10-14T06:01:00Z"),
        "event_id": " " + first["event_id"] + " ",
        "home_team": "Inter",
    }
    with pytest.raises(ValueError, match="surrounding whitespace"):
        prepare_forward_capture(
            [first, second],
            [],
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: pytest.fail("archive access before identity rejection"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent verification before identity rejection"),
        )


def test_quote_with_identical_canonical_teams_is_rejected_before_archive_access():
    item = {**quote(), "home_team": "Atalanta", "away_team": "Atalanta BC"}
    with pytest.raises(ValueError, match="identical canonical teams"):
        prepare_forward_capture(
            [item],
            [],
            as_of_utc=NOW,
            load_archive=lambda _artifact_id: pytest.fail("archive access before identity rejection"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent verification before identity rejection"),
        )


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
        SOURCE_WORKFLOW_PATH: forward_capture_module.EXPECTED_SOURCE_WORKFLOW_BLOB_SHA1,
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
    assert result["source_workflow_blob_sha1"] == forward_capture_module.EXPECTED_SOURCE_WORKFLOW_BLOB_SHA1
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
    assert forward_capture_module.EXPECTED_SOURCE_WORKFLOW_BLOB_SHA1 == _repository_git_blob_sha1(
        root / SOURCE_WORKFLOW_PATH
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

    assert events.index("access") < events.index("parent") < events.index("archive") < events.index("quotes")
    assert events.count("quotes") == 1
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

@pytest.mark.parametrize("entrypoint", ["discover_archives", "verify_source_run", "get_archive", "prepare_forward_capture"])
def test_original_forward_public_entrypoints_require_direct_access_before_io(
    entrypoint, monkeypatch, tmp_path
):
    import sys
    from types import ModuleType

    events = []

    def deny_access():
        events.append("access")
        raise PermissionError("provider/private-storage access is not cleared")

    access_module = ModuleType("market_anchor_v2_direct_access")
    access_module.require_v2_inference_access = deny_access
    monkeypatch.setitem(sys.modules, "market_anchor_v2_direct_access", access_module)

    def forbidden_get(*_args, **_kwargs):
        events.append("network")
        raise AssertionError("GitHub network must not be reached before the rights gate")

    def forbidden_callback(*_args, **_kwargs):
        events.append("callback")
        raise AssertionError("caller callbacks must not run before the rights gate")

    with pytest.raises(PermissionError, match="provider/private-storage access is not cleared"):
        if entrypoint == "discover_archives":
            discover_archives(token="offline-token", get=forbidden_get)
        elif entrypoint == "verify_source_run":
            verify_source_run({}, quote_time=NOW, token="offline-token", get=forbidden_get)
        elif entrypoint == "get_archive":
            get_archive(123, token="offline-token", get=forbidden_get)
        else:
            prepare_forward_capture(
                [],
                [],
                as_of_utc=NOW,
                load_archive=forbidden_callback,
                verify_parent_run=forbidden_callback,
                write_archives_to=tmp_path / "must-not-be-created",
            )

    assert events == ["access"]
    assert not (tmp_path / "must-not-be-created").exists()


def test_original_source_artifact_upload_requires_successful_complete_capture():
    """A failed multi-CSV fetch must never publish a partial source artifact."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml").read_text(
        encoding="utf-8"
    )
    lines = workflow.splitlines()
    capture_name = "      - name: Fetch and SHA-archive public source, preview original frozen V2 diagnostics"
    upload_name = "      - name: Archive diagnostic and exact public CSV bytes for provenance"

    capture_start = lines.index(capture_name)
    capture_end = next(
        (i for i in range(capture_start + 1, len(lines)) if lines[i].startswith("      - name: ") or lines[i].startswith("      - uses: ")),
        len(lines),
    )
    capture_block = "\\n".join(lines[capture_start:capture_end])
    assert "        id: capture_original_v2" in capture_block
    assert "serie_a_v2_live_diagnostic_report.py" in capture_block

    upload_start = lines.index(upload_name)
    upload_end = next(
        (i for i in range(upload_start + 1, len(lines)) if lines[i].startswith("      - name: ") or lines[i].startswith("      - uses: ")),
        len(lines),
    )
    upload_block = "\\n".join(lines[upload_start:upload_end])
    assert "steps.capture_original_v2.outcome == 'success'" in upload_block
    assert "always()" not in upload_block
    assert "if-no-files-found: warn" not in upload_block
    assert "if-no-files-found: error" in upload_block
    assert 'cron: "13 6 * * *"' in workflow


def test_original_forward_report_write_is_atomic_on_serialization_failure(tmp_path, monkeypatch):
    target = tmp_path / "forward.json"
    previous = '{"previous":true}'
    target.write_text(previous, encoding="utf-8")

    def fail_after_partial_write(payload, stream, **_kwargs):
        stream.write('{"partial":')
        raise OSError("simulated serialization failure")

    monkeypatch.setattr(forward_capture_module.json, "dump", fail_after_partial_write)
    with pytest.raises(OSError, match="simulated serialization failure"):
        forward_capture_module._write_json_atomically(target, {"new": True})

    assert target.read_text(encoding="utf-8") == previous
    assert list(tmp_path.glob(".forward.json.tmp-*")) == []


def test_original_forward_report_write_publishes_complete_json(tmp_path):
    target = tmp_path / "forward.json"
    forward_capture_module._write_json_atomically(
        target,
        {"schema_version": "SERIE_A_ORIGINAL_V2_FORWARD_SOURCE_BEFORE_QUOTE_V1", "no_bet": True},
    )

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "schema_version": "SERIE_A_ORIGINAL_V2_FORWARD_SOURCE_BEFORE_QUOTE_V1",
        "no_bet": True,
    }
    assert list(tmp_path.glob(".forward.json.tmp-*")) == []


def test_original_forward_report_write_rejects_symlink_target(tmp_path):
    target = tmp_path / "forward.json"
    destination = tmp_path / "destination.json"
    target.symlink_to(destination)

    with pytest.raises(ValueError, match="cannot be a symlink"):
        forward_capture_module._write_json_atomically(target, {"no_bet": True})

    assert not destination.exists()


def test_original_forward_artifact_upload_requires_successful_complete_capture():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/serie-a-v2-forward-preview.yml").read_text(
        encoding="utf-8"
    )
    lines = workflow.splitlines()
    capture_name = "      - name: Generate actual original frozen V2 source-verified read-only preview"
    upload_name = "      - name: Save immutable original V2 predictions and exact older source bytes"

    capture_start = lines.index(capture_name)
    capture_end = next(
        (i for i in range(capture_start + 1, len(lines)) if lines[i].startswith("      - name: ") or lines[i].startswith("      - uses: ")),
        len(lines),
    )
    capture_block = "\\n".join(lines[capture_start:capture_end])
    assert "id: forward_capture" in capture_block
    assert "serie_a_v2_forward_capture.py" in capture_block

    upload_start = lines.index(upload_name)
    upload_end = next(
        (i for i in range(upload_start + 1, len(lines)) if lines[i].startswith("      - name: ") or lines[i].startswith("      - uses: ")),
        len(lines),
    )
    upload_block = "\\n".join(lines[upload_start:upload_end])
    assert "steps.forward_capture.outcome == 'success'" in upload_block
    assert "always()" not in upload_block
    assert "if-no-files-found: error" in upload_block
    assert 'cron: "8 8 * * *"' in workflow



def test_original_forward_cli_defers_supabase_quote_reader_until_source_preflight(monkeypatch, tmp_path):
    """Exercise the actual CLI orchestration, not only the pure preflight helper."""
    import sys
    from types import ModuleType

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
            return value if tz is None else value.astimezone(tz)

    monkeypatch.setattr(forward_capture_module, "datetime", FrozenDateTime)
    raw, metadata = make_source_archive()
    metadata[0]["created_at"] = FrozenDateTime(2026, 10, 13, 15, 0, tzinfo=timezone.utc)
    events = []

    access_module = ModuleType("market_anchor_v2_direct_access")
    access_module.require_v2_inference_access = lambda: events.append("rights")
    monkeypatch.setitem(sys.modules, "market_anchor_v2_direct_access", access_module)

    database_module = ModuleType("database")
    database_module.supabase = object()
    monkeypatch.setitem(sys.modules, "database", database_module)

    monkeypatch.setenv("GITHUB_REPOSITORY", forward_capture_module.REPOSITORY)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-read-only-token")
    monkeypatch.setattr(
        forward_capture_module,
        "discover_archives",
        lambda token: events.append("discover") or metadata,
    )
    monkeypatch.setattr(
        forward_capture_module,
        "verify_source_run",
        lambda archive, quote_time, token: events.append("parent")
        or fake_verified_parent_run(archive, quote_time),
    )
    monkeypatch.setattr(
        forward_capture_module,
        "get_archive",
        lambda artifact_id, token: events.append("archive") or raw,
    )
    monkeypatch.setattr(
        forward_capture_module,
        "fetch_saved_upcoming_serie_a_quotes",
        lambda client, now: events.append("quotes") or [quote()],
    )

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

    forward_capture_module.main()

    assert events[0] == "rights"
    assert events.index("rights") < events.index("discover")
    assert events.index("discover") < events.index("parent")
    assert events.index("parent") < events.index("archive")
    assert events.index("archive") < events.index("quotes")
    assert events.count("quotes") == 1
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["source_preflight"]["verified"] is True
    assert report["source_preflight"]["quotes_read_after_source_preflight"] is True
    assert report["v2_diagnostic_previews_captured"] == 1
    assert len(list(sources.glob("source_artifact_*.zip"))) == 1


def test_original_forward_cli_without_source_archive_never_imports_database_or_reads_quotes(
    monkeypatch, tmp_path
):
    """The actual original-forward CLI must fail before importing its lazy quote reader."""
    import builtins
    import sys
    from types import ModuleType

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 14, 7, 0, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(forward_capture_module, "datetime", FrozenDateTime)
    events = []

    access_module = ModuleType("market_anchor_v2_direct_access")
    access_module.require_v2_inference_access = lambda: events.append("rights")
    monkeypatch.setitem(sys.modules, "market_anchor_v2_direct_access", access_module)

    monkeypatch.setenv("GITHUB_REPOSITORY", forward_capture_module.REPOSITORY)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-read-only-token")
    monkeypatch.setattr(
        forward_capture_module,
        "discover_archives",
        lambda token: events.append("discover") or [],
    )

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "database":
            events.append("database_import")
            raise AssertionError("Supabase must not be imported without a verified source archive")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(
        forward_capture_module,
        "verify_source_run",
        lambda *args, **kwargs: pytest.fail("parent verification is impossible without an archive"),
    )
    monkeypatch.setattr(
        forward_capture_module,
        "get_archive",
        lambda *args, **kwargs: pytest.fail("archive download is impossible without metadata"),
    )
    monkeypatch.setattr(
        forward_capture_module,
        "fetch_saved_upcoming_serie_a_quotes",
        lambda *args, **kwargs: pytest.fail("saved quotes must never be read without a source archive"),
    )

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

    with pytest.raises(RuntimeError, match="no original V2 source archive before quote read"):
        forward_capture_module.main()

    assert events.count("rights") >= 1
    assert events.index("rights") < events.index("discover")
    assert "database_import" not in events
    assert not output.exists()
    assert not sources.exists()
