"""Direct-entrypoint rights regressions for original MARKET_ANCHOR_1X2_V2.

All tests are synthetic. The real checked-in Football-Data manifest remains HOLD.
"""
import json
import sys
from datetime import datetime, timezone

import pytest

import market_anchor_v2_direct_access
import serie_a_v2_attest_real_source as attestation
import serie_a_v2_forward_capture as forward_capture


NOW = datetime(2026, 10, 14, 16, tzinfo=timezone.utc)


def _deny_inference(calls):
    def deny():
        calls.append("inference-rights")
        raise PermissionError("provider inference scope is unresolved")
    return deny


def _deny_capture(calls):
    def deny():
        calls.append("source-capture-rights")
        raise PermissionError("provider source-capture scope is unresolved")
    return deny


def _allow_live(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")


def test_forward_preparation_denies_before_iterating_quote_or_archive_inputs(monkeypatch):
    _allow_live(monkeypatch)
    calls = []
    monkeypatch.setattr(
        market_anchor_v2_direct_access,
        "require_v2_inference_access",
        _deny_inference(calls),
    )

    class Poison:
        def __iter__(self):
            raise AssertionError("input must not be touched before rights clearance")

    with pytest.raises(PermissionError, match="inference scope"):
        forward_capture.prepare_forward_capture(
            Poison(), Poison(), as_of_utc=NOW,
            load_archive=lambda *_: b"",
            verify_parent_run=lambda *_: {},
        )
    assert calls == ["inference-rights"]


def test_source_preflight_denies_before_any_callback(monkeypatch):
    _allow_live(monkeypatch)
    calls = []
    monkeypatch.setattr(
        market_anchor_v2_direct_access,
        "require_v2_inference_access",
        _deny_inference(calls),
    )
    callbacks = []

    with pytest.raises(PermissionError, match="inference scope"):
        forward_capture.capture_forward_with_source_preflight(
            [],
            as_of_utc=NOW,
            fetch_quotes=lambda: callbacks.append("quotes"),
            load_archive=lambda *_: callbacks.append("archive"),
            verify_parent_run=lambda *_: callbacks.append("parent"),
        )
    assert calls == ["inference-rights"]
    assert callbacks == []


@pytest.mark.parametrize(
    "operation",
    [
        lambda get: forward_capture._github_json(
            forward_capture.GITHUB_API + "/actions/artifacts",
            token="synthetic-token", get=get,
        ),
        lambda get: forward_capture.verify_source_run(
            {}, quote_time=NOW, token="synthetic-token", get=get,
        ),
        lambda get: forward_capture.get_archive(
            123, token="synthetic-token", get=get,
        ),
        lambda get: forward_capture.require_private_repository(
            token="synthetic-token", get=get,
        ),
    ],
)
def test_forward_github_entrypoints_deny_before_http(monkeypatch, operation):
    _allow_live(monkeypatch)
    rights_calls = []
    http_calls = []
    monkeypatch.setattr(
        market_anchor_v2_direct_access,
        "require_v2_inference_access",
        _deny_inference(rights_calls),
    )

    def forbidden_http(*args, **kwargs):
        http_calls.append((args, kwargs))
        raise AssertionError("HTTP must not run before provider rights clearance")

    with pytest.raises(PermissionError, match="inference scope"):
        operation(forbidden_http)
    assert rights_calls == ["inference-rights"]
    assert http_calls == []


def test_forward_cli_writes_metadata_only_block_before_archive_or_supabase(monkeypatch, tmp_path):
    _allow_live(monkeypatch)
    monkeypatch.setenv("GITHUB_REPOSITORY", forward_capture.REPOSITORY)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    output = tmp_path / "reports" / "blocked.json"
    sources = tmp_path / "source-zips"
    monkeypatch.setattr(sys, "argv", [
        "serie_a_v2_forward_capture.py",
        "--output", str(output),
        "--sources-output-dir", str(sources),
    ])
    rights_calls = []
    monkeypatch.setattr(
        market_anchor_v2_direct_access,
        "require_v2_inference_access",
        _deny_inference(rights_calls),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("archive discovery must not run while rights are unresolved")

    monkeypatch.setattr(forward_capture, "discover_archives", forbidden)
    forward_capture.main()

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE"
    assert report["supabase_reads"] == 0
    assert report["supabase_writes"] == 0
    assert report["quotes_read"] == 0
    assert report["forecasts_created"] == 0
    assert report["paid_provider_calls"] == 0
    assert rights_calls == ["inference-rights"]
    assert not sources.exists()


def test_source_attestation_denies_before_discovery_or_archive_callbacks(monkeypatch):
    calls = []
    monkeypatch.setattr(
        market_anchor_v2_direct_access,
        "require_v2_source_capture_access",
        _deny_capture(calls),
    )
    with pytest.raises(PermissionError, match="source-capture scope"):
        attestation.attest_latest_source(
            token="synthetic-token",
            now=NOW,
            discover=lambda **kwargs: pytest.fail("archive discovery must not run"),
            load=lambda *args, **kwargs: pytest.fail("archive download must not run"),
            verify_run=lambda *args, **kwargs: pytest.fail("parent lookup must not run"),
        )
    assert calls == ["source-capture-rights"]


def test_source_attestation_cli_denies_before_token_or_network(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", forward_capture.REPOSITORY)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    output = tmp_path / "attestation.json"
    monkeypatch.setattr(sys, "argv", ["serie_a_v2_attest_real_source.py", "--output", str(output)])
    calls = []
    monkeypatch.setattr(
        market_anchor_v2_direct_access,
        "require_v2_source_capture_access",
        _deny_capture(calls),
    )
    with pytest.raises(PermissionError, match="source-capture scope"):
        attestation.main()
    assert calls == ["source-capture-rights"]
    assert not output.exists()
