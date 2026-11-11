from __future__ import annotations

from pathlib import Path
import inspect

import market_anchor_v2_artifact_privacy as privacy

import pytest

from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts


class _PrivacyResponse:
    def __init__(self, payload, *, status_code=200, url=None):
        self._payload = payload
        self.status_code = status_code
        self.url = url or "https://api.github.com/repos/MaksimBlud/football-ai"

    def json(self):
        return self._payload


def test_public_repository_blocks_source_artifact_access(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _PrivacyResponse({"full_name": "MaksimBlud/football-ai", "private": False})

    monkeypatch.setattr(privacy.requests, "get", fake_get)
    with pytest.raises(PermissionError, match="require a private GitHub repository"):
        require_private_repository_for_source_artifacts(
            "MaksimBlud/football-ai", "synthetic-token"
        )
    assert len(calls) == 1
    assert calls[0][0] == "https://api.github.com/repos/MaksimBlud/football-ai"
    assert calls[0][1]["allow_redirects"] is False


def test_private_repository_allows_only_exact_authenticated_metadata_target(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _PrivacyResponse({"full_name": "MaksimBlud/football-ai", "private": True})

    monkeypatch.setattr(privacy.requests, "get", fake_get)
    result = require_private_repository_for_source_artifacts(
        "MaksimBlud/football-ai", "synthetic-token"
    )
    assert result == {
        "repository": "MaksimBlud/football-ai",
        "private": True,
        "storage_policy": "PRIVATE_GITHUB_ACTIONS_ARTIFACTS",
    }
    assert len(calls) == 1
    assert calls[0][1]["headers"]["Authorization"] == "Bearer synthetic-token"


def test_privacy_lookup_fails_closed_on_redirect_wrong_identity_and_http_error(monkeypatch):
    def wrong_identity(url, **kwargs):
        return _PrivacyResponse({"full_name": "someone/else", "private": True})

    monkeypatch.setattr(privacy.requests, "get", wrong_identity)
    with pytest.raises(PermissionError, match="identity does not match"):
        require_private_repository_for_source_artifacts(
            "MaksimBlud/football-ai", "synthetic-token"
        )

    def redirect(url, **kwargs):
        return _PrivacyResponse(
            {"full_name": "MaksimBlud/football-ai", "private": True},
            url="https://api.github.com/repos/other/football-ai",
        )

    monkeypatch.setattr(privacy.requests, "get", redirect)
    with pytest.raises(PermissionError, match="lookup failed"):
        require_private_repository_for_source_artifacts(
            "MaksimBlud/football-ai", "synthetic-token"
        )

    def unavailable(url, **kwargs):
        return _PrivacyResponse({}, status_code=503)

    monkeypatch.setattr(privacy.requests, "get", unavailable)
    with pytest.raises(PermissionError, match="lookup failed"):
        require_private_repository_for_source_artifacts(
            "MaksimBlud/football-ai", "synthetic-token"
        )


def test_missing_repository_or_token_blocks_without_network(monkeypatch):
    calls = []

    def forbidden_get(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("privacy lookup must not run without validated identity and token")

    monkeypatch.setattr(privacy.requests, "get", forbidden_get)
    with pytest.raises(PermissionError, match="identity is missing or malformed"):
        require_private_repository_for_source_artifacts(
            "bad-repository", "synthetic-token"
        )
    with pytest.raises(PermissionError, match="GitHub token is required"):
        require_private_repository_for_source_artifacts(
            "MaksimBlud/football-ai", ""
        )
    assert calls == []


def test_all_live_v2_workflows_require_rights_then_private_storage_before_source_access():
    root = Path(__file__).resolve().parents[1]
    cases = {
        ".github/workflows/serie-a-v2-current-form-source-capture.yml": (
            "Check existing verified source before diagnostic-triggered refresh",
            "Check shared public-source download budget",
        ),
        ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml": (
            "Check shared public-source download budget",
            "Fetch and SHA-archive public source, preview original frozen V2 diagnostics",
        ),
        ".github/workflows/serie-a-v2-forward-preview.yml": (
            "Attest original historical source ZIP from real GitHub Actions (no quotes read)",
            "Generate actual original frozen V2 source-verified read-only preview",
        ),
        ".github/workflows/serie-a-v2-current-form-forward-preview.yml": (
            "Generate read-only current-form V2 shadow from already saved quotes",
        ),
    }
    for relative, downstream_steps in cases.items():
        source = (root / relative).read_text(encoding="utf-8")
        rights_gate = (
            "require_personal_research_source_capture_scope()"
            if relative.endswith("serie-a-v2-current-form-source-capture.yml")
            else "require_personal_research_inference_scope()"
        )
        rights_call = source.index(rights_gate)
        privacy_call = source.index("require_private_repository_for_source_artifacts()")
        assert rights_call < privacy_call, f"{relative} must establish provider rights first"
        for step in downstream_steps:
            assert privacy_call < source.index(step), (
                f"{relative}: private storage gate must precede {step!r}"
            )
        assert "GITHUB_TOKEN: ${{ github.token }}" in source
        assert "GITHUB_REPOSITORY: ${{ github.repository }}" in source


def test_every_live_v2_artifact_upload_is_guarded_by_private_storage_preflight():
    """A failed privacy preflight must not publish even a partial source artifact."""
    root = Path(__file__).resolve().parents[1]
    workflows = (
        ".github/workflows/serie-a-v2-current-form-source-capture.yml",
        ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
        ".github/workflows/serie-a-v2-forward-preview.yml",
        ".github/workflows/serie-a-v2-current-form-forward-preview.yml",
    )
    for relative in workflows:
        lines = (root / relative).read_text(encoding="utf-8").splitlines()
        upload_indexes = [
            index for index, line in enumerate(lines)
            if "uses: actions/upload-artifact@v4" in line
        ]
        assert upload_indexes, f"{relative} must expose its artifact-upload steps for audit"
        for upload_index in upload_indexes:
            starts = [
                index for index in range(upload_index)
                if lines[index].startswith("      - name:")
            ]
            assert starts, f"{relative}: upload step has no enclosing named step"
            step_start = starts[-1]
            step_end = next(
                (
                    index for index in range(upload_index + 1, len(lines))
                    if lines[index].startswith("      - name:")
                ),
                len(lines),
            )
            step = "\\n".join(lines[step_start:step_end])
            assert "if:" in step, f"{relative}: artifact upload must have an explicit condition"
            assert "steps.rights_preflight.outputs.allowed == 'true'" in step, (
                f"{relative}: artifact upload is not disabled when private-storage preflight blocks"
            )


def test_private_storage_gate_does_not_accept_caller_supplied_http_transport():
    assert "get" not in inspect.signature(require_private_repository_for_source_artifacts).parameters

def test_privacy_lookup_fails_closed_when_success_response_omits_url(monkeypatch):
    class ResponseWithoutUrl:
        status_code = 200

        def json(self):
            return {"full_name": "MaksimBlud/football-ai", "private": True}

    monkeypatch.setattr(
        privacy.requests,
        "get",
        lambda url, **kwargs: ResponseWithoutUrl(),
    )
    with pytest.raises(PermissionError, match="lookup failed"):
        require_private_repository_for_source_artifacts(
            "MaksimBlud/football-ai", "synthetic-token"
        )

