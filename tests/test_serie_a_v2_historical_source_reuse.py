from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
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
SOURCE_OBSERVED = "2026-11-02T13:53:10Z"
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
    gate_identities = [
        [(date(2026, 8, 1) + timedelta(days=index)).isoformat(), f"Home {index:02d}", f"Away {index:02d}"]
        for index in range(90)
    ]
    gate_identity_sha = reuse._fixture_identity_sha256(gate_identities)
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
            "checked_at_utc": "2026-11-02T13:53:05Z",
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "gate_fixture_identity_count": len(gate_identities),
            "gate_fixture_identity_sha256": gate_identity_sha,
            "gate_fixture_identities": gate_identities,
            "current_source_fixture_identity_count": len(gate_identities),
            "current_source_fixture_identity_sha256": gate_identity_sha,
            "gate_fixture_identities_covered_by_current_source": len(gate_identities),
            "gate_fixture_identities_missing_from_current_source": 0,
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


def _rewrite_manifest(raw: bytes, mutate) -> bytes:
    with zipfile.ZipFile(BytesIO(raw), "r") as source:
        members = {
            info.filename: source.read(info.filename)
            for info in source.infolist()
            if info.filename != reuse.MANIFEST_FILENAME
        }
        manifest = json.loads(source.read(reuse.MANIFEST_FILENAME).decode("utf-8"))
    mutate(manifest)
    members[reuse.MANIFEST_FILENAME] = (
        json.dumps(manifest, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, body in members.items():
            target.writestr(name, body)
    return stream.getvalue()


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


def _fake_get(raw, artifact_list, parent_run, origin_artifact=None, origin_parent_run=None):
    calls = []
    stream = StreamResponse([raw[:1000], raw[1000:]])
    def get(url, **kwargs):
        calls.append((url, kwargs))
        if "/actions/artifacts?name=" in url:
            return JsonResponse(url, artifact_list)
        if url.endswith(f"/actions/runs/{RUN_ID}"):
            return JsonResponse(url, parent_run)
        if origin_artifact is not None and url.endswith("/actions/artifacts/122"):
            return JsonResponse(url, origin_artifact)
        if origin_parent_run is not None and url.endswith("/actions/runs/455"):
            return JsonResponse(url, origin_parent_run)
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
    assert all(item["source_observed_at_utc"] == "2026-11-02T13:53:10+00:00" for item in audits)
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


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_identity_digest",
        "wrong_identity_digest",
        "identity_count_mismatch",
        "identity_list_missing",
        "coverage_missing",
        "metadata_columns_widened",
        "gate_checked_after_source",
    ],
)
def test_historical_cache_requires_digest_bound_fresh_identity_gate(mutation):
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()

    def mutate(manifest):
        gate = manifest["feature_source_gate"]
        if mutation == "missing_identity_digest":
            gate.pop("gate_fixture_identity_sha256")
        elif mutation == "wrong_identity_digest":
            gate["gate_fixture_identity_sha256"] = "0" * 64
        elif mutation == "identity_count_mismatch":
            gate["gate_fixture_identity_count"] = gate["observed_completed_primary_events"] - 1
        elif mutation == "identity_list_missing":
            gate.pop("gate_fixture_identities")
        elif mutation == "coverage_missing":
            gate["gate_fixture_identities_missing_from_current_source"] = 1
        elif mutation == "metadata_columns_widened":
            gate["metadata_fields_read"] = ["match_date", "home_team", "away_team", "result"]
        elif mutation == "gate_checked_after_source":
            gate["checked_at_utc"] = "2026-11-02T13:54:00Z"

    raw = _rewrite_manifest(raw, mutate)
    artifact_list["artifacts"][0]["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    get, _calls, _stream = _fake_get(raw, artifact_list, parent_run)
    with pytest.raises(ValueError, match="feature-source gate|identity"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)


def test_source_parent_must_be_exact_successful_main_run_before_download():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    parent_run["conclusion"] = "failure"
    get, calls, _stream = _fake_get(raw, artifact_list, parent_run)
    with pytest.raises(ValueError, match="successful main source workflow"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)
    assert not any(url.endswith("/zip") for url, _ in calls)


def test_push_created_source_artifact_is_rejected_before_zip_download():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    parent_run["event"] = "push"
    get, calls, _stream = _fake_get(raw, artifact_list, parent_run)

    with pytest.raises(ValueError, match="successful main source workflow"):
        reuse.load_verified_historical_source_archive(token="test-token", now=NOW, get=get)

    assert not any(url.endswith("/zip") for url, _ in calls)


def test_guarded_workflow_run_source_artifact_is_accepted():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    parent_run["event"] = "workflow_run"
    get, calls, _stream = _fake_get(raw, artifact_list, parent_run)

    history, audits, provenance = reuse.load_verified_historical_source_archive(
        token="test-token", now=NOW, get=get
    )

    assert len(history) == len(reuse.HISTORICAL_CODES)
    assert len(audits) == len(reuse.HISTORICAL_CODES)
    assert provenance["mode"] == "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY"
    assert any(url.endswith("/zip") for url, _ in calls)
    assert not any("football-data.co.uk" in url for url, _ in calls)


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

 

def _make_reused_artifact(raw):
    origin_created = "2026-11-01T13:53:57Z"
    origin_completed = "2026-11-01T13:54:01Z"
    origin_head = "b" * 40
    origin_sha = "c" * 64
    stream = BytesIO()
    with zipfile.ZipFile(BytesIO(raw), "r") as source:
        members = {name: source.read(name) for name in source.namelist() if name != reuse.MANIFEST_FILENAME}
        manifest = json.loads(source.read(reuse.MANIFEST_FILENAME).decode("utf-8"))
    for item in manifest["source_files"]:
        if item["season_code"] != reuse.CURRENT_CODE:
            item["source_observed_at_utc"] = "2026-11-01T13:52:00Z"
    manifest["historical_source_reuse"] = {
        "schema_version": reuse.SCHEMA_VERSION,
        "mode": "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY",
        "source_artifact_id": 122,
        "source_artifact_sha256": origin_sha,
        "source_artifact_created_at_utc": origin_created,
        "source_parent_run_id": 455,
        "source_parent_run_head_sha": origin_head,
        "source_parent_run_completed_at_utc": origin_completed,
        "historical_files_reused": len(reuse.HISTORICAL_CODES),
        "public_historical_csv_requests": 0,
        "current_season_file_reused": False,
        "prior_feature_gate_reused": False,
        "protected_2026_27_source_file_read": False,
        "target_outcomes_read": False,
        "supabase_writes": 0,
        "paid_provider_calls": 0,
    }
    members[reuse.MANIFEST_FILENAME] = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, body in members.items():
            target.writestr(name, body)
    new_raw = stream.getvalue()
    origin_artifact = {
        "id": 122,
        "name": reuse.ARTIFACT_NAME,
        "expired": False,
        "digest": "sha256:" + origin_sha,
        "created_at": origin_created,
        "workflow_run": {"id": 455, "head_branch": "main", "head_sha": origin_head},
    }
    origin_parent = {
        "id": 455,
        "path": reuse.SOURCE_WORKFLOW_PATH,
        "name": reuse.SOURCE_WORKFLOW_NAME,
        "head_branch": "main",
        "head_sha": origin_head,
        "status": "completed",
        "conclusion": "success",
        "event": "schedule",
        "created_at": "2026-11-01T13:53:01Z",
        "updated_at": origin_completed,
    }
    return new_raw, origin_artifact, origin_parent


def test_reused_artifact_must_point_back_to_a_verified_original_main_artifact():
    raw, _artifact, artifact_list, parent_run = _artifact_fixture()
    raw, origin_artifact, origin_parent = _make_reused_artifact(raw)
    artifact_list["artifacts"][0]["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    get, calls, _stream = _fake_get(raw, artifact_list, parent_run, origin_artifact, origin_parent)
    history, audits, provenance = reuse.load_verified_historical_source_archive(
        token="test-token", now=NOW, get=get
    )
    assert len(history) == 10
    assert len(audits) == 10
    assert provenance["source_artifact_id"] == 122
    assert provenance["source_artifact_sha256"] == "c" * 64
    assert provenance["source_parent_run_id"] == 455
    assert provenance["source_parent_run_head_sha"] == "b" * 40
    assert provenance["source_artifact_created_at_utc"] == "2026-11-01T13:53:57+00:00"
    assert any(url.endswith("/actions/artifacts/122") for url, _ in calls)
    assert any(url.endswith("/actions/runs/455") for url, _ in calls)
