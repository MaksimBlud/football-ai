from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import serie_a_v2_public_source_download_budget as budget


UTC = timezone.utc
SOURCE_PATH = ".github/workflows/serie-a-v2-current-form-source-capture.yml"
DIAGNOSTIC_PATH = ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml"
SHA = "a" * 40


class FakeResponse:
    def __init__(self, url, payload, status=200):
        self.url = url
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload


def test_first_download_is_allowed_without_any_marker():
    allowed, next_allowed = budget.decide_download_permission(
        now=datetime(2026, 11, 2, tzinfo=UTC), latest_attempt_at=None
    )
    assert allowed is True
    assert next_allowed is None


@pytest.mark.parametrize("hours,allowed", [(169, False), (169.99, False), (170, True), (240, True)])
def test_each_workflow_has_a_170_hour_cooldown(hours, allowed):
    latest = datetime(2026, 11, 1, tzinfo=UTC)
    now = latest + timedelta(hours=hours)
    actual, next_allowed = budget.decide_download_permission(
        now=now, latest_attempt_at=latest
    )
    assert actual is allowed
    assert next_allowed == latest + timedelta(hours=170)


def test_two_workflows_each_get_one_slot_per_seven_day_span_without_starvation():
    assert budget.MIN_DOWNLOAD_INTERVAL > timedelta(days=7)
    assert set(budget.ALLOWED_WORKFLOW_PATHS) == {SOURCE_PATH, DIAGNOSTIC_PATH}
    start = datetime(2026, 11, 2, 5, 50, tzinfo=UTC)
    diagnostic = start + timedelta(minutes=23)
    attempts = [
        (SOURCE_PATH, start),
        (DIAGNOSTIC_PATH, diagnostic),
        (SOURCE_PATH, start + budget.MIN_DOWNLOAD_INTERVAL),
        (DIAGNOSTIC_PATH, diagnostic + budget.MIN_DOWNLOAD_INTERVAL),
    ]
    for workflow_path in budget.ALLOWED_WORKFLOW_PATHS:
        times = [at for path, at in attempts if path == workflow_path]
        assert all((right - left) >= budget.MIN_DOWNLOAD_INTERVAL for left, right in zip(times, times[1:]))
    for window_start in (start, diagnostic, start + timedelta(days=1)):
        in_window = [at for _, at in attempts if window_start <= at < window_start + timedelta(days=7)]
        assert len(in_window) <= 2
    source_allowed, _ = budget.decide_download_permission(now=diagnostic, latest_attempt_at=start)
    diagnostic_allowed, _ = budget.decide_download_permission(now=diagnostic, latest_attempt_at=diagnostic - budget.MIN_DOWNLOAD_INTERVAL)
    assert source_allowed is False
    assert diagnostic_allowed is True


def test_offsetless_and_future_clocks_fail_closed():
    with pytest.raises(ValueError, match="real UTC offset"):
        budget.decide_download_permission(
            now=datetime(2026, 11, 2), latest_attempt_at=None
        )
    with pytest.raises(ValueError, match="future"):
        budget.decide_download_permission(
            now=datetime(2026, 11, 2, tzinfo=UTC),
            latest_attempt_at=datetime(2026, 11, 3, tzinfo=UTC),
        )


def test_marker_is_metadata_only_and_pins_approved_workflow():
    marker = budget.build_attempt_marker(
        now=datetime(2026, 11, 2, tzinfo=UTC),
        workflow_path=SOURCE_PATH,
        run_id=123,
        head_sha=SHA,
        latest_attempt_at=None,
    )
    assert marker["schema_version"] == "SERIE_A_V2_PUBLIC_SOURCE_DOWNLOAD_ATTEMPT_V1"
    assert marker["minimum_interval_hours"] == 170
    assert marker["no_paid_provider_calls"] is True
    assert marker["budget_guard_uses_supabase"] is False
    assert marker["budget_guard_reads_target_outcomes"] is False
    assert not any(key.lower() in {"score", "result", "home_goals", "away_goals", "ftr"} for key in marker)


def test_marker_rejects_unapproved_workflow_or_bad_identity():
    with pytest.raises(ValueError, match="not allowed"):
        budget.build_attempt_marker(
            now=datetime(2026, 11, 2, tzinfo=UTC),
            workflow_path=".github/workflows/other.yml",
            run_id=123,
            head_sha=SHA,
            latest_attempt_at=None,
        )
    with pytest.raises(ValueError, match="positive"):
        budget.build_attempt_marker(
            now=datetime(2026, 11, 2, tzinfo=UTC),
            workflow_path=SOURCE_PATH,
            run_id=0,
            head_sha=SHA,
            latest_attempt_at=None,
        )


@pytest.mark.parametrize("event", ["schedule", "workflow_run"])
def test_discovery_uses_only_exact_main_marker_and_verifies_parent_run(event):
    artifact_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name={budget.MARKER_ARTIFACT_NAME}"
        "&per_page=100&page=1"
    )
    run_url = f"{budget.GITHUB_API}/actions/runs/123"
    artifact = {
        "id": 99,
        "name": budget.MARKER_ARTIFACT_NAME,
        "expired": False,
        "created_at": "2026-11-01T00:00:00Z",
        "workflow_run": {"id": 123, "head_branch": "main", "head_sha": SHA},
    }
    run = {
        "id": 123,
        "path": SOURCE_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": event,
        "status": "completed",
        "created_at": "2026-11-01T00:00:00Z",
        "updated_at": "2026-11-01T00:01:00Z",
    }
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(url, {"total_count": 1, "artifacts": [artifact]} if url == artifact_url else run)

    latest = budget.discover_latest_download_attempt(token="test-token", workflow_path=SOURCE_PATH, get=get)
    assert latest == datetime(2026, 11, 1, tzinfo=UTC)
    assert [x[0] for x in calls] == [artifact_url, run_url]
    assert all(x[1]["allow_redirects"] is False for x in calls)


def test_other_workflow_marker_does_not_block_requested_workflow():
    marker_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name={budget.MARKER_ARTIFACT_NAME}"
        "&per_page=100&page=1"
    )
    source_run_url = f"{budget.GITHUB_API}/actions/runs/123"
    diagnostic_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name=serie-a-v2-free-real-quote-diagnostic"
        "&per_page=100&page=1"
    )
    marker = {
        "id": 99,
        "name": budget.MARKER_ARTIFACT_NAME,
        "expired": False,
        "created_at": "2026-11-02T05:50:00Z",
        "workflow_run": {"id": 123, "head_branch": "main", "head_sha": SHA},
    }
    source_run = {
        "id": 123,
        "path": SOURCE_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-11-02T05:50:00Z",
        "updated_at": "2026-11-02T05:51:00Z",
    }
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        if url == marker_url:
            return FakeResponse(url, {"artifacts": [marker]})
        if url == source_run_url:
            return FakeResponse(url, source_run)
        if url == diagnostic_url:
            return FakeResponse(url, {"artifacts": []})
        raise AssertionError(f"unexpected GitHub API URL: {url}")

    assert budget.discover_latest_download_attempt(
        token="test-token", workflow_path=DIAGNOSTIC_PATH, get=get
    ) is None
    assert calls == [marker_url, source_run_url, diagnostic_url]


def test_discovery_ignores_non_main_artifact_without_run_lookup():
    artifact_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name={budget.MARKER_ARTIFACT_NAME}"
        "&per_page=100&page=1"
    )
    artifact = {
        "id": 99,
        "name": budget.MARKER_ARTIFACT_NAME,
        "expired": False,
        "created_at": "2026-11-01T00:00:00Z",
        "workflow_run": {"id": 123, "head_branch": "feature", "head_sha": SHA},
    }
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return FakeResponse(url, {"total_count": 1, "artifacts": [artifact]})

    assert budget.discover_latest_download_attempt(token="test-token", workflow_path=SOURCE_PATH, get=get) is None
    assert calls == [artifact_url, f"{budget.GITHUB_API}/actions/artifacts?name=serie-a-v2-current-form-source-capture&per_page=100&page=1"]


@pytest.mark.parametrize("mutation", ["wrong_path", "wrong_sha", "wrong_event", "push_event", "missing_parent"])
def test_bad_main_marker_parent_fails_closed(mutation):
    artifact_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name={budget.MARKER_ARTIFACT_NAME}"
        "&per_page=100&page=1"
    )
    artifact = {
        "id": 99,
        "name": budget.MARKER_ARTIFACT_NAME,
        "expired": False,
        "created_at": "2026-11-01T00:00:00Z",
        "workflow_run": {"id": 123, "head_branch": "main", "head_sha": SHA},
    }
    run = {
        "id": 123,
        "path": SOURCE_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "created_at": "2026-11-01T00:00:00Z",
        "updated_at": "2026-11-01T00:01:00Z",
    }
    if mutation == "wrong_path":
        run["path"] = ".github/workflows/unrelated.yml"
    elif mutation == "wrong_sha":
        run["head_sha"] = "b" * 40
    elif mutation == "wrong_event":
        run["event"] = "pull_request"
    elif mutation == "push_event":
        run["event"] = "push"
    elif mutation == "missing_parent":
        artifact["workflow_run"] = None

    def get(url, **kwargs):
        if url == artifact_url:
            return FakeResponse(url, {"total_count": 1, "artifacts": [artifact]})
        return FakeResponse(url, run)

    with pytest.raises(ValueError):
        budget.discover_latest_download_attempt(token="test-token", workflow_path=SOURCE_PATH, get=get)


def test_api_redirect_or_error_fails_closed():
    def redirect(url, **kwargs):
        return FakeResponse(url + "/redirect", {}, status=302)

    with pytest.raises(ValueError, match="unexpected URL"):
        budget.discover_latest_download_attempt(token="test-token", workflow_path=SOURCE_PATH, get=redirect)

    def error(url, **kwargs):
        return FakeResponse(url, {}, status=503)

    with pytest.raises(RuntimeError, match="HTTP 503"):
        budget.discover_latest_download_attempt(token="test-token", workflow_path=SOURCE_PATH, get=error)


def test_workflow_contracts_keep_crons_and_shared_concurrency():
    root = Path(__file__).resolve().parents[1]
    source = (root / SOURCE_PATH).read_text(encoding="utf-8")
    diagnostic = (root / DIAGNOSTIC_PATH).read_text(encoding="utf-8")

    assert 'cron: "50 5 * * *"' in source
    assert 'cron: "13 6 * * *"' in diagnostic
    assert "group: serie-a-v2-public-source-download-budget" in source
    assert "group: serie-a-v2-public-source-download-budget" in diagnostic
    assert '--workflow-path ".github/workflows/serie-a-v2-current-form-source-capture.yml"' in source
    assert '--workflow-path ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml"' in diagnostic
    for workflow, download_step in (
        (source, "Capture frozen historical seasons plus gated current-form source"),
        (diagnostic, "Fetch and SHA-archive public source, preview original frozen V2 diagnostics"),
    ):
        assert "actions: read" in workflow
        assert "GITHUB_TOKEN: ${{ github.token }}" in workflow
        assert "serie_a_v2_public_source_download_budget.py" in workflow
        assert "serie-a-v2-public-source-download-attempt" in workflow
        assert workflow.index("Upload shared public-source download attempt marker") < workflow.index(download_step)
        assert "steps.public_source_budget.outputs.allowed == 'true'" in workflow
        assert "steps.upload_public_source_budget.outcome == 'success'" in workflow
        assert "The Odds API" not in workflow
        assert "ODDS_API_KEY" not in workflow
    assert "contents: read" in source and "contents: read" in diagnostic
    validation_job = diagnostic.split("  validate-free-diagnostic:\n", 1)[1].split("\n  free-diagnostic:\n", 1)[0]
    assert "if: github.event_name == 'push'" in validation_job
    assert "SUPABASE_URL" not in validation_job
    assert "SUPABASE_KEY" not in validation_job
    assert "GITHUB_TOKEN" not in validation_job
    assert "serie_a_v2_live_diagnostic_report.py" in validation_job
    assert "tests/test_serie_a_v2_public_source_download_budget.py" in validation_job
    diagnostic_job = diagnostic.split("  free-diagnostic:\n", 1)[1].split("\n    steps:", 1)[0]
    assert "if: ${{ github.ref == 'refs/heads/main' && github.event_name != 'push' }}" in diagnostic_job
    assert diagnostic_job.index("if:") < diagnostic_job.index("env:")
    assert "serie_a_v2_public_source_download_budget.py" in source
    assert "tests/test_serie_a_v2_public_source_download_budget.py" in source
    assert "serie_a_v2_public_source_download_budget.py" in diagnostic
    assert "tests/test_serie_a_v2_public_source_download_budget.py" in diagnostic
    assert "if: ${{ steps.rights_preflight.outputs.allowed == 'true' && steps.public_source_budget.outputs.allowed == 'true' && steps.upload_public_source_budget.outcome == 'success' }}" in source

    diagnostic_budget_block = diagnostic.split(
        "      - name: Check shared public-source download budget", 1
    )[1].split(
        "      - name: Upload shared public-source download attempt marker", 1
    )[0]
    assert "if: ${{ steps.rights_preflight.outputs.allowed == 'true' && steps.quote_preflight.outputs.eligible_quote_rows != '0' }}" in diagnostic_budget_block
    diagnostic_archive_block = diagnostic.split(
        "      - name: Archive diagnostic and exact public CSV bytes for provenance", 1
    )[1]
    assert "if: ${{ always() && steps.rights_preflight.outputs.allowed == 'true' && steps.quote_preflight.outputs.eligible_quote_rows != '0' && steps.public_source_budget.outputs.allowed == 'true' && steps.upload_public_source_budget.outcome == 'success' }}" in diagnostic_archive_block
    assert "github.event_name != 'push'" in diagnostic
    assert "if: ${{ github.event_name != 'push' && steps.rights_preflight.outputs.allowed == 'true' && steps.quote_preflight.outputs.eligible_quote_rows != '0' && steps.public_source_budget.outputs.allowed == 'true' && steps.upload_public_source_budget.outcome == 'success' }}" in diagnostic



def test_discovery_bootstraps_cooldown_from_latest_existing_main_source_artifact():
    marker_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name={budget.MARKER_ARTIFACT_NAME}"
        "&per_page=100&page=1"
    )
    source_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name=serie-a-v2-current-form-source-capture"
        "&per_page=100&page=1"
    )
    diagnostic_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name=serie-a-v2-free-real-quote-diagnostic"
        "&per_page=100&page=1"
    )
    source_artifacts = [
        {
            "id": 13231843819,
            "name": "serie-a-v2-current-form-source-capture",
            "expired": False,
            "created_at": "2026-11-03T13:02:59Z",
            "workflow_run": {"id": 41640753996, "head_branch": "main", "head_sha": SHA},
        },
        {
            "id": 13327281383,
            "name": "serie-a-v2-current-form-source-capture",
            "expired": False,
            "created_at": "2026-11-04T13:19:46Z",
            "workflow_run": {"id": 41836971469, "head_branch": "main", "head_sha": SHA},
        },
        {
            "id": 13418048952,
            "name": "serie-a-v2-current-form-source-capture",
            "expired": False,
            "created_at": "2026-11-05T13:31:55Z",
            "workflow_run": {"id": 42036450692, "head_branch": "main", "head_sha": SHA},
        },
        {
            "id": 13504817564,
            "name": "serie-a-v2-current-form-source-capture",
            "expired": False,
            "created_at": "2026-11-06T13:17:15Z",
            "workflow_run": {"id": 42224162373, "head_branch": "main", "head_sha": SHA},
        },
    ]
    diagnostic_artifacts = [
        {
            "id": 13236383688,
            "name": "serie-a-v2-free-real-quote-diagnostic",
            "expired": False,
            "created_at": "2026-11-03T14:05:06Z",
            "workflow_run": {"id": 41650074683, "head_branch": "main", "head_sha": SHA},
        },
        {
            "id": 13332260799,
            "name": "serie-a-v2-free-real-quote-diagnostic",
            "expired": False,
            "created_at": "2026-11-04T14:25:54Z",
            "workflow_run": {"id": 41847314320, "head_branch": "main", "head_sha": SHA},
        },
        {
            "id": 13424482168,
            "name": "serie-a-v2-free-real-quote-diagnostic",
            "expired": False,
            "created_at": "2026-11-05T14:33:47Z",
            "workflow_run": {"id": 42046051819, "head_branch": "main", "head_sha": SHA},
        },
        {
            "id": 13510280643,
            "name": "serie-a-v2-free-real-quote-diagnostic",
            "expired": False,
            "created_at": "2026-11-06T14:11:58Z",
            "workflow_run": {"id": 42231648250, "head_branch": "main", "head_sha": SHA},
        },
    ]
    source_run = {
        "id": 41836971469,
        "path": SOURCE_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-11-04T13:18:57Z",
        "updated_at": "2026-11-04T13:19:49Z",
    }
    diagnostic_run = {
        "id": 41847314320,
        "path": DIAGNOSTIC_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-11-04T14:24:55Z",
        "updated_at": "2026-11-04T14:25:58Z",
    }
    source_run_latest = {
        "id": 42224162373,
        "path": SOURCE_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-11-06T13:16:23Z",
        "updated_at": "2026-11-06T13:17:18Z",
    }
    diagnostic_run_latest = {
        "id": 42231648250,
        "path": DIAGNOSTIC_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-11-06T14:11:04Z",
        "updated_at": "2026-11-06T14:12:00Z",
    }
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        if url == marker_url:
            return FakeResponse(url, {"artifacts": []})
        if url == source_url:
            return FakeResponse(url, {"artifacts": source_artifacts})
        if url == diagnostic_url:
            return FakeResponse(url, {"artifacts": diagnostic_artifacts})
        if url.endswith("/actions/runs/42224162373"):
            return FakeResponse(url, source_run_latest)
        if url.endswith("/actions/runs/42231648250"):
            return FakeResponse(url, diagnostic_run_latest)
        if url.endswith("/actions/runs/41836971469"):
            return FakeResponse(url, source_run)
        if url.endswith("/actions/runs/41847314320"):
            return FakeResponse(url, diagnostic_run)
        raise AssertionError(f"unexpected GitHub API URL: {url}")

    latest = budget.discover_latest_download_attempt(token="test-token", workflow_path=DIAGNOSTIC_PATH, get=get)
    assert latest == datetime(2026, 11, 6, 14, 11, 58, tzinfo=UTC)
    assert "football-data.co.uk" not in " ".join(calls)
    assert calls == [marker_url, diagnostic_url, f"{budget.GITHUB_API}/actions/runs/42231648250"]
    allowed, next_allowed = budget.decide_download_permission(
        now=datetime(2026, 11, 6, 15, 0, tzinfo=UTC), latest_attempt_at=latest
    )
    assert allowed is False
    assert next_allowed == datetime(2026, 11, 13, 16, 11, 58, tzinfo=UTC)

    # The source-capture slot must select the latest of multiple legacy main artifacts.
    calls.clear()
    source_latest = budget.discover_latest_download_attempt(
        token="test-token", workflow_path=SOURCE_PATH, get=get
    )
    assert source_latest == datetime(2026, 11, 6, 13, 17, 15, tzinfo=UTC)
    assert calls == [marker_url, source_url, f"{budget.GITHUB_API}/actions/runs/42224162373"]
    source_allowed, source_next_allowed = budget.decide_download_permission(
        now=datetime(2026, 11, 6, 14, 0, tzinfo=UTC), latest_attempt_at=source_latest
    )
    assert source_allowed is False
    assert source_next_allowed == datetime(2026, 11, 13, 15, 17, 15, tzinfo=UTC)


def test_discovery_bootstrap_rejects_legacy_artifact_from_wrong_workflow():
    marker_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name={budget.MARKER_ARTIFACT_NAME}"
        "&per_page=100&page=1"
    )
    source_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name=serie-a-v2-current-form-source-capture"
        "&per_page=100&page=1"
    )
    diagnostic_url = (
        f"{budget.GITHUB_API}/actions/artifacts?name=serie-a-v2-free-real-quote-diagnostic"
        "&per_page=100&page=1"
    )
    artifact = {
        "id": 13236383688,
        "name": "serie-a-v2-free-real-quote-diagnostic",
        "expired": False,
        "created_at": "2026-11-03T14:05:06Z",
        "workflow_run": {"id": 41650074683, "head_branch": "main", "head_sha": SHA},
    }
    bad_run = {
        "id": 41650074683,
        "path": SOURCE_PATH,
        "head_branch": "main",
        "head_sha": SHA,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-11-03T14:04:13Z",
        "updated_at": "2026-11-03T14:05:09Z",
    }

    def get(url, **kwargs):
        if url == marker_url:
            return FakeResponse(url, {"artifacts": []})
        if url == diagnostic_url:
            return FakeResponse(url, {"artifacts": [artifact]})
        if url.endswith("/actions/runs/41650074683"):
            return FakeResponse(url, bad_run)
        raise AssertionError(f"unexpected GitHub API URL: {url}")

    with pytest.raises(ValueError, match="approved main source workflow"):
        budget.discover_latest_download_attempt(token="test-token", workflow_path=DIAGNOSTIC_PATH, get=get)

def test_current_form_forward_reader_does_not_run_on_push_validation():
    root = Path(__file__).resolve().parents[1]
    forward = (root / ".github" / "workflows" / "serie-a-v2-current-form-forward-preview.yml").read_text(encoding="utf-8")
    job = forward.split("  current-form-forward-preview:\n", 1)[1].split("\n    runs-on:", 1)[0]
    assert "github.ref == 'refs/heads/main'" in job
    assert "github.event_name == 'schedule'" in job
    assert "github.event_name == 'workflow_dispatch'" in job
    assert "github.event_name == 'workflow_run'" in job
    assert "github.event.workflow_run.event == 'schedule'" in job
    assert "github.event.workflow_run.event == 'workflow_dispatch'" in job
    assert "github.event_name != 'workflow_run'" not in job
    assert "github.event.workflow_run.event != 'pull_request'" not in job


def test_fresh_source_refresh_skips_budget_reservation_and_public_download():
    root = Path(__file__).resolve().parents[1]
    source = (root / SOURCE_PATH).read_text(encoding="utf-8")
    preflight = source.index("Check existing verified source before diagnostic-triggered refresh")
    budget_step = source.index("Check shared public-source download budget")
    marker_step = source.index("Upload shared public-source download attempt marker")
    capture_step = source.index("Capture frozen historical seasons plus gated current-form source")
    assert preflight < budget_step < marker_step < capture_step
    budget_block = source[budget_step:marker_step]
    assert "if: ${{ steps.rights_preflight.outputs.allowed == 'true' && steps.source_refresh.outputs.capture != 'false' }}" in budget_block
    assert "steps.source_refresh.outputs.capture != 'false'" in source
    assert "steps.public_source_budget.outputs.allowed == 'true'" in source
    assert "steps.upload_public_source_budget.outcome == 'success'" in source
