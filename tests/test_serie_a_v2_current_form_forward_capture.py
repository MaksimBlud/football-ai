from datetime import date, datetime, timedelta, timezone, tzinfo
from io import BytesIO
import hashlib
import json
import zipfile
from typing import Any

import pytest
import serie_a_v2_current_form_forward_capture as forward_capture_module

from serie_a_v2_current_form_forward_capture import (
    ARTIFACT_NAME,
    MANIFEST_FILENAME,
    SOURCE_WORKFLOW_PATH,
    _latest_quotes,
    get_archive,
    prepare_forward_capture as _prepare_forward_capture,
    verify_and_load_archive,
    verify_latest_source_archive,
)
from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE, CURRENT_FILENAME, CURRENT_SEASON, CURRENT_URL, REQUIRED_COLUMNS,
)
from serie_a_v2_current_form_source_capture import (
    _current_source_fixture_identities, _fixture_identity_sha256, validate_current_season_csv,
)
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes


SOURCE_OBSERVED = "2026-10-18T06:25:00+00:00"
ARCHIVE_DECLARED = "2026-10-18T06:30:00+00:00"
ARTIFACT_CREATED = datetime(2026, 10, 18, 6, 31, tzinfo=timezone.utc)
PARENT_CREATED = "2026-10-18T06:00:00+00:00"
PARENT_COMPLETED = "2026-10-18T06:32:00+00:00"
HEAD = "a" * 40


class OffsetlessTZ(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None


def quote(
    snapshot="2026-10-19T05:30:00Z",
    kickoff="2026-10-19T18:00:00Z",
):
    return {
        "event_id": "v2-current-form-test-event",
        "league": "SERIE_A",
        "home_team": "Juventus",
        "away_team": "Napoli",
        "snapshot_time_utc": snapshot,
        "commence_time_utc": kickoff,
        "home_odds": 2.2,
        "draw_odds": 3.4,
        "away_odds": 3.1,
    }


def make_current_csv():
    header = ",".join(REQUIRED_COLUMNS)
    rows = []
    start = date(2026, 8, 1)
    for i in range(30):
        day = start + timedelta(days=i)
        rows.append(
            f"{day.strftime('%d/%m/%Y')},Juventus,Napoli,1,0,H,5,3,2,1,0,0"
        )
    return (header + "\n" + "\n".join(rows) + "\n").encode()


def make_archive():
    files = {}
    source_files = []
    for code in _source_codes():
        filename = f"serie_a_{code}.csv"
        body = (
            "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HC,AC,HY,AY,HR,AR\n"
            f"01/10/{2000 + int(code[:2])},Juventus,Napoli,1,0,H,5,3,2,1,0,0\n"
        ).encode()
        files[filename] = body
        source_files.append({
            "season_code": code,
            "source_url": f"{PUBLIC_BASE}/{code}/I1.csv",
            "archived_source_name": filename,
            "csv_sha256": hashlib.sha256(body).hexdigest(),
            "source_observed_at_utc": "2026-10-18T06:10:00+00:00",
            "completed_source_rows": 1,
        })
    current = make_current_csv()
    files[CURRENT_FILENAME] = current
    current_frame, _ = validate_current_season_csv(
        current, captured_at=datetime.fromisoformat(SOURCE_OBSERVED)
    )
    current_identities = _current_source_fixture_identities(current_frame)
    current_identity_sha256 = _fixture_identity_sha256(current_identities)
    source_files.append({
        "season_code": CURRENT_CODE,
        "season": CURRENT_SEASON,
        "source_url": CURRENT_URL,
        "archived_source_name": CURRENT_FILENAME,
        "csv_sha256": hashlib.sha256(current).hexdigest(),
        "source_observed_at_utc": SOURCE_OBSERVED,
        "completed_source_rows": 30,
        "total_source_rows": 30,
        "excluded_incomplete_or_same_day_rows": 0,
    })
    manifest = {
        "schema_version": "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1",
        "experiment_id": "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY",
        "mode": "RESEARCH_ONLY_CURRENT_FORM_SOURCE_ARCHIVE",
        "repository": "MaksimBlud/football-ai",
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "git_sha": HEAD,
        "workflow_run_id": "123",
        "source_archive_created_at_utc": ARCHIVE_DECLARED,
        "frozen_candidate_sha256": FROZEN_SHA,
        "original_feature_builder_git_blob_sha1": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
        "feature_count": 19,
        "historical_season_codes": list(_source_codes()),
        "current_season_code": CURRENT_CODE,
        "current_season": CURRENT_SEASON,
        "current_season_source_url": CURRENT_URL,
        "current_season_source_sha256": hashlib.sha256(current).hexdigest(),
        "current_season_source_observed_at_utc": SOURCE_OBSERVED,
        "current_season_completed_prior_day_rows": 30,
        "current_season_total_csv_rows": 30,
        "current_season_excluded_incomplete_or_same_day_rows": 0,
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": CURRENT_SEASON,
            "minimum_completed_primary_events": 30,
            "observed_completed_primary_events": 30,
            "checked_at_utc": "2026-10-18T06:00:00+00:00",
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "gate_fixture_identity_sha256": current_identity_sha256,
            "gate_fixture_identities": [list(identity) for identity in sorted(current_identities)],
            "gate_fixture_identity_count": len(current_identities),
            "gate_fixture_identities_covered_by_current_source": len(current_identities),
            "gate_fixture_identities_missing_from_current_source": 0,
            "current_source_fixture_identity_sha256": current_identity_sha256,
            "current_source_fixture_identity_count": len(current_identities),
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
            "purpose_after_gate": "diagnostic review only; no fitting, selection, or promotion",
        },
        "source_files": source_files,
        "historical_old_season_file_count": 10,
        "source_file_count": 11,
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
    files[MANIFEST_FILENAME] = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    bio = BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for name, body in files.items():
            z.writestr(name, body)
    raw = bio.getvalue()
    meta = {
        "artifact_id": 9876,
        "run_id": 123,
        "head_sha": HEAD,
        "created_at": ARTIFACT_CREATED,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return raw, [meta]


def _fixture_current_gate_identities():
    current_frame, _ = validate_current_season_csv(
        make_current_csv(), captured_at=datetime.fromisoformat(SOURCE_OBSERVED)
    )
    return _current_source_fixture_identities(current_frame)


def prepare_forward_capture(*args, **kwargs):
    """Existing unit fixtures model a live metadata gate that matches their source archive."""
    kwargs.setdefault("current_gate_identities", _fixture_current_gate_identities())
    return _prepare_forward_capture(*args, **kwargs)


def valid_parent(archive, *, quote_time):
    assert archive["run_id"] == 123
    assert quote_time.tzinfo is not None
    return {
        "run_id": 123,
        "run_head_sha": HEAD,
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_created_at_utc": PARENT_CREATED,
        "run_completed_at_utc": PARENT_COMPLETED,
    }


def test_current_form_v2_scores_only_future_quote_with_prequote_source_and_stays_no_bet(tmp_path):
    raw, archives = make_archive()
    report = prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda artifact_id: raw,
        verify_parent_run=valid_parent,
        write_sources_to=tmp_path,
    )
    assert report["quotes_seen"] == 1
    assert report["v2_current_form_shadow_captured"] == 1
    row = report["rows"][0]
    assert row["status"] == "CURRENT_FORM_V2_SHADOW_CAPTURED_PREKICKOFF"
    preview = row["v2_preview"]
    assert preview["model_candidate_sha256"] == FROZEN_SHA
    assert preview["eligible_for_current_form_forward_shadow"] is True
    assert preview["eligible_for_frozen_prospective_cohort"] is False
    assert preview["no_bet"] is True
    assert preview["observed_frozen_feature_count"] == 19
    assert preview["median_imputed_frozen_feature_count"] == 0
    assert preview["market_1x2"] == pytest.approx(preview["active_market_fallback_1x2"])
    assert sum(preview["shadow_v2_residual_1x2"]) == pytest.approx(1.0)
    assert row["source_age_at_quote_seconds"] < 24 * 60 * 60
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["target_outcome_evaluation_gate_open"] is False
    assert report["model_refit_or_selection"] is False
    assert report["production_or_supabase_writes"] == 0
    assert report["paid_provider_calls"] == 0
    assert len(list(tmp_path.glob("current-form-source-artifact-*.zip"))) == 1


def test_real_archive_verification_is_reported_even_without_any_fresh_quote(tmp_path):
    raw, archives = make_archive()
    report = verify_latest_source_archive(
        archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda artifact_id: raw,
        verify_parent_run=valid_parent,
        current_gate_identities=_fixture_current_gate_identities(),
        write_sources_to=tmp_path,
    )
    assert report["status"] == "VERIFIED"
    assert report["verified"] is True
    assert report["artifact_id"] == 9876
    assert report["artifact_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["feature_input_gate_count"] == 30
    assert report["historical_old_season_file_count"] == 10
    assert report["source_file_count"] == 11
    assert report["current_season_history_rows"] == 30
    attestation = report["feature_source_gate_attestation"]
    assert attestation["verified"] is True
    assert attestation["gate_fixture_identity_count"] == 30
    assert attestation["gate_fixture_identities_covered_by_current_source"] == 30
    assert attestation["gate_fixture_identities_missing_from_current_source"] == 0
    assert attestation["current_source_fixture_identity_count"] == 30
    expected_frame, _ = validate_current_season_csv(
        make_current_csv(), captured_at=datetime.fromisoformat(SOURCE_OBSERVED)
    )
    expected_identity_sha256 = _fixture_identity_sha256(
        _current_source_fixture_identities(expected_frame)
    )
    assert attestation["current_source_fixture_identity_sha256"] == expected_identity_sha256
    assert report["fresh_for_new_quote"] is True
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0
    assert len(list(tmp_path.glob("current-form-source-artifact-*.zip"))) == 1




def test_forward_capture_fails_closed_when_new_completed_fixture_is_missing_from_archive(monkeypatch):
    raw, archives = make_archive()
    current_gate = _fixture_current_gate_identities() | {
        ("2026-09-01", "Newly Completed Home", "Newly Completed Away")
    }
    monkeypatch.setattr(
        forward_capture_module,
        "shadow_preview",
        lambda *_args, **_kwargs: pytest.fail("stale source must be blocked before inference"),
    )
    report = _prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        current_gate_identities=current_gate,
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["SOURCE_GATE_STALE"] == 1
    assert report["rows"][0]["status"] == "SOURCE_GATE_STALE"
    assert report["rows"][0]["source_gate_freshness"]["missing_identity_count"] == 1
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["production_or_supabase_writes"] == 0
    assert report["paid_provider_calls"] == 0

    verification = verify_latest_source_archive(
        archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        current_gate_identities=current_gate,
    )
    assert verification["fresh_for_current_feature_gate"] is False
    assert verification["fresh_for_new_quote"] is False
    assert verification["feature_source_gate_freshness"]["missing_identity_count"] == 1


@pytest.mark.parametrize("gate_size", [0, 29])
def test_forward_capture_fails_closed_when_current_gate_is_empty_or_below_minimum(monkeypatch, gate_size):
    raw, archives = make_archive()
    identities = sorted(_fixture_current_gate_identities())
    current_gate = set(identities[:gate_size])

    monkeypatch.setattr(
        forward_capture_module,
        "shadow_preview",
        lambda *_args, **_kwargs: pytest.fail("incomplete current gate must block before inference"),
    )
    report = _prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        current_gate_identities=current_gate,
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["SOURCE_GATE_STALE"] == 1
    assert report["rows"][0]["status"] == "SOURCE_GATE_STALE"
    freshness = report["rows"][0]["source_gate_freshness"]
    assert freshness["fresh"] is False
    assert freshness["reason"] == "CURRENT_GATE_BELOW_MINIMUM"
    assert freshness["current_gate_identity_count"] == gate_size
    assert freshness["minimum_completed_primary_events"] == 30
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["production_or_supabase_writes"] == 0
    assert report["paid_provider_calls"] == 0

    verification = verify_latest_source_archive(
        archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        current_gate_identities=current_gate,
    )
    assert verification["fresh_for_current_feature_gate"] is False
    assert verification["fresh_for_new_quote"] is False
    assert verification["feature_source_gate_freshness"]["reason"] == "CURRENT_GATE_BELOW_MINIMUM"


def test_missing_source_artifact_is_explicitly_reported_without_reading_outcomes():
    report = verify_latest_source_archive(
        [],
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: (_ for _ in ()).throw(
            AssertionError("no source artifact should be downloaded")
        ),
        verify_parent_run=valid_parent,
    )
    assert report["status"] == "NO_SOURCE_ARCHIVE"
    assert report["verified"] is False
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False



def test_latest_failed_source_artifact_is_skipped_for_previous_verified_archive(tmp_path):
    raw, archives = make_archive()
    previous = archives[0]
    failed = {
        **previous,
        "artifact_id": 9877,
        "run_id": 456,
        "created_at": previous["created_at"] + timedelta(minutes=1),
    }
    loaded = []

    def verify_parent(archive, *, quote_time):
        if archive["run_id"] == 456:
            raise ValueError("artifact parent is not a successful main current-form source run")
        return valid_parent(archive, quote_time=quote_time)

    report = verify_latest_source_archive(
        [previous, failed],
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda artifact_id: (loaded.append(artifact_id), raw)[1],
        verify_parent_run=verify_parent,
        current_gate_identities=_fixture_current_gate_identities(),
        write_sources_to=tmp_path,
    )

    assert report["status"] == "VERIFIED"
    assert report["artifact_id"] == previous["artifact_id"]
    assert loaded == [previous["artifact_id"]]
    assert report["unverified_parent_artifact_ids"] == [failed["artifact_id"]]
    assert report["unverified_parent_artifact_count"] == 1


def test_only_failed_source_artifacts_are_reported_without_download():
    _raw, archives = make_archive()
    failed = {
        **archives[0],
        "artifact_id": 9877,
        "run_id": 456,
        "created_at": archives[0]["created_at"] + timedelta(minutes=1),
    }

    report = verify_latest_source_archive(
        [failed],
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: (_ for _ in ()).throw(
            AssertionError("unverified failed-run artifact must not be downloaded")
        ),
        verify_parent_run=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("artifact parent is not a successful main current-form source run")
        ),
        current_gate_identities=_fixture_current_gate_identities(),
    )

    assert report["status"] == "NO_SOURCE_ARCHIVE"
    assert report["verified"] is False
    assert report["source_archive_rejection_reason"] == "NO_VERIFIED_SUCCESSFUL_SOURCE_PARENT"
    assert report["unverified_parent_artifact_count"] == 1
    assert report["unverified_parent_artifact_ids"] == [failed["artifact_id"]]
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False

def test_latest_source_verification_rejects_offsetless_clock_before_callbacks(tmp_path):
    raw, archives = make_archive()
    callbacks = []

    def load_archive(_artifact_id):
        callbacks.append("load_archive")
        return raw

    def verify_parent_run(_archive, *, quote_time):
        callbacks.append("verify_parent_run")
        return valid_parent(_archive, quote_time=quote_time)

    with pytest.raises(ValueError, match="explicit UTC offset"):
        verify_latest_source_archive(
            archives,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=OffsetlessTZ()),
            load_archive=load_archive,
            verify_parent_run=verify_parent_run,
            write_sources_to=tmp_path,
        )

    assert callbacks == []
    assert list(tmp_path.iterdir()) == []


def test_forward_capture_rejects_offsetless_clock_before_callbacks_or_output(tmp_path):
    raw, archives = make_archive()
    callbacks = []

    def load_archive(_artifact_id):
        callbacks.append("load_archive")
        return raw

    def verify_parent_run(_archive, *, quote_time):
        callbacks.append("verify_parent_run")
        return valid_parent(_archive, quote_time=quote_time)

    with pytest.raises(ValueError, match="explicit UTC offset"):
        prepare_forward_capture(
            [quote()],
            archives,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=OffsetlessTZ()),
            load_archive=load_archive,
            verify_parent_run=verify_parent_run,
            write_sources_to=tmp_path,
        )

    assert callbacks == []
    assert list(tmp_path.iterdir()) == []


def _rewrite_gate_manifest(raw: bytes, archives: list[dict], *, field: str, value: Any, remove: bool = False):
    with zipfile.ZipFile(BytesIO(raw), "r") as original:
        files = {name: original.read(name) for name in original.namelist()}
    manifest = json.loads(files[MANIFEST_FILENAME])
    gate = manifest["feature_source_gate"]
    if remove:
        gate.pop(field, None)
    else:
        gate[field] = value
    files[MANIFEST_FILENAME] = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as rewritten:
        for name, body in files.items():
            rewritten.writestr(name, body)
    tampered = buffer.getvalue()
    archives[0]["sha256"] = hashlib.sha256(tampered).hexdigest()
    return tampered


@pytest.mark.parametrize(
    ("field", "value", "remove", "message"),
    [
        ("gate_fixture_identity_sha256", "not-a-sha256", False, "identity attestation"),
        ("gate_fixture_identity_count", 29, False, "identity attestation"),
        ("gate_fixture_identities_covered_by_current_source", 29, False, "identity attestation"),
        ("gate_fixture_identities_missing_from_current_source", 1, False, "identity attestation"),
        ("current_source_fixture_identity_count", 31, False, "identity digest/count mismatch"),
        ("current_source_fixture_identity_sha256", "0" * 64, False, "identity digest/count mismatch"),
        ("gate_fixture_identity_sha256", "", True, "identity attestation"),
    ],
)
def test_forward_reader_rejects_missing_or_inconsistent_gate_identity_attestation(
    field, value, remove, message
):
    raw, archives = make_archive()
    tampered = _rewrite_gate_manifest(raw, archives, field=field, value=value, remove=remove)
    with pytest.raises(ValueError, match=message):
        verify_latest_source_archive(
            archives,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            load_archive=lambda _artifact_id: tampered,
            verify_parent_run=valid_parent,
        )


def test_precontract_quote_is_never_backfilled_from_a_later_source_archive():
    raw, archives = make_archive()
    old_quote = quote(
        snapshot="2026-10-13T14:00:00Z",
        kickoff="2026-10-25T18:00:00Z",
    )
    report = prepare_forward_capture(
        [old_quote], archives,
        as_of_utc=datetime(2026, 10, 14, 10, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: (_ for _ in ()).throw(
            AssertionError("a later source archive must never be downloaded for an earlier quote")
        ),
        verify_parent_run=valid_parent,
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["NO_EARLIER_SOURCE_ARCHIVE"] == 1
    assert report["rows"][0]["status"] == "NO_EARLIER_SOURCE_ARCHIVE"


def test_source_archive_digest_tampering_fails_closed():
    raw, archives = make_archive()
    with pytest.raises(ValueError, match="artifact SHA256 mismatch"):
        prepare_forward_capture(
            [quote()], archives,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            load_archive=lambda _artifact_id: raw + b"tampered",
            verify_parent_run=valid_parent,
        )


def test_current_form_quote_cannot_contain_target_outcome_fields():
    raw, archives = make_archive()
    malicious = {**quote(), "result": "H"}
    with pytest.raises(ValueError, match="outcomes or settlement fields forbidden"):
        prepare_forward_capture(
            [malicious], archives,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            load_archive=lambda _artifact_id: raw,
            verify_parent_run=valid_parent,
        )


def test_current_form_source_older_than_24h_at_quote_is_blocked():
    raw, archives = make_archive()
    # Source was observed on Oct 18 at 06:25, while the quote is later than 24h.
    stale_quote = quote(snapshot="2026-10-19T07:00:00Z", kickoff="2026-10-19T18:00:00Z")
    report = prepare_forward_capture(
        [stale_quote], archives,
        as_of_utc=datetime(2026, 10, 19, 7, 5, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["SOURCE_ARCHIVE_TOO_OLD"] == 1
    assert report["rows"][0]["status"] == "SOURCE_ARCHIVE_TOO_OLD"


def test_unverified_parent_cannot_admit_quote():
    raw, archives = make_archive()
    report = prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("parent run not verified")
        ),
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["SOURCE_PARENT_UNVERIFIED"] == 1
    assert report["rows"][0]["status"] == "SOURCE_PARENT_UNVERIFIED"



def test_latest_quotes_rejects_event_id_reused_for_a_different_fixture():
    now = datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc)
    first = quote(snapshot="2026-10-19T05:30:00Z")
    conflicting = {
        **quote(snapshot="2026-10-19T05:31:00Z"),
        "home_team": "AC Milan",
    }
    with pytest.raises(ValueError, match="event_id maps to conflicting fixture identity"):
        _latest_quotes([first, conflicting], now=now)


def test_latest_quotes_rejects_same_fixture_split_across_event_ids():
    now = datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc)
    first = quote(snapshot="2026-10-19T05:30:00Z")
    duplicate_fixture = {
        **quote(snapshot="2026-10-19T05:31:00Z"),
        "event_id": "different-provider-event-id",
    }
    with pytest.raises(ValueError, match="fixture identity maps to conflicting event_id"):
        _latest_quotes([first, duplicate_fixture], now=now)


def test_latest_quotes_rejects_same_fixture_split_across_event_ids_when_team_alias_changes():
    now = datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc)
    first = {
        **quote(snapshot="2026-10-19T05:30:00Z"),
        "home_team": "Atalanta BC",
        "away_team": "Juventus",
    }
    duplicate_fixture = {
        **quote(snapshot="2026-10-19T05:31:00Z"),
        "event_id": "different-provider-event-id",
        "home_team": "Atalanta",
        "away_team": "Juventus",
    }
    with pytest.raises(ValueError, match="fixture identity maps to conflicting event_id"):
        _latest_quotes([first, duplicate_fixture], now=now)


def test_latest_quotes_collapses_same_event_alias_variants_to_latest_snapshot():
    now = datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc)
    first = {
        **quote(snapshot="2026-10-19T05:30:00Z"),
        "home_team": "Atalanta BC",
        "away_team": "Juventus",
    }
    later = {
        **quote(snapshot="2026-10-19T05:31:00Z"),
        "home_team": "Atalanta",
        "away_team": "Juventus",
    }
    selected = _latest_quotes([first, later], now=now)
    assert len(selected) == 1
    assert selected[0]["snapshot_time_utc"] == "2026-10-19T05:31:00Z"
    assert selected[0]["home_team"] == "Atalanta"

@pytest.mark.parametrize(
    ("gate_checked_at", "error"),
    [
        ("2026-10-18T06:26:00+00:00", "feature-source gate timestamp"),
        ("2026-10-18T06:00:00", "naive clock-time not allowed"),
    ],
)
def test_feature_source_gate_clock_is_offset_aware_and_precedes_source(gate_checked_at, error):
    raw, archives = make_archive()
    with zipfile.ZipFile(BytesIO(raw), "r") as original:
        files = {name: original.read(name) for name in original.namelist()}
    manifest = json.loads(files[MANIFEST_FILENAME])
    manifest["feature_source_gate"]["checked_at_utc"] = gate_checked_at
    files[MANIFEST_FILENAME] = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as rewritten:
        for name, body in files.items():
            rewritten.writestr(name, body)
    tampered = buffer.getvalue()
    # Recompute the outer digest so this test reaches the temporal-contract check.
    archives[0]["sha256"] = hashlib.sha256(tampered).hexdigest()
    with pytest.raises(ValueError, match=error):
        prepare_forward_capture(
            [quote()],
            archives,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            load_archive=lambda _artifact_id: tampered,
            verify_parent_run=valid_parent,
        )

def _rewrite_source_manifest(raw, mutate):
    with zipfile.ZipFile(BytesIO(raw), "r") as source:
        files = {name: source.read(name) for name in source.namelist()}
    manifest = json.loads(files[MANIFEST_FILENAME])
    mutate(manifest)
    files[MANIFEST_FILENAME] = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for name, body in files.items():
            target.writestr(name, body)
    return output.getvalue()


def test_archive_loader_rejects_control_character_in_gate_identity_even_with_rehashed_archive():
    raw, archives = make_archive()

    def mutate(manifest):
        manifest["feature_source_gate"]["gate_fixture_identities"][0][1] = "Atalanta\tBC"

    tampered = _rewrite_source_manifest(raw, mutate)
    archive = {**archives[0], "sha256": hashlib.sha256(tampered).hexdigest()}
    parent = valid_parent(
        archive,
        quote_time=datetime(2026, 10, 19, 5, 30, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="control characters"):
        verify_and_load_archive(tampered, archive, parent)


@pytest.mark.parametrize(
    "target, field, value, expected_error",
    [
        ("feature_policy", "future_or_unplayed_fixtures_used", True, "feature policy"),
        ("feature_policy", "model_weights_or_feature_definitions_changed", True, "feature policy"),
        ("feature_policy", "model_refit", True, "feature policy"),
        ("feature_policy", "model_selection", True, "feature policy"),
        ("manifest", "feature_policy", None, "feature policy"),
        ("feature_policy", "same_calendar_day_matches_excluded", False, "feature policy"),
        ("feature_source_gate", "metadata_fields_read",
         ["match_date", "home_team", "away_team", "home_goals"], "fixture metadata"),
        ("manifest", "eligible_for_product_publication", True, "eligibility"),
        ("manifest", "eligible_for_frozen_old_season_cohort", True, "eligibility"),
        ("manifest", "eligible_for_current_form_forward_shadow", True, "eligibility"),
        ("manifest", "no_bet", False, "eligibility"),
    ],
)
def test_archive_loader_rejects_manifest_safety_contract_drift(
    target, field, value, expected_error
):
    raw, archives = make_archive()
    def mutate(manifest):
        container = manifest if target == "manifest" else manifest[target]
        container[field] = value

    tampered = _rewrite_source_manifest(raw, mutate)
    archive = {**archives[0], "sha256": hashlib.sha256(tampered).hexdigest()}
    parent = valid_parent(
        archive,
        quote_time=datetime(2026, 10, 19, 5, 30, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match=expected_error):
        verify_and_load_archive(tampered, archive, parent)


def test_archive_loader_recomputes_gate_identity_coverage_against_current_source():
    raw, archives = make_archive()

    def mutate(manifest):
        gate = manifest["feature_source_gate"]
        identities = [list(identity) for identity in gate["gate_fixture_identities"]]
        # Replace one real source fixture with a different, valid metadata-only identity.
        identities[0] = [identities[0][0], "Unrelated Home", "Unrelated Away"]
        identity_set = {tuple(identity) for identity in identities}
        gate["gate_fixture_identities"] = identities
        gate["gate_fixture_identity_count"] = len(identity_set)
        gate["observed_completed_primary_events"] = len(identity_set)
        gate["gate_fixture_identity_sha256"] = _fixture_identity_sha256(identity_set)
        # Simulate a manifest that self-claims full coverage despite the missing fixture.
        gate["gate_fixture_identities_covered_by_current_source"] = len(identity_set)
        gate["gate_fixture_identities_missing_from_current_source"] = 0

    tampered = _rewrite_source_manifest(raw, mutate)
    archive = {**archives[0], "sha256": hashlib.sha256(tampered).hexdigest()}
    parent = valid_parent(
        archive,
        quote_time=datetime(2026, 10, 19, 5, 30, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="source fixture identities do not cover the feature-source gate"):
        verify_and_load_archive(tampered, archive, parent)


def test_archive_loader_rejects_missing_gate_identity_list():
    raw, archives = make_archive()
    tampered = _rewrite_source_manifest(
        raw, lambda manifest: manifest["feature_source_gate"].pop("gate_fixture_identities")
    )
    archive = {**archives[0], "sha256": hashlib.sha256(tampered).hexdigest()}
    parent = valid_parent(
        archive,
        quote_time=datetime(2026, 10, 19, 5, 30, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="gate identity list is missing or inconsistent"):
        verify_and_load_archive(tampered, archive, parent)

class _StreamingCurrentFormArtifactResponse:
    def __init__(self, chunks, headers=None):
        self.chunks = list(chunks)
        self.headers = headers or {}
        self.iterated = 0
        self.chunk_size = None
        self.closed = False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        self.chunk_size = chunk_size
        for chunk in self.chunks:
            self.iterated += 1
            yield chunk

    def close(self):
        self.closed = True


def test_current_form_artifact_zip_download_streams_and_closes_response():
    raw = b"PK\\x03\\x04bounded-current-form-v2"
    response = _StreamingCurrentFormArtifactResponse(
        [raw[:3], b"", raw[3:]],
        headers={"Content-Length": str(len(raw))},
    )
    request = {}

    def fake_get(url, **kwargs):
        request["url"] = url
        request.update(kwargs)
        return response

    assert get_archive(9876, token="test-token", get=fake_get) == raw
    assert request["url"].endswith("/actions/artifacts/9876/zip")
    assert request["stream"] is True
    assert response.chunk_size == 64 * 1024
    assert response.closed is True


def test_current_form_artifact_zip_declared_oversize_fails_before_body_read(monkeypatch):
    monkeypatch.setattr(forward_capture_module, "MAX_ARCHIVE_BYTES", 5)
    response = _StreamingCurrentFormArtifactResponse(
        [b"must-not-read"],
        headers={"Content-Length": "6"},
    )

    with pytest.raises(ValueError, match="current-form source archive is empty or too large"):
        get_archive(
            9876,
            token="test-token",
            get=lambda _url, **_kwargs: response,
        )

    assert response.iterated == 0
    assert response.closed is True


def test_current_form_artifact_zip_stream_oversize_stops_at_first_excess_chunk(monkeypatch):
    monkeypatch.setattr(forward_capture_module, "MAX_ARCHIVE_BYTES", 5)
    response = _StreamingCurrentFormArtifactResponse([b"12345", b"6", b"never-read"])

    with pytest.raises(ValueError, match="current-form source archive is empty or too large"):
        get_archive(
            9876,
            token="test-token",
            get=lambda _url, **_kwargs: response,
        )

    assert response.iterated == 2
    assert response.closed is True



class _FakeArchiveMember:
    def __init__(self, filename, file_size, compress_size=1):
        self.filename = filename
        self.file_size = file_size
        self.compress_size = compress_size

    def is_dir(self):
        return False


class _FakeArchiveReader:
    def __init__(self, members):
        self.members = members
        self.read_calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def infolist(self):
        return self.members

    def read(self, name):
        self.read_calls.append(name)
        raise AssertionError("ZIP members must not be decompressed before size validation")


def _fake_expected_archive_members():
    historical = {f"serie_a_{code}.csv" for code in _source_codes()}
    expected = historical | {CURRENT_FILENAME, MANIFEST_FILENAME}
    return historical, expected


def _assert_archive_rejected_before_member_read(monkeypatch, members, expected_error):
    fake_zip = _FakeArchiveReader(members)
    monkeypatch.setattr(
        forward_capture_module.zipfile,
        "ZipFile",
        lambda *_args, **_kwargs: fake_zip,
    )
    raw = b"synthetic-zip-envelope"
    archive = {"sha256": hashlib.sha256(raw).hexdigest()}
    with pytest.raises(ValueError, match=expected_error):
        verify_and_load_archive(raw, archive, {})
    assert fake_zip.read_calls == []


def test_current_form_archive_rejects_oversized_manifest_before_decompression(monkeypatch):
    historical, expected = _fake_expected_archive_members()
    members = [
        _FakeArchiveMember(name, forward_capture_module.MAX_MANIFEST_BYTES + 1 if name == MANIFEST_FILENAME else 1)
        for name in sorted(expected)
    ]
    _assert_archive_rejected_before_member_read(
        monkeypatch, members, "manifest member exceeds uncompressed size limit"
    )


def test_current_form_archive_rejects_oversized_historical_csv_before_decompression(monkeypatch):
    historical, expected = _fake_expected_archive_members()
    oversized = sorted(historical)[0]
    members = [
        _FakeArchiveMember(name, forward_capture_module.MAX_HISTORICAL_CSV_BYTES + 1 if name == oversized else 1)
        for name in sorted(expected)
    ]
    _assert_archive_rejected_before_member_read(
        monkeypatch, members, "historical CSV member exceeds uncompressed size limit"
    )


def test_current_form_archive_rejects_historical_aggregate_overflow_before_decompression(monkeypatch):
    historical, expected = _fake_expected_archive_members()
    members = []
    for index, name in enumerate(sorted(expected)):
        size = 4_000_000 if name in set(sorted(historical)[:3]) else 1
        members.append(_FakeArchiveMember(name, size))
    _assert_archive_rejected_before_member_read(
        monkeypatch, members, "historical CSV members exceed aggregate uncompressed size limit"
    )


def test_current_form_archive_rejects_total_uncompressed_overflow_before_decompression(monkeypatch):
    historical, expected = _fake_expected_archive_members()
    monkeypatch.setattr(forward_capture_module, "MAX_ARCHIVE_UNCOMPRESSED_BYTES", 5)
    members = [_FakeArchiveMember(name, 1) for name in sorted(expected)]
    _assert_archive_rejected_before_member_read(
        monkeypatch, members, "archive exceeds total uncompressed size limit"
    )

