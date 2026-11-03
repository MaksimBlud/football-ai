from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

import serie_a_v2_historical_source_reuse as reuse


NOW = datetime(2026, 11, 3, 7, 0, tzinfo=timezone.utc)
RUN_ID = 456
ARTIFACT_ID = 123
HEAD_SHA = "a" * 40
RUN_CREATED = "2026-11-02T13:53:01Z"
SOURCE_OBSERVED = "2026-11-02T13:52:00Z"
CURRENT_OBSERVED = "2026-11-02T13:53:40Z"
ARCHIVE_CREATED = "2026-11-02T13:53:50Z"
ARTIFACT_CREATED = "2026-11-02T13:53:57Z"
RUN_COMPLETED = "2026-11-02T13:54:01Z"


def _historical_csv(code: str, *, date_text: str | None = None) -> bytes:
    year = 2000 + int(code[:2])
    date_value = date_text or f"01/10/{year}"
    return (
        "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
        f"{date_value},Juventus,Napoli,1,0,H,5,3,2,1,0,0\n"
    ).encode()


def _artifact_fixture(*, bad_url: bool = False, protected_old_date: bool = False):
    current_bytes = b"this is deliberately not parsed as a 2026/27 CSV"
    payloads = {}
    audits = []
    for code in reuse.HISTORICAL_CODES:
        date_text = "01/07/2026" if protected_old_date and code == reuse.HISTORICAL_CODES[-1] else None
        body = _historical_csv(code, date_text=date_text)
        filename = f"serie_a_{code}.csv"
        url = (
            f"{reuse.PUBLIC_BASE}/{code}/"
            f"{reuse.SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
        )
        if bad_url and code == reuse.HISTORICAL_CODES[0]:
            url = "https://example.invalid/forged.csv"
        payloads[filename] = body
        audits.append({
            "season_code": code,
            "source_url": url,
            "archived_source_name": filename,
            "csv_sha256": hashlib.sha256(body).hexdigest(),
            "source_observed_at_utc": SOURCE_OBSERVED,
            "completed_source_rows": 1,
        })
    payloads[reuse.CURRENT_FILENAME] = current_bytes
    audits.append({
        "season_code": reuse.CURRENT_CODE,
        "source_url": reuse.CURRENT_URL,
        "archived_source_name": reuse.CURRENT_FILENAME,
        "csv_sha256": hashlib.sha256(current_bytes).hexdigest(),
        "source_observed_at_utc": CURRENT_OBSERVED,
        "completed_source_rows": 90,
        "total_source_rows": 90,
    })
    manifest = {
        "schema_version": "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1",
        "experiment_id": "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY",
        "repository": reuse.REPOSITORY,
        "workflow_path": reuse.SOURCE_WORKFLOW_PATH,
        "git_sha": HEAD_SHA,
        "workflow_run_id": str(RUN_ID),
        "source_archive_created_at_utc": ARCHIVE_CREATED,
        "frozen_candidate_sha256": reuse.FROZEN_SHA,
        "original_feature_builder_git_blob_sha1": reuse.EXPECTED_BUILDER_BLOB_SHA1,
        "feature_count": 19,
        "historical_season_codes": list(reuse.HISTORICAL_CODES),
        "current_season_code": reuse.CURRENT_CODE,
        "current_season": reuse.CURRENT_SEASON,
        "current_season_source_url": reuse.CURRENT_URL,
        "current_season_source_sha256": hashlib.sha256(current_bytes).hexdigest(),
        "current_season_source_observed_at_utc": CURRENT_OBSERVED,
        "current_season_completed_prior_day_rows": 90,
        "current_season_total_csv_rows": 90,
        "current_season_excluded_incomplete_or_same_day_rows": 0,
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": reuse.CURRENT_SEASON,
            "minimum_completed_primary_events": 30,
            "observed_completed_primary_events": 90,
            "checked_at_utc": "2026-11-02T13:52:00Z",
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "passed": True,
        },
        "feature_policy": {
            "use_current_season_matches_only_as_lagged_features": True,
            "same_calendar_day_matches_excluded": True,
            "future_or_unplayed_fixtures_used": False,
            "model_weights_or_feature_definitions_changed": False,
            "model_refit": False,
            "model_selection": False,
        },
        "target_outcome_evaluation_gate": {
            "minimum_completed_eligible_prospective_forecasts": 30,
            "outcomes_read_for_evaluation": False,
            "outcome_gate_open": False,
        },
        "source_files": audits,
        "historical_old_season_file_count": len(reuse.HISTORICAL_CODES),
        "source_file_count": len(audits),
        "eligible_for_frozen_old_season_cohort": False,
        "eligible_for_current_form_forward_shadow": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_reads": 1,
        "supabase_writes": 0,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "model_refit_or_promotion": False,
    }
    payloads[reuse.MANIFEST_FILENAME] = (
        json.dumps(manifest, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in payloads.items():
            archive.writestr(name, body)
    raw = stream.getvalue()
    digest = hashlib.sha256(raw).hexdigest()
    artifact = {
        "artifact_id": ARTIFACT_ID,
        "run_id": RUN_ID,
        "head_sha": HEAD_SHA,
        "created_at": datetime.fromisoformat(ARTIFACT_CREATED.replace("Z", "+00:00")),
        "sha256": digest,
    }
    artifact_list = {
        "artifacts": [{
            "id": ARTIFACT_ID,
            "name": reuse.ARTIFACT_NAME,
            "expired": False,
            "digest": "sha256:" + digest,
            "created_at": ARTIFACT_CREATED,
            "workflow_run": {
                "id": RUN_ID,
                "head_branch": "main",
                "head_sha": HEAD_SHA,
            },
        }]
    }
    parent_run = {
        "id": RUN_ID,
        "path": reuse.SOURCE_WORKFLOW_PATH,
        "name": reuse.SOURCE_WORKFLOW_NAME,
        "head_branch": "main",
        "head_sha": HEAD_SHA,
        "status": "completed",
        "conclusion": "success",
        "event": "schedule",
        "created_at": RUN_CREATED,
        "updated_at": RUN_COMPLETED,
    }
    return raw, artifact, artifact_list, parent_run


class JsonResponse:
    def __init__(self, url, payload):
        self.url = url
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


class StreamResponse:
    def __init__(self, chunks, *, url="https://objects.githubusercontent.com/signed/source.zip", headers=None):
        self.url = url
        self.status_code = 200
        self.headers = headers or {}
        self.chunks = list(chunks)
        self.closed = False
        self.iterated = False

    def iter_content(self, chunk_size):
        assert chunk_size == 64 * 1024
        self.iterated = True
        yield from self.chunks

    def close(self):
        self.closed = True


def _fake_get(raw, artifact_list, parent_run):
    calls = []
    stream = StreamResponse([raw[:1000], raw[1000:]])
    def get(url, **kwargs):
        calls.append((url, kwargs))
        if "/actions/artifacts?name=" in url:
            return JsonResponse(url, artifact_list)
        if url.endswith(f"/actions/runs/{RUN_ID}"):
            return JsonResponse(url, parent_run)
        if url.endswith(f"/actions/artifacts/{ARTIFACT_ID}/zip"):
            return stream
        raise AssertionError(f"unexpected URL: {url}")
    return get, calls, stream


def test_reuses_only_historical_csv_bytes_from_authenticated_successful_main_artifact(tmp_path):
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    get, calls, stream = _fake_get(raw, artifact_list, parent_run)

    history, audits, provenance = reuse.load_verified_historical_source_archive(
        token="test-token", now=NOW, get=get, capture_dir=tmp_path
    )

    assert len(history) == len(reuse.HISTORICAL_CODES)
    assert len(audits) == len(reuse.HISTORICAL_CODES)
    assert history["Date"].str.endswith(tuple(str(2000 + int(code[:2])) for code in reuse.HISTORICAL_CODES)).all()
    assert all(item["source_observed_at_utc"] == "2026-11-02T13:52:00+00:00" for item in audits)
    assert provenance["mode"] == "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY"
    assert provenance["historical_files_reused"] == 10
    assert provenance["public_historical_csv_requests"] == 0
    assert provenance["current_season_file_reused"] is False
    assert provenance["prior_feature_gate_reused"] is False
    assert provenance["protected_2026_27_source_file_read"] is False
    assert provenance["target_outcomes_read"] is False
    assert provenance["supabase_writes"] == provenance["paid_provider_calls"] == 0
    assert len(list(tmp_path.glob("serie_a_*.csv"))) == 10
    assert not (tmp_path / reuse.CURRENT_FILENAME).exists()
    assert stream.closed is True and stream.iterated is True
    assert all("football-data.co.uk" not in url for url, _ in calls)
    assert all(kwargs.get("stream") is True for url, kwargs in calls if url.endswith("/zip"))


def test_current_season_member_is_not_parsed_or_extracted_for_historical_reuse(tmp_path):
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    get, _calls, _stream = _fake_get(raw, artifact_list, parent_run)
    history, _audits, provenance = reuse.load_verified_historical_source_archive(
        token="test-token", now=NOW, get=get, capture_dir=tmp_path
    )
    assert len(history) == 10
    assert not (tmp_path / reuse.CURRENT_FILENAME).exists()
    assert provenance["current_season_file_reused"] is False
    assert provenance["prior_feature_gate_reused"] is False


def test_source_parent_must_be_exact_successful_main_run_before_download():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    parent_run["conclusion"] = "failure"
    get, calls, _stream = _fake_get(raw, artifact_list, parent_run)
    with pytest.raises(ValueError, match="successful main source workflow"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)
    assert not any(url.endswith("/zip") for url, _ in calls)


def test_artifact_zip_digest_mismatch_fails_closed():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    artifact_list["artifacts"][0]["digest"] = "sha256:" + ("0" * 64)
    get, _calls, _stream = _fake_get(raw, artifact_list, parent_run)
    with pytest.raises(ValueError, match="SHA-256"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)


def test_historical_source_url_must_match_the_exact_approved_csv_endpoint():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture(bad_url=True)
    get, _calls, _stream = _fake_get(raw, artifact_list, parent_run)
    with pytest.raises(ValueError, match="unexpected URL"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)


def test_protected_season_date_cannot_enter_the_reused_historical_cache():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture(protected_old_date=True)
    get, _calls, _stream = _fake_get(raw, artifact_list, parent_run)
    with pytest.raises(ValueError, match="protected 2026/27 date"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)


def test_missing_cache_fails_closed_without_public_source_fallback():
    url = f"{reuse.GITHUB_API}/actions/artifacts?name={reuse.ARTIFACT_NAME}&per_page=100&page=1"
    def get(received_url, **kwargs):
        assert received_url == url
        return JsonResponse(url, {"artifacts": []})
    with pytest.raises(RuntimeError, match="no successful-main"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)


def test_oversized_artifact_declared_length_stops_before_body_read_and_closes(monkeypatch):
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    monkeypatch.setattr(reuse, "MAX_ARCHIVE_BYTES", 10)
    get, calls, stream = _fake_get(raw, artifact_list, parent_run)
    stream.headers = {"Content-Length": "11"}
    with pytest.raises(ValueError, match="compressed-size bound"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)
    assert stream.iterated is False
    assert stream.closed is True
