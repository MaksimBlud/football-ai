from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile

import pandas as pd
import pytest

import serie_a_v2_verified_historical_source_archive as source
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE, CURRENT_FILENAME, CURRENT_SEASON, CURRENT_URL,
    MANIFEST_FILENAME, SCHEMA_VERSION,
)
from serie_a_v2_current_form_forward_capture import SOURCE_WORKFLOW_PATH
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA

UTC = timezone.utc
NOW = datetime(2026, 11, 2, 12, 2, tzinfo=UTC)
RUN_CREATED = datetime(2026, 11, 2, 11, 59, tzinfo=UTC)
MANIFEST_CREATED = datetime(2026, 11, 2, 12, 0, 20, tzinfo=UTC)
ARTIFACT_CREATED = datetime(2026, 11, 2, 12, 0, 30, tzinfo=UTC)
RUN_COMPLETED = datetime(2026, 11, 2, 12, 1, tzinfo=UTC)
RUN_SHA = "a" * 40


def _old_csv(code: str, index: int) -> bytes:
    year = 2000 + int(code[:2])
    frame = pd.DataFrame([{
        "Date": f"10/10/{year}",
        "HomeTeam": f"Home_{index}",
        "AwayTeam": f"Away_{index}",
        "FTHG": 2,
        "FTAG": 0,
        "FTR": "H",
        "HC": 5,
        "AC": 3,
        "HY": 1,
        "AY": 2,
        "HR": 0,
        "AR": 0,
    }])
    return frame.to_csv(index=False).encode("utf-8")


def build_archive(*, mutate_manifest=None, mutate_old_member=False):
    codes = list(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)
    manifest_created = MANIFEST_CREATED.isoformat()
    audits = []
    members = {}
    for i, code in enumerate(codes):
        filename = f"serie_a_{code}.csv"
        body = _old_csv(code, i)
        if mutate_old_member and i == 0:
            body += b"\n"
        observed = (datetime(2026, 11, 2, 12, 0, 1, tzinfo=UTC) + timedelta(seconds=i)).isoformat()
        audits.append({
            "season_code": code,
            "source_url": f"{source.PUBLIC_BASE}/{code}/{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv",
            "archived_source_name": filename,
            "csv_sha256": sha256(body).hexdigest(),
            "source_observed_at_utc": observed,
            "completed_source_rows": 1,
        })
        members[filename] = body

    current_observed = datetime(2026, 11, 2, 12, 0, 19, tzinfo=UTC).isoformat()
    current_sha = "c" * 64
    audits.append({
        "season_code": CURRENT_CODE,
        "season": CURRENT_SEASON,
        "source_url": CURRENT_URL,
        "archived_source_name": CURRENT_FILENAME,
        "csv_sha256": current_sha,
        "source_observed_at_utc": current_observed,
        "completed_source_rows": 30,
        "total_source_rows": 30,
        "excluded_incomplete_or_same_day_rows": 0,
    })
    # Deliberately opaque protected bytes. Tests assert ZipFile.read never opens this member.
    members[CURRENT_FILENAME] = b"PROTECTED_2026_27_OUTCOME_BYTES_MUST_NOT_BE_OPENED"

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY",
        "mode": "RESEARCH_ONLY_CURRENT_FORM_SOURCE_ARCHIVE",
        "repository": "MaksimBlud/football-ai",
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "git_sha": RUN_SHA,
        "workflow_run_id": "123",
        "source_archive_created_at_utc": manifest_created,
        "frozen_candidate_sha256": FROZEN_SHA,
        "feature_count": 19,
        "historical_season_codes": codes,
        "current_season_code": CURRENT_CODE,
        "current_season": CURRENT_SEASON,
        "current_season_source_url": CURRENT_URL,
        "current_season_source_sha256": current_sha,
        "current_season_source_observed_at_utc": current_observed,
        "current_season_completed_prior_day_rows": 30,
        "current_season_total_csv_rows": 30,
        "current_season_excluded_incomplete_or_same_day_rows": 0,
        "feature_policy": {
            "use_current_season_matches_only_as_lagged_features": True,
            "same_calendar_day_matches_excluded": True,
            "future_or_unplayed_fixtures_used": False,
            "model_weights_or_feature_definitions_changed": False,
            "model_refit": False,
            "model_selection": False,
        },
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": CURRENT_SEASON,
            "minimum_completed_primary_events": 30,
            "observed_completed_primary_events": 30,
            "checked_at_utc": datetime(2026, 11, 2, 12, 0, tzinfo=UTC).isoformat(),
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "passed": True,
        },
        "target_outcome_evaluation_gate": {
            "minimum_completed_eligible_prospective_forecasts": 30,
            "outcomes_read_for_evaluation": False,
            "outcome_gate_open": False,
        },
        "source_files": audits,
        "source_file_count": len(codes) + 1,
        "historical_old_season_file_count": len(codes),
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "model_refit_or_promotion": False,
    }
    if mutate_manifest:
        mutate_manifest(manifest)
    members[MANIFEST_FILENAME] = json.dumps(manifest, sort_keys=True).encode("utf-8")
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, body in members.items():
            z.writestr(name, body)
    raw = buffer.getvalue()
    archive = {
        "artifact_id": 77,
        "run_id": 123,
        "head_sha": RUN_SHA,
        "sha256": sha256(raw).hexdigest(),
        "created_at": ARTIFACT_CREATED,
    }
    parent = {
        "run_id": 123,
        "run_head_sha": RUN_SHA,
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_created_at_utc": RUN_CREATED.isoformat(),
        "run_completed_at_utc": RUN_COMPLETED.isoformat(),
    }
    return raw, archive, parent


def test_verifies_all_ten_historical_members_without_opening_current_season(tmp_path, monkeypatch):
    raw, archive, parent = build_archive()
    original_read = zipfile.ZipFile.read
    reads = []

    def guarded_read(self, name, *args, **kwargs):
        filename = name.filename if isinstance(name, zipfile.ZipInfo) else name
        reads.append(filename)
        if filename == CURRENT_FILENAME:
            raise AssertionError("protected 2026/27 member was opened")
        return original_read(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "read", guarded_read)
    result = source.verify_historical_only_archive(
        raw, archive, parent, now=NOW, capture_dir=tmp_path
    )
    assert len(result["history"]) == len(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)
    assert len(result["source_audit"]) == 10
    assert result["source_archive"]["historical_match_rows"] == 10
    assert result["source_archive"]["current_season_member_opened"] is False
    assert result["source_archive"]["current_season_member_sha_checked"] is False
    assert CURRENT_FILENAME not in reads
    assert (tmp_path / MANIFEST_FILENAME).exists()
    assert not (tmp_path / CURRENT_FILENAME).exists()
    assert len(list(tmp_path.glob("serie_a_*.csv"))) == 10


def test_artifact_digest_mismatch_fails_before_zip_parsing():
    raw, archive, parent = build_archive()
    archive["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="artifact SHA256 mismatch"):
        source.verify_historical_only_archive(raw, archive, parent, now=NOW)


def test_old_season_csv_sha_mismatch_fails_closed():
    raw, archive, parent = build_archive(
        mutate_manifest=lambda m: m["source_files"][0].update({"csv_sha256": "0" * 64})
    )
    archive["sha256"] = sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="historical source CSV SHA256 mismatch"):
        source.verify_historical_only_archive(raw, archive, parent, now=NOW)


def test_manifest_rejects_open_target_outcome_gate():
    raw, archive, parent = build_archive(
        mutate_manifest=lambda m: m["target_outcome_evaluation_gate"].update({"outcome_gate_open": True})
    )
    archive["sha256"] = sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="target-outcome embargo"):
        source.verify_historical_only_archive(raw, archive, parent, now=NOW)


def test_historical_source_observed_after_manifest_fails_closed():
    def mutate(m):
        m["source_files"][0]["source_observed_at_utc"] = (
            MANIFEST_CREATED + timedelta(seconds=1)
        ).isoformat()
    raw, archive, parent = build_archive(mutate_manifest=mutate)
    archive["sha256"] = sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="observed after source archive creation"):
        source.verify_historical_only_archive(raw, archive, parent, now=NOW)


def test_current_season_member_size_is_checked_without_reading_bytes(monkeypatch):
    raw, archive, parent = build_archive()
    original_read = zipfile.ZipFile.read

    def guarded_read(self, name, *args, **kwargs):
        filename = name.filename if isinstance(name, zipfile.ZipInfo) else name
        if filename == CURRENT_FILENAME:
            raise AssertionError("protected member must not be read")
        return original_read(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "read", guarded_read)
    result = source.verify_historical_only_archive(raw, archive, parent, now=NOW)
    assert result["source_archive"]["current_season_member_opened"] is False


def test_latest_loader_uses_only_authenticated_github_artifact(monkeypatch):
    raw, archive, parent = build_archive()
    calls = []

    def discover(*, token, get):
        calls.append(("discover", token))
        return [archive]

    def verify(item, *, quote_time, token, get):
        calls.append(("verify", item["artifact_id"], quote_time, token))
        return parent

    def download(artifact_id, *, token, get):
        calls.append(("download", artifact_id, token))
        return raw

    monkeypatch.setattr(source, "discover_archives", discover)
    monkeypatch.setattr(source, "verify_source_run", verify)
    monkeypatch.setattr(source, "get_archive", download)
    result = source.load_latest_historical_source_archive(token="read-only-token", now=NOW)
    assert result["source_archive"]["artifact_id"] == 77
    assert [call[0] for call in calls] == ["discover", "verify", "download"]
    assert all("football-data.co.uk" not in str(call) for call in calls)


def test_missing_verified_source_archive_fails_closed(monkeypatch):
    monkeypatch.setattr(source, "discover_archives", lambda **kwargs: [])
    with pytest.raises(RuntimeError, match="no earlier main current-form source artifact"):
        source.load_latest_historical_source_archive(token="read-only-token", now=NOW)
