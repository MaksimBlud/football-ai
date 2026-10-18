from datetime import date, datetime, timedelta, timezone
from io import BytesIO
import hashlib
import json
import zipfile

import pytest

from serie_a_v2_current_form_forward_capture import (
    ARTIFACT_NAME,
    MANIFEST_FILENAME,
    SOURCE_WORKFLOW_PATH,
    fetch_saved_serie_a_fixture_metadata,
    prepare_forward_capture,
    verify_latest_source_archive,
)
from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE, CURRENT_FILENAME, CURRENT_SEASON, CURRENT_URL, REQUIRED_COLUMNS,
)
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes


SOURCE_OBSERVED = "2026-10-18T06:25:00+00:00"
ARCHIVE_DECLARED = "2026-10-18T06:30:00+00:00"
ARTIFACT_CREATED = datetime(2026, 10, 18, 6, 31, tzinfo=timezone.utc)
PARENT_CREATED = "2026-10-18T06:00:00+00:00"
PARENT_COMPLETED = "2026-10-18T06:32:00+00:00"
HEAD = "a" * 40


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


def make_archive(*, legacy=False):
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
        "schema_version": "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1_1",
        "policy_revision": "1.1",
        "policy_path": "experiments/market_anchor_1x2_v2_current_form_policy_v1_1.json",
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
        "current_season_latest_match_date": "2026-08-30",
        "current_season_days_since_latest_match_at_capture": 49,
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": CURRENT_SEASON,
            "minimum_completed_primary_events": 30,
            "observed_completed_primary_events": 30,
            "checked_at_utc": "2026-10-18T06:00:00+00:00",
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
    if legacy:
        manifest["schema_version"] = "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1"
        for key in (
            "policy_revision", "policy_path",
            "current_season_latest_match_date",
            "current_season_days_since_latest_match_at_capture",
        ):
            manifest.pop(key, None)
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


def schedule_metadata(*, include_gap=False):
    rows = [
        {
            "event_id": "known-prior-fixture",
            "league": "SERIE_A",
            "home_team": "Juventus",
            "away_team": "Napoli",
            "commence_time_utc": "2026-08-10T18:00:00Z",
            "snapshot_time_utc": "2026-08-09T12:00:00Z",
        },
        {
            "event_id": "v2-current-form-test-event",
            "league": "SERIE_A",
            "home_team": "Juventus",
            "away_team": "Napoli",
            "commence_time_utc": "2026-10-19T18:00:00Z",
            "snapshot_time_utc": "2026-10-19T05:30:00Z",
        },
    ]
    if include_gap:
        rows.append({
            "event_id": "missing-prior-day-fixture",
            "league": "SERIE_A",
            "home_team": "Atalanta BC",
            "away_team": "Frosinone",
            "commence_time_utc": "2026-10-16T18:45:00Z",
            "snapshot_time_utc": "2026-10-13T14:48:53Z",
        })
    return rows


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
        fixture_metadata=schedule_metadata(),
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
        write_sources_to=tmp_path,
        fixture_metadata=schedule_metadata(),
    )
    assert report["status"] == "VERIFIED_FRESH"
    assert report["verified"] is True
    assert report["artifact_id"] == 9876
    assert report["artifact_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["feature_input_gate_count"] == 30
    assert report["historical_old_season_file_count"] == 10
    assert report["source_file_count"] == 11
    assert report["current_season_history_rows"] == 30
    assert report["current_season_latest_match_date"] == "2026-08-30"
    assert report["current_season_days_since_latest_match_at_capture"] == 49
    assert report["source_schedule_completeness"]["complete"] is True
    assert report["fresh_for_new_quote"] is True
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False
    assert report["paid_provider_calls"] == report["supabase_writes"] == 0
    assert len(list(tmp_path.glob("current-form-source-artifact-*.zip"))) == 1


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




def test_missing_prior_day_schedule_fixture_blocks_fresh_quote():
    raw, archives = make_archive()
    report = prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        fixture_metadata=schedule_metadata(include_gap=True),
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["CURRENT_FORM_SOURCE_BEHIND_SCHEDULE"] == 1
    row = report["rows"][0]
    assert row["status"] == "CURRENT_FORM_SOURCE_BEHIND_SCHEDULE"
    assert row["source_schedule_completeness"]["gap_count"] == 1
    assert row["source_schedule_completeness"]["gaps"][0]["event_id"] == "missing-prior-day-fixture"
    assert row["source_schedule_completeness"]["gaps"][0]["missing_fixture_key"] == [
        "2026-10-16", "Atalanta", "Frosinone"
    ]
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False


def test_schedule_metadata_unavailable_blocks_fresh_quote():
    raw, archives = make_archive()
    report = prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        fixture_metadata=[],
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["SCHEDULE_METADATA_UNAVAILABLE"] == 1
    assert report["rows"][0]["status"] == "SCHEDULE_METADATA_UNAVAILABLE"


def test_legacy_source_archive_is_verified_but_never_admitted_to_new_policy():
    raw, archives = make_archive(legacy=True)
    verification = verify_latest_source_archive(
        archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        fixture_metadata=schedule_metadata(),
    )
    assert verification["verified"] is True
    assert verification["policy_revision"] == "1.0_LEGACY"
    assert verification["status"] == "VERIFIED_LEGACY_POLICY_NOT_ELIGIBLE"
    assert verification["fresh_for_new_quote"] is False

    report = prepare_forward_capture(
        [quote()], archives,
        as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
        load_archive=lambda _artifact_id: raw,
        verify_parent_run=valid_parent,
        fixture_metadata=schedule_metadata(),
    )
    assert report["v2_current_form_shadow_captured"] == 0
    assert report["blocked"]["LEGACY_SOURCE_POLICY_NOT_ELIGIBLE"] == 1
    assert report["rows"][0]["status"] == "LEGACY_SOURCE_POLICY_NOT_ELIGIBLE"


def test_schedule_metadata_query_selects_only_identity_and_time_fields():
    class FakeQuery:
        def __init__(self):
            self.selected = None
        def table(self, _name): return self
        def select(self, fields): self.selected = fields; return self
        def eq(self, *_args): return self
        def gte(self, *_args): return self
        def order(self, *_args, **_kwargs): return self
        def limit(self, *_args): return self
        def execute(self): return type("Response", (), {"data": schedule_metadata()})()

    client = FakeQuery()
    rows = fetch_saved_serie_a_fixture_metadata(client)
    assert len(rows) == 2
    assert client.selected == (
        "event_id,league,home_team,away_team,commence_time_utc,snapshot_time_utc"
    )
    assert not any("score" in field.lower() or "result" in field.lower()
                   for field in client.selected.split(","))


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
