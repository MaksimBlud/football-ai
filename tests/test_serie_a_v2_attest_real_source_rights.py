"""Original V2 source attestation must fail before archive discovery without provider rights."""
from datetime import datetime, timezone

import pytest

import market_anchor_v2_direct_access as direct_access
from serie_a_v2_attest_real_source import attest_latest_source


def test_source_attestation_denies_before_discovery_or_archive_callbacks(monkeypatch):
    monkeypatch.setenv("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "true")
    calls = []

    def deny():
        raise PermissionError("provider source-capture scope is unresolved")

    monkeypatch.setattr(direct_access, "require_v2_source_capture_access", deny)

    with pytest.raises(PermissionError, match="source-capture scope is unresolved"):
        attest_latest_source(
            token="synthetic-token",
            now=datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc),
            discover=lambda **kwargs: calls.append("discover"),
            load=lambda *args, **kwargs: calls.append("load"),
            verify_run=lambda *args, **kwargs: calls.append("verify"),
        )

    assert calls == []
