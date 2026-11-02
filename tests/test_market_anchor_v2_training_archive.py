from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile

import pytest

import market_anchor_v2_training_archive as archive


ARTIFACT_CREATED = datetime(2026, 11, 1, 13, 15, 0, tzinfo=timezone.utc)
RUN = {
    "id": 42,
    "path": archive.SOURCE_WORKFLOW_PATH,
    "head_branch": "main",
    "head_sha": "a" * 40,
    "status": "completed",
    "conclusion": "success",
    "event": "schedule",
    "created_at": "2026-11-01T13:14:16Z",
    "updated_at": "2026-11-01T13:15:03Z",
}


def _bundle(*, extra_current=False, bad_report=None, mutate_csv=False, late_source=False):
    output = BytesIO()
    audits = []
    members = {}
    for index, code in enumerate(archive.SEASON_CODES):
        year = 2016 + index
        csv_body = (
            "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
            f"01/10/{year},Home {index},Away {index},1,0,H,5,3,2,1,0,0\n"
        ).encode()
        if mutate_csv and index == 0:
            csv_body += b"02/10/2016,Other,Other Away,0,0,D,2,2,1,1,0,0\n"
        members[archive.SOURCE_DIR + f"serie_a_{code}.csv"] = csv_body
        observed = ARTIFACT_CREATED - timedelta(seconds=20-index)
        if late_source and index == 0:
            observed = ARTIFACT_CREATED + timedelta(seconds=1)
        audits.append({
            "season_code": code,
            "archived_source_name": f"serie_a_{code}.csv",
            "source_url": f"{archive.PUBLIC_BASE}/{code}/{archive.COMPETITION_CODE}.csv",
            "csv_sha256": hashlib.sha256(csv_body).hexdigest(),
            "source_observed_at_utc": observed.isoformat(),
            "completed_source_rows": 2 if mutate_csv and index == 0 else 1,
        })
    report = {
        "schema_version": "SERIE_A_V2_LIVE_DIAGNOSTIC_SOURCE_ATTESTATION_V1",
        "mode": "RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET",
        "historical_source": "FOOTBALL_DATA_CSV",
        "frozen_candidate_sha256": archive.CANDIDATE_SHA,
        "protect_2026_27_prospective_outcomes": True,
        "2026_27_public_results_downloaded": False,
        "paid_provider_requests": 0,
        "supabase_writes": 0,
        "model_training": False,
        "model_promotion": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "feature_count": 19,
        "public_http_requests": len(archive.SEASON_CODES),
        "as_of_utc": (ARTIFACT_CREATED - timedelta(seconds=1)).isoformat(),
        "public_source_files": audits,
        "history_rows": sum(x["completed_source_rows"] for x in audits),
        "diagnostic_previews": [],
    }
    if bad_report:
        report.update(bad_report)
    members[archive.REPORT_NAME] = json.dumps(report, sort_keys=True).encode()
    if extra_current:
        members[archive.SOURCE_DIR + "serie_a_2627.csv"] = b"protected,current,season\n"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, body in members.items():
            z.writestr(name, body)
    raw = output.getvalue()
    artifact = {
        "id": 99,
        "name": archive.SOURCE_ARTIFACT_NAME,
        "expired": False,
        "size_in_bytes": len(raw),
        "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "created_at": ARTIFACT_CREATED.isoformat(),
    }
    return raw, artifact


def _verify(raw, artifact, *, run=RUN, output_dir=None):
    if output_dir is None:
        output_dir = Path("/tmp/unused-v2-training-archive")
    return archive.verify_and_extract_archive(
        raw,
        artifact=artifact,
        run=run,
        output_dir=output_dir,
        now=datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc),
    )


def test_existing_training_artifact_extracts_exactly_ten_pre_2026_27_csvs(tmp_path):
    raw, artifact_meta = _bundle()
    out = tmp_path / "training"
    manifest = _verify(raw, artifact_meta, output_dir=out)
    assert len(list(out.glob("serie_a_*.csv"))) == 10
    assert not (out / "serie_a_2627.csv").exists()
    assert manifest["artifact_sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["historical_match_rows"] == 10
    assert manifest["protected_2026_27_csv_opened"] is False
    assert manifest["target_outcomes_read"] is False
    assert manifest["season_codes"] == list(archive.SEASON_CODES)


def test_training_archive_rejects_github_digest_mismatch(tmp_path):
    raw, artifact_meta = _bundle()
    artifact_meta["digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _verify(raw, artifact_meta, output_dir=tmp_path / "training")


def test_training_archive_rejects_any_current_season_member_even_if_rehashed(tmp_path):
    raw, artifact_meta = _bundle(extra_current=True)
    artifact_meta["size_in_bytes"] = len(raw)
    artifact_meta["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="exactly the ten frozen old-season CSVs"):
        _verify(raw, artifact_meta, output_dir=tmp_path / "training")


def test_training_archive_rejects_report_that_claims_protected_results_downloaded(tmp_path):
    raw, artifact_meta = _bundle(bad_report={"2026_27_public_results_downloaded": True})
    artifact_meta["size_in_bytes"] = len(raw)
    artifact_meta["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="historical-only recovery contract"):
        _verify(raw, artifact_meta, output_dir=tmp_path / "training")


def test_training_archive_rejects_source_csv_sha_tampering(tmp_path):
    raw, artifact_meta = _bundle(mutate_csv=True)
    artifact_meta["size_in_bytes"] = len(raw)
    artifact_meta["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="CSV SHA-256 mismatch"):
        _verify(raw, artifact_meta, output_dir=tmp_path / "training")


def test_training_archive_rejects_source_observation_after_archive(tmp_path):
    raw, artifact_meta = _bundle(late_source=True)
    artifact_meta["size_in_bytes"] = len(raw)
    artifact_meta["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="source observation is after"):
        _verify(raw, artifact_meta, output_dir=tmp_path / "training")


def test_training_archive_rejects_non_main_or_failed_parent_run(tmp_path):
    raw, artifact_meta = _bundle()
    bad_run = {**RUN, "head_branch": "feature/test"}
    with pytest.raises(ValueError, match="successful approved main"):
        _verify(raw, artifact_meta, run=bad_run, output_dir=tmp_path / "training")


def test_training_archive_loader_uses_only_github_api_and_existing_artifact(tmp_path):
    raw, artifact_meta = _bundle()
    calls = []

    class JsonResponse:
        status_code = 200
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return self.payload

    class ZipResponse:
        status_code = 200
        url = "https://pipelines.actions.githubusercontent.com/signed/archive"
        headers = {"Content-Length": str(len(raw))}
        def raise_for_status(self):
            return None
        def iter_content(self, chunk_size):
            for start in range(0, len(raw), chunk_size):
                yield raw[start:start + chunk_size]
        def close(self):
            self.closed = True

    def fake_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/actions/workflows?per_page=100"):
            return JsonResponse({"workflows": [{
                "id": 123,
                "path": archive.SOURCE_WORKFLOW_PATH,
                "state": "active",
            }]})
        if url.endswith("/actions/workflows/123/runs?branch=main&per_page=100"):
            return JsonResponse({"workflow_runs": [RUN]})
        if url.endswith("/actions/runs/42/artifacts"):
            return JsonResponse({"artifacts": [artifact_meta]})
        if url.endswith("/actions/artifacts/99/zip"):
            return ZipResponse()
        raise AssertionError("unexpected URL: " + url)

    out = tmp_path / "training"
    manifest = archive.load_latest_training_archive(
        out,
        token="read-only-test-token",
        repository=archive.REPOSITORY,
        now=datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc),
        get=fake_get,
    )
    assert manifest["artifact_id"] == 99
    assert len(list(out.glob("serie_a_*.csv"))) == 10
    assert all("football-data.co.uk" not in url for url in calls)
    assert all(url.startswith("https://api.github.com/repos/MaksimBlud/football-ai/") for url in calls)


def test_training_archive_loader_requires_token_before_network(tmp_path):
    calls = []
    with pytest.raises(ValueError, match="actions:read token"):
        archive.load_latest_training_archive(
            tmp_path / "training",
            token="",
            repository=archive.REPOSITORY,
            now=datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc),
            get=lambda *args, **kwargs: calls.append(args[0]),
        )
    assert calls == []
