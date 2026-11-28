from datetime import date, datetime, timedelta, timezone
from io import BytesIO
import hashlib
import json
import zipfile

import pytest
import market_anchor_v2_direct_access as direct_access
import serie_a_v2_current_form_forward_capture as forward_capture

from serie_a_v2_current_form_forward_capture import (
    ARTIFACT_NAME,
    MANIFEST_FILENAME,
    SOURCE_WORKFLOW_PATH,
    prepare_forward_capture,
    verify_latest_source_archive,
    discover_archives,
    get_archive,
)
from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE, CURRENT_FILENAME, CURRENT_SEASON, CURRENT_URL, REQUIRED_COLUMNS,
)
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
import serie_a_v2_frozen_shadow_preview as frozen_preview
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes


SOURCE_OBSERVED = "2026-10-18T06:25:00+00:00"
ARCHIVE_DECLARED = "2026-10-18T06:30:00+00:00"
ARTIFACT_CREATED = datetime(2026, 10, 18, 6, 31, tzinfo=timezone.utc)
PARENT_CREATED = "2026-10-18T06:00:00+00:00"
PARENT_COMPLETED = "2026-10-18T06:32:00+00:00"


@pytest.fixture(autouse=True)
def _allow_synthetic_provider_rights_for_offline_current_form_tests(monkeypatch):
    monkeypatch.setattr(frozen_preview, "require_v2_source_capture_rights", lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"})
    monkeypatch.setattr(frozen_preview, "require_v2_inference_access", lambda: {"access_scope": "SYNTHETIC_TEST_ONLY"})
    monkeypatch.setattr(direct_access, "require_v2_inference_access", lambda: {"access_scope": "SYNTHETIC_TEST_ONLY"})
    monkeypatch.setattr(direct_access, "require_v2_source_capture_rights", lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"})
    monkeypatch.setattr(direct_access, "require_v2_inference_rights", lambda: {"scope_status": "SYNTHETIC_TEST_ONLY"})
HEAD = "a" * 40


def quote(
    snapshot="2026-10-19T05:30:00Z",
    kickoff="2026-10-19T18:00:00Z",
    created_at=None,
):
    if created_at is None:
        snapshot_dt = datetime.fromisoformat(snapshot.replace("Z", "+00:00"))
        created_at = (snapshot_dt + timedelta(seconds=1)).isoformat()
    return {
        "event_id": "v2-current-form-test-event",
        "league": "SERIE_A",
        "home_team": "Juventus",
        "away_team": "Napoli",
        "snapshot_time_utc": snapshot,
        "created_at": created_at,
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
    assert row["quote_row_created_at_utc"] == "2026-10-19T05:30:01+00:00"
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
    )
    assert report["status"] == "VERIFIED"
    assert report["verified"] is True
    assert report["artifact_id"] == 9876
    assert report["artifact_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["feature_input_gate_count"] == 30
    assert report["historical_old_season_file_count"] == 10
    assert report["source_file_count"] == 11
    assert report["current_season_history_rows"] == 30
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



def test_current_form_artifact_discovery_defaults_to_denied_before_github_access(monkeypatch):
    monkeypatch.delenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", raising=False)
    calls = []

    def forbidden_get(url, **kwargs):
        calls.append(url)
        raise AssertionError("GitHub must not be accessed while V2 live access is held")

    with pytest.raises(PermissionError, match="MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=true"):
        discover_archives(token="synthetic-token", get=forbidden_get)
    assert calls == []


def test_current_form_artifact_discovery_rejects_public_repo_before_catalog_read(monkeypatch):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []

    class Response:
        url = GITHUB_API
        status_code = 200

        def json(self):
            return {"full_name": "MaksimBlud/football-ai", "private": False}

    def fake_get(url, **kwargs):
        calls.append(url)
        assert url == GITHUB_API
        return Response()

    with pytest.raises(PermissionError, match="requires the exact GitHub repository to be private"):
        discover_archives(token="synthetic-token", get=fake_get)
    assert calls == [GITHUB_API]


def test_current_form_source_zip_download_rejects_public_repo_before_artifact_bytes(monkeypatch):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []

    class Response:
        url = GITHUB_API
        status_code = 200

        def json(self):
            return {"full_name": "MaksimBlud/football-ai", "private": False}

    def fake_get(url, **kwargs):
        calls.append(url)
        assert url == GITHUB_API
        return Response()

    with pytest.raises(PermissionError, match="requires the exact GitHub repository to be private"):
        get_archive(9876, token="synthetic-token", get=fake_get)
    assert calls == [GITHUB_API]


def _private_repository_get(fake_artifact_get, calls):
    from serie_a_v2_live_access_guard import GITHUB_API

    class RepoResponse:
        url = GITHUB_API
        status_code = 200

        def json(self):
            return {"full_name": "MaksimBlud/football-ai", "private": True}

    def wrapped(url, **kwargs):
        calls.append((url, kwargs))
        if url == GITHUB_API:
            assert kwargs.get("allow_redirects") is False
            return RepoResponse()
        return fake_artifact_get(url, **kwargs)

    return wrapped


class _FakeArtifactDownloadResponse:
    def __init__(self, status_code, url, *, headers=None, content=b"", history=()):
        self.status_code = status_code
        self.url = url
        self.headers = headers or {}
        self.content = content
        self.history = list(history)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_current_form_source_zip_download_checks_private_repo_and_safe_redirect(monkeypatch):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = f"{GITHUB_API}/actions/artifacts/9876/zip"
    signed_url = (
        "https://productionresultssa0.blob.core.windows.net/"
        "actions-results/container/archive.zip?sig=synthetic"
    )
    archive_bytes = bytes.fromhex("504b0304") + b"synthetic-private-zip"
    calls = []

    def fake_artifact_get(url, **kwargs):
        if url == api_url:
            assert kwargs["allow_redirects"] is False
            assert kwargs["headers"]["Authorization"] == "Bearer synthetic-token"
            return _FakeArtifactDownloadResponse(
                302, api_url, headers={"Location": signed_url}
            )
        assert url == signed_url
        assert kwargs["allow_redirects"] is False
        assert "headers" not in kwargs
        return _FakeArtifactDownloadResponse(200, signed_url, content=archive_bytes)

    assert get_archive(
        9876, token="synthetic-token",
        get=_private_repository_get(fake_artifact_get, calls),
    ) == archive_bytes
    assert [url for url, _ in calls] == [GITHUB_API, api_url, signed_url]


@pytest.mark.parametrize(
    "location",
    [
        "http://productionresultssa0.blob.core.windows.net/actions-results/a.zip?sig=x",
        "https://evil.example/actions-results/a.zip?sig=x",
        "https://productionresults.evil.blob.core.windows.net/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net/other/a.zip?sig=x",
        "https://user@productionresultssa0.blob.core.windows.net/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net:444/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net/actions-results/a.zip",
        "https://productionresultssa0.blob.core.windows.net/actions-results/../a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net:/actions-results/a.zip?sig=x",
        "https://productionresultssa0.blob.core.windows.net/actions-results/a.zip?sig=x#fragment",
    ],
)
def test_current_form_get_archive_rejects_untrusted_redirect_before_second_request(
    monkeypatch, location
):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = f"{GITHUB_API}/actions/artifacts/123/zip"
    calls = []

    def fake_artifact_get(url, **kwargs):
        assert url == api_url
        return _FakeArtifactDownloadResponse(
            302, api_url, headers={"Location": location}
        )

    with pytest.raises(ValueError, match="redirect"):
        get_archive(
            123, token="synthetic-token",
            get=_private_repository_get(fake_artifact_get, calls),
        )
    assert [url for url, _ in calls] == [GITHUB_API, api_url]


def test_current_form_get_archive_rejects_missing_location_and_non_redirect_response(monkeypatch):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = f"{GITHUB_API}/actions/artifacts/123/zip"
    calls = []

    def missing_location(url, **kwargs):
        return _FakeArtifactDownloadResponse(302, api_url)

    with pytest.raises(ValueError, match="Location"):
        get_archive(
            123, token="synthetic-token",
            get=_private_repository_get(missing_location, calls),
        )
    assert [url for url, _ in calls] == [GITHUB_API, api_url]

    calls.clear()

    def api_200(url, **kwargs):
        return _FakeArtifactDownloadResponse(200, api_url, content=b"not-a-redirect")

    with pytest.raises(ValueError, match="HTTP 302"):
        get_archive(
            123, token="synthetic-token",
            get=_private_repository_get(api_200, calls),
        )
    assert [url for url, _ in calls] == [GITHUB_API, api_url]


def test_current_form_get_archive_rejects_second_redirect_without_forwarding_token(monkeypatch):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = f"{GITHUB_API}/actions/artifacts/123/zip"
    signed_url = (
        "https://productionresultssa0.blob.core.windows.net/"
        "actions-results/container/archive.zip?sig=synthetic"
    )
    calls = []

    def fake_artifact_get(url, **kwargs):
        if url == api_url:
            return _FakeArtifactDownloadResponse(
                302, api_url, headers={"Location": signed_url}
            )
        return _FakeArtifactDownloadResponse(
            302, signed_url, headers={"Location": "https://evil.example/next"}
        )

    with pytest.raises(ValueError, match="HTTP 200"):
        get_archive(
            123, token="synthetic-token",
            get=_private_repository_get(fake_artifact_get, calls),
        )
    assert [url for url, _ in calls] == [GITHUB_API, api_url, signed_url]
    assert "headers" not in calls[-1][1]
    assert calls[-1][1]["allow_redirects"] is False


def test_current_form_get_archive_rejects_unexpected_final_url_and_history(monkeypatch):
    from serie_a_v2_live_access_guard import GITHUB_API

    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    api_url = f"{GITHUB_API}/actions/artifacts/123/zip"
    signed_url = (
        "https://productionresultssa0.blob.core.windows.net/"
        "actions-results/container/archive.zip?sig=synthetic"
    )
    calls = []

    def wrong_final_url(url, **kwargs):
        if url == api_url:
            return _FakeArtifactDownloadResponse(
                302, api_url, headers={"Location": signed_url}
            )
        return _FakeArtifactDownloadResponse(200, "https://evil.example/other", content=b"zip")

    with pytest.raises(ValueError, match="HTTP 200"):
        get_archive(
            123, token="synthetic-token",
            get=_private_repository_get(wrong_final_url, calls),
        )

    def hidden_redirect_history(url, **kwargs):
        return _FakeArtifactDownloadResponse(
            302, api_url, headers={"Location": signed_url}, history=[object()]
        )

    with pytest.raises(ValueError, match="HTTP 302"):
        get_archive(
            123, token="synthetic-token",
            get=_private_repository_get(hidden_redirect_history, calls),
        )


@pytest.mark.parametrize("artifact_id", [True, 0, -1, "123"])
def test_current_form_get_archive_rejects_invalid_artifact_identity_before_network(
    monkeypatch, artifact_id
):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []
    with pytest.raises(ValueError, match="artifact id"):
        get_archive(
            artifact_id, token="synthetic-token",
            get=lambda *args, **kwargs: calls.append((args, kwargs)),
        )
    assert calls == []


def test_current_form_get_archive_rejects_missing_token_before_network(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []
    with pytest.raises(ValueError, match="token missing"):
        get_archive(
            123, token=" ",
            get=lambda *args, **kwargs: calls.append((args, kwargs)),
        )
    assert calls == []


@pytest.mark.parametrize(
    ("created_at", "remove_created_at", "as_of_utc", "message"),
    [
        (
            None, True, datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            "saved quote row is missing created_at",
        ),
        (
            "2026-10-19T05:29:59Z", False,
            datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            "saved quote row persisted before declared snapshot time",
        ),
        (
            "2026-10-19T05:40:01Z", False,
            datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            "saved quote row persisted after capture clock",
        ),
        (
            "2026-10-19T18:00:00Z", False,
            datetime(2026, 10, 19, 19, 0, tzinfo=timezone.utc),
            "saved quote row persisted at or after kickoff",
        ),
    ],
)
def test_current_form_quote_persistence_is_preflighted_before_source_callbacks(
    created_at, remove_created_at, as_of_utc, message
):
    raw, archives = make_archive()
    candidate = quote(created_at=None if remove_created_at else created_at)
    if remove_created_at:
        candidate.pop("created_at")
    callbacks = []

    with pytest.raises(ValueError, match=message):
        prepare_forward_capture(
            [candidate],
            archives,
            as_of_utc=as_of_utc,
            load_archive=lambda _artifact_id: callbacks.append("archive") or raw,
            verify_parent_run=lambda *_args, **_kwargs: callbacks.append("parent") or {},
        )

    assert callbacks == [], "invalid quote persistence must fail before source or parent I/O"

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


class _UntouchableForwardInput:
    def __iter__(self):
        raise AssertionError("caller input was inspected before provider-rights preflight")

    def __bool__(self):
        raise AssertionError("caller input truthiness was inspected before provider-rights preflight")

    def __len__(self):
        raise AssertionError("caller input length was inspected before provider-rights preflight")

    def get(self, *_args, **_kwargs):
        raise AssertionError("caller mapping was inspected before provider-rights preflight")


@pytest.mark.parametrize(
    ("blocked_scope", "expected_calls"),
    [
        ("source_capture", ["source_capture"]),
        ("inference", ["source_capture", "inference"]),
    ],
)
def test_current_form_prepare_requires_both_provider_scopes_before_quotes_or_callbacks(
    monkeypatch, tmp_path, blocked_scope, expected_calls
):
    calls = []

    def source_rights():
        calls.append("source_capture")
        if blocked_scope == "source_capture":
            raise PermissionError("source capture rights unresolved")
        return {"scope_status": "SYNTHETIC_TEST_ONLY"}

    def inference_rights():
        calls.append("inference")
        if blocked_scope == "inference":
            raise PermissionError("frozen inference rights unresolved")
        return {"scope_status": "SYNTHETIC_TEST_ONLY"}

    monkeypatch.setattr(direct_access, "require_v2_source_capture_rights", source_rights)
    monkeypatch.setattr(direct_access, "require_v2_inference_rights", inference_rights)
    output_dir = tmp_path / "must-not-be-created"

    with pytest.raises(PermissionError, match="rights unresolved"):
        prepare_forward_capture(
            _UntouchableForwardInput(),
            _UntouchableForwardInput(),
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            load_archive=lambda *_args, **_kwargs: pytest.fail("archive callback ran before rights"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent callback ran before rights"),
            write_sources_to=output_dir,
        )

    assert calls == expected_calls
    assert not output_dir.exists()


def test_current_form_artifact_discovery_and_download_require_provider_rights_before_private_check_or_network(
    monkeypatch,
):
    calls = []

    def denied_source_rights():
        calls.append("source_capture")
        raise PermissionError("source capture rights unresolved")

    monkeypatch.setattr(direct_access, "require_v2_source_capture_rights", denied_source_rights)
    monkeypatch.setattr(
        direct_access, "require_v2_inference_rights",
        lambda: pytest.fail("inference rights checked after source rights were denied"),
    )
    monkeypatch.setattr(
        forward_capture, "require_private_repository",
        lambda **_kwargs: pytest.fail("private-repository lookup ran before provider-rights preflight"),
    )
    network_calls = []

    with pytest.raises(PermissionError, match="source capture rights unresolved"):
        forward_capture.discover_archives(
            token="synthetic-token",
            get=lambda *args, **kwargs: network_calls.append((args, kwargs)),
        )
    with pytest.raises(PermissionError, match="source capture rights unresolved"):
        forward_capture.get_archive(
            123,
            token="synthetic-token",
            get=lambda *args, **kwargs: network_calls.append((args, kwargs)),
        )

    assert calls == ["source_capture", "source_capture"]
    assert network_calls == []


def test_current_form_archive_parsing_and_parent_verification_require_rights_before_inputs(monkeypatch):
    def denied_source_rights():
        raise PermissionError("source capture rights unresolved")

    monkeypatch.setattr(direct_access, "require_v2_source_capture_rights", denied_source_rights)
    monkeypatch.setattr(
        direct_access, "require_v2_inference_rights",
        lambda: pytest.fail("inference rights checked after source rights were denied"),
    )
    untouched = _UntouchableForwardInput()

    with pytest.raises(PermissionError, match="source capture rights unresolved"):
        forward_capture.verify_and_load_archive(untouched, untouched, untouched)
    with pytest.raises(PermissionError, match="source capture rights unresolved"):
        forward_capture.verify_source_run(
            untouched,
            quote_time=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            token="synthetic-token",
            get=lambda *_args, **_kwargs: pytest.fail("GitHub API was called before rights"),
        )
    with pytest.raises(PermissionError, match="source capture rights unresolved"):
        forward_capture.verify_latest_source_archive(
            untouched,
            as_of_utc=datetime(2026, 10, 19, 5, 40, tzinfo=timezone.utc),
            load_archive=lambda *_args, **_kwargs: pytest.fail("archive callback ran before rights"),
            verify_parent_run=lambda *_args, **_kwargs: pytest.fail("parent callback ran before rights"),
        )


def test_current_form_forward_cli_checks_provider_rights_before_argument_or_credential_access(monkeypatch):
    monkeypatch.setattr(
        direct_access, "require_v2_source_capture_rights",
        lambda: (_ for _ in ()).throw(PermissionError("source capture rights unresolved")),
    )
    monkeypatch.setattr(
        direct_access, "require_v2_inference_rights",
        lambda: pytest.fail("inference rights checked after source rights were denied"),
    )

    with pytest.raises(PermissionError, match="source capture rights unresolved"):
        forward_capture.main()
