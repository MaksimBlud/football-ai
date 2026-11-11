"""Fail-closed confidentiality gate for V2 source artifacts in GitHub Actions.

Provider rights and repository privacy are separate requirements. This module
checks only GitHub repository metadata; it does not read source, quotes, or
model data and does not mutate repository settings.
"""
from __future__ import annotations

import os
import re

import requests


def require_private_repository_for_source_artifacts(
    repository: str | None = None,
    token: str | None = None,
) -> dict:
    """Require the exact source-artifact repository to be private.

    A public repository exposes Actions artifacts to repository readers. SHA
    digests prove integrity, not confidentiality. Missing credentials, redirects,
    lookup errors, identity mismatches, and public repositories all fail closed.
    """
    repo = repository if repository is not None else os.environ.get("GITHUB_REPOSITORY", "")
    credential = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
    if not isinstance(repo, str) or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) is None:
        raise PermissionError("source archive repository identity is missing or malformed")
    if not isinstance(credential, str) or not credential.strip():
        raise PermissionError("GitHub token is required to verify private source-archive storage")

    url = f"https://api.github.com/repos/{repo}"
    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {credential}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=15,
            allow_redirects=False,
        )
    except Exception as exc:
        raise PermissionError(
            "GitHub repository privacy could not be verified; source archive access is blocked"
        ) from exc

    if getattr(response, "status_code", None) != 200 or getattr(response, "url", None) != url:
        raise PermissionError(
            "GitHub repository privacy lookup failed; source archive access is blocked"
        )
    try:
        payload = response.json()
    except Exception as exc:
        raise PermissionError(
            "GitHub repository privacy response is invalid; source archive access is blocked"
        ) from exc
    if not isinstance(payload, dict):
        raise PermissionError("GitHub repository privacy response is not an object")
    canonical_name = payload.get("full_name")
    if not isinstance(canonical_name, str) or canonical_name.casefold() != repo.casefold():
        raise PermissionError(
            "GitHub repository identity does not match the configured source archive target"
        )
    if payload.get("private") is not True:
        raise PermissionError(
            "source archives require a private GitHub repository; public Actions artifacts are visible to repository readers"
        )
    return {
        "repository": canonical_name,
        "private": True,
        "storage_policy": "PRIVATE_GITHUB_ACTIONS_ARTIFACTS",
    }
